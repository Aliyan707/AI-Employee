---
description: "Task list for CS AI FTE — 24/7 Customer Success Agent"
---

# Tasks: CS AI FTE — 24/7 Customer Success Agent

**Input**: Design documents from `specs/001-cs-ai-fte/`
**Branch**: `001-cs-ai-fte` | **Date**: 2026-03-01
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**Effort key**: `[S]` ≤ 1h | `[M]` 1–3h | `[L]` 3–6h
**Story map**: US1=Inquiry Resolved | US2=Cross-Channel Continuity | US3=Escalation | US4=Ticket History | US5=Daily Report

---

## Format: `[ID] [P?] [Story?] Description — Effort | AC | Deps`

- **[P]**: Safe to run in parallel (no shared file conflicts)
- **[USx]**: User story this task belongs to
- **AC**: Acceptance criteria (what "done" looks like)
- **Deps**: Task IDs that must complete first

---

## Phase 1: Incubation — Project Setup

**Purpose**: Scaffold the repo, local infrastructure, and environment so every
subsequent task has a runnable baseline.
**Checkpoint**: `docker compose up -d` succeeds; Postgres and Kafka reachable.

- [x] T001 Create top-level folder structure: `agent/sub_agents/`, `agent/tools/`, `channels/gmail/`, `channels/whatsapp/`, `channels/webform/`, `workers/`, `api/routers/`, `api/middleware/`, `database/repositories/`, `database/migrations/`, `frontend/src/`, `k8s/`, `tests/unit/`, `tests/integration/`, `tests/contract/` — **[S]**
  - AC: All directories exist; each contains a `.gitkeep` or `__init__.py`
  - Deps: none

- [x] T002 [P] Create `requirements.txt` with pinned versions: fastapi==0.115, uvicorn[standard], openai>=1.50, aiokafka==0.11, sqlalchemy[asyncio]==2.0, asyncpg, pgvector, pydantic-settings, python-multipart, python-dotenv, phonenumbers, httpx, apscheduler, pytest, pytest-asyncio — **[S]**
  - AC: `pip install -r requirements.txt` completes without errors
  - Deps: T001

