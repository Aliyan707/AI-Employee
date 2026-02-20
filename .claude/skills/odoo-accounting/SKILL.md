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
