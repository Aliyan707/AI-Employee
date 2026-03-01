# Implementation Plan: CS AI FTE — 24/7 Customer Success Agent

**Branch**: `001-cs-ai-fte` | **Date**: 2026-03-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-cs-ai-fte/spec.md`

---

## Summary

Build a production-grade, 24/7 AI customer success agent that receives
inquiries from Gmail, WhatsApp (Twilio), and a React/Next.js web form;
routes them through a strict 7-step pipeline; resolves customer identity
across channels via a PostgreSQL CRM; searches a pgvector-indexed knowledge
base; enforces hard escalation guardrails; and delivers channel-formatted
responses in under 3 seconds — all orchestrated by the OpenAI Agents SDK
with sub-agent specialisation and deployed on Docker + Kubernetes.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node.js 20 (web form)
**Primary Dependencies**:
- FastAPI 0.115 (API layer + webhook receivers)
- OpenAI Agents SDK + gpt-4o (agent orchestration)
- aiokafka 0.11 (async Kafka producer/consumer)
- SQLAlchemy 2.0 + asyncpg (ORM + async PostgreSQL driver)
- pgvector 0.3 (Python client for vector operations)
- Next.js 14 / React 18 (web support form only)

**Storage**: PostgreSQL 16 + pgvector extension (single source of truth)
**Testing**: pytest + pytest-asyncio (backend), Jest (frontend)
**Target Platform**: Linux containers (Docker + Kubernetes, K8s 1.29+)
**Project Type**: Web application (FastAPI backend + minimal Next.js frontend)
**Performance Goals**:
- End-to-end pipeline: < 3s p95
- KB semantic search: < 500ms
- Ticket creation success: > 99.5%

**Constraints**:
- No external CRM (PostgreSQL only — Constitution Principle IV)
- Escalation rate target: < 20%
- Cross-channel ID accuracy: > 95%
- Response limits: Email ≤ 500 words, WhatsApp ≤ 300 chars, Web ≤ 300 words
- Hackathon scope: 48–72 hours → MVP-first, no multi-tenant, English only

**Scale/Scope**: Single SaaS product, ~hundreds of concurrent users,
English-only at launch, single-region Kubernetes deployment.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Multi-Channel Adaptive Response | Three channels implemented; `format_for_channel` enforces per-channel limits at step 6 | ✅ PASS |
| II. Strict Workflow Order | 7-step pipeline hardcoded in `OrchestratorAgent`; no step skippable | ✅ PASS |
| III. Hard Guardrails & Escalation | `EscalationAgent` checks all 7 guardrail categories before step 6; `send_response` blocked on guardrail hit | ✅ PASS |
| IV. PostgreSQL-First CRM | All data in PostgreSQL; no Salesforce/HubSpot integration | ✅ PASS |
| V. Performance SLOs | p95 < 3s via parallel steps 2–3; HNSW index for KB; `agent_metrics` for monitoring | ✅ PASS |
| VI. Incubation → Specialisation | Phase 1 = prototype with mock data; Phase 2 = OpenAI Agents SDK production | ✅ PASS |
| VII. AI Agent Reliability | Idempotency keys on `create_ticket` + `send_response`; E001–E005 taxonomy; structured logging | ✅ PASS |

**All gates pass. Proceeding to Phase 0.**

---

## Project Structure

### Documentation (this feature)

```text
specs/001-cs-ai-fte/
├── plan.md           ← this file
├── research.md       ← Phase 0 decisions
├── data-model.md     ← database schema
├── quickstart.md     ← local dev guide
├── contracts/
│   ├── agent-tools.md       ← tool input/output contracts
│   ├── api.openapi.yaml     ← REST API OpenAPI spec
│   └── kafka-schemas.md     ← Kafka topic message schemas
└── tasks.md          ← Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
cs-ai-fte/
├── agent/
│   ├── orchestrator.py          # OrchestratorAgent — drives 7-step pipeline
│   ├── sub_agents/
│   │   ├── sentiment_agent.py   # SentimentAgent (analyze_sentiment tool)
│   │   ├── kb_agent.py          # KBAgent (search_knowledge_base tool)
│   │   └── escalation_agent.py  # EscalationAgent (escalate_to_human tool)
│   └── tools/
│       ├── create_ticket.py
│       ├── get_customer_history.py
│       ├── search_knowledge_base.py
│       ├── analyze_sentiment.py
│       ├── escalate_to_human.py
│       ├── send_response.py
│       └── format_for_channel.py  # pure function, not an SDK tool
│
├── channels/
│   ├── gmail/
│   │   ├── reader.py    # Gmail push notification decoder
│   │   └── sender.py    # Gmail reply sender (thread-aware)
│   ├── whatsapp/
│   │   ├── webhook.py   # Twilio signature validation + decode
│   │   └── sender.py    # Twilio API send
│   └── webform/
│       └── handler.py   # Web form payload normaliser
│
├── workers/
│   ├── intake_worker.py    # Consumes cs.intake → runs pipeline
│   ├── response_worker.py  # Consumes cs.response → calls channel sender
│   ├── metrics_worker.py   # Consumes cs.metrics → writes agent_metrics
│   └── report_worker.py    # APScheduler job → daily report at 07:00
│
├── api/
│   ├── main.py              # FastAPI app factory + lifespan
│   ├── routers/
│   │   ├── webhooks.py      # POST /webhooks/{gmail,whatsapp,webform}
│   │   ├── tickets.py       # GET /tickets/{id}
│   │   ├── customers.py     # GET /customers/{id}/history
│   │   └── reports.py       # GET/POST /reports/daily/...
│   └── middleware/
│       ├── auth.py          # API key / HMAC validation
│       └── logging.py       # Structured JSON request logging
│
├── database/
│   ├── models.py            # SQLAlchemy 2.0 ORM models (all 8 tables)
│   ├── session.py           # Async engine + session factory
│   ├── migrate.py           # Migration runner (up/down/reset)
│   ├── seed_kb.py           # KB seeder from markdown files
│   ├── repositories/
│   │   ├── customer_repo.py     # identity resolution, CRUD
│   │   ├── ticket_repo.py       # ticket + message CRUD, dedup
│   │   ├── kb_repo.py           # pgvector search
│   │   └── metrics_repo.py      # agent_metrics insert + daily aggregation
│   └── migrations/
│       ├── 001_extensions.sql / 001_extensions_down.sql
│       ├── 002_customers.sql / 002_customers_down.sql
│       ├── 003_tickets_messages.sql / 003_tickets_messages_down.sql
│       ├── 004_kb.sql / 004_kb_down.sql
│       ├── 005_metrics_reports.sql / 005_metrics_reports_down.sql
│       └── 006_idempotency.sql / 006_idempotency_down.sql
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Root page (support form)
│   │   │   └── layout.tsx
│   │   └── components/
│   │       ├── SupportForm.tsx     # Email + message + submit
│   │       └── ResponseDisplay.tsx # Shows AI response or "agent assigned"
│   ├── package.json
│   └── next.config.js
│
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml            # Non-secret env vars
│   ├── secret.yaml               # Sealed secrets (template only, no real values)
│   ├── api-deployment.yaml       # FastAPI pod (replicas: 2)
│   ├── worker-deployment.yaml    # Kafka workers (replicas: 1 each)
│   ├── frontend-deployment.yaml  # Next.js pod (replicas: 1)
│   ├── hpa.yaml                  # HPA: api scales 2–10 on CPU 70%
│   ├── services.yaml             # ClusterIP + LoadBalancer
│   └── postgres-statefulset.yaml # Single-node PG (prod: managed DB)
│
├── tests/
│   ├── unit/
│   │   ├── test_format_for_channel.py   # All channel limits, edge cases
│   │   ├── test_identity_resolution.py  # customer_identifiers lookup
│   │   ├── test_escalation_rules.py     # All 7 guardrail triggers
│   │   └── test_idempotency.py          # Duplicate ticket/message prevention
│   ├── integration/
│   │   ├── test_pipeline_email.py       # Full 7-step via Gmail payload
│   │   ├── test_pipeline_whatsapp.py    # Full 7-step via Twilio payload
│   │   ├── test_pipeline_webform.py     # Full 7-step via web form
│   │   ├── test_cross_channel.py        # Identity resolution across channels
│   │   └── test_daily_report.py         # Report generation + content
│   └── contract/
│       └── test_tool_contracts.py       # Each tool input/output schema
│
├── docker-compose.yml     # Local dev: postgres, kafka, zookeeper
├── Dockerfile             # Multi-stage: builder + runtime
├── requirements.txt
├── .env.example
└── README.md
```

**Structure Decision**: Web application layout. Backend (`api/`, `agent/`,
`workers/`, `database/`) is the primary service. Frontend (`frontend/`) is
a minimal Next.js app for the web-form channel only. Kubernetes manifests
live in `k8s/`. This layout supports independent Docker builds for
API pods and worker pods.

---

## Architecture: Component Interaction

```
Customer
  │
  ├─[Gmail]──────────────────────────────────┐
  ├─[WhatsApp/Twilio webhook]─────────────── │
  └─[Next.js Web Form]──────────────────────►│
                                             │
                                    FastAPI Webhook Routers
                                    (api/routers/webhooks.py)
                                             │
                                    Kafka Producer
                                    (publishes to cs.intake)
                                             │
                                    ┌────────▼────────┐
                                    │  intake_worker  │
                                    │  (cs.intake)    │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────────────────┐
                                    │   OrchestratorAgent         │
                                    │   (OpenAI Agents SDK)       │
                                    │                             │
                                    │  1. create_ticket ──────────┼──► PostgreSQL
                                    │  2+3 (parallel):            │
                                    │    get_customer_history ────┼──► PostgreSQL
                                    │    search_knowledge_base ───┼──► pgvector
                                    │  4. SentimentAgent ─────────┼──► gpt-4o
                                    │  5. EscalationAgent ────────┼──► guardrail rules
                                    │  6. format_for_channel ─────┼──► pure function
                                    │  7. send_response ──────────┼──► cs.response topic
                                    └─────────────────────────────┘
                                             │
                                    ┌────────▼─────────┐
                                    │ response_worker  │
                                    │ (cs.response)    │
                                    └────────┬─────────┘
                                             │
                            ┌────────────────┼──────────────────┐
                            ▼                ▼                  ▼
                     Gmail sender    Twilio sender       WebSocket/Poll
                     (reply thread)  (WA message)        (web form response)

                     [On escalation]
                     cs.escalation topic → escalation_worker → human queue webhook
