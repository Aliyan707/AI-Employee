---
description: "Implementation tasks for Silver-Tier Multi-Agent AI Employee"
---

# Tasks: Silver-Tier Multi-Agent AI Employee

**Input**: Design documents from `/specs/002-silver-tier/`
**Prerequisites**: plan.md ✅, spec.md ✅, Watchers implemented ✅, Skills created ✅, Vault initialized ✅

**Tests**: No explicit test tasks (manual validation via acceptance scenarios from spec.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Current Status**: Watcher infrastructure, agent skills, vault structure, and deployment configuration are complete. Remaining work focuses on MCP server implementation and end-to-end integration testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a **vault-based orchestration system** with no traditional src/ structure. Paths reference:
- `mcp-servers/` - MCP server implementations
- `watchers/` - Watcher scripts (COMPLETE)
- `System/` - Agent prompts (COMPLETE)
- `.claude/skills/` - Agent skills (COMPLETE)
- Vault folders - Needs_Action/, In_Progress/, Pending_Approval/, Approved/, Done/, Plans/, Logs/, Dashboard.md

---

## Phase 1: Setup (MCP Server Infrastructure)

**Purpose**: Initialize MCP server projects for email and LinkedIn integration

- [ ] T001 Create mcp-servers/ directory structure with email-mcp/ and browser-mcp/ subdirectories
- [ ] T002 [P] Initialize email-mcp Node.js project in mcp-servers/email-mcp/ with package.json, dependencies (gmail API, MCP SDK)
- [ ] T003 [P] Initialize browser-mcp Node.js project in mcp-servers/browser-mcp/ with package.json, dependencies (playwright, MCP SDK)
- [ ] T004 [P] Create mcp-servers/email-mcp/README.md with setup instructions and API documentation
- [ ] T005 [P] Create mcp-servers/browser-mcp/README.md with setup instructions and LinkedIn posting workflow

---

## Phase 2: Foundational (US4/P0 - Main Orchestrator Coordination)

**Purpose**: Core orchestration infrastructure (ALREADY IMPLEMENTED - validation only)

**⚠️ CRITICAL**: This phase validates existing implementation. No new code required.

**Goal**: Verify Main Orchestrator correctly delegates work to sub-agents, prevents conflicts, and maintains system-wide visibility

**Independent Test**: Drop files into Needs_Action/, verify correct sub-agent claims file (EMAIL_* → email-sub-agent, SOCIAL_* → comms-sub-agent), Dashboard.md updates, no duplicate processing

- [ ] T006 [US4] Validate Main Orchestrator cycle implementation in System/silver-main.md (45s cycle, delegation logic)
- [ ] T007 [US4] Test claim-by-move coordination by dropping 3 files simultaneously into Needs_Action/ (verify exclusive ownership, atomic moves)
- [ ] T008 [US4] Verify Dashboard.md updates correctly (last active timestamp, pending approvals count, active plans count, items in queues)
- [ ] T009 [US4] Test orchestrator detects stuck Pending_Approval/ files (>48h) and flags in Dashboard.md
- [ ] T010 [US4] Validate logging: all claim operations logged to Logs/YYYY-MM-DD.md in JSON format with timestamp (PKT), agent, action, file, status

**Checkpoint**: Foundation ready - Main Orchestrator validates correctly, claim-by-move prevents conflicts, Dashboard.md reflects real-time status

---

## Phase 3: User Story 1 - Automated Email Processing & Response (Priority: P1) 🎯 MVP

**Goal**: Email Sub-Agent processes emails automatically, drafts professional responses, requires human approval before sending via email-mcp

**Independent Test**: Drop EMAIL_*.md into Needs_Action/Email/, verify Email Sub-Agent claims file, drafts response (email-drafter skill), moves to Pending_Approval/, sends via email-mcp after human approval, archives to Done/Email/SENT_*.md with audit log

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement email-mcp server core in mcp-servers/email-mcp/index.js with Gmail API integration (authenticate, send email)
- [ ] T012 [P] [US1] Implement send_email operation in mcp-servers/email-mcp/index.js (extract to/subject/body from approved file, call Gmail API)
- [ ] T013 [US1] Implement pre-execution checklist validation in email-mcp (file exists in Approved/, all fields present, approval <24h, no errors)
- [ ] T014 [US1] Implement success handling in email-mcp (move Approved/EMAIL_*.md → Done/Email/SENT_*.md, log to Logs/YYYY-MM-DD.md, update Dashboard.md)
- [ ] T015 [US1] Implement failure handling in email-mcp (move back to Pending_Approval/, append error note, log error, flag for human review in Dashboard.md)
- [ ] T016 [US1] Configure email-mcp in ~/.config/claude-code/mcp.json with Gmail credentials path and OAuth token
- [ ] T017 [US1] Create email-mcp authentication flow (OAuth2 consent, token storage, refresh logic)
- [ ] T018 [US1] Test Email Sub-Agent end-to-end: watcher detects email → agent drafts → human approves → email-mcp sends → archived to Done/
- [ ] T019 [US1] Validate email-drafter skill integration (invoked by Email Sub-Agent, generates professional Karachi business tone, classifies sensitivity high/medium/low)
- [ ] T020 [US1] Test HITL approval workflow (draft in Pending_Approval/ waits for human, only sends when moved to Approved/, timeout after 24h)
- [ ] T021 [US1] Verify audit trail completeness (Needs_Action → In_Progress → Pending_Approval → Approved → Done with timestamps in Logs/)

**Checkpoint**: Email processing fully functional - watcher detects, agent drafts, human approves, email-mcp sends, complete audit trail exists

---

## Phase 4: User Story 2 - LinkedIn Sales Post Generation (Priority: P2)

**Goal**: Comms Sub-Agent generates LinkedIn sales posts (1-2 daily), requires human approval before posting via browser-mcp

**Independent Test**: Trigger daily post generation or drop SOCIAL_linkedin_*.md, verify Comms Sub-Agent drafts professional Karachi-focused content (100-250 words, #KarachiBusiness, #AIEmployee), moves to Pending_Approval/, posts via browser-mcp after approval, archives to Done/Social/POSTED_*.md

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement browser-mcp server core in mcp-servers/browser-mcp/index.js with Playwright integration (headless browser, LinkedIn session)
- [ ] T023 [P] [US2] Implement post_to_linkedin operation in browser-mcp (extract content/hashtags from approved file, navigate to LinkedIn, post via Playwright)
- [ ] T024 [US2] Implement pre-execution checklist validation in browser-mcp (file in Approved/, content 100-250 words, hashtags present, approval <24h)
- [ ] T025 [US2] Implement success handling in browser-mcp (move Approved/SOCIAL_*.md → Done/Social/POSTED_*.md, log timestamp, update Dashboard.md)
- [ ] T026 [US2] Implement failure handling in browser-mcp (move back to Pending_Approval/, append error, log, flag for human review)
- [ ] T027 [US2] Configure browser-mcp in ~/.config/claude-code/mcp.json with LinkedIn session path (persistent browser context)
- [ ] T028 [US2] Create LinkedIn authentication flow for browser-mcp (login via Playwright, save session, reuse on subsequent posts)
- [ ] T029 [US2] Test Comms Sub-Agent end-to-end: scheduled trigger (10 AM PKT) → agent generates post → human approves → browser-mcp posts → archived
- [ ] T030 [US2] Validate social-linkedin-poster skill integration (invoked by Comms Sub-Agent, generates 100-250 words, Karachi context, hashtags, value-first hooks)
- [ ] T031 [US2] Test cultural calendar awareness (Company_Handbook.md config, no posts during Eid/Ramadan evening, respects weekend rules)
- [ ] T032 [US2] Verify daily posting limit enforcement (max 2 posts per day, check Done/Social/POSTED_*$(date).md count before generating)
- [ ] T033 [US2] Test sales opportunity detection (WhatsApp/Email keywords "pricing", "demo" trigger LinkedIn post draft via Comms Sub-Agent)

**Checkpoint**: LinkedIn posting fully functional - scheduled/triggered generation, professional content, human approval, browser-mcp posts, cultural awareness enforced

---

## Phase 5: User Story 3 - Multi-Step Plan Creation & Tracking (Priority: P3)

**Goal**: Planner Sub-Agent creates multi-step plans (3-8 checkboxes) for complex tasks, tracks progress, updates Dashboard.md

**Independent Test**: Drop complex task file (>2 steps required), verify Planner creates Plans/PLAN_*.md with checkboxes, updates progress on each cycle, archives to Done/Plans/ when complete

### Implementation for User Story 3

- [ ] T034 [P] [US3] Validate Planner Sub-Agent cycle implementation in System/Planner-Sub.md (120s cycle, plan creation, progress tracking)
- [ ] T035 [US3] Test plan-creator skill integration (invoked by Planner, generates 3-8 actionable checkboxes with owner/dependencies/approval gates)
- [ ] T036 [US3] Verify plan file format (YAML frontmatter with plan_id, created, updated, status, priority, owner, estimated_steps, completed_steps)
- [ ] T037 [US3] Test plan progress updates (Planner marks checkboxes complete when evidence exists in Done/ folder, updates completed_steps counter, timestamp)
- [ ] T038 [US3] Validate plan completion detection (all checkboxes checked → move Plans/PLAN_*.md to Done/Plans/, update Dashboard.md, remove from active plans)
- [ ] T039 [US3] Test plan delegation (Planner creates delegated tasks in Needs_Action/Email/ or Needs_Action/Comms/ for sub-agents to execute)
- [ ] T040 [US3] Verify plan-based approval gates (steps marked "APPROVAL GATE" → create entry in Pending_Approval/, wait for human before proceeding)
- [ ] T041 [US3] Test plan dependency handling (steps with dependencies MUST wait until prerequisite steps completed)
- [ ] T042 [US3] Validate Dashboard.md plan tracking (active plans count, plan status updates in ## Recent Activity, plan completion logged)

**Checkpoint**: Planning fully functional - complex tasks broken into trackable plans, progress updated automatically, delegated tasks executed by sub-agents, complete on all checkboxes

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, final integration validation

- [ ] T043 [P] Update System/DEPLOYMENT.md with MCP server setup instructions (email-mcp and browser-mcp installation, authentication, configuration)
- [ ] T044 [P] Create mcp-servers/TESTING.md with end-to-end test scenarios for each user story
- [ ] T045 [P] Enhance WATCHER_QUICKSTART.md with MCP integration testing steps
- [ ] T046 Create comprehensive integration test script in .specify/scripts/bash/test-silver-integration.sh (tests all 4 user stories end-to-end)
- [ ] T047 [P] Document error recovery procedures in System/TROUBLESHOOTING.md (MCP failures, watcher issues, stuck files)
- [ ] T048 Validate complete audit trail for sample workflow (email arrives → drafted → approved → sent, verify every step logged)
- [ ] T049 Performance testing: process 10 emails, 3 LinkedIn posts, 2 plans concurrently, verify no conflicts or data loss
- [ ] T050 [P] Security review: verify no credentials in git, .env files in .gitignore, OAuth tokens stored securely, MCP pre-execution checks enforced
- [ ] T051 Update SILVER_TIER_STATUS.md to reflect 100% Silver tier completion with MCP servers implemented
- [ ] T052 Run quickstart.md validation (follow guide end-to-end, verify all steps work, update any outdated instructions)
- [ ] T053 Create demo video script in specs/002-silver-tier/DEMO_SCRIPT.md (5-10 min walkthrough showing all features)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Validation only, can run in parallel with Phase 1
- **User Story 1 (Phase 3)**: Depends on Setup (T001-T005 for email-mcp project), Foundational validation helpful but not blocking
- **User Story 2 (Phase 4)**: Depends on Setup (T001, T003, T005 for browser-mcp project), independent of US1
- **User Story 3 (Phase 5)**: Depends on Foundational validation, independent of US1 and US2
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (US1/P1 - MVP)**: Can start after Setup - No dependencies on other stories, implements email-mcp
- **User Story 2 (US2/P2)**: Can start after Setup - Independent of US1, implements browser-mcp
- **User Story 3 (US3/P3)**: Can start after Foundational validation - Independent of US1 and US2, validates existing Planner
- **All stories integrate with Main Orchestrator (US4/P0) but can be tested independently**

### Within Each User Story

- **US1 (Email)**:
  - email-mcp server implementation (T011-T015) can run in parallel
  - Configuration (T016-T017) depends on server implementation
  - Integration testing (T018-T021) depends on everything prior

- **US2 (LinkedIn)**:
  - browser-mcp server implementation (T022-T026) can run in parallel
  - Configuration (T027-T028) depends on server implementation
  - Integration testing (T029-T033) depends on everything prior

- **US3 (Planning)**:
  - All tasks are validation/testing of existing implementation
  - Can run in sequence T034 → T042

### Parallel Opportunities

- **Setup (Phase 1)**: T002, T003 (both MCP projects) can run in parallel
- **Setup (Phase 1)**: T004, T005 (both README files) can run in parallel
- **US1 Implementation**: T011, T012 (email-mcp core files) can run in parallel
- **US2 Implementation**: T022, T023 (browser-mcp core files) can run in parallel
- **Polish (Phase 6)**: T043, T044, T045 (documentation) can run in parallel
- **Polish (Phase 6)**: T047, T050 (error recovery, security review) can run in parallel
- **User Stories**: US1, US2, US3 can all be worked on in parallel if team capacity allows

---

## Parallel Example: User Story 1 (Email Processing)

```bash
# Launch MCP server implementation tasks in parallel:
Task T011: "Implement email-mcp server core in mcp-servers/email-mcp/index.js"
Task T012: "Implement send_email operation in mcp-servers/email-mcp/index.js"

# Launch documentation tasks in parallel:
Task T004: "Create mcp-servers/email-mcp/README.md"
Task T043: "Update System/DEPLOYMENT.md with email-mcp setup"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005) - MCP server projects initialized
2. Complete Phase 2: Foundational (T006-T010) - Validate existing orchestration
3. Complete Phase 3: User Story 1 (T011-T021) - Email processing end-to-end
4. **STOP and VALIDATE**: Test email flow independently
   - Gmail watcher detects email → EMAIL_*.md created
   - Email Sub-Agent claims file → drafts response
   - Human approves → email-mcp sends
   - Complete audit trail in Logs/ and Done/Email/
5. Deploy/demo if ready - **This is production-ready HITL email system**

**Time Estimate**: 8-10 hours for full MVP (MCP server + integration testing)

### Incremental Delivery

1. Complete Setup + Foundational (Phase 1 + 2) → Foundation validated (2-3 hours)
2. Add User Story 1 (Phase 3) → Test independently → Deploy/Demo (**MVP - Email automation!**) (6-8 hours)
3. Add User Story 2 (Phase 4) → Test independently → Deploy/Demo (LinkedIn posting added) (6-8 hours)
4. Add User Story 3 (Phase 5) → Test independently → Deploy/Demo (Planning added) (4-5 hours)
5. Polish (Phase 6) → Documentation, security, performance (3-4 hours)

**Total Time Estimate**: 21-28 hours (within Silver tier 20-30 hour guidance)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together (Phase 1: 2 hours)
2. One developer validates Foundational (Phase 2: 2 hours) while another starts US1 setup
3. Once Setup complete:
   - **Developer A**: User Story 1 (email-mcp) - T011-T021
   - **Developer B**: User Story 2 (browser-mcp) - T022-T033
   - **Developer C**: User Story 3 (Planner validation) - T034-T042
4. Stories complete and integrate independently
5. Team reconvenes for Polish (Phase 6)

**Parallel Time Estimate**: 12-15 hours with 3 developers

---

## Suggested MVP Scope

**Minimum Viable Product**: Complete **Phase 1, 2, and 3 only** (Setup + Foundational + User Story 1)

This delivers:
- ✅ Complete email automation (watcher → agent → HITL → email-mcp → sent)
- ✅ Professional email drafting with Karachi business tone
- ✅ 100% HITL approval enforcement
- ✅ Complete audit trail
- ✅ Dashboard monitoring
- ✅ Saves 5-8 hours/week on email processing

**Why this is sufficient for MVP**:
- Email is highest priority user story (P1)
- Provides immediate business value
- Demonstrates full HITL workflow
- Proves vault-based orchestration works
- Can add LinkedIn (US2) and Planning (US3) later without refactoring

**Next Increments**:
- **v1.1**: Add User Story 2 (LinkedIn posting) - another 6-8 hours
- **v1.2**: Add User Story 3 (Planning) - another 4-5 hours
- **v2.0**: Polish phase - documentation, optimization, security hardening

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- **[Story] label** maps task to specific user story for traceability (US1, US2, US3, US4)
- **Each user story should be independently completable and testable**
- **No formal test suite** - validation via manual acceptance scenarios from spec.md
- **Commit after each task or logical group** for incremental progress
- **Stop at any checkpoint to validate story independently** before proceeding
- **Avoid**: vague tasks, same file conflicts, cross-story dependencies that break independence
- **MCP servers are the critical path** - all other infrastructure already implemented
- **Watchers, skills, vault structure, agent prompts are COMPLETE** - focus on MCP integration

---

## Current Implementation Status

**Already Complete** (from previous work):
- ✅ Constitution v2.0.0 with 8 principles
- ✅ Specification with 4 user stories (37 functional requirements)
- ✅ Implementation plan with vault architecture
- ✅ Watchers (Gmail + FileSystem) - 740 lines Python
- ✅ Agent Skills (email-drafter, social-linkedin-poster, plan-creator)
- ✅ Agent Prompts (System/silver-main.md, Email-Sub.md, Comms-Sub.md, Planner-Sub.md)
- ✅ Vault structure initialized (all folders + Dashboard.md + Company_Handbook.md)
- ✅ HITL approval workflow (Pending_Approval/ → Approved/)
- ✅ Deployment guide (System/DEPLOYMENT.md)
- ✅ Dual logging system (JSON logs + Dashboard.md)

**Remaining for 100% Silver Tier** (this tasks.md):
- ⚠️ MCP servers (email-mcp, browser-mcp) - **PRIMARY FOCUS**
- ⚠️ End-to-end integration testing
- ⚠️ Documentation updates with MCP setup
- ⚠️ Security review and error recovery documentation

**Estimated Time to 100% Silver**: 21-28 hours (or 12-15 hours with 3 developers in parallel)
