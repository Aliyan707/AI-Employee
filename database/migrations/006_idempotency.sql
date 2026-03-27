-- 006_idempotency.sql
-- Idempotency key store for deduplicating tool calls.
-- Uses SHA-256 hex keys with TTL-based expiry.

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key        CHAR(64)     PRIMARY KEY,   -- SHA-256 hex string
    result     JSONB,                      -- cached response payload
    created_at TIMESTAMPTZ  DEFAULT NOW(),
    expires_at TIMESTAMPTZ  NOT NULL
);

-- Index for efficient TTL cleanup queries
-- Cleanup query: DELETE FROM idempotency_keys WHERE expires_at < NOW();
CREATE INDEX IF NOT EXISTS idx_idem_expires ON idempotency_keys (expires_at);
