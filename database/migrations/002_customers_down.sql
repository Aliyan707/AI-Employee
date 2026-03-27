-- 002_customers_down.sql
-- Drop customer tables and associated enum types.

DROP TABLE IF EXISTS customer_identifiers CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TYPE  IF EXISTS identifier_type;
