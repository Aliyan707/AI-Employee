---
id: 002
title: Bronze Inbox Automation Plan
stage: plan
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: bronze-inbox-automation
branch: 001-bronze-inbox-automation
user: Aliyan 707
command: /sp.plan
labels: ["plan", "architecture", "bronze-tier", "automation-loop"]
links:
  spec: specs/001-bronze-inbox-automation/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-bronze-inbox-automation/plan.md
tests:
 - none
---

## Prompt

/sp.plan

Bronze execution cycle — repeat forever in simple while loop:

Phase 1 – Observe
• Read Dashboard.md (for current status & recent logs)
• List all files in Needs_Action/

Phase 2 – Classify & Delegate to Skill
For each file in Needs_Action/:
  • If filename starts with EMAIL_ or looks like email → call task-triage skill
  • If filename starts with FILE_ or generic drop → call file-handler skill
  • Otherwise → use task-triage as fallback

Phase 3 – Execute skill instructions
• Follow exactly the step-by-step workflow in the chosen SKILL.md
• Write classification / summary / suggestions at bottom of the current file
• If high urgency and multi-step → create minimal Plans/PLAN_*.md with 2–4 checkboxes
• Append one log line to Dashboard.md → ## Recent Activity
  Example: "- 2026-02-15 07:15 Processed EMAIL_client-invoice.md : HIGH – summary written, moved to Done"

Phase 4 – Clean up
• Move processed file(s) to Done/
• If no more files in Needs_Action/ → output "<idle>No pending items. Waiting for watcher.</idle>"

Phase 5 – Report
• End every full cycle with:
  <cycle-complete>
  Items processed: N
  New plans created: M
  Human attention needed: yes/no
  </cycle-complete>

## Response snapshot

Successfully created comprehensive implementation plan for Bronze-tier inbox automation system following the 5-phase execution cycle pattern.

**Plan Details:**
- **File**: specs/001-bronze-inbox-automation/plan.md
- **Architecture**: Event-driven loop with skill delegation pattern
- **Execution Model**: Infinite while loop with 5-phase cycle
- **Implementation Timeline**: 8-12 hours (4 phases)

**Core Architecture**:

**5-Phase Execution Cycle**:
1. **Observe**: Read Dashboard.md status, list Needs_Action/ files
2. **Classify & Delegate**: Route EMAIL_* → task-triage, FILE_* → file-handler
3. **Execute**: Invoke skill, write analysis, create plans, log to Dashboard
4. **Clean Up**: Move to Done/, handle collisions, output <idle> if empty
5. **Report**: Output <cycle-complete> with statistics

**Technical Decisions (5 documented)**:
- **TD-001**: Simple while loop (60s sleep) vs. file watcher → chose simplicity
- **TD-002**: Use Skill tool invocation, not direct SKILL.md parsing
- **TD-003**: XML-style status tags (<status>DONE</status>)
- **TD-004**: ISO 8601 timestamps (YYYY-MM-DD HH:MM in PKT)
- **TD-005**: Plan creation threshold (high priority + 3+ actions)

**Implementation Phases**:
- **Phase 0**: Validation (30 min) - Verify environment readiness
- **Phase 1**: Core Loop (4-5 hrs) - Implement bronze-automation-loop.sh
- **Phase 2**: Integration & Testing (2-3 hrs) - Test with varied items
- **Phase 3**: Error Handling (1-2 hrs) - Graceful failure handling
- **Phase 4**: Documentation (1-2 hrs) - Quickstart, contracts, finalization

**Key Components**:
- Main script: `.specify/scripts/bronze-automation-loop.sh`
- Skill delegation: Claude Code Skill tool invocations
- Contracts: skill-interface.md, dashboard-log-format.md
- Error handling: ERROR_ prefix, [ERROR] logging, non-fatal errors

**Skill Interface Contract**:
- Input: Filename in Needs_Action/
- Output: Analysis appended to file, log to Dashboard, optional Plan, status tag
- Main loop: Moves file to Done/, tracks statistics, outputs cycle report

**Success Criteria Validation**:
- All 8 SC criteria mapped to implementation approach
- Validation methods defined for each
- Testing strategy covers edge cases

**Constitution Compliance**: ✅ PASS
- All 8 core principles satisfied
- No violations requiring complexity justification

## Outcome

- ✅ Impact: Created detailed implementation plan with 5-phase architecture, 5 technical decisions, 4 implementation phases, and complete contracts
- 🧪 Tests: Testing strategy defined in Phase 2 (5+ test files, edge case coverage)
- 📁 Files: Created 1 file (plan.md), contracts to be created in Phase 4
- 🔁 Next prompts: `/sp.tasks` to generate task breakdown, then `/sp.implement` to execute
- 🧠 Reflection: Plan successfully translates user's 5-phase execution cycle into concrete implementation strategy. Technical decisions documented with rationales. Architecture is appropriately simple for Bronze tier (no over-engineering). All success criteria have validation methods. Timeline of 8-12 hours is realistic given phased approach.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Constitution check - PASS (all 8 principles)
- Prompt variant (if applicable): User provided specific 5-phase cycle structure
- Next experiment (smallest change to try): Generate tasks and validate phase breakdown completeness
