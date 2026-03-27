-- 003_tickets_messages_down.sql
-- Drop ticket, message, and escalation tables.

DROP TABLE IF EXISTS escalation_records CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TYPE  IF EXISTS message_direction;
DROP TYPE  IF EXISTS channel_type;
DROP TYPE  IF EXISTS ticket_priority;
DROP TYPE  IF EXISTS ticket_status;