- [x] T003 [P] Create `.env.example` with all required variables: `OPENAI_API_KEY`, `GMAIL_CREDENTIALS_PATH`, `GMAIL_TOPIC_NAME`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`, `POSTGRES_HOST/PORT/DB/USER/PASSWORD`, `KAFKA_BOOTSTRAP_SERVERS`, `SECRET_KEY`, `ENVIRONMENT`, `LOG_LEVEL`, `DAILY_REPORT_HOUR`, `ESCALATION_QUEUE_WEBHOOK` — **[S]**
  - AC: File documents every env var with a comment; no real secrets present; `.env` is in `.gitignore`
  - Deps: T001

- [x] T004 [P] Create `docker-compose.yml` with services: `postgres` (postgres:16, port 5432, healthcheck), `zookeeper` (confluentinc/cp-zookeeper:7.6, port 2181), `kafka` (confluentinc/cp-kafka:7.6, port 9092, depends_on zookeeper, healthcheck), named volumes for postgres data — **[M]**
  - AC: `docker compose up -d && docker compose ps` shows all three services healthy within 30s
  - Deps: T001

- [x] T005 [P] Create multi-stage `Dockerfile`: builder stage installs deps from `requirements.txt`; runtime stage copies app code; default `CMD` starts the FastAPI server; includes `.dockerignore` excluding `.env`, `__pycache__`, `.venv` — **[S]**
  - AC: `docker build -t cs-fte .` succeeds; image runs `uvicorn api.main:app --host 0.0.0.0 --port 8000`
  - Deps: T002

- [x] T006 [P] Create `pyproject.toml` (or `setup.cfg`) configuring pytest: `asyncio_mode = auto`, `testpaths = tests`, `python_files = test_*.py` — **[S]**
  - AC: `pytest --collect-only` finds test directories without errors (0 tests found is fine at this stage)
  - Deps: T001

- [x] T007 [P] Initialise Next.js 14 frontend: `npx create-next-app@14 frontend --typescript --app --no-git --no-eslint`; add `NEXT_PUBLIC_API_URL` to `frontend/.env.local.example`; delete default boilerplate pages — **[M]**
  - AC: `cd frontend && npm run dev` starts on port 3000 without errors
  - Deps: T001

- [x] T008 Create `pydantic_settings`-based `config.py` at repo root loading all `.env` variables with type validation; expose a `get_settings()` cached singleton — **[S]**
  - AC: `from config import get_settings; s = get_settings()` works; missing required vars raise `ValidationError` with field names
  - Deps: T003

---

## Phase 2: Database & CRM Schema (Foundational)

**Purpose**: All 8 PostgreSQL tables, SQLAlchemy ORM models, migration runner,
and repositories. BLOCKS every subsequent user story.
**Checkpoint**: `python database/migrate.py up` applies all 6 migrations; `psql` `\dt` shows all tables.

- [x] T009 Create `database/migrations/001_extensions.sql` enabling `uuid-ossp` and `vector` (pgvector) extensions; create paired `001_extensions_down.sql` dropping them — **[S]**
  - AC: Migration applies idempotently (`CREATE EXTENSION IF NOT EXISTS`); down script reverses cleanly
  - Deps: T004

- [x] T010 [P] Create `database/migrations/002_customers.sql` with `customers` table (id UUID PK, display_name, company, primary_email UNIQUE lowercase, primary_phone E.164, created_at, updated_at) and `customer_identifiers` table (id BIGSERIAL, customer_id FK, identifier_type enum, identifier_value, UNIQUE constraint); indexes on email, phone, and `(type, value)` lookup; paired down script — **[M]**
  - AC: `\d customer_identifiers` shows unique index on `(identifier_type, identifier_value)`
  - Deps: T009

- [x] T011 [P] Create `database/migrations/003_tickets_messages.sql` with `ticket_status` enum, `ticket_priority` enum, `channel_type` enum, `tickets` table (id UUID, customer_id FK, channel, status, priority, subject, escalated bool, escalation_reason, parent_ticket_id self-FK, kb_article_ids UUID[], timestamps), `message_direction` enum, `messages` table (id BIGSERIAL, ticket_id FK, direction, channel, raw_content, content_hash CHAR(64), sentiment_score NUMERIC(4,3), agent_decision JSONB, sent_at, delivery_status); paired down script — **[M]**
  - AC: All ENUMs created before tables; foreign keys enforced; indexes on ticket customer_id, status, channel, created_at
  - Deps: T010

- [x] T012 [P] Create `database/migrations/004_kb.sql` with `knowledge_base` table (id UUID, title, content, topic_tags TEXT[], embedding VECTOR(1536), source_url, timestamps); HNSW index `USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`; paired down script — **[M]**
  - AC: `\d knowledge_base` shows `embedding` column type `vector(1536)`; HNSW index visible in `\di`
  - Deps: T009

- [x] T013 [P] Create `database/migrations/005_metrics_reports.sql` with `agent_metrics` table (id BIGSERIAL, ticket_id UUID FK nullable, tool_name, channel, input_hash, output_status, duration_ms, error_code, created_at) and `daily_reports` table (id UUID, report_date DATE UNIQUE, total_tickets, tickets_by_channel JSONB, top_topics JSONB, mean_sentiment, escalation_count, escalation_rate NUMERIC(5,2), generated_at); paired down script — **[M]**
  - AC: Indexes on `agent_metrics.created_at` and `agent_metrics.output_status`; `daily_reports.report_date` is UNIQUE
  - Deps: T011

- [x] T014 [P] Create `database/migrations/006_idempotency.sql` with `idempotency_keys` table (key CHAR(64) PK, result JSONB, created_at, expires_at TIMESTAMPTZ); index on `expires_at` for TTL cleanup; paired down script — **[S]**
  - AC: Index present; down script drops table cleanly
  - Deps: T009

- [x] T015 Create `database/migrate.py` migration runner supporting `up` (applies unapplied migrations in order), `down <name>` (rolls back named migration), `reset` (down all then up all); tracks applied migrations in a `schema_migrations` table — **[M]**
  - AC: `python database/migrate.py up` applies all 6; re-running is idempotent; `down 006_idempotency` removes only that table
  - Deps: T009, T010, T011, T012, T013, T014

- [x] T016 Create `database/models.py` with SQLAlchemy 2.0 async ORM models for all 8 tables: `Customer`, `CustomerIdentifier`, `Ticket`, `Message`, `EscalationRecord`, `KnowledgeBase`, `AgentMetric`, `DailyReport`, `IdempotencyKey`; use `mapped_column` and `Mapped[T]` typed annotations; Vector column via pgvector SQLAlchemy extension — **[M]**
  - AC: `from database.models import Customer, Ticket` imports without error; all relationships declared (customer→tickets, ticket→messages)
  - Deps: T015

- [x] T017 Create `database/session.py` with async SQLAlchemy engine (`create_async_engine`), `AsyncSession` factory via `async_sessionmaker`, and `get_db` FastAPI dependency that yields a session per request and closes on exit — **[S]**
  - AC: `async with get_db() as db: pass` completes without error against running Postgres
  - Deps: T016

- [x] T018 Create `database/repositories/customer_repo.py` implementing `resolve_or_create_customer(session, identifiers: dict) -> tuple[UUID, bool]`: normalise email (lowercase), phone (E.164 via `phonenumbers`), wa_id; `SELECT FOR UPDATE` lookup in `customer_identifiers`; create new customer + identifiers if not found; insert missing identifiers if found; return `(customer_id, was_created)` — **[M]**
  - AC: Unit test: same email on two concurrent calls returns same `customer_id`; new email creates new record; `was_created=False` on second call
  - Deps: T017

- [x] T019 [P] Create `database/repositories/ticket_repo.py` implementing: `create_ticket_idempotent(session, customer_id, channel, content_hash, raw_content, subject) -> (UUID, bool)` — checks `idempotency_keys` table (60s window) before inserting; `get_ticket_with_messages(session, ticket_id) -> Ticket`; `update_ticket_status(session, ticket_id, status)`; `get_open_ticket_for_customer(session, customer_id, channel) -> Ticket | None` — **[M]**
  - AC: Two calls with same content_hash within 60s return same ticket_id with `duplicate=True`; after 60s a new ticket is created
  - Deps: T017

- [x] T020 [P] Create `database/repositories/kb_repo.py` implementing `semantic_search(session, query_text: str, top_k=5, threshold=0.75) -> list[KBResult]`: embed query via `openai.embeddings.create(model="text-embedding-3-small")`; run pgvector cosine query `ORDER BY embedding <=> $vec LIMIT 5`; filter by score ≥ threshold; return `KBResult(article_id, title, content, score, topic_tags)` — **[M]**
  - AC: With seeded KB, query "password reset" returns at least 1 result with score ≥ 0.75 within 500ms
  - Deps: T017

---

## Phase 3: Web Form Channel — US1 MVP Core

**Goal**: A customer submits a question via the React web form and receives
an AI-generated, correctly-formatted response within 3 seconds. This is the
first fully-working end-to-end pipeline, web-form channel only.
**Independent Test**: Fill in `http://localhost:3000`, submit "How do I reset my password?", see response in UI within 3s; check `tickets` table has 1 row.