```

---

## Cross-Channel Customer Resolution (Detail)

Implemented in `database/repositories/customer_repo.py`:

```python
async def resolve_or_create_customer(
    session: AsyncSession,
    identifiers: dict[str, str]  # {"email": ..., "phone": ..., "whatsapp_id": ...}
) -> tuple[UUID, bool]:          # (customer_id, was_created)

# Step 1: Normalise
#   email → lowercase strip
#   phone → E.164 via phonenumbers library
#   whatsapp_id → strip "whatsapp:" prefix

# Step 2: Bulk lookup
#   SELECT customer_id FROM customer_identifiers
#   WHERE (identifier_type, identifier_value) IN (...)
#   LIMIT 1

# Step 3a: Found → insert any new identifiers, return customer_id
# Step 3b: Not found → INSERT customers, INSERT all identifiers, return new id
```

All steps run in a single database transaction with `SELECT FOR UPDATE`
on the identifier rows to prevent race conditions under concurrent messages.

---

## Channel Format Adapter (Detail)

`agent/tools/format_for_channel.py` — pure function, fully unit-testable.

```python
CHANNEL_RULES = {
    "email": {
        "max_words":    500,
        "tone":         "formal",
        "markdown":     True,
        "requires_greeting": True,
        "requires_signoff":  True,
    },
    "whatsapp": {
        "max_chars":    300,
        "tone":         "conversational",
        "markdown":     False,
        "strip_emoji":  False,
    },
    "webform": {
        "max_words":    300,
        "tone":         "semi-formal",
        "markdown":     True,
        "requires_greeting": False,
    },
}

