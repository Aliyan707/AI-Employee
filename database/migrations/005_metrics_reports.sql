-- 005_metrics_reports.sql
-- Agent performance metrics and daily aggregated reports.

-- agent_metrics: append-only telemetry for every tool call in the pipeline
CREATE TABLE IF NOT EXISTS agent_metrics (
    id            BIGSERIAL    PRIMARY KEY,
    ticket_id     UUID         REFERENCES tickets(id),   -- nullable (pre-ticket events)
    tool_name     VARCHAR(64)  NOT NULL,
    channel       channel_type,
    input_hash    CHAR(64),
    output_status VARCHAR(16)  NOT NULL,  -- 'success' | 'E001'..'E005'
    duration_ms   INTEGER,
    error_code    VARCHAR(8),
    created_at    TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_ticket  ON agent_metrics (ticket_id);
CREATE INDEX IF NOT EXISTS idx_metrics_created ON agent_metrics (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_status  ON agent_metrics (output_status);

-- daily_reports: one row per calendar day, populated by report_worker
CREATE TABLE IF NOT EXISTS daily_reports (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date        DATE        NOT NULL UNIQUE,
    total_tickets      INTEGER     DEFAULT 0,
    tickets_by_channel JSONB,       -- {"email":N,"whatsapp":N,"webform":N}
    top_topics         JSONB,       -- [{"topic":"...","count":N}, ...]  top 5
    mean_sentiment     NUMERIC(4,3),
    escalation_count   INTEGER     DEFAULT 0,
    escalation_rate    NUMERIC(5,2),   -- percentage 0.00–100.00
    generated_at       TIMESTAMPTZ DEFAULT NOW()
);