- [x] T021 [P] [US1] Create `api/main.py` FastAPI app with lifespan (startup: verify DB connection, Kafka producer init; shutdown: close connections); include routers for `webhooks`, `tickets`, `customers`, `reports`; add CORS middleware allowing `localhost:3000`; add structured JSON logging middleware in `api/middleware/logging.py` — **[M]**
  - AC: `GET /` returns `{"status":"ok"}`; `GET /docs` loads Swagger UI; startup logs show "DB connected" and "Kafka connected"
  - Deps: T017

- [x] T022 [P] [US1] Create `channels/webform/handler.py` with `WebformPayload` Pydantic model (email, name, phone optional, message, subject optional); `normalise_webform(payload) -> IntakeEvent` converting to the common internal event schema matching `contracts/kafka-schemas.md` `cs.intake` format; validate email format; reject empty message with `400` — **[S]**
  - AC: Empty message raises `ValidationError`; valid payload produces `IntakeEvent` with `channel="webform"` and correct `content_hash`
  - Deps: T008

- [x] T023 [P] [US1] Create `agent/tools/format_for_channel.py` pure function `format_for_channel(raw: str, channel: str, customer_name: str | None, retry: bool) -> FormattedResponse`; implement `CHANNEL_RULES` dict; word-count for email/webform, char-count for WhatsApp; inject greeting + sign-off for email; one LLM trim retry via `gpt-4o` with budget-specific prompt; return `FormattedResponse(text, within_limits, word_count, char_count, error)` — **[M]**
  - AC: 600-word email draft → trimmed to ≤500 words; 400-char WhatsApp draft → trimmed to ≤300 chars; 2nd trim failure → `within_limits=False, error="E004"`
  - Deps: T008

- [x] T024 [P] [US1] Create `agent/tools/create_ticket.py` calling `ticket_repo.create_ticket_idempotent`; emit `agent_metrics` Kafka message after call; return `ToolResult(ticket_id, created, duplicate)` — **[S]**
  - AC: Calling twice with same content_hash returns same `ticket_id` with `duplicate=True`; metrics event published to `cs.metrics`
  - Deps: T019

- [x] T025 [P] [US1] Create `agent/tools/get_customer_history.py` calling `customer_repo.resolve_or_create_customer` then fetching last 20 tickets via `ticket_repo`; return structured history dict matching `contracts/agent-tools.md` schema — **[S]**
  - AC: New customer returns empty tickets list and `last_sentiment=null`; known customer returns correct ticket count
  - Deps: T018, T019

- [x] T026 [P] [US1] Create `agent/tools/search_knowledge_base.py` calling `kb_repo.semantic_search`; handle timeout (E001: return `kb_miss=True`, do not raise); log metric — **[S]**
  - AC: Valid query with seeded KB returns ≥1 result; KB miss (irrelevant query) returns `kb_miss=True` without raising exception
  - Deps: T020

- [x] T027 [US1] Create `agent/tools/analyze_sentiment.py` calling OpenAI `gpt-4o` with a structured prompt scoring the customer message 0.0–1.0; detect profanity via keyword list as fast pre-check before LLM call; return `SentimentResult(score, label, profanity_detected, escalate)` where `escalate=True` if `score < 0.3` or `profanity_detected` — **[M]**
  - AC: "I'm furious!!!" → score < 0.3, `escalate=True`; "Thanks for your help!" → score > 0.7, `escalate=False`; profanity keyword → `profanity_detected=True` regardless of LLM score
  - Deps: T008

- [x] T028 [US1] Create `agent/tools/send_response.py` checking idempotency key `SHA256(ticket_id + response_hash)`; saving outbound `Message` row; for webform channel: publish to `cs.response` Kafka topic (or call sender directly in prototype mode); return `SendResult(message_id, sent, duplicate)` — **[M]**
  - AC: Two calls with same ticket_id + response produce `duplicate=True` on second call; message row exists in DB; delivery_status="sent"
  - Deps: T019, T023

- [x] T029 [US1] Create `agent/orchestrator.py` `OrchestratorAgent` class wiring all 7 steps in strict order using OpenAI Agents SDK; steps 2+3 run via `asyncio.gather` after step 1 completes; implement `call_tool_with_retry` wrapper (E001: 1 retry after 500ms, E002: return None, E003: re-raise for escalation, E004: re-format once, E005: alert + escalate); circuit breaker dict tracking consecutive failures per tool — **[L]**
  - AC: Full pipeline runs against a seeded KB; "How do I reset my password?" → formatted webform response returned in < 3s; pipeline JSON log shows all 7 step results
  - Deps: T024, T025, T026, T027, T028

- [x] T030 [US1] Create `api/routers/webhooks.py` `POST /webhooks/webform` endpoint: validate `WebformPayload`, call `handler.normalise_webform`, call `OrchestratorAgent.run` directly (pre-Kafka, prototype mode), return formatted response in JSON — **[M]**
  - AC: `POST /webhooks/webform {"email":"t@test.com","message":"How do I reset my password?"}` → 200 with `response_text` in ≤3s; ticket row created in DB
  - Deps: T021, T022, T029

---

## Phase 4: Channel Handlers — WhatsApp & Gmail