def format_for_channel(raw: str, channel: str, retry: bool = False) -> FormattedResponse:
    rules = CHANNEL_RULES[channel]
    # 1. Validate raw draft against limit
    # 2. If within limit → return as-is (with greeting/sign-off injected for email)
    # 3. If over limit → call LLM with trim prompt + exact budget
    # 4. If still over after 1 retry → return FormattedResponse(within_limits=False, error=E004)
```

The LLM trim prompt:
```
You are a response editor. Rewrite the following customer support response
for the {channel} channel. Requirements:
- Tone: {tone}
- Maximum: {limit} {unit}
- Preserve all factual content; cut filler words first
- Do NOT add new information

Response to trim:
{raw_response}
```

---

## Error Handling & Retry Strategy

Every tool call is wrapped by the OrchestratorAgent with this logic:

```python
async def call_tool_with_retry(tool_fn, *args, error_code_map, **kwargs):
    try:
        return await asyncio.wait_for(tool_fn(*args, **kwargs), timeout=3.0)
    except asyncio.TimeoutError:
        # E001: retry once after 500ms
        await asyncio.sleep(0.5)
        try:
            return await asyncio.wait_for(tool_fn(*args, **kwargs), timeout=3.0)
        except asyncio.TimeoutError:
            raise ToolError("E001", f"{tool_fn.__name__} timed out after retry")
    except AuthError:
        raise ToolError("E005", f"{tool_fn.__name__} authentication failed")
    except NotFoundError:
        return None  # E002: proceed with empty context
