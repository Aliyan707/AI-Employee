# Quickstart: CS AI FTE — Local Development

**Date**: 2026-03-01 | **Branch**: `001-cs-ai-fte`
**Estimated setup time**: ~15 minutes

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Docker Desktop | 4.x+ | `docker --version` |
| Docker Compose | v2 | `docker compose version` |
| Python | 3.12+ | `python --version` |
| Node.js | 20 LTS | `node --version` |
| Git | any | `git --version` |

---

## 1. Clone & Configure Environment

```bash
git clone <repo-url> cs-ai-fte
cd cs-ai-fte
git checkout 001-cs-ai-fte

cp .env.example .env
```

Edit `.env` and fill in:

```dotenv
# OpenAI
OPENAI_API_KEY=sk-...

# Gmail (Google Cloud OAuth2 service account or Gmail API credentials)
GMAIL_CREDENTIALS_PATH=./secrets/gmail_credentials.json
GMAIL_TOPIC_NAME=projects/<project>/topics/cs-intake-gmail

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cs_fte
POSTGRES_USER=cs_fte_user
POSTGRES_PASSWORD=changeme

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# App
SECRET_KEY=change-this-in-production
ENVIRONMENT=development
LOG_LEVEL=INFO
DAILY_REPORT_HOUR=7        # 24h, business local time
ESCALATION_QUEUE_WEBHOOK=http://localhost:9999/escalation  # stub for local dev
```

---

## 2. Start Infrastructure (Docker Compose)

```bash
docker compose up -d postgres kafka zookeeper
```

Wait for health checks (~20s):

```bash
docker compose ps   # all should show "healthy"
```

---

## 3. Run Database Migrations

```bash
cd database
python migrate.py up
# Expected output:
#   ✅ 001_extensions
#   ✅ 002_customers
#   ✅ 003_tickets_messages
#   ✅ 004_kb
#   ✅ 005_metrics_reports
#   ✅ 006_idempotency
```

To rollback a migration:
```bash
python migrate.py down 005_metrics_reports
```

---

## 4. Seed Knowledge Base

```bash
python database/seed_kb.py --source docs/product_faq.md
# Embeds articles using text-embedding-3-small and inserts into knowledge_base
```

---

## 5. Install Python Dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 6. Start the FastAPI Server

```bash
uvicorn api.main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

---

## 7. Start Kafka Workers

Open three terminal tabs:

```bash
# Tab 1 — Intake worker (drives the 7-step pipeline)
python -m workers.intake_worker

# Tab 2 — Response worker (sends channel responses)
python -m workers.response_worker

# Tab 3 — Metrics writer
python -m workers.metrics_worker
```

---

## 8. Start the Web Form (Next.js)

```bash
cd frontend
npm install
npm run dev
# Open: http://localhost:3000
```

---

## 9. Smoke Tests

### Test A: Web Form end-to-end
1. Open http://localhost:3000
2. Fill in email `test@example.com`, message `How do I reset my password?`
3. Submit
4. Expected: response appears in the form UI within 3 seconds
5. Check DB: `SELECT * FROM tickets ORDER BY created_at DESC LIMIT 1;`

### Test B: Escalation trigger
1. Send message `I want a full refund immediately` via web form
2. Expected: response = "A team member will contact you shortly."
3. Check: `SELECT * FROM escalation_records ORDER BY created_at DESC LIMIT 1;`
   — `trigger_rule` should be `refund`, `priority` should be `P1`

### Test C: Cross-channel continuity
1. POST to `http://localhost:8000/webhooks/webform` with `email=x@y.com`
2. POST to `http://localhost:8000/webhooks/whatsapp` with `From=whatsapp:+1XXXXXXXX`
   (use a phone registered to same customer)
3. Check: both tickets link to the same `customer_id`

### Test D: KB miss
1. Send message `What is the airspeed velocity of an unladen swallow?`
2. Expected: agent responds with an honest "I'll look into this" message
3. Check: ticket has `escalation_reason` = null but KB miss flag in `agent_decision` JSON

---

## 10. Run Test Suite

```bash
pytest tests/unit/           # ~5s
pytest tests/integration/    # ~30s (requires Docker infra running)
pytest tests/contract/       # ~10s
```

---

## Useful Commands

```bash
# View Kafka topics
docker exec -it kafka kafka-topics.sh --bootstrap-server localhost:9092 --list

# Consume cs.intake topic (debug)
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic cs.intake --from-beginning

# Trigger daily report manually
curl -X POST http://localhost:8000/reports/daily/trigger \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-03-01"}'

# Reset DB (dev only)
python database/migrate.py reset
```

---

## Stopping Everything

```bash
docker compose down      # stops infra (keeps volumes)
docker compose down -v   # stops infra AND deletes volumes (fresh start)
```