**Goal**: All three channels operational. Customer contacts via any channel
and gets a correctly formatted, channel-specific response.
**Independent Test**: POST a Twilio-format payload to `/webhooks/whatsapp`; check response ≤300 chars conversational; POST Gmail payload to `/webhooks/gmail`; check response ≤500 words formal with sign-off.

- [x] T031 [P] [US1] Create `channels/whatsapp/webhook.py` with `TwilioWebhookPayload` Pydantic model (From, To, Body, MessageSid); HMAC-SHA1 Twilio signature validation using `TWILIO_AUTH_TOKEN`; `normalise_whatsapp(payload) -> IntakeEvent` extracting `phone` from `From` field (strip `whatsapp:` prefix), setting `channel="whatsapp"` — **[M]**
  - AC: Request with invalid HMAC returns 403; valid payload produces `IntakeEvent` with `channel="whatsapp"` and E.164 phone
  - Deps: T022

- [x] T032 [P] [US1] Create `channels/whatsapp/sender.py` `send_whatsapp(to_number: str, text: str) -> bool` using Twilio REST API (`twilio` SDK); assert `len(text) <= 300` before sending; return True on success, False on failure (log error, do not raise) — **[S]**
  - AC: Mock Twilio API call verifies `Body` param length ≤300; function returns False (not exception) on Twilio API error
  - Deps: T008

- [x] T033 [P] [US1] Create `channels/gmail/reader.py` `decode_gmail_push(pubsub_data: str) -> IntakeEvent` decoding base64 PubSub notification, fetching full message via Gmail API using service-account credentials from `GMAIL_CREDENTIALS_PATH`, extracting `from_address`, `thread_id`, `subject`, `body`; setting `channel="email"` — **[M]**
  - AC: Given a captured Gmail PubSub JSON fixture, `decode_gmail_push` returns correct `IntakeEvent` with email and thread_id
  - Deps: T022

- [x] T034 [P] [US1] Create `channels/gmail/sender.py` `send_gmail_reply(thread_id: str, to_address: str, subject: str, html_body: str) -> bool` replying in the same Gmail thread; word-count guard asserts ≤500 words before sending — **[M]**
  - AC: Reply includes `threadId` header; function returns False (not exception) on Gmail API error; word count > 500 raises `AssertionError` before API call
  - Deps: T008

- [x] T035 [US1] Add `POST /webhooks/whatsapp` to `api/routers/webhooks.py`: validate Twilio signature, normalise payload, call `OrchestratorAgent.run`, call `channels/whatsapp/sender.send_whatsapp` with formatted response; return Twilio-compatible 200 XML response — **[M]**
  - AC: `POST /webhooks/whatsapp` with valid Twilio payload → WhatsApp reply ≤300 chars; ticket row in DB with `channel="whatsapp"`
  - Deps: T031, T032, T030

- [x] T036 [US1] Add `POST /webhooks/gmail` to `api/routers/webhooks.py`: decode PubSub notification, call `channels/gmail/reader.decode_gmail_push`, call `OrchestratorAgent.run`, call `channels/gmail/sender.send_gmail_reply` — **[M]**
  - AC: Simulated Gmail push → reply appears in Gmail thread; response ≤500 words with greeting and sign-off; ticket row in DB with `channel="email"`
  - Deps: T033, T034, T030

- [x] T037 [P] [US1] Create `api/routers/webhooks.py` `/webhooks/simulate` debug endpoint accepting a normalised `IntakeEvent` JSON (bypasses OAuth/HMAC); calls `OrchestratorAgent.run` directly; enables local testing of any channel without real credentials — **[S]**
  - AC: `POST /webhooks/simulate {"channel":"whatsapp","raw_content":"Hello","customer_identifiers":{"phone":"+14155551234"}}` → 200 with formatted response; only enabled when `ENVIRONMENT=development`
  - Deps: T030

- [x] T038 [P] Seed `knowledge_base` table with 15 FAQ articles: account (password reset, 2FA setup, profile update), billing (plan details, upgrade, downgrade), integrations (SSO, API keys, webhooks), troubleshooting (login issues, slow performance, data export); run `database/seed_kb.py` generating embeddings via `text-embedding-3-small` — **[M]**
  - AC: `SELECT COUNT(*) FROM knowledge_base` = 15; query "password reset" returns ≥1 result with score ≥ 0.75
  - Deps: T020

---

## Phase 5: Agent & Tools — Escalation & Full Pipeline (US2, US3)

**Goal**: Escalation rules fully enforced; cross-channel identity resolution working;
all 5 spec tools complete and integrated into the orchestrator.
**Independent Test (US3)**: POST `{"message":"I want a full refund"}` → response is holding message; `escalation_records` has 1 row with `trigger_rule="refund"`, `priority="P1"`. **Independent Test (US2)**: Two messages from same customer on different channels → both tickets have same `customer_id`.

- [x] T039 [US3] Create `agent/tools/escalate_to_human.py` implementing idempotency check (one escalation per ticket); update ticket status to `escalated`; insert `EscalationRecord` row with all required fields from `contracts/agent-tools.md`; POST escalation payload to `ESCALATION_QUEUE_WEBHOOK`; publish to `cs.escalation` Kafka topic; return holding message text appropriate for channel — **[M]**
  - AC: Two calls for same ticket_id return `already_escalated` on second call; `escalation_records` row exists; webhook POST fired once; channel-appropriate holding message returned (≤300 chars for WhatsApp)
  - Deps: T019, T028, T029

