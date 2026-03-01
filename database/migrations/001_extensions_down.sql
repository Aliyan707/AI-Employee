-- 001_extensions_down.sql
-- Drop PostgreSQL extensions.
-- WARNING: Dropping vector extension will fail if knowledge_base table exists.
-- Run 004_kb_down.sql first.

DROP EXTENSION IF EXISTS vector;
DROP EXTENSION IF EXISTS "uuid-ossp";