```

**Circuit breaker** (tracked in Redis or in-memory dict for hackathon):
```
consecutive_failures[tool_name] += 1
if consecutive_failures[tool_name] >= 3:
    skip tool for 60s, route ticket to escalation with reason=circuit_open
```

**Pipeline failure cascade**:
```
Step 1 (create_ticket) fails → E001 retry → if still fails → log + drop message
                                             (customer gets no response; ticket not created;
                                              alert fires to on-call)

Steps 2–3 fail → E002 → proceed without history/KB context
Step 4 (sentiment) fails → default score = 0.5 (neutral, no escalation triggered)
Step 5 (escalation) fails → E001 retry → if fails → conservative: escalate as P2
Step 6 (format) fails → E004 → one retry → if fails → escalate with reason=format_failure
Step 7 (send_response) fails → E001 retry → if fails → queue to dead-letter topic
```

---

## Monitoring: `agent_metrics` Table

Emitted by the orchestrator after every tool call; consumed by
`metrics_worker` from `cs.metrics` topic.

Key dashboard queries (for daily report and operational health):

```sql
-- Pipeline p95 latency (last hour)
SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms
FROM agent_metrics
WHERE tool_name = 'send_response'
  AND created_at > NOW() - INTERVAL '1 hour';

-- Escalation rate (today)
SELECT
  COUNT(*) FILTER (WHERE output_status = 'E003') * 100.0 / COUNT(*) AS escalation_pct
FROM agent_metrics
WHERE tool_name = 'decide_escalation'
  AND created_at >= CURRENT_DATE;