- [x] T040 [US3] Create `agent/sub_agents/escalation_agent.py` `EscalationAgent` wrapping the guardrail decision logic: topic classification (pricing/refund/legal/competitor keywords + LLM classifier for ambiguous cases); sentiment threshold check (score < 0.3); profanity flag; return `EscalationDecision(should_escalate, trigger_rule, trigger_detail, priority)` — **[M]**
  - AC: "I want a refund" → `should_escalate=True, trigger_rule="refund", priority="P1"`; "How do I export data?" → `should_escalate=False`; score=0.22 → `should_escalate=True, trigger_rule="sentiment"`
  - Deps: T027

- [x] T041 [US3] Update `agent/orchestrator.py` step 5 to call `EscalationAgent`; if `should_escalate=True`, call `escalate_to_human` tool, call `send_response` with holding message, and STOP pipeline (skip step 6 normal format, return early) — **[M]**
  - AC: Escalation-triggering messages never reach normal response generation; holding message is always ≤ channel limit; ticket status = `escalated` after pipeline
  - Deps: T039, T040

- [x] T042 [US2] Create `agent/sub_agents/sentiment_agent.py` `SentimentAgent` as a dedicated OpenAI Agents SDK sub-agent (separate from orchestrator) that calls `analyze_sentiment` tool; receives message text + ticket_id; returns `SentimentResult` — **[S]**
  - AC: Sub-agent is independently callable; `SentimentAgent.run("I am so frustrated")` returns score < 0.5; integrates into orchestrator at step 4
  - Deps: T027

- [x] T043 [US2] Create `agent/sub_agents/kb_agent.py` `KBAgent` as dedicated sub-agent calling `search_knowledge_base` tool; handles `kb_miss` gracefully by returning empty results without raising — **[S]**
  - AC: `KBAgent.run("password reset")` returns results with scores; `KBAgent.run("nonsense xyz123")` returns `kb_miss=True` without exception
  - Deps: T026

- [x] T044 [US2] Update `agent/orchestrator.py` to use `asyncio.gather` for steps 2+3: `get_customer_history` and `KBAgent.run` execute in parallel; result of step 1 (ticket_id, customer_id) feeds both; merge results before step 4 — **[M]**
  - AC: Total time for steps 2+3 combined < time for each individually; both results available for step 4; pipeline log shows parallel execution timestamps
  - Deps: T042, T043, T041

- [x] T045 [US2] Update `api/routers/webhooks.py` all three endpoints to pass resolved `customer_id` (from `customer_repo.resolve_or_create_customer`) into `OrchestratorAgent.run`; ensure cross-channel: same email or phone resolves to same customer_id regardless of originating channel — **[M]**
  - AC: Two requests (email channel + WhatsApp channel) with same email/phone → both tickets have identical `customer_id` in DB
  - Deps: T018, T035, T036, T044

- [x] T046 [US4] Create `api/routers/tickets.py` with `GET /tickets/{ticket_id}` returning full ticket + all messages; `GET /tickets/{ticket_id}/escalation` returning escalation record if exists; response matches `contracts/api.openapi.yaml` `TicketDetail` schema — **[M]**
  - AC: `GET /tickets/<uuid>` returns 200 with messages array; `GET /tickets/<unknown>` returns 404; escalated ticket includes `escalation_reason` field
  - Deps: T019, T021

- [x] T047 [US4] Create `api/routers/customers.py` with `GET /customers/{customer_id}/history` returning full cross-channel history; supports `?channel=whatsapp` filter and `?limit=20` pagination; response matches `CustomerHistory` schema — **[M]**
  - AC: Customer with email + WhatsApp tickets shows both when no filter; `?channel=whatsapp` returns only WA tickets; `?limit=2` returns at most 2 tickets
  - Deps: T019, T021

---

## Phase 6: Kafka Integration

**Goal**: All channels produce to `cs.intake`; workers consume and drive the
pipeline; responses dispatched via `cs.response`; metrics recorded.
**Checkpoint**: `docker exec kafka kafka-topics.sh --list` shows all 4 topics; end-to-end webform → Kafka → worker → response completes in < 3s.

- [x] T048 Create `workers/kafka_client.py` shared module with: async `KafkaProducer` singleton (aiokafka, JSON serialisation, `acks="all"`); `create_topics()` function creating the 4 topics (`cs.intake`, `cs.response`, `cs.escalation`, `cs.metrics`) with correct partition counts and retention; `get_producer()` dependency for FastAPI — **[M]**
  - AC: `create_topics()` idempotent; `await producer.send("cs.intake", ...)` succeeds; topics visible in Kafka CLI
  - Deps: T004, T008

- [x] T049 Update `api/routers/webhooks.py` all three webhook endpoints to publish `IntakeEvent` to `cs.intake` topic (instead of calling OrchestratorAgent directly); return `202 Accepted` with `{"accepted": true, "idempotency_key": "..."}` immediately — **[M]**
  - AC: Webhook returns in < 100ms regardless of pipeline duration; message visible in `cs.intake` via consumer CLI; no duplicate messages for same idempotency_key
  - Deps: T048, T035, T036

- [x] T050 Create `workers/intake_worker.py` aiokafka consumer of `cs.intake` topic, consumer group `intake-worker`: deserialise `IntakeEvent`; call `customer_repo.resolve_or_create_customer`; call `OrchestratorAgent.run`; on success publish formatted response to `cs.response`; on pipeline failure publish to dead-letter log; commit offset after successful processing — **[L]**
  - AC: Consumer processes 1 intake message end-to-end; correct channel response appears in `cs.response`; metrics message in `cs.metrics`; uncommitted offset on exception (message not lost)
  - Deps: T049, T029, T048

