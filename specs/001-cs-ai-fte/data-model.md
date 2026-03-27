# Data Model: CS AI FTE — 24/7 Customer Success Agent

**Date**: 2026-03-01 | **Branch**: `001-cs-ai-fte`
**Database**: PostgreSQL 16 + pgvector extension

---

## Schema Overview

```
customers
  └─── customer_identifiers (1:N)
  └─── tickets (1:N)
         └─── messages (1:N)
         └─── escalation_records (1:0..1)

knowledge_base (standalone, vector-indexed)
agent_metrics  (standalone, append-only)
daily_reports  (standalone, one per day)
idempotency_keys (standalone, TTL-cleaned)
```

---

## Table Definitions

### `customers`

Central customer record. Canonical source of truth for identity.

```sql
CREATE TABLE customers (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name  VARCHAR(255),
    company       VARCHAR(255),
    primary_email VARCHAR(320) UNIQUE,        -- normalised to lowercase
    primary_phone VARCHAR(20),                -- E.164 format, e.g. +14155552671
    created_at    TIMESTAMPTZ  DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  DEFAULT NOW()
);
CREATE INDEX idx_customers_email ON customers (primary_email);
CREATE INDEX idx_customers_phone ON customers (primary_phone);
```

---

### `customer_identifiers`

Maps any contact method to a `customer_id`. Supports cross-channel
identity resolution (FR-007, FR-008).

```sql
CREATE TYPE identifier_type AS ENUM (
    'email', 'phone', 'whatsapp_id', 'web_session'
);

CREATE TABLE customer_identifiers (
    id              BIGSERIAL    PRIMARY KEY,
    customer_id     UUID         NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type identifier_type NOT NULL,
    identifier_value VARCHAR(320) NOT NULL,    -- normalised value
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (identifier_type, identifier_value)
);
CREATE INDEX idx_ci_lookup ON customer_identifiers (identifier_type, identifier_value);
CREATE INDEX idx_ci_customer ON customer_identifiers (customer_id);
```

**Resolution query**:
```sql
SELECT customer_id FROM customer_identifiers
WHERE (identifier_type, identifier_value) IN (
    ('email', $email), ('phone', $phone), ('whatsapp_id', $wa_id)
)
LIMIT 1;
```

---

### `tickets`

One ticket per support interaction lifecycle (FR-020, FR-021).

```sql
CREATE TYPE ticket_status AS ENUM (
    'open', 'escalated', 'pending_human', 'resolved', 'closed'
);
CREATE TYPE ticket_priority AS ENUM ('P1', 'P2', 'P3');
CREATE TYPE channel_type AS ENUM ('email', 'whatsapp', 'webform');

CREATE TABLE tickets (
    id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id       UUID          NOT NULL REFERENCES customers(id),
    channel           channel_type  NOT NULL,
    status            ticket_status NOT NULL DEFAULT 'open',
    priority          ticket_priority DEFAULT 'P3',
    subject           TEXT,                           -- extracted from first message
    escalated         BOOLEAN       DEFAULT FALSE,
    escalation_reason TEXT,
    parent_ticket_id  UUID          REFERENCES tickets(id),  -- for follow-ups
    kb_article_ids    UUID[],                         -- articles cited in response
    created_at        TIMESTAMPTZ   DEFAULT NOW(),
    updated_at        TIMESTAMPTZ   DEFAULT NOW(),
    resolved_at       TIMESTAMPTZ,
    resolved_by       VARCHAR(255)                    -- human agent name or 'ai'
);
CREATE INDEX idx_tickets_customer ON tickets (customer_id);
CREATE INDEX idx_tickets_status   ON tickets (status);
CREATE INDEX idx_tickets_channel  ON tickets (channel);
CREATE INDEX idx_tickets_created  ON tickets (created_at DESC);
```

---

### `messages`

Every inbound and outbound message under a ticket (FR-021).

```sql
CREATE TYPE message_direction AS ENUM ('inbound', 'outbound');

CREATE TABLE messages (
    id               BIGSERIAL         PRIMARY KEY,
    ticket_id        UUID              NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    direction        message_direction NOT NULL,
    channel          channel_type      NOT NULL,
    raw_content      TEXT              NOT NULL,
    content_hash     CHAR(64),                      -- SHA-256, for idempotency
    sentiment_score  NUMERIC(4,3),                  -- 0.000 – 1.000, NULL if not scored
    agent_decision   JSONB,                         -- step-by-step pipeline decisions
    sent_at          TIMESTAMPTZ       DEFAULT NOW(),
    delivery_status  VARCHAR(32)       DEFAULT 'pending'  -- pending|sent|failed
);
CREATE INDEX idx_messages_ticket   ON messages (ticket_id, sent_at);
CREATE INDEX idx_messages_hash     ON messages (content_hash);
```

---

### `escalation_records`

