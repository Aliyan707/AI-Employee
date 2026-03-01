# Phase 0 Research: CS AI FTE — 24/7 Customer Success Agent

**Date**: 2026-03-01 | **Branch**: `001-cs-ai-fte`

---

## 1. Cross-Channel Customer Identity Resolution

**Decision**: `customer_identifiers` lookup table with a normalised identifier
type enum, joined against a central `customers` record.

**Rationale**: A single `customers` row stores canonical data (name, company,
created_at). All contact methods — email, phone, WhatsApp sender ID,
web-session fingerprint — are stored as rows in `customer_identifiers`
pointing back to `customers.id`. On any new inbound message, the agent
performs a single indexed lookup by `(identifier_type, identifier_value)`.
If found, the existing `customer_id` is used. If not found, a new
`customers` row is created and the new identifier is inserted.

**Resolution flow**:
```
inbound message arrives
  └─ extract identifiers (email, phone, wa_id)
  └─ SELECT customer_id FROM customer_identifiers
       WHERE (type, value) IN (list)
       LIMIT 1
  ├─ FOUND → use customer_id
  │          INSERT new identifier if it wasn't already linked
  └─ NOT FOUND → INSERT customers, INSERT customer_identifiers
                 return new customer_id
```

**95% accuracy target**: Achieved by normalising phone numbers to E.164
format on write and by case-lowercasing emails. A merge-request flow
(FR-008) handles the rare mismatch case.

**Alternatives considered**:
- External identity graph (Segment, mParticle) — rejected: adds vendor
  dependency, unnecessary for single-product SaaS at hackathon scale.
- Fuzzy matching on name — rejected: high false-positive rate, name changes.

---

## 2. OpenAI Agents SDK Sub-Agent Decomposition

**Decision**: One orchestrator agent + three specialised sub-agents, each
mapped to a distinct pipeline responsibility.

| Sub-agent | Responsibility | Key tool |
|-----------|---------------|----------|
| `OrchestratorAgent` | Drives 7-step pipeline, delegates | All tools |
| `SentimentAgent` | Scores sentiment 0.0–1.0 | `analyze_sentiment` |
| `KBAgent` | Semantic search over knowledge base | `search_knowledge_base` |
| `EscalationAgent` | Applies guardrail rules, decides | `escalate_to_human` |

Steps 2 (`get_customer_history`) and 3 (`search_knowledge_base`) can run in
parallel after step 1 confirms ticket creation, reducing p95 latency.

**Rationale**: Isolation per sub-agent enables independent testing, swapping
the embedding model without touching escalation logic, and tracing failures
to a specific agent boundary.

**Alternatives considered**:
- Single monolithic agent — rejected: hard to test escalation rules in
  isolation; makes SLO debugging opaque.
- Four fully peer agents with message passing — rejected: over-engineered for
  a 48-72 hour hackathon; orchestrator pattern is simpler.

---

## 3. Kafka Topic Design

**Decision**: Four topics, partitioned by channel.

| Topic | Partitions | Retention | Purpose |
|-------|-----------|-----------|---------|
| `cs.intake` | 3 (one per channel) | 24 h | All inbound messages |
| `cs.response` | 3 | 1 h | Outbound responses queued for send |
| `cs.escalation` | 1 | 7 days | Escalation events (audit trail) |
| `cs.metrics` | 1 | 30 days | Agent pipeline timing & status |

**Consumer groups**:
- `intake-worker` — reads `cs.intake`, drives the 7-step pipeline.
- `response-worker` — reads `cs.response`, dispatches to channel sender.
- `metrics-worker` — reads `cs.metrics`, writes to `agent_metrics` table.

**Rationale**: Separating intake from response decouples message receipt
from send latency. `cs.escalation` having 7-day retention supports the
audit trail (FR-026) without hitting the main DB on every alert query.

**Alternatives considered**:
- Single topic with message-type field — rejected: makes consumer-group
  filtering more complex and mixes retention requirements.
