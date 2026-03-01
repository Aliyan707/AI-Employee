-- 004_kb.sql
-- Knowledge base with pgvector embeddings for semantic search.

CREATE TABLE IF NOT EXISTS knowledge_base (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    topic_tags  TEXT[],
    embedding   VECTOR(1536),                -- text-embedding-3-small output dimension
    source_url  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for approximate nearest-neighbour cosine similarity search
-- m=16: max connections per node (higher = better recall, more memory)
-- ef_construction=64: size of dynamic candidate list during build (higher = better quality)
-- Meets the < 500ms SLO for KB search at scale
CREATE INDEX IF NOT EXISTS idx_kb_embedding ON knowledge_base
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