-- Error distribution
SELECT output_status, COUNT(*) FROM agent_metrics
WHERE created_at >= CURRENT_DATE
GROUP BY output_status ORDER BY count DESC;
```

---

## Deployment: Docker + Kubernetes

### Docker images (two, built from same Dockerfile)

```dockerfile
# Multi-stage: builder → runtime
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY . .
```

`CMD` overridden per pod:
- **API pod**: `CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]`
- **Worker pod**: `CMD ["python", "-m", "workers.intake_worker"]`

### Kubernetes topology

| Workload | Kind | Min Replicas | Max Replicas | Scales on |
|----------|------|-------------|-------------|-----------|
| `cs-api` | Deployment | 2 | 10 | CPU > 70% (HPA) |
| `cs-intake-worker` | Deployment | 1 | 3 | Kafka lag (KEDA, or manual) |
| `cs-response-worker` | Deployment | 1 | 3 | Kafka lag |
| `cs-metrics-worker` | Deployment | 1 | 1 | N/A |
| `cs-report-worker` | Deployment | 1 | 1 | N/A (cron-like) |
| `cs-frontend` | Deployment | 1 | 2 | CPU > 70% |
| `postgres` | StatefulSet | 1 | 1 | N/A (managed DB in prod) |

### HPA (API pod)

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cs-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cs-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## Hackathon MVP Scope (48–72 hours)

To ship a working demo in the hackathon window, implement in this order:

### Hour 0–8: Infrastructure
- [ ] Docker Compose up (Postgres, Kafka, Zookeeper)
- [ ] DB migrations (all 6 files)
- [ ] KB seeded with 10–15 sample FAQ articles
- [ ] FastAPI app skeleton + `/webhooks/webform` endpoint live

### Hour 8–20: Core Pipeline
- [ ] `create_ticket` + `customer_repo.resolve_or_create_customer`
- [ ] `get_customer_history`
- [ ] `search_knowledge_base` (pgvector semantic search)
- [ ] `analyze_sentiment` (gpt-4o call)
- [ ] `format_for_channel` (pure function, all 3 channels)
- [ ] `send_response` (web form channel only first)
- [ ] OrchestratorAgent wiring all 7 steps

### Hour 20–32: Channels + Escalation
- [ ] WhatsApp webhook + Twilio sender
- [ ] Gmail webhook + reply sender
- [ ] `escalate_to_human` with all 7 guardrail rules
- [ ] Idempotency keys for create_ticket + send_response
- [ ] Cross-channel identity resolution

### Hour 32–44: Workers + Frontend
- [ ] `intake_worker` (Kafka consumer → orchestrator)
- [ ] `response_worker` (Kafka consumer → channel send)
- [ ] Next.js web form UI
- [ ] `report_worker` (daily report generation)

### Hour 44–56: Hardening + Demo
- [ ] Unit tests for format_for_channel, escalation rules, idempotency
- [ ] Integration test: full pipeline email + whatsapp + webform
- [ ] Docker multi-stage build tested
- [ ] K8s manifests validated with `kubectl apply --dry-run`
- [ ] Quickstart validated end-to-end by a second team member

---

## Complexity Tracking

> No constitution violations. All additions are justified below.

| Addition | Why Needed | Simpler Alternative Rejected Because |
|----------|-----------|--------------------------------------|
| Kafka (aiokafka) | Decouples webhook receipt from pipeline processing; enables retry on agent failure without losing messages | Direct async queue (in-memory) — loses messages on pod restart; not production-grade |
| Sub-agent decomposition (3 sub-agents) | Constitution Principle VI mandates separate specialised agents; independent testability | Single monolithic agent — impossible to unit-test escalation rules in isolation |
| `customer_identifiers` table | Supports cross-channel identity resolution to ≥95% accuracy (FR-007, FR-008) | Simple email-only lookup — breaks as soon as customer uses WhatsApp |
| `idempotency_keys` table | Constitution Principle VII; prevents duplicate tickets on network retry (FR-022) | In-memory cache — lost on pod restart |

---

## Risks & Mitigations

1. **OpenAI Agents SDK latency eating the 3s SLO**: Mitigate by running
   steps 2+3 in parallel; using `gpt-4o-mini` for sentiment (cheaper,
   faster) and reserving `gpt-4o` for final response generation only.

2. **pgvector HNSW index not built before demo**: Mitigate by running
   `seed_kb.py` as part of the migration pipeline so the index is always
   present after `migrate.py up`.

3. **Twilio + Gmail OAuth not configured in hackathon env**: Mitigate by
   building a `/webhooks/simulate` debug endpoint that accepts the same
   normalised payload as any channel, bypassing OAuth for local testing.