- [x] T051 Create `workers/response_worker.py` aiokafka consumer of `cs.response` topic, consumer group `response-worker`: route to correct channel sender based on `channel` field; `email` → `gmail/sender.send_gmail_reply`; `whatsapp` → `whatsapp/sender.send_whatsapp`; `webform` → update `messages.delivery_status` to `sent` (web form polls or uses SSE); retry once on `E001` before dead-lettering — **[M]**
  - AC: WhatsApp response event → Twilio API called with correct `to_number` and `Body ≤ 300 chars`; delivery_status updated to "sent" after success
  - Deps: T050, T032, T034

- [x] T052 Create `workers/metrics_worker.py` aiokafka consumer of `cs.metrics` topic, consumer group `metrics-worker`: deserialise tool-execution event; batch-insert into `agent_metrics` table every 5 seconds or 100 messages; handle DB errors without losing offset — **[S]**
  - AC: After 10 pipeline runs, `SELECT COUNT(*) FROM agent_metrics` ≥ 70 (7 steps × 10 runs); no duplicate rows for same event_id
  - Deps: T050, T013

- [x] T053 [US5] Create `workers/report_worker.py` APScheduler job running daily at `DAILY_REPORT_HOUR`: query `tickets` for `report_date`; aggregate `tickets_by_channel`, `top_topics` (from `messages.agent_decision` JSONB or LLM topic extraction), `mean_sentiment`, `escalation_count`, `escalation_rate`; upsert into `daily_reports`; handle zero-activity day (all zeros, `mean_sentiment=null`) — **[M]**
  - AC: After 5+ tickets exist, trigger manually via `POST /reports/daily/trigger`; report row created with correct counts; zero-activity date produces valid row with `total_tickets=0` not an error
  - Deps: T013, T048

- [x] T054 [US5] Create `api/routers/reports.py` with `GET /reports/daily/{date}` returning `DailyReport` schema; `POST /reports/daily/trigger` queuing an immediate report job; `GET /reports/daily/{date}` returns 404 for future dates — **[S]**
  - AC: `GET /reports/daily/2026-03-01` returns correct JSON after report generated; future date → 404; `POST /reports/daily/trigger` returns 202
  - Deps: T053, T021

---

## Phase 7: Kubernetes Manifests

**Purpose**: All K8s manifests written and dry-run validated.
**Checkpoint**: `kubectl apply --dry-run=client -f k8s/` passes with 0 errors.

- [x] T055 [P] Create `k8s/namespace.yaml` (`cs-fte` namespace) and `k8s/configmap.yaml` with non-secret env vars (`ENVIRONMENT`, `LOG_LEVEL`, `DAILY_REPORT_HOUR`, `KAFKA_BOOTSTRAP_SERVERS`, `POSTGRES_HOST/PORT/DB`); create `k8s/secret.yaml` template (base64 placeholders only, no real values, add to `.gitignore`) — **[S]**
  - AC: `kubectl apply --dry-run=client -f k8s/namespace.yaml -f k8s/configmap.yaml` passes; secret template has no real values committed
  - Deps: T005

- [x] T056 [P] Create `k8s/api-deployment.yaml` for `cs-api` Deployment: 2 replicas, image `cs-fte:api`, port 8000, envFrom configmap + secret, liveness probe `GET /` 200, readiness probe `GET /` 200, resource limits `cpu: 500m, memory: 512Mi` — **[S]**
  - AC: `kubectl apply --dry-run=client` passes; liveness/readiness probes configured; resource limits present
  - Deps: T055

- [x] T057 [P] Create `k8s/worker-deployment.yaml` with 3 separate Deployments (1 replica each): `cs-intake-worker` (`CMD python -m workers.intake_worker`), `cs-response-worker`, `cs-metrics-worker`; all use same image with different CMD; resource limits `cpu: 250m, memory: 256Mi` — **[S]**
  - AC: All 3 deployments dry-run clean; separate Deployment objects (not one with 3 containers)
  - Deps: T055

- [x] T058 [P] Create `k8s/hpa.yaml` HorizontalPodAutoscaler for `cs-api`: `minReplicas: 2`, `maxReplicas: 10`, CPU utilisation target 70%; matching `scaleTargetRef` to `cs-api` Deployment — **[S]**
  - AC: `kubectl apply --dry-run=client -f k8s/hpa.yaml` passes; scaleTargetRef name matches Deployment name exactly
  - Deps: T056

- [x] T059 [P] Create `k8s/services.yaml` with ClusterIP Service for `cs-api` (port 8000) and `cs-frontend` (port 3000); LoadBalancer Service exposing `cs-api` on port 80 → 8000 and `cs-frontend` on port 3000; note: use NodePort for local `minikube` testing — **[S]**
  - AC: `kubectl apply --dry-run=client` passes; selector labels match Deployment pod template labels
  - Deps: T056

- [x] T060 [P] Create `k8s/frontend-deployment.yaml` for Next.js frontend: 1 replica, image `cs-fte:frontend`, port 3000, env `NEXT_PUBLIC_API_URL` from configmap, resource limits `cpu: 200m, memory: 256Mi` — **[S]**
  - AC: Dry-run passes; NEXT_PUBLIC_API_URL configured via configmap reference
  - Deps: T055

