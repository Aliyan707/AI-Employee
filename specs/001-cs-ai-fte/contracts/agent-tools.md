# Agent Tool Contracts: CS AI FTE

**Date**: 2026-03-01 | **Branch**: `001-cs-ai-fte`

All tools are called by the OrchestratorAgent via the OpenAI Agents SDK.
Every tool MUST be idempotent where marked. Error codes follow the
constitution taxonomy (E001–E005).

---

## Tool: `create_ticket`

**Idempotent**: YES (60-second dedup window by content_hash + customer_id)

### Input
```json
{
  "customer_id":   "uuid",
  "channel":       "email | whatsapp | webform",
  "raw_content":   "string (full message text)",
  "content_hash":  "string (SHA-256 of raw_content)",
  "subject":       "string (optional, auto-extracted if omitted)",
  "parent_ticket_id": "uuid | null"
}
```

### Output — Success
```json
{
  "ticket_id":    "uuid",
  "status":       "open",
  "created":      true,
  "duplicate":    false
}
```

### Output — Duplicate (idempotent hit)
```json
{
  "ticket_id":    "uuid",
  "status":       "open",
  "created":      false,
  "duplicate":    true
}
```

### Errors
| Code | Condition | Message |
|------|-----------|---------|
| E001 | DB timeout | "Ticket creation timed out" |
| E005 | Auth failure | "DB connection auth failed" |

---

## Tool: `get_customer_history`

**Idempotent**: YES (read-only)

### Input
```json
{
  "customer_id": "uuid",
  "limit":       20,
  "channel_filter": "email | whatsapp | webform | null (all)"
}
```

### Output — Success
```json
{
  "customer": {
    "id":           "uuid",
    "display_name": "string",
    "company":      "string",
    "channels_used": ["email", "whatsapp"]
  },
  "tickets": [
    {
      "ticket_id":   "uuid",
      "channel":     "string",
      "status":      "string",
      "subject":     "string",
      "created_at":  "ISO8601",
      "message_count": 3
    }
  ],
  "last_sentiment": 0.72,
  "open_ticket_count": 1
}
```

### Output — Not Found
```json
{
  "customer": null,
  "tickets":  [],
  "last_sentiment": null,
  "open_ticket_count": 0
}
```

### Errors
| Code | Condition | Message |
|------|-----------|---------|
| E001 | DB timeout | "History lookup timed out" |
| E002 | Customer not found | Returns not-found payload (no error) |

---

## Tool: `search_knowledge_base`

**Idempotent**: YES (read-only)

### Input
```json
{
  "query":              "string (customer question, normalised)",
  "similarity_threshold": 0.75,
  "top_k":              5
}
```

### Output — Success
```json
{
  "results": [
    {
      "article_id":   "uuid",
      "title":        "string",
      "content":      "string",
      "score":        0.87,
      "topic_tags":   ["billing", "account"]
    }
  ],
  "kb_miss": false
}
```

### Output — KB Miss
```json
{
  "results": [],
  "kb_miss": true
}
```

### Errors
| Code | Condition | Message |
|------|-----------|---------|
| E001 | pgvector timeout | "KB search timed out — proceeding without KB context" |
| E002 | No articles above threshold | Returns kb_miss:true (graceful, not error) |

---

## Tool: `escalate_to_human`

**Idempotent**: YES (one escalation record per ticket)

### Input
```json
{
  "ticket_id":       "uuid",
  "trigger_rule":    "pricing | refund | legal | competitor | sentiment | profanity | undocumented",
  "trigger_detail":  "string (specific trigger text)",
  "sentiment_score": 0.22,
  "priority":        "P1 | P2 | P3",
  "conversation_context": "string (full history summary)"
}
```

### Output — Success
```json
{
  "escalation_id":   "bigint",
  "ticket_id":       "uuid",
  "status":          "escalated",
  "queue_position":  3,
  "customer_message": "A team member will contact you shortly."
}
```

### Output — Already Escalated (idempotent hit)
```json
{
  "escalation_id":   "bigint",
  "ticket_id":       "uuid",
  "status":          "already_escalated",
  "queue_position":  null,
  "customer_message": null
}
```

### Errors
| Code | Condition | Message |
|------|-----------|---------|
| E001 | Escalation queue timeout | "Escalation queue unreachable — ticket flagged for manual review" |
| E005 | Auth failure | "Escalation auth failed" |

---

## Tool: `send_response`

**Idempotent**: YES (keyed by ticket_id + response_hash)

### Input
```json
{
  "ticket_id":     "uuid",
  "channel":       "email | whatsapp | webform",
  "response_text": "string (already formatted for channel)",
  "response_hash": "string (SHA-256 of response_text)",
  "metadata": {
    "kb_article_ids": ["uuid"],
    "sentiment_score": 0.72,
    "is_escalation_holding_message": false
  }
}
```

### Output — Success
```json
{
  "message_id":    "bigint",
  "ticket_id":     "uuid",
  "channel":       "string",
  "sent":          true,
  "duplicate":     false,
  "sent_at":       "ISO8601"
}
```

### Output — Duplicate (idempotent hit)
```json
{
  "message_id":    "bigint",
  "ticket_id":     "uuid",
  "channel":       "string",
  "sent":          false,
  "duplicate":     true
}
```

### Errors
| Code | Condition | Message |
|------|-----------|---------|
| E001 | Channel API timeout | "Channel delivery timed out — will retry" |
| E004 | Format validation fail | "Response exceeds channel limits after reformat attempt" |
| E005 | Channel auth failure | "Channel credential invalid" |

---

## Tool: `analyze_sentiment` (Internal sub-agent tool)

**Idempotent**: YES (deterministic per input text)

### Input
```json
{
  "text":      "string (customer message)",
  "ticket_id": "uuid"
}
```

### Output
```json
{
  "score":      0.24,
  "label":      "angry | negative | neutral | positive",
  "profanity_detected": false,
  "escalate":   true
}
```

---

## Tool: `format_for_channel` (Internal orchestrator call)

Not an SDK tool — a pure Python function called inline.

### Signature
```python
def format_for_channel(
    raw_response: str,
    channel: Literal["email", "whatsapp", "webform"],
    customer_name: str | None = None,
    retry: bool = False
) -> FormattedResponse:
    ...

@dataclass
class FormattedResponse:
    text: str
    within_limits: bool
    word_count: int | None
    char_count: int | None
    error: str | None   # E004 detail if within_limits=False after retry
```
