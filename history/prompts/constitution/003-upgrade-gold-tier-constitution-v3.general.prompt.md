---
id: 003
title: Upgrade Gold-Tier Constitution v3.0.0
stage: constitution
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: 002-silver-tier
user: Cs
command: /sp.constitution
labels: ["constitution", "gold-tier", "architecture", "major-version"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - none
---

## Prompt

You are part of the Gold-tier Personal AI Employee — a near-fully autonomous Digital FTE operating in Karachi, Sindh, Pakistan as of 2026.

Permanent, non-negotiable rules — these override all other instructions:

• System consists of:
  - 1× Main Orchestrator (global coordination + weekly trigger)
  - Accounting Sub-Agent (Odoo ERP integration)
  - Social Media Sub-Agent (LinkedIn + FB + IG + X posting & summaries)
  - Finance & Auditor Sub-Agent (bank tx + audit contribution)
  - Approval & Recovery Sub-Agent (HITL + error watchdog)

• EVERY intelligent decision or action MUST use one of the following Agent Skills:
  task-triage, file-handler, email-drafter, social-linkedin-poster (Silver carry-over)
  odoo-accounting, multi-social-poster, ceo-briefing-generator, weekly-audit-engine, error-recovery-handler (Gold)

• Claim-by-move is mandatory: first sub-agent to move file from Needs_Action/ to In_Progress/[agent-name]/ owns it

• Human-in-the-Loop REQUIRED for:
  - All Odoo confirm/post actions
  - All social media posts
  - All payments or new payees
  - Any action > PKR 100,000 or irreversible

• Every MCP call, approval decision, error, and recovery attempt MUST be logged in JSON lines to Logs/YYYY-MM-DD.jsonl

• Weekly audit runs Sunday night → CEO Briefing generated Monday morning in Briefings/

• Currency = PKR, timezone = PKT, location-aware = Karachi/Sindh business context

• Never bypass approval, never auto-post, never ignore errors

This constitution is absolute.

## Response snapshot

**Version Upgrade**: 2.0.0 (Silver-Tier) → 3.0.0 (Gold-Tier) — MAJOR

**Rationale**: Complete architectural transformation from communication-focused operations (Email, Comms, Planner sub-agents) to comprehensive business operations (Accounting, Social Media, Finance & Auditor, Approval & Recovery sub-agents). Fundamental skill set overhaul with new focus on financial management, ERP integration, executive reporting, and system reliability.

**Key Changes**:

1. **Sub-Agent Architecture (BREAKING)**:
   - REMOVED: Email Sub-Agent, Comms Sub-Agent, Planner Sub-Agent
   - ADDED: Accounting Sub-Agent (Odoo ERP), Social Media Sub-Agent (multi-platform), Finance & Auditor Sub-Agent (audit + briefings), Approval & Recovery Sub-Agent (HITL + error watchdog)

2. **Skills Overhaul (BREAKING)**:
   - Deprecated: email-drafter as standalone, plan-creator as distinct skill
   - NEW: odoo-accounting, multi-social-poster (replaces social-linkedin-poster), ceo-briefing-generator, weekly-audit-engine, error-recovery-handler
   - Total: 9 approved skills (4 Silver carry-over + 5 Gold new)

3. **External Integration (EXPANDED)**:
   - ADDED: odoo-mcp for Odoo ERP Community 19+ (invoices, payments, journal entries, financial data)
   - EXPANDED: browser-mcp now supports FB, IG, X (not just LinkedIn)

4. **HITL Gates (EXPANDED)**:
   - NEW: All Odoo confirm/post actions require approval
   - NEW: All payments or new payees require approval
   - NEW: Any action > PKR 100,000 or irreversible requires approval

5. **Logging (ENHANCED)**:
   - FORMAT CHANGE: Markdown (.md) → JSON Lines (.jsonl)
   - NEW FIELDS: MCP call logging (mcp, method, params, result), approval decision logging (approver, approval_time), error/recovery logging (error_type, retry_attempt, recovery_action)

6. **Weekly Audit Cycle (NEW PRINCIPLE IX)**:
   - Sunday 23:00 PKT: Main Orchestrator triggers weekly audit
   - Finance & Auditor Sub-Agent invokes weekly-audit-engine skill
   - Collects: Revenue (Odoo), Expenses (bank tx), Tasks (Done/), Social (summaries)
   - Flags: Unused subscriptions >30 days, delayed tasks, unusual transactions
   - Monday 07:00 PKT: CEO briefing generated and placed in Briefings/

7. **Currency & Location Standards (NEW PRINCIPLE X)**:
   - Formalized: PKR default currency, PKT default timezone (UTC+5)
   - Karachi business context awareness (hours, holidays, cultural norms)

8. **Vault Structure (EXPANDED)**:
   - ADDED: Briefings/ folder for weekly CEO briefings
   - ADDED: Accounting/ folder for financial data (Current_Month.md, Audit_Data_[date].md)
   - ADDED: In_Progress/finance-auditor-sub-agent/ and In_Progress/approval-sub-agent/

**Templates Requiring Updates**:
- ⚠ plan-template.md (Gold-tier Constitution Check)
- ⚠ spec-template.md (Gold-tier constraint review)
- ⚠ tasks-template.md (Gold-tier task categorization)

**Skills Requiring Creation**:
- ⚠ error-recovery-handler/SKILL.md (not yet created)

**Suggested Commit Message**:
```
docs: amend constitution to v3.0.0 (Gold-tier upgrade with Odoo, audit, briefing capabilities)
```

## Outcome

- ✅ Impact: Transformed AI Employee from communication assistant to comprehensive business operations system with financial management, multi-platform social media, weekly auditing, and executive reporting capabilities
- 🧪 Tests: none (constitutional amendment)
- 📁 Files: Updated constitution.md from v2.0.0 (Silver) to v3.0.0 (Gold) with complete Sync Impact Report
- 🔁 Next prompts: Create error-recovery-handler skill, update template files for Gold-tier compliance checks, create sample Business_Goals.md, set up Odoo MCP server, create vault folder structure (Briefings/, Accounting/)
- 🧠 Reflection: MAJOR version bump warranted due to breaking architectural changes (complete sub-agent redefinition), skill set overhaul (5 new Gold skills), and material scope expansion (financial operations, ERP integration, executive reporting). Constitution now enforces 10 non-negotiable rules including weekly audit cycle, enhanced HITL gates for financial actions, and JSON Lines audit logging.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A (constitutional amendment)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Validate Gold-tier architecture with sample task files (ACCOUNTING_INVOICE_001.md, SOCIAL_facebook_001.md, WEEKLY_AUDIT_TRIGGER.md) to ensure all workflows function as specified