Created exactly once per escalated ticket (FR-018).

```sql
CREATE TABLE escalation_records (
    id               BIGSERIAL    PRIMARY KEY,
    ticket_id        UUID         NOT NULL UNIQUE REFERENCES tickets(id),
    trigger_rule     VARCHAR(64)  NOT NULL,  -- e.g. 'pricing', 'sentiment<0.3', 'profanity'
    trigger_detail   TEXT,
    sentiment_score  NUMERIC(4,3),
    priority         ticket_priority NOT NULL,
    assigned_agent   VARCHAR(255),           -- human agent (nullable until assigned)
    resolved         BOOLEAN      DEFAULT FALSE,
    created_at       TIMESTAMPTZ  DEFAULT NOW(),
    resolved_at      TIMESTAMPTZ
);
CREATE INDEX idx_escalation_ticket   ON escalation_records (ticket_id);
CREATE INDEX idx_escalation_resolved ON escalation_records (resolved, created_at);
```

---

### `knowledge_base`

Product documentation with vector embeddings for semantic search (FR-010).

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_base (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    topic_tags  TEXT[],
    embedding   VECTOR(1536),                 -- text-embedding-3-small
    source_url  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for approximate nearest-neighbour search (<= 500ms SLO)
CREATE INDEX idx_kb_embedding ON knowledge_base
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

### `agent_metrics`

Append-only performance telemetry for every tool call (FR-025).

```sql
CREATE TABLE agent_metrics (
    id            BIGSERIAL    PRIMARY KEY,
    ticket_id     UUID         REFERENCES tickets(id),
    tool_name     VARCHAR(64)  NOT NULL,
    channel       channel_type,
    input_hash    CHAR(64),
    output_status VARCHAR(16)  NOT NULL,  -- 'success' | 'E001'..'E005'
    duration_ms   INTEGER,
    error_code    VARCHAR(8),
    created_at    TIMESTAMPTZ  DEFAULT NOW()
);
CREATE INDEX idx_metrics_ticket  ON agent_metrics (ticket_id);
CREATE INDEX idx_metrics_created ON agent_metrics (created_at DESC);
CREATE INDEX idx_metrics_status  ON agent_metrics (output_status);
```

---

### `daily_reports`

One row per calendar day; populated by the report worker (FR-023).

```sql
CREATE TABLE daily_reports (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date       DATE        NOT NULL UNIQUE,
    total_tickets     INTEGER     DEFAULT 0,
    tickets_by_channel JSONB,     -- {"email":N,"whatsapp":N,"webform":N}
    top_topics        JSONB,      -- [{"topic":"..","count":N}, ...]  top 5
    mean_sentiment    NUMERIC(4,3),
    escalation_count  INTEGER     DEFAULT 0,
    escalation_rate   NUMERIC(5,2),  -- percentage 0.00–100.00
    generated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

### `idempotency_keys`

TTL-based deduplication store (FR-022, Constitution Principle VII).

```sql
CREATE TABLE idempotency_keys (
    key        CHAR(64)     PRIMARY KEY,   -- SHA-256 hex
    result     JSONB,                      -- cached response payload
    created_at TIMESTAMPTZ  DEFAULT NOW(),
    expires_at TIMESTAMPTZ  NOT NULL
);
CREATE INDEX idx_idem_expires ON idempotency_keys (expires_at);
-- Cleanup job: DELETE FROM idempotency_keys WHERE expires_at < NOW();
```

---

## State Machine: Ticket Status

```
                  ┌─────────────┐
   message        │    open     │
   arrives ──────►│             │
                  └──────┬──────┘
                         │
             ┌───────────┴───────────┐
             │                       │
        guardrail                AI resolves
        triggered                    │
             │                       ▼
             ▼                ┌─────────────┐
      ┌────────────┐          │  resolved   │
      │ escalated  │          └──────┬──────┘
      └─────┬──────┘                 │
            │                   customer
       human takes               closes /
       action                   no reply 7d
            │                       │
            ▼                       ▼
     ┌──────────────┐         ┌──────────┐
     │pending_human │         │  closed  │
     └──────┬───────┘         └──────────┘
            │ human resolves
            ▼
       ┌──────────┐
       │ resolved │
       └──────────┘
```

---

## Migration Files

| File | Description |
|------|-------------|
| `001_extensions.sql` | Enable `uuid-ossp`, `pgvector` |
| `002_customers.sql` | `customers` + `customer_identifiers` |
| `003_tickets_messages.sql` | `tickets`, `messages`, `escalation_records` |
| `004_kb.sql` | `knowledge_base` + HNSW index |
| `005_metrics_reports.sql` | `agent_metrics`, `daily_reports` |
| `006_idempotency.sql` | `idempotency_keys` |

Each file ships a paired `_down.sql` for rollback (Constitution requirement).
