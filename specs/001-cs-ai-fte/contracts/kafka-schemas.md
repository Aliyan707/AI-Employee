# Kafka Message Schemas: CS AI FTE

**Date**: 2026-03-01 | **Branch**: `001-cs-ai-fte`

---

## Topic: `cs.intake`

**Partitions**: 3 (one per channel key: email=0, whatsapp=1, webform=2)
**Retention**: 24 hours
**Consumer group**: `intake-worker`
**Partition key**: channel name

### Message Schema
```json
{
  "schema_version": "1.0",
  "event_type": "customer.message.received",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "channel": "email | whatsapp | webform",
  "idempotency_key": "sha256-hex",
  "payload": {
    "raw_content":  "string",
    "content_hash": "sha256-hex",
    "customer_identifiers": {
      "email":        "string | null",
      "phone":        "string | null (E.164)",
      "whatsapp_id":  "string | null",
      "web_session":  "string | null"
    },
    "channel_metadata": {
      "email": {
        "gmail_message_id": "string",
        "thread_id":        "string",
        "subject":          "string",
        "from_address":     "string"
      },
      "whatsapp": {
        "twilio_sid":  "string",
        "wa_from":     "string",
        "wa_to":       "string"
      },
      "webform": {
        "session_id":  "string",
        "form_name":   "string | null"
      }
    }
  }
}
```

---

## Topic: `cs.response`

**Partitions**: 3 (partitioned by channel)
**Retention**: 1 hour
**Consumer group**: `response-worker`

### Message Schema
```json
{
  "schema_version": "1.0",
  "event_type": "agent.response.ready",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "ticket_id": "uuid",
  "channel": "email | whatsapp | webform",
  "idempotency_key": "sha256-hex",
  "payload": {
    "response_text":  "string (already formatted for channel)",
    "response_hash":  "sha256-hex",
    "is_escalation":  false,
    "kb_article_ids": ["uuid"],
    "channel_metadata": {
      "email": {
        "reply_to_thread_id": "string",
        "to_address":         "string"
      },
      "whatsapp": {
        "to_number": "string (E.164)"
      },
      "webform": {
        "session_id": "string"
      }
    }
  }
}
```

---

## Topic: `cs.escalation`

**Partitions**: 1
**Retention**: 7 days
**Consumer group**: `escalation-worker` (writes to human queue)

### Message Schema
```json
{
  "schema_version": "1.0",
  "event_type": "ticket.escalated",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "ticket_id": "uuid",
  "customer_id": "uuid",
  "channel": "string",
  "payload": {
    "trigger_rule":    "pricing|refund|legal|competitor|sentiment|profanity|undocumented",
    "trigger_detail":  "string",
    "sentiment_score": 0.22,
    "priority":        "P1|P2|P3",
    "conversation_summary": "string",
    "customer_holding_message": "string"
  }
}
```

---

## Topic: `cs.metrics`

**Partitions**: 1
**Retention**: 30 days
**Consumer group**: `metrics-worker` (writes to `agent_metrics` table)

### Message Schema
```json
{
  "schema_version": "1.0",
  "event_type": "agent.tool.executed",
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "ticket_id": "uuid",
  "payload": {
    "tool_name":      "string",
    "channel":        "string",
    "input_hash":     "sha256-hex",
    "output_status":  "success|E001|E002|E003|E004|E005",
    "duration_ms":    142,
    "error_code":     "string | null"
  }
}
```
