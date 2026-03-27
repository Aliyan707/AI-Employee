---
id: "001"
title: "Customer Success Digital FTE Constitution"
stage: constitution
date: 2026-03-01
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: Aliyan 707
command: /sp.constitution
labels: ["constitution","customer-success","multi-channel","ai-agent","guardrails","slo","escalation"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - history/prompts/constitution/001-customer-success-fte-constitution.constitution.prompt.md
tests:
  - "N/A — constitution stage; no tests"
---

## Prompt

/sp.constitution
Project: Customer Success Digital FTE (24/7 AI Employee for SaaS support)

Unbreakable rules / constitution:

1. Multi-channel MUST: Email (Gmail), WhatsApp (Twilio), Web Form – sab responses channel ke hisaab se adapt hon (formal/long email, short/conversational WhatsApp, semi-formal web)

2. ALWAYS follow strict workflow order:
   - 1. create_ticket (channel metadata ke saath)
   - 2. get_customer_history (cross-channel)
   - 3. search_knowledge_base (if product question)
   - 4. analyze sentiment
   - 5. decide escalation
   - 6. format response channel ke liye
   - 7. send_response (kabhi direct mat jawab dena)

3. Hard guardrails (kabhi violate mat karna):
   - Pricing, refunds, legal, competitors → escalate immediately with reason
   - Angry customer (sentiment < 0.3) ya profanity → escalate
   - Response limits: Email ≤500 words, WhatsApp ≤300 chars, Web ≤300 words
   - NEVER promise undocumented features

4. PostgreSQL is our CRM – external Salesforce/HubSpot nahi use karna

5. Performance targets: <3s processing, <20% escalation, >95% cross-channel customer ID accuracy

6. Development style: Incubation → Specialization (Claude Code se prototype → OpenAI Agents SDK production)

Generate constitution.md with these rules + any additional best practices for reliable AI agents.

## Response snapshot

Created `.specify/memory/constitution.md` v1.0.0 with 7 core principles:
I. Multi-Channel Adaptive Response (Email/WhatsApp/Web with format+length rules)
II. Strict 7-Step Workflow Order (create_ticket → … → send_response)
III. Hard Guardrails & Escalation Rules (pricing/legal/sentiment<0.3/profanity)
IV. PostgreSQL-First CRM (no external CRM)
V. Performance SLOs (<3s p95, <20% escalation, >95% ID accuracy)
VI. Incubation→Specialization Dev Lifecycle (Claude Code → OpenAI Agents SDK)
VII. AI Agent Reliability & Observability (idempotency, error taxonomy, degradation)
Plus: Escalation Matrix table, Governance section, version 1.0.0.

## Outcome

- ✅ Impact: Project constitution established from scratch; all 7 principles defined with NON-NEGOTIABLE markers and testable acceptance criteria
- 🧪 Tests: N/A — constitution stage
- 📁 Files: .specify/memory/constitution.md (created/overwritten), history/prompts/constitution/001-customer-success-fte-constitution.constitution.prompt.md (created)
- 🔁 Next prompts: /sp.specify <feature-name> to create first feature spec; /sp.adr for significant architectural decisions
- 🧠 Reflection: User provided very concrete rules; minimal inference required. Added best-practice additions (idempotency, error taxonomy, circuit breaker, observability) that naturally complement the stated rules.

## Evaluation notes (flywheel)

- Failure modes observed: None — all placeholders resolved from explicit user input
- Graders run and results (PASS/FAIL): Manual validation PASS — no bracket tokens remain, dates ISO, principles declarative and testable
- Prompt variant (if applicable): N/A
- Next experiment: Run /sp.specify on first feature (e.g., email-channel or ticket-creation) to validate constitution check gates in plan-template.md
