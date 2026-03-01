---
id: 001
title: Create Gold-Tier Specification
stage: spec
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-gold-tier-employee
branch: 001-gold-tier-employee
user: Cs
command: /sp.specify
labels: ["spec", "gold-tier", "autonomous-employee", "multi-agent"]
links:
  spec: specs/001-gold-tier-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-gold-tier-employee/spec.md
  - specs/001-gold-tier-employee/checklists/requirements.md
tests:
  - none
---

## Prompt

Gold tier scope — 40+ hour autonomous employee deliverable

Active sub-agents & responsibilities:
• Main Orchestrator → delegates, triggers weekly audit, monitors stuck items
• Accounting Sub-Agent → Odoo draft/create/post invoices/payments/journals
• Social Media Sub-Agent → multi-platform posting (LinkedIn/FB/IG/X) + summaries
• Finance & Auditor Sub-Agent → bank tx parsing, subscription audit, audit data contribution
• Approval & Recovery Sub-Agent → central HITL processor + error watchdog/recovery

Capabilities — exactly and only these in Gold:
• Full Odoo JSON-RPC integration via dedicated MCP (draft → approve → post)
• Multi-social posting via browser-mcp (draft → approve → post)
• Weekly autonomous audit: revenue, bottlenecks, suggestions, subscription flags
• CEO Briefing generation in Briefings/ folder
• Comprehensive audit logging (every action + outcome)
• Error recovery: retry transient, pause persistent, flag critical
• Cross-domain data flow via vault files only

MCP servers required:
• email-mcp
• browser-mcp (or multi-social variant)
• odoo-jsonrpc (custom – must expose create_draft, confirm, post methods)

Out of scope in Gold:
• Cloud/local hybrid split
• Direct A2A agent communication (file hand-off only)
• Banking API auto-payments
• Advanced A2A protocol upgrade
• Production HTTPS/backups for Odoo (local/VM ok)

Vault folders actively used in Gold:
Needs_Action/[Accounting|Social|Finance|Email|Comms]/
In_Progress/[Accounting|Social|Finance|Approval|Main]/
Pending_Approval/   Approved/   Rejected/
Accounting/   Briefings/   Logs/   Plans/   Done/
Dashboard.md   Business_Goals.md   Company_Handbook.md

## Response snapshot

**Branch Created**: `001-gold-tier-employee`
**Spec File**: `specs/001-gold-tier-employee/spec.md`
**Checklist**: `specs/001-gold-tier-employee/checklists/requirements.md`

**Specification Summary**:

Created comprehensive Gold-Tier Autonomous AI Employee specification with:

- **7 User Stories** (prioritized P1/P2):
  - P1: Odoo Financial Operations (invoice/payment drafting with HITL approval)
  - P2: Multi-Platform Social Media Management (LinkedIn, FB, IG, X with platform-specific content)
  - P1: Weekly Audit and CEO Briefing (Sunday night audit → Monday morning briefing)
  - P2: Error Detection and Recovery (transient retry, persistent flag, watchdog monitoring)
  - P1: Human-in-the-Loop Approval Workflow (all sensitive actions require approval)
  - P2: Cross-Domain Coordination via Vault (claim-by-move parallelization)
  - P1: Comprehensive Audit Logging (JSON Lines format, complete traceability)

- **71 Functional Requirements** organized by domain:
  - FR-001 to FR-005: Sub-Agent Architecture (4 specialized agents + Main Orchestrator)
  - FR-006 to FR-011: Accounting Operations (Odoo draft/post workflow)
  - FR-012 to FR-019: Social Media Operations (multi-platform, tailored content)
  - FR-020 to FR-029: Weekly Audit Cycle (Sunday trigger, Monday briefing)
  - FR-030 to FR-037: Error Recovery (retry, pause, flag, watchdog)
  - FR-038 to FR-045: HITL Approval (Odoo, social, payments, >PKR 100k)
  - FR-046 to FR-051: Vault Coordination (claim-by-move, atomic moves)
  - FR-052 to FR-059: Audit Logging (JSON Lines, timestamps PKT, never log secrets)
  - FR-060 to FR-065: MCP Integration (email-mcp, browser-mcp, odoo-mcp)
  - FR-066 to FR-071: Currency & Location (PKR default, PKT timezone, Karachi context)

- **23 Success Criteria** (measurable, technology-agnostic):
  - Automation: 40 hrs/week saved, 5 min invoice draft, 10 min social post, 15 min briefing
  - Reliability: 90% transient error recovery, zero duplicate processing, 99% uptime
  - Audit: 100% logging, complete traceability, PKR currency, PKT timezone
  - Business Intelligence: 100% subscription flagging, 90% unusual transaction detection
  - User Experience: 10 min/day approval time, clear error messages, professional Karachi tone

- **7 Edge Cases**: Odoo unreachable, browser-mcp failure, approval timeout, concurrent data access, audit trigger failure, missing folders, malformed files

- **12 Assumptions**: Odoo setup, MCP availability, vault structure, bank transaction access, social credentials, Company_Handbook thresholds, audit timing, Karachi context, human availability, error recovery scope, data retention, skill definitions

- **Dependencies**: External systems (Odoo ERP 19+, Gmail, LinkedIn/FB/IG/X), MCP servers (email-mcp, browser-mcp, odoo-mcp custom), Constitution v3.0.0, approved skills, data sources (Business_Goals.md, Company_Handbook.md, bank CSV)

- **Out of Scope** (12 items): Cloud/local hybrid, direct A2A communication, automated banking APIs, advanced protocols, production Odoo infrastructure, real-time collaboration, mobile app, advanced analytics, multi-currency, automated social engagement, email auto-response, custom reporting

**Validation**: ✅ All quality checklist items passed. Spec ready for `/sp.plan`.

## Outcome

- ✅ Impact: Defined comprehensive Gold-Tier system delivering 40+ hour/week autonomous business operations across accounting (Odoo), social media (4 platforms), finance auditing, and error recovery with mandatory HITL gates
- 🧪 Tests: none (specification phase)
- 📁 Files: Created spec.md (71 FRs, 23 SCs, 7 user stories, 7 edge cases) and requirements.md checklist (all items ✅)
- 🔁 Next prompts: `/sp.plan` to generate implementation plan, or `/sp.clarify` if clarification needed (none required currently)
- 🧠 Reflection: Spec provides complete business requirements without implementation details. All functional requirements testable, success criteria measurable and technology-agnostic. Clear scope boundaries (Out of Scope: 12 items). Constitution v3.0.0 alignment ensures HITL gates, claim-by-move coordination, JSON Lines logging, PKR/PKT standards enforced.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Specification Quality Checklist - PASS (all items ✅)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Validate spec against real vault structure (create sample ACCOUNTING_INVOICE_001.md, SOCIAL_linkedin_001.md, WEEKLY_AUDIT_TRIGGER.md files to verify requirements are implementable)