- [x] T061 [P] Create `k8s/postgres-statefulset.yaml` single-node PostgreSQL StatefulSet with PersistentVolumeClaim (`5Gi`); note in comments this is for local/hackathon use only (prod: use managed DB); add init ConfigMap with `CREATE DATABASE cs_fte` — **[S]**
  - AC: Dry-run passes; PVC template present; readme note added: "replace with RDS/Cloud SQL in production"
  - Deps: T055

---

## Phase 8: Testing & E2E

**Purpose**: Unit, integration, and contract test coverage for all critical paths.
**Checkpoint**: `pytest tests/` passes; coverage ≥ 70% on `agent/tools/` and `database/repositories/`.

- [x] T062 [P] Write `tests/unit/test_format_for_channel.py`: test all three channels within limits; test trim on email (600→≤500 words); test trim on WhatsApp (400→≤300 chars); test E004 on double-fail; test greeting/sign-off injection for email; test markdown stripped for WhatsApp — **[M]**
  - AC: All 8 test cases pass; no OpenAI API call needed (mock LLM trim); 100% branch coverage on `format_for_channel.py`
  - Deps: T023

- [x] T063 [P] Write `tests/unit/test_escalation_rules.py`: test each of 7 guardrail triggers (pricing, refund, legal, competitor, sentiment<0.3, profanity, undocumented); test non-triggering messages; test `escalate_to_human` idempotency (second call → `already_escalated`) — **[M]**
  - AC: All 9 test cases pass; each trigger fires correct `trigger_rule` value; second escalation call for same ticket does not insert duplicate row
  - Deps: T039, T040

- [x] T064 [P] Write `tests/unit/test_identity_resolution.py`: test same email resolves same customer_id; test phone-only resolution; test wa_id resolution; test new identifiers linked to existing customer; test concurrent resolution (same email, two tasks) returns same id; test phone normalisation (various formats → E.164) — **[M]**
  - AC: All 6 test cases pass; concurrent test uses `asyncio.gather`; phone "+1 (415) 555-1234" normalises to "+14155551234"
  - Deps: T018

- [x] T065 [P] Write `tests/unit/test_idempotency.py`: test `create_ticket` duplicate within 60s window; test `send_response` duplicate with same response hash; test expired idempotency key (mock time) allows new ticket; test different customers same content creates two tickets — **[M]**
  - AC: All 4 test cases pass; no extra DB rows created on duplicate; `duplicate=True` returned correctly
  - Deps: T024, T028

- [x] T066 Write `tests/integration/test_pipeline_webform.py`: spin up test DB and mock Kafka; POST to `/webhooks/webform` with product question; assert response ≤300 words, ticket created, message row saved, metrics event produced — **[M]**
  - AC: Test passes end-to-end with real PostgreSQL (test DB); LLM calls mocked with pytest fixture returning canned responses; total test time < 10s
  - Deps: T030, T050

- [x] T067 [P] Write `tests/integration/test_pipeline_escalation.py`: POST refund request; assert holding message returned; escalation_record created with `trigger_rule="refund"`, `priority="P1"`; no KB search attempted; ticket status = `escalated` — **[M]**
  - AC: Test passes; verify pipeline stopped before step 6 normal format (mock shows KB tool NOT called after escalation decision)
  - Deps: T041

- [x] T068 [P] Write `tests/integration/test_cross_channel.py`: create customer via webform (email=x@y.com); send WhatsApp message with phone registered to same customer; assert both tickets share same `customer_id`; assert second pipeline receives history from first interaction — **[M]**
  - AC: Both tickets have identical `customer_id` UUID; history in second pipeline run shows `open_ticket_count=1` from first run
  - Deps: T045

- [x] T069 [P] Write `tests/integration/test_daily_report.py`: insert 10 tickets (mix of channels, statuses, sentiments); trigger report via `POST /reports/daily/trigger`; assert `DailyReport` row has correct `total_tickets`, `escalation_rate`, `mean_sentiment`; test zero-activity produces valid row — **[M]**
  - AC: Report counts match inserted fixture data; zero-activity report `total_tickets=0`, no exception raised
  - Deps: T053, T054

- [x] T070 [P] Write `tests/contract/test_tool_contracts.py`: for each of 6 tools, assert input schema validates correctly (Pydantic); assert success output matches schema; assert error output matches schema; assert idempotency key format is correct SHA-256 hex — **[M]**
  - AC: All 6 tool schemas validated; invalid inputs raise `ValidationError` with field names; no tool returns extra undocumented fields
  - Deps: T024, T025, T026, T027, T028, T039

---

## Phase N: Polish & Web Form UI

**Purpose**: Complete the React web form UI, add the simulation endpoint,
and validate the full quickstart guide end-to-end.

- [x] T071 [US1] Build `frontend/src/components/SupportForm.tsx` React component: email (required), name (optional), message (required, minLength=10); `POST` to `NEXT_PUBLIC_API_URL/webhooks/webform`; show spinner during submission; display response text in `ResponseDisplay.tsx` or show "A team member will follow up" on escalation — **[M]**
  - AC: Form submits to API; AI response renders within 3s; escalated response shows holding message without raw API data
  - Deps: T030

- [x] T072 [P] [US1] Style `frontend/src/app/page.tsx` with a minimal professional support widget layout: logo placeholder, form, response area, disclaimer "Powered by AI — escalated queries handled by humans"; mobile-responsive — **[S]**
  - AC: Renders correctly on 375px (mobile) and 1440px (desktop); no horizontal scroll on mobile
  - Deps: T071

- [ ] T073 [P] Validate `specs/001-cs-ai-fte/quickstart.md` end-to-end: follow all 10 steps from scratch on clean machine; verify all 4 smoke tests (A–D) pass; update any steps that are outdated — **[M]**
  - AC: Smoke test A (web form), B (escalation), C (cross-channel), D (KB miss) all produce expected results as described in quickstart.md
  - Deps: T038, T045, T050

