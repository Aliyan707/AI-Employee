---
id: 002
title: Create Silver-tier implementation plan
stage: plan
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-silver-tier
branch: 002-silver-tier
user: Aliyan 707
command: /sp.plan
labels: ["planning", "silver-tier", "architecture", "agent-cycle", "multi-agent", "vault-orchestration"]
links:
  spec: specs/002-silver-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-silver-tier/plan.md
tests:
  - none
---

## Prompt

Silver system cycle — each sub-agent follows a similar pattern:

1. Observe
   • Read Dashboard.md + Company_Handbook.md
   • Scan own domain folder in Needs_Action/ + In_Progress/[self]/
   • Scan Approved/ for own pending approvals

2. Claim & Prioritize
   • Move unclaimed files from Needs_Action/ to In_Progress/[self]/ (claim)
   • Prioritize: Approved/ items first → then In_Progress/ → then new Needs_Action/

3. Process with Skills
   • Use task-triage / file-handler to classify incoming
   • Delegate logic to Silver skills:
     - Email → email-drafter
     - LinkedIn/sales → social-linkedin-poster
     - Complex → plan-creator
     - Approvals → approval-handler

4. HITL & Execution
   • Drafts → Pending_Approval/
   • If human moved to Approved/ → call corresponding MCP
   • Update plan checkboxes if Planner

5. Clean & Report
   • Move completed files to Done/
   • Append log to Dashboard.md → ## Recent Activity
   • Append detailed JSON log to Logs/[date].md
   • If nothing left → output <idle>[agent-name] idle</idle>

6. Coordination signal
   • Main Orchestrator watches all In_Progress/ folders
   • If Planner creates new task → writes to Needs_Action/ for delegation

Main Orchestrator special step:
• Every cycle: check for stuck Pending_Approval/ (>48h) → flag in Dashboard.md

## Response snapshot

Created comprehensive implementation plan for Silver-tier multi-agent AI Employee system with vault-based orchestration architecture.

**Plan Structure:**
- **Summary**: Multi-agent file-based orchestration with 6-step cycle (Observe → Claim → Process → HITL → Execute → Report → Coordinate)
- **Technical Context**: Vault-based agent system using Claude Code + MCP servers, no traditional code required
- **Constitution Check**: ✅ ALL 8 PRINCIPLES PASSED (full constitutional compliance v2.0.0)
- **Project Structure**: Complete vault hierarchy + skill definitions + MCP integration architecture
- **Complexity Tracking**: ✅ NO VIOLATIONS - vault architecture inherently enforces all constitutional requirements

**Technical Approach:**
- **No traditional source code** - system implemented through vault structure + skill definitions + automation scripts
- **File-based coordination** - agents communicate via atomic file moves (claim-by-move rule)
- **Skills-only intelligence** - all behavior defined in .claude/skills/ (email-drafter, social-linkedin-poster, plan-creator, etc.)
- **MCP for external actions** - email-mcp (Gmail) + browser-mcp (LinkedIn/WhatsApp)
- **HITL gates** - Pending_Approval/ → Approved/ workflow enforces human oversight

**Phase 0 Research Areas Identified (7 high/medium priority):**
1. Agent Cycle Implementation Pattern (HIGH - how to execute 6-step cycle)
2. Atomic File Move Operations (HIGH - claim-by-move coordination)
3. MCP Server Integration (HIGH - skill → MCP invocation)
4. Skill Invocation Mechanism (HIGH - orchestrator → sub-agent delegation)
5. Dashboard.md Update Strategy (MEDIUM - concurrent write safety)
6. Orchestrator Scheduling (MEDIUM - 5-minute cycle implementation)
7. Company_Handbook.md Format (LOW - agent-readable business rules)

**Phase 1 Design Deliverables Defined:**
- data-model.md (5 entities: EmailDraft, LinkedInPost, Plan, LogEntry, Dashboard)
- contracts/ (5 contracts: email-drafter, social-linkedin-poster, plan-creator, email-mcp, browser-mcp)
- quickstart.md (prerequisites, vault init, first agent cycle walkthrough)
- Agent context update (Claude-specific configuration)

**Agent Cycle Documented:**
- 6-step pattern: Observe → Claim & Prioritize → Process with Skills → HITL & Execution → Clean & Report → Coordination Signal
- Main Orchestrator: watches In_Progress/, flags stuck Pending_Approval/ (>48h), updates Dashboard.md status
- Email Sub-Agent: Needs_Action/Email/ → email-drafter → Pending_Approval/ → email-mcp
- Comms Sub-Agent: Needs_Action/Comms/ → social-linkedin-poster → Pending_Approval/ → browser-mcp
- Planner Sub-Agent: complex tasks → plan-creator → Plans/PLAN_*.md with checkboxes

**Critical Design Constraints:**
1. Atomicity (file moves must be atomic for claim-by-move)
2. Idempotency (agent cycles safe to re-run)
3. No Direct A2A Messaging (coordination via files only)
4. Immutable Done/ (audit trail integrity)
5. HITL Non-Negotiable (no auto-execution without Approved/)

## Outcome

- ✅ Impact: Complete architectural plan for Silver-tier vault orchestration system ready for task generation
- 🧪 Tests: Constitutional compliance validation passed all 8 principles
- 📁 Files: specs/002-silver-tier/plan.md (606 lines, comprehensive architecture + agent cycle + contracts)
- 🔁 Next prompts: Generate research.md (Phase 0), then data-model.md + contracts/ (Phase 1), then `/sp.tasks` for implementation breakdown
- 🧠 Reflection: Vault-based architecture elegantly satisfies all constitutional requirements without traditional code. Claim-by-move coordination via atomic file operations provides clean multi-agent coordination. 6-step agent cycle provides clear workflow that can be validated against acceptance criteria.

## Evaluation notes (flywheel)

- Failure modes observed: none (plan creation successful, constitution check passed)
- Graders run and results (PASS/FAIL): Constitution Check - ALL PASS (8/8 principles compliant)
- Prompt variant (if applicable): N/A (standard /sp.plan workflow with detailed agent cycle input)
- Next experiment (smallest change to try): Prototype atomic file move operations on target platform (Windows/Linux/macOS) to validate claim-by-move coordination assumptions
