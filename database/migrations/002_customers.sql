-- 002_customers.sql
-- Customer identity tables.
-- customers: canonical customer record
-- customer_identifiers: cross-channel identifier mapping

-- Identifier type enum
CREATE TYPE identifier_type AS ENUM (
    'email', 'phone', 'whatsapp_id', 'web_session'
);

-- Central customer record
CREATE TABLE IF NOT EXISTS customers (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name  VARCHAR(255),
    company       VARCHAR(255),
    primary_email VARCHAR(320) UNIQUE,        -- normalised to lowercase
    primary_phone VARCHAR(20),                -- E.164 format, e.g. +14155552671
    created_at    TIMESTAMPTZ   DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (primary_email);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers (primary_phone);

-- Cross-channel identifier mapping
-- One customer can have multiple identifiers (email, phone, WhatsApp ID, etc.)
CREATE TABLE IF NOT EXISTS customer_identifiers (
    id               BIGSERIAL       PRIMARY KEY,
    customer_id      UUID            NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type  identifier_type NOT NULL,
    identifier_value VARCHAR(320)    NOT NULL,    -- normalised value
    created_at       TIMESTAMPTZ     DEFAULT NOW(),
    UNIQUE (identifier_type, identifier_value)
);

-- Fast lookup index for identity resolution
CREATE INDEX IF NOT EXISTS idx_ci_lookup   ON customer_identifiers (identifier_type, identifier_value);
CREATE INDEX IF NOT EXISTS idx_ci_customer ON customer_identifiers (customer_id);