- Redis Streams — rejected: weaker delivery guarantees; not specified in
  user requirements.

---

## 4. pgvector Embedding Strategy

**Decision**: `text-embedding-3-small` (1536 dims), cosine similarity,
HNSW index on `knowledge_base.embedding`, similarity threshold ≥ 0.75.

**Storage**: `knowledge_base.embedding VECTOR(1536)`.

**Search query pattern**:
```sql
SELECT id, title, content, 1 - (embedding <=> $query_vec) AS score
FROM knowledge_base
ORDER BY embedding <=> $query_vec
LIMIT 5;
```
Filter `score >= 0.75` in application layer; if zero results pass threshold,
treat as KB miss (FR-011).

**Rationale**: `text-embedding-3-small` balances cost and quality for
FAQ-scale corpora (hundreds to low thousands of articles). HNSW index gives
sub-100ms retrieval at that scale, meeting the 500ms KB SLO.

**Alternatives considered**:
- `text-embedding-3-large` — rejected: 3× cost, negligible quality gain for
  structured product docs at hackathon scope.
- Separate vector DB (Pinecone, Weaviate) — rejected: adds operational
  complexity; PostgreSQL + pgvector sufficient for this scale.

---

## 5. Idempotency Strategy

**Decision**: Idempotency keys stored in `idempotency_keys` table with
`(key, expires_at)`.

- `create_ticket`: key = SHA-256(`customer_id + channel + message_hash + minute_bucket`).
  Within same 60-second window, duplicate key returns existing ticket ID.
- `send_response`: key = SHA-256(`ticket_id + response_hash`).
  If key exists and status = "sent", skip send and return 200.

**Rationale**: The 60-second deduplication window (FR-022) prevents the
common case of a customer double-sending. Hashing the message content
catches exact duplicates even if they arrive slightly outside the window.

---

## 6. Error Handling & Retry Strategy (Constitution Error Taxonomy)

| Code | Trigger | Retry | After Retry |
|------|---------|-------|-------------|
| E001 | Tool timeout (>3s) | 1× after 500ms | Escalate with reason=timeout |
| E002 | DB / KB row not found | None | Proceed with empty context |
| E003 | Guardrail rule hit | None | Escalate immediately |
| E004 | Channel format validation fail | 1× reformat | Escalate with reason=format |
| E005 | Auth failure (API key, OAuth) | None | Alert + escalate |

Circuit breaker: 3 consecutive E001s on any tool → bypass that tool for
60s, route to human.

---

## 7. Monitoring: `agent_metrics` Table

Columns:
```
id              BIGSERIAL PK
ticket_id       UUID NOT NULL FK
tool_name       VARCHAR(64)
channel         VARCHAR(16)
input_hash      CHAR(64)     -- SHA-256, for dedup detection
output_status   VARCHAR(16)  -- success | error_code
duration_ms     INTEGER
error_code      VARCHAR(8)   -- E001..E005 or NULL
created_at      TIMESTAMPTZ  DEFAULT NOW()
```

Daily report query aggregates from this table for escalation rate and
mean processing time alongside ticket and sentiment data.

---

## 8. Channel Format Adapter

**Decision**: Single `format_for_channel(raw: str, channel: Channel) -> str`
pure function, enforced by the `FormatAgent` step (step 6 of the pipeline).

```python
CHANNEL_RULES = {
    "email":    {"max_words": 500, "tone": "formal",        "markdown": True},
    "whatsapp": {"max_chars": 300, "tone": "conversational","markdown": False},
    "webform":  {"max_words": 300, "tone": "semi-formal",   "markdown": True},
}
```

If the LLM-generated draft exceeds limits, the orchestrator calls the LLM
**once** with a trim prompt specifying the exact remaining word/char budget.
If the second attempt still fails, E004 fires.

**Rationale**: A pure function is independently unit-testable and cannot
accidentally skip channel enforcement — it is the only path between raw
LLM output and `send_response`.
