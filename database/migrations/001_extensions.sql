-- 001_extensions.sql
-- Enable PostgreSQL extensions required by the application.
-- uuid-ossp: provides gen_random_uuid() for UUID generation
-- vector: pgvector extension for semantic search embeddings

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
