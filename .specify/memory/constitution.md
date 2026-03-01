<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 (template) → 1.0.0 (initial ratification)
Modified principles:
  - All 7 principles: template placeholders → concrete values
Added sections:
  - Core Principles (7 principles)
  - Hard Guardrails & Escalation Matrix
  - Performance Standards & SLOs
  - Development Lifecycle
  - Governance
Removed sections: None (template slots replaced, no deletions)
Templates requiring updates:
  - .specify/templates/plan-template.md      ✅ Constitution Check section compatible
  - .specify/templates/spec-template.md      ✅ FR/SC format compatible
  - .specify/templates/tasks-template.md     ✅ Phase structure compatible
Follow-up TODOs:
  - None. All fields resolved from user input dated 2026-03-01.
-->

# Customer Success Digital FTE Constitution

## Core Principles

### I. Multi-Channel Adaptive Response (NON-NEGOTIABLE)

The agent MUST operate across exactly three channels: **Email (Gmail)**,
**WhatsApp (Twilio)**, and **Web Form**. Each channel enforces distinct
tone, format, and length rules:

| Channel   | Tone            | Max Length  | Format         |
|-----------|-----------------|-------------|----------------|
| Email     | Formal, detailed| ≤ 500 words | Structured prose with greeting/sign-off |
| WhatsApp  | Conversational  | ≤ 300 chars | Short, plain, emoji-safe                |
| Web Form  | Semi-formal     | ≤ 300 words | Concise paragraphs, no jargon           |

**Rules:**
- Responses MUST be reformatted per channel before sending; a generic
  response MUST NOT be sent as-is across channels.
- Channel metadata MUST be captured at ticket creation and carried through
  the entire workflow.
- Exceeding length limits is a hard failure; truncation with a polite
  continuation prompt is preferred over silent truncation.

**Rationale:** Customers switch channels; tone mismatch destroys trust and
increases escalation rates. Channel-specific formatting is a first-class
product feature, not a cosmetic concern.

### II. Strict Workflow Order (NON-NEGOTIABLE)

Every customer interaction MUST follow this exact 7-step pipeline. No step
may be skipped or reordered:

```
1. create_ticket        — with channel metadata attached
2. get_customer_history — cross-channel lookup (≥95% match accuracy)
3. search_knowledge_base — only if the inquiry is product/feature related
4. analyze_sentiment    — score 0.0–1.0; drives escalation decision
5. decide_escalation    — apply guardrail rules (see Principle III)
6. format_response      — channel-specific format and length enforcement
7. send_response        — NEVER respond directly; always through this step
```

**Rules:**
- Steps MUST execute in order. Any tool failure MUST halt the pipeline and
  surface a human-readable error before escalating.
- `send_response` is the ONLY permitted output path for customer-facing
  messages.
- Sub-agents may parallelize internal lookups (steps 2–3) only after
  `create_ticket` (step 1) is confirmed.

**Rationale:** Deterministic ordering ensures auditability, prevents
partial-state responses, and makes the pipeline testable at each step
boundary.

### III. Hard Guardrails & Escalation Rules (NON-NEGOTIABLE)

The following conditions MUST trigger immediate escalation to a human agent.
No AI-generated response is permitted for these cases:

**Topic-based escalation triggers:**
- Pricing negotiation or billing disputes
- Refund or chargeback requests
- Legal threats, contract terms, or compliance inquiries
- Competitor comparisons or disparagement requests

**Sentiment-based escalation triggers:**
- Sentiment score < 0.3 (angry/distressed customer)
- Presence of profanity or threatening language

**Capability-based guardrails:**
- The agent MUST NEVER promise features not documented in the knowledge base.
- The agent MUST NEVER fabricate product specifications, SLAs, or pricing.
- The agent MUST NEVER make commitments on behalf of the business without
  human approval.

**Escalation format:** Every escalation MUST include:
1. Ticket ID
2. Trigger reason (specific rule violated)
3. Full conversation context
4. Suggested priority (P1 = immediate, P2 = within 1 hour, P3 = next business day)

**Rationale:** AI errors in pricing, legal, or angry-customer contexts
carry disproportionate business and reputational risk. Hard stops are
cheaper than damage control.

### IV. PostgreSQL-First CRM (NON-NEGOTIABLE)

PostgreSQL is the single source of truth for all customer data, ticket
history, and cross-channel identity resolution.

**Rules:**
- External CRM platforms (Salesforce, HubSpot, Zendesk, etc.) MUST NOT be
  integrated as authoritative data sources.
- All `get_customer_history` lookups MUST query PostgreSQL directly.
- Cross-channel identity matching (email ↔ phone ↔ web session) MUST be
  resolved via PostgreSQL joins, not external enrichment APIs.
- Schema migrations MUST be versioned and reversible.
- Sensitive PII fields MUST be encrypted at rest.

**Rationale:** A single owned data store eliminates sync latency, reduces
vendor lock-in, and provides a reliable audit trail for compliance.

### V. Performance SLOs

The following targets are binding for production deployments:

| Metric                              | Target    | Critical Threshold |
|-------------------------------------|-----------|--------------------|
| End-to-end pipeline processing time | < 3s p95  | > 5s = incident    |
| Escalation rate                     | < 20%     | > 30% = review     |
| Cross-channel customer ID accuracy  | > 95%     | < 90% = incident   |
| Knowledge base search latency       | < 500ms   | > 1s = alert       |
| Ticket creation success rate        | > 99.5%   | < 99% = incident   |

