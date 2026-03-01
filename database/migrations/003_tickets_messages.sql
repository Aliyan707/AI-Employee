-- 003_tickets_messages.sql
-- Ticket lifecycle, messages, and escalation records.

-- ENUMs (created before tables that reference them)
CREATE TYPE ticket_status AS ENUM (
    'open', 'escalated', 'pending_human', 'resolved', 'closed'
);

CREATE TYPE ticket_priority AS ENUM ('P1', 'P2', 'P3');

CREATE TYPE channel_type AS ENUM ('email', 'whatsapp', 'webform');

CREATE TYPE message_direction AS ENUM ('inbound', 'outbound');

-- Main tickets table
-- One ticket per support interaction lifecycle
CREATE TABLE IF NOT EXISTS tickets (
    id                UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id       UUID            NOT NULL REFERENCES customers(id),
    channel           channel_type    NOT NULL,
    status            ticket_status   NOT NULL DEFAULT 'open',
    priority          ticket_priority DEFAULT 'P3',
    subject           TEXT,                           -- extracted from first message
    escalated         BOOLEAN         DEFAULT FALSE,
    escalation_reason TEXT,
    parent_ticket_id  UUID            REFERENCES tickets(id),  -- for follow-up threads
    kb_article_ids    UUID[],                         -- KB articles cited in response
    created_at        TIMESTAMPTZ     DEFAULT NOW(),
    updated_at        TIMESTAMPTZ     DEFAULT NOW(),
    resolved_at       TIMESTAMPTZ,
    resolved_by       VARCHAR(255)                    -- 'ai' or human agent name
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets (customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status   ON tickets (status);
CREATE INDEX IF NOT EXISTS idx_tickets_channel  ON tickets (channel);
CREATE INDEX IF NOT EXISTS idx_tickets_created  ON tickets (created_at DESC);

-- Messages: every inbound and outbound message under a ticket
CREATE TABLE IF NOT EXISTS messages (
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

CREATE INDEX IF NOT EXISTS idx_messages_ticket ON messages (ticket_id, sent_at);
CREATE INDEX IF NOT EXISTS idx_messages_hash   ON messages (content_hash);

-- Escalation records: exactly one per escalated ticket
CREATE TABLE IF NOT EXISTS escalation_records (
    id               BIGSERIAL       PRIMARY KEY,
    ticket_id        UUID            NOT NULL UNIQUE REFERENCES tickets(id),
    trigger_rule     VARCHAR(64)     NOT NULL,  -- 'pricing'|'sentiment<0.3'|'profanity' etc.
    trigger_detail   TEXT,
    sentiment_score  NUMERIC(4,3),
    priority         ticket_priority NOT NULL,
    assigned_agent   VARCHAR(255),               -- human agent (nullable until assigned)
    resolved         BOOLEAN         DEFAULT FALSE,
    created_at       TIMESTAMPTZ     DEFAULT NOW(),
    resolved_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_escalation_ticket   ON escalation_records (ticket_id);
CREATE INDEX IF NOT EXISTS idx_escalation_resolved ON escalation_records (resolved, created_at);
