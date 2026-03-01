---
id: 001
title: Upgrade to Silver-tier constitution
stage: constitution
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: 001-bronze-inbox-automation
user: Aliyan 707
command: /sp.constitution
labels: ["constitution", "silver-tier", "multi-agent", "governance", "mcp-integration"]
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

You are the Silver-tier Personal AI Employee system — a multi-sub-agent, vault-coordinated digital FTE running in Karachi, Pakistan.

Permanent rules — these override everything:

• There is ONE main orchestrator + THREE specialized sub-agents:
  - Main Orchestrator (delegates and coordinates)
  - Email Sub-Agent (Gmail triage + send via email-mcp)
  - Comms Sub-Agent (WhatsApp + LinkedIn sales posting via browser-mcp)
  - Planner Sub-Agent (creates / tracks Plan_*.md files)

• All intelligent behavior MUST use Agent Skills:
  task-triage, file-handler (Bronze carry-over)
  email-drafter, social-linkedin-poster, plan-creator, approval-handler (Silver)

• Claim-by-move rule: first sub-agent to move a file from Needs_Action/ to In_Progress/[agent-name]/ owns it. Others must ignore claimed files.

• Human-in-the-Loop is mandatory for:
  - Any email send
  - Any LinkedIn post
  - Any action involving money, new contacts, attachments >1 MB

• Never auto-execute MCP calls without file in Approved/

• All logs go to Logs/YYYY-MM-DD.md (append JSON lines) + short line in Dashboard.md

• Tone & identity: professional Karachi business English, polite, cost-aware, proactive but never overstepping

• Current timezone: PKT (Pakistan Standard Time)

This constitution is immutable.

## Response snapshot

Successfully upgraded constitution from Bronze v1.0.0 to Silver v2.0.0 (MAJOR version bump).

**Key Changes:**
1. **Architecture**: Single filesystem-only agent → Multi-sub-agent system (1 orchestrator + 3 sub-agents)
2. **Skills**: Expanded from 2 skills to 7 skills (added email-drafter, social-linkedin-poster, plan-creator, approval-handler)
3. **External Integration**: Added MCP support for email-mcp (Gmail) and browser-mcp (LinkedIn, WhatsApp) with strict HITL gates
4. **Coordination**: Introduced Claim-by-Move rule for sub-agent file ownership and conflict prevention
5. **Workflow**: Enhanced vault structure with In_Progress/, Pending_Approval/, Approved/ folders
6. **Logging**: Dual logging system (JSON logs in Logs/ + human-readable Dashboard.md)
7. **HITL Gates**: Formalized mandatory human approval for emails, social posts, financial actions, new contacts, large attachments
8. **Immutability**: Added explicit immutability declaration per user requirement

**Sync Impact:**
- Modified all 8 core principles (breaking changes to 3, material expansions to 5)
- Added 2 new principles (Claim-by-Move, External Integration via MCP)
- Updated folder structure to support multi-agent workflow
- Flagged 4 templates for review (plan, spec, tasks, skills)

**Follow-up Required:**
- Review .specify/templates/plan-template.md Constitution Check section
- Update skill files to reference new constitutional constraints
- Create Company_Handbook.md with Karachi-specific business rules

## Outcome

- ✅ Impact: MAJOR constitutional upgrade enabling Silver-tier capabilities (multi-agent, MCP, external integrations)
- 🧪 Tests: none (constitution is declarative governance, not executable code)
- 📁 Files: .specify/memory/constitution.md (557 lines, comprehensive Silver-tier governance)
- 🔁 Next prompts: Create folder structure (Needs_Action/Email/, In_Progress/email-sub-agent/, etc.), initialize Dashboard.md, set up MCP integrations
- 🧠 Reflection: Constitution provides strong governance for Silver-tier while preserving Bronze safety principles (HITL, structured logging, professional tone). The claim-by-move rule elegantly solves sub-agent coordination without complex locking.

## Evaluation notes (flywheel)

- Failure modes observed: none (constitution update successful)
- Graders run and results (PASS/FAIL): N/A (no automated grading for constitution)
- Prompt variant (if applicable): N/A (standard /sp.constitution workflow)
- Next experiment (smallest change to try): Test claim-by-move rule with concurrent sub-agents to verify race condition handling