- [x] T074 [P] Add `database/repositories/metrics_repo.py` `get_daily_summary(session, date) -> dict` aggregating ticket counts, mean sentiment, escalation rate from `tickets` + `messages` + `agent_metrics` tables for the report worker — **[S]**
  - AC: Returns correct aggregates for a date with known fixture data; empty date returns zeros not null errors
  - Deps: T013, T053

- [x] T075 [P] Add structured JSON logging to all pipeline steps: every tool call emits `{"timestamp","ticket_id","tool_name","input_hash","output_status","duration_ms","channel"}` to stdout; configure `LOG_LEVEL` from env; mask PII (email, phone) in log values — **[S]**
  - AC: Pipeline run produces ≥7 log lines (one per step); log is valid JSON; email/phone masked as `***` in output
  - Deps: T029

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)           → no deps — start immediately
Phase 2 (Database)        → Phase 1 complete
Phase 3 (Web Form MVP)    → Phase 2 complete — BLOCKS all user story work
Phase 4 (Channels)        → Phase 3 complete
Phase 5 (Agent/Escalation)→ Phase 3 complete (can overlap with Phase 4)
Phase 6 (Kafka)           → Phase 3 + Phase 5 complete
Phase 7 (K8s)             → Phase 5 complete (can run in parallel with Phase 6)
Phase 8 (Testing)         → Phase 4 + Phase 5 + Phase 6 tasks it covers
Phase N (Polish)          → Phase 6 + Phase 8 complete
```

### User Story Dependencies

| Story | Can Start After | Independently Testable When |
|-------|----------------|----------------------------|
| US1 (Inquiry Resolved) | Phase 2 complete | T030 merged (webform POST → response) |
| US3 (Escalation) | US1 T029 merged | T041 merged (guardrail stops pipeline) |
| US2 (Cross-Channel) | US1 + US3 merged | T045 merged (same customer_id across channels) |
| US4 (Ticket History) | US1 merged | T046–T047 merged (history APIs respond) |
| US5 (Daily Report) | Phase 6 complete | T053–T054 merged (report endpoint returns data) |

### Critical Path (MVP in < 24 hours)

```
T001 → T004 → T009-T014 → T015 → T016-T020 → T021 → T022-T028 → T029 → T030
```
This path delivers: Docker infra + DB + web form pipeline. Enough for Smoke Test A.

### Parallel Opportunities

#### Phase 1 (all independent, run together)
```
T002, T003, T004, T005, T006, T007, T008  (all after T001)
```

#### Phase 2 (migrations independent after T009)
```
T010, T011, T012, T013, T014  (all after T009, run together)
T015 (after all migrations)
T016 → T017 → [T018, T019, T020 in parallel]
```

#### Phase 3 (tools independent, wire last)
```
T022, T023, T024, T025, T026  (all after T021, run together)
T027 → T028 → T029 → T030
```

#### Phase 4 (channels independent of each other)
```
T031, T032 (WhatsApp, parallel) → T035
T033, T034 (Gmail, parallel)    → T036
T037, T038 (debug endpoint + KB seed, parallel)
```

#### Phase 8 (tests independent of each other)
```
T062, T063, T064, T065  (unit tests, all parallel)
T066, T067, T068, T069  (integration, parallel after their deps)
T070 (contract, after all tools)
```

---

## Implementation Strategy

### Hackathon MVP (Target: First 24 hours)

1. Complete Phase 1 (Setup) — ~2h
2. Complete Phase 2 (Database) — ~4h
3. Complete Phase 3 T021→T030 (Web Form pipeline) — ~6h
4. **STOP + VALIDATE**: Smoke Test A passes (web form → AI response → DB row)
5. Demo-ready checkpoint: working end-to-end for one channel

### Incremental Delivery

```
+24h: Phase 4 (channels) — all 3 channels live → Smoke Tests A+B+C+D
+36h: Phase 5 (escalation + sub-agents + Kafka) → full production pipeline
+48h: Phase 6 (Kafka workers) + Phase 7 (K8s dry-run) → deployment-ready
+56h: Phase 8 (tests) + Phase N (polish) → demo quality
```

### Parallel Team Strategy (2 developers)

```
Developer A: Phase 2 (DB) → Phase 3 (pipeline) → Phase 5 (escalation)
Developer B: Phase 1 (setup) → Phase 4 (channels) → Phase 6 (Kafka) → Phase 8 (tests)
Sync point: After Phase 3 T029 (orchestrator) — integrate channels + escalation together
```

---

## Task Summary

| Phase | Tasks | Parallel | Story |
|-------|-------|----------|-------|
| Phase 1: Incubation | T001–T008 | 7/8 | Setup |
| Phase 2: Database | T009–T020 | 10/12 | Foundational |
| Phase 3: Web Form MVP | T021–T030 | 5/10 | US1 |
| Phase 4: Channels | T031–T038 | 5/8 | US1 |
| Phase 5: Agent/Escalation | T039–T047 | 2/9 | US2, US3, US4 |
| Phase 6: Kafka | T048–T054 | 0/7 | US5 |
| Phase 7: Kubernetes | T055–T061 | 6/7 | Deploy |
| Phase 8: Testing | T062–T070 | 7/9 | All |
| Phase N: Polish | T071–T075 | 4/5 | US1 |
| **Total** | **75 tasks** | **47 parallelizable** | |
