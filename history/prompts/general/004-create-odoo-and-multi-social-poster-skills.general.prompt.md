---
id: 004
title: Create Odoo and Multi-Social Poster Skills
stage: general
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: 002-silver-tier
user: Cs
command: manual
labels: ["skills", "configuration", "odoo", "social-media", "automation"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/odoo-accounting/SKILL.md
  - .claude/skills/multi-social-poster/SKILL.md
tests:
  - none
---

## Prompt

create skill in .claude/skills/odoo-accounting/SKILL.md

---
name: odoo-accounting
description: Interact with self-hosted Odoo Community 19+ via JSON-RPC MCP. Draft/create/post invoices, payments, journal entries, generate summaries. Use for Accounting/ tasks, invoice requests, or weekly audit data collection. Always require HITL for post/confirm actions.
---

# Odoo Accounting Skill

## When to use
Triggered by Accounting sub-agent on Needs_Action/Accounting/* or weekly audit trigger.

## Core Rules
- Odoo MCP must be configured and available
- Never confirm/post without file in Approved/
- Log every RPC call (method, params, result) to Logs/odoo_[date].jsonl
- Use Company_Handbook.md for approval thresholds (e.g., payments > PKR 50,000)
- Currency: PKR default

## Workflow
1. Read task file (e.g. invoice request from WhatsApp/email)
2. Extract: partner name/email, amount, description, due date, products
3. Draft Odoo record via MCP draft call (e.g. account.move create)
4. Write preview + draft ID to Pending_Approval/ACCOUNTING_INVOICE_[id].md

---

create skill in .claude/skills/odoo-accounting/SKILL.md

---
name: multi-social-poster
description: Generate platform-appropriate posts for Facebook, Instagram, Twitter/X, draft in Pending_Approval/, post via browser-mcp after approval, generate activity summaries. Use for Social/ tasks or scheduled promotion.
---

# Multi-Social Poster Skill

## When to use
Triggered on Needs_Action/Social/* or weekly content schedule.

## Core Rules
- Tailor content: LinkedIn/FB professional, IG visual/story, X concise
- Always HITL approval
- Include Karachi/Sindh/local hashtags when relevant
- Post max 3×/day across platforms
- Summarize: engagement stats if watcher provides, or just "Posted successfully"

## Workflow
1. Determine platform(s) from task
2. Generate content:
   - FB/IG: longer + image suggestion
   - X: <280 chars + link/hashtags
3. Draft + preview → Pending_Approval/SOCIAL_[platform]_[id].md
4. On Approved/ → call browser-mcp (navigate, fill, post)
5. After post: create summary file Social/Summary_[date].md

## Response snapshot

Created two skill configuration files:
1. `.claude/skills/odoo-accounting/SKILL.md` - Enables interaction with Odoo ERP for accounting tasks (invoices, payments, journal entries) with HITL approval workflow
2. `.claude/skills/multi-social-poster/SKILL.md` - Enables multi-platform social media posting (FB, IG, X) with platform-specific content generation and HITL approval

Both skills enforce human-in-the-loop approval before executing sensitive actions (posting Odoo records, publishing social media content).

## Outcome

- ✅ Impact: Added two critical automation skills to the AI Employee system - accounting integration and multi-platform social media management
- 🧪 Tests: none (configuration files)
- 📁 Files: Created 2 new skill files in `.claude/skills/` directory structure
- 🔁 Next prompts: Consider creating corresponding agent configuration files if needed, or testing the skills with sample tasks
- 🧠 Reflection: Skills follow established HITL pattern for sensitive actions, integrate with existing vault folder structure (Needs_Action/, Pending_Approval/, Approved/)

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Test skills with actual task files to validate workflow integration