**Rules:**
- SLO breaches at the "Critical Threshold" level MUST auto-page on-call.
- Performance metrics MUST be emitted as structured logs on every pipeline run.
- Load testing MUST be performed before any production release.

**Rationale:** Measurable targets make reliability visible, drive
prioritization, and provide an objective definition of "working."

### VI. Incubation → Specialization Development Lifecycle

All features follow a two-phase development model:

**Phase 1 — Incubation (Claude Code / prototype):**
- Rapid prototype using Claude Code and agent-native tools.
- Goal: validate behavior, discover edge cases, define tool contracts.
- Acceptance gate: all 7 workflow steps execute end-to-end with mock data.

**Phase 2 — Specialization (OpenAI Agents SDK / production):**
- Migrate validated prototype to OpenAI Agents SDK for production hardening.
- Sub-agent decomposition: sentiment, knowledge retrieval, escalation
  decision MUST be separate specialized agents.
- Goal: production-grade reliability, observability, and testability.

**Rules:**
- No feature moves to Phase 2 without a passing Phase 1 end-to-end test.
- Tool contracts (inputs, outputs, error codes) defined in Phase 1 MUST be
  preserved in Phase 2 without breaking changes.
- Phase 2 agents MUST expose structured logs for every tool call.

**Rationale:** Prototyping in Claude Code accelerates discovery; production
in OpenAI Agents SDK provides the multi-agent orchestration, retry logic,
and observability needed for 24/7 uptime.

### VII. AI Agent Reliability & Observability

Every agent and sub-agent MUST satisfy the following reliability baseline:

**Idempotency:** `create_ticket` and `send_response` MUST be idempotent;
duplicate invocations MUST NOT create duplicate tickets or send duplicate
messages.

**Structured Logging:** Every tool call MUST emit a log entry containing:
`{ ticket_id, tool_name, input_hash, output_status, duration_ms, channel }`.

**Error Taxonomy:**

| Code  | Category       | Action                        |
|-------|----------------|-------------------------------|
| E001  | Tool timeout   | Retry once, then escalate     |
| E002  | Data not found | Proceed with empty context    |
| E003  | Guardrail hit  | Escalate immediately          |
| E004  | Format error   | Re-format once, then escalate |
| E005  | Auth failure   | Alert + escalate              |

**Graceful Degradation:** If `search_knowledge_base` fails, the pipeline
MUST continue without KB context rather than blocking the response.

**Rationale:** 24/7 AI agents fail in production without idempotency guards,
structured observability, and defined error paths. Reliability is a feature.

## Hard Guardrails & Escalation Matrix

| Trigger                        | Condition              | Action                      |
|--------------------------------|------------------------|-----------------------------|
| Pricing / billing              | Topic detected         | Escalate P1, no AI response |
| Refund / chargeback            | Topic detected         | Escalate P1, no AI response |
| Legal / contract / compliance  | Topic detected         | Escalate P1, no AI response |
| Competitor mention             | Topic detected         | Escalate P2                 |
| Angry sentiment                | Score < 0.3            | Escalate P1                 |
| Profanity / threats            | Detected               | Escalate P1                 |
| Undocumented feature promise   | Agent about to promise | Block + escalate P2         |

## Performance Standards & SLOs

See **Principle V** for binding numeric targets.

Additional standards:
- Uptime target: **99.9%** monthly (≤ 43 min downtime/month).
- Retry policy: max 1 automatic retry per tool call with 500ms backoff.
- Circuit breaker: after 3 consecutive tool failures, route to human.
- PII: MUST NOT appear in logs; mask before emission.

## Development Lifecycle

See **Principle VI** for the two-phase Incubation → Specialization model.

Additional workflow rules:
- All specs MUST define acceptance criteria testable at each pipeline step.
- All tasks MUST reference the specific tool call they implement.
- No secrets or API keys in source code; use `.env` with `.env.example`.
- Database migrations MUST include both `up` and `down` scripts.

## Governance

This Constitution is the authoritative source of truth for the
**Customer Success Digital FTE** project. It supersedes all other
development practices, ticket acceptance criteria, and agent behavior
specifications.

**Amendment procedure:**
1. Propose change in a spec or ADR with clear rationale.
2. Obtain explicit user/owner sign-off before merging.
3. Increment version per semantic versioning rules below.
4. Update all downstream templates (plan, spec, tasks) for consistency.
5. Record amendment in SYNC IMPACT REPORT at file top.

**Versioning policy:**
- **MAJOR** — removing or fundamentally redefining a numbered Principle.
- **MINOR** — adding a new Principle or materially expanding a section.
- **PATCH** — wording clarifications, typo fixes, non-semantic refinements.

**Compliance review:**
- Every plan.md MUST contain a "Constitution Check" section that verifies
  the feature does not violate Principles I–VII.
- Every PR MUST confirm no hard guardrails (Principle III) are bypassed.
- Escalation rate and processing time MUST be reviewed monthly against SLOs.

**Runtime guidance:** See `.specify/memory/constitution.md` (this file) as
the single reference for agent behavior rules during development.

---

**Version**: 1.0.0 | **Ratified**: 2026-03-01 | **Last Amended**: 2026-03-01
