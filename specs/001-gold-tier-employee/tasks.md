# Tasks: Gold-Tier Autonomous AI Employee

**Input**: Design documents from `/specs/001-gold-tier-employee/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅, research.md ✅, quickstart.md ✅

**Tests**: Not explicitly requested in specification - focus on end-to-end workflow validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Agent configurations**: `.claude/agents/*.md`
- **Skills**: `.claude/skills/*/SKILL.md`
- **MCP servers**: `.claude/mcp-servers/odoo-mcp/`
- **Vault structure**: Repository root folders (Needs_Action/, In_Progress/, etc.)
- **Logs**: `Logs/YYYY-MM-DD.jsonl`
- **Documentation**: Root-level Markdown files (Dashboard.md, Business_Goals.md, Company_Handbook.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Vault structure initialization and basic documentation files

- [ ] T001 Create vault folder structure: Needs_Action/ with subdirectories (Accounting/, Social/, Finance/, Email/, Comms/)
- [ ] T002 [P] Create vault folder structure: In_Progress/ with subdirectories (accounting-sub-agent/, social-sub-agent/, finance-auditor-sub-agent/, approval-sub-agent/)
- [ ] T003 [P] Create vault folder structure: Pending_Approval/, Approved/, Done/ with subdirectories (Accounting/, Social/)
- [ ] T004 [P] Create vault folder structure: Briefings/, Accounting/, Logs/, Plans/
- [ ] T005 [P] Create Dashboard.md template with sections: Status, Pending Approvals, Weekly Audit Status, Recent Activity, Error Log
- [ ] T006 [P] Create Business_Goals.md template with sample business objectives and KPIs for CEO briefing context
- [ ] T007 [P] Create Company_Handbook.md template with approval thresholds (PKR 50,000 dual approval, PKR 25,000 unusual transaction), subscription monitoring (30 days)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Odoo MCP Server Development (PREREQUISITE for US1)

- [ ] T008 Create odoo-mcp project structure in .claude/mcp-servers/odoo-mcp/ (server.py, odoo_client.py, methods/, config.json)
- [ ] T009 Implement Odoo JSON-RPC client in .claude/mcp-servers/odoo-mcp/odoo_client.py (odoo-rpc library, connection, authentication)
- [ ] T010 [P] Implement create_draft method in .claude/mcp-servers/odoo-mcp/methods/create_draft.py (account.move draft creation, invoice/payment support)
- [ ] T011 [P] Implement confirm method in .claude/mcp-servers/odoo-mcp/methods/confirm.py (draft confirmation with approval check)
- [ ] T012 [P] Implement post method in .claude/mcp-servers/odoo-mcp/methods/post.py (post to ledger with approval check)
- [ ] T013 [P] Implement search_records method in .claude/mcp-servers/odoo-mcp/methods/search_records.py (read-only queries for audit data collection)
- [ ] T014 Implement MCP server main in .claude/mcp-servers/odoo-mcp/server.py (FastAPI/stdio, method routing, Pydantic schemas, error handling)
- [ ] T015 Create odoo-mcp config.json with connection settings (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD_FILE env vars)
- [ ] T016 Test odoo-mcp server: create draft invoice, confirm, post workflow with Odoo Community 19+ instance

### Agent & Skill Carry-Over from Silver

- [ ] T017 [P] Verify task-triage skill exists in .claude/skills/task-triage/SKILL.md (Silver carry-over - classify urgency, suggest actions)
- [ ] T018 [P] Verify file-handler skill exists in .claude/skills/file-handler/SKILL.md (Silver carry-over - summarize file content)

### Main Orchestrator Agent (PREREQUISITE for all sub-agents)

- [ ] T019 Create main-orchestrator agent configuration in .claude/agents/main-orchestrator.md (delegation, weekly audit trigger, stuck file monitoring, Dashboard updates)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 7 - Comprehensive Audit Logging (Priority: P1) 🎯 Foundational Logging

**Goal**: Implement JSON Lines logging infrastructure for complete auditability of all actions, MCP calls, approvals, and errors

**Independent Test**: Drop a test file in Needs_Action/, manually claim it, process with skill, verify Logs/YYYY-MM-DD.jsonl contains structured JSON entries with all required fields (timestamp PKT, agent, action, file, status, metadata)

**Why First**: Logging is foundational for US1, US2, US3, US4, US5 - all agents must log actions. Implementing this first ensures all subsequent work includes proper audit trail.

### Implementation for User Story 7

- [ ] T020 [US7] Create log entry JSON schema validation in specs/001-gold-tier-employee/contracts/logs.schema.json (verify required fields, special field sets)
- [ ] T021 [US7] Add logging helper functions to .claude/agents/gold-main-orchestrator.md instructions: log_action(agent, action, file, status, metadata)
- [ ] T022 [US7] Add logging helper functions for MCP calls: log_mcp_call(agent, file, mcp, method, params, result)
- [ ] T023 [US7] Add logging helper functions for approvals: log_approval(agent, file, approver, approval_time)
- [ ] T024 [US7] Add logging helper functions for errors: log_error(agent, file, error_type, error_message, retry_attempt)
- [ ] T025 [US7] Test logging workflow: Create test file, claim, process, verify JSON Lines format in Logs/2026-02-15.jsonl with PKT timezone
- [ ] T026 [US7] Implement Dashboard.md Recent Activity update from Logs/ (read last 20 entries, reverse chronological)
- [ ] T027 [US7] Implement Dashboard.md Error Log update from Logs/ (read last 24h errors, group by type, show status)

**Checkpoint**: Logging infrastructure ready - all agents can now log actions to Logs/YYYY-MM-DD.jsonl and update Dashboard.md

---

## Phase 4: User Story 5 - Human-in-the-Loop Approval Workflow (Priority: P1) 🎯 Foundational HITL

**Goal**: Implement approval workflow infrastructure for sensitive actions (Odoo posts, social posts, payments >PKR 100k)

**Independent Test**: Manually create draft file in Pending_Approval/, verify no execution until moved to Approved/, move to Approved/, verify execution, check Done/ for COMPLETED_ file and Logs/ for approval_granted entry

**Why Second**: HITL workflow is required for US1 (Odoo operations) and US2 (social media) - implements constitutional safety gates.

### Implementation for User Story 5

- [ ] T028 [P] [US5] Create approval-recovery-sub-agent configuration in .claude/agents/approval-recovery-sub-agent.md (monitor Pending_Approval/, execute from Approved/, 24h timeout)
- [ ] T029 [P] [US5] Add Phase 1 to approval-recovery-sub-agent: Scan Pending_Approval/ for files >24h, move to Done/REJECTED_* with timeout_no_approval reason
- [ ] T030 [US5] Add Phase 2 to approval-recovery-sub-agent: Scan Approved/ for files, validate timestamp <24h, log approval_granted
- [ ] T031 [US5] Add Phase 3 to approval-recovery-sub-agent: Execute MCP calls from Approved/ files only (pre-execution checklist: file exists, complete payload, recent timestamp)
- [ ] T032 [US5] Add Phase 5 to approval-recovery-sub-agent: Move executed files to Done/[domain]/COMPLETED_*, update Dashboard.md Pending Approvals section
- [ ] T033 [US5] Test HITL workflow: Create ACCOUNTING_INVOICE_TEST.md in Pending_Approval/, leave for 25h, verify auto-rejection to Done/REJECTED_*, check Logs/ for approval_rejected
- [ ] T034 [US5] Test HITL approval: Create SOCIAL_linkedin_TEST.md in Pending_Approval/, move to Approved/, verify approval-recovery-sub-agent logs approval_granted and executes
- [ ] T035 [US5] Implement Dashboard.md Pending Approvals section update (list files with time since draft, partner/amount for accounting, platform/topic for social)

**Checkpoint**: HITL workflow ready - US1 and US2 can now draft to Pending_Approval/ and execute from Approved/ with human oversight

---

## Phase 5: User Story 1 - Odoo Financial Operations (Priority: P1) 🎯 MVP

**Goal**: Enable AI Employee to draft invoices and payments in Odoo ERP with human approval before posting

**Independent Test**: Drop ACCOUNTING_INVOICE_001.md in Needs_Action/Accounting/ with invoice details (partner, amount PKR 50,000, description). Verify accounting-sub-agent drafts in Odoo via odoo-mcp, creates preview in Pending_Approval/, human approves, system posts to Odoo, file moves to Done/Accounting/POSTED_*

**Why MVP**: Highest business value (saves 15-20 hours/week), critical business function, demonstrates full workflow (claim → draft → approve → post → log)

### Implementation for User Story 1

- [ ] T036 [P] [US1] Create accounting-sub-agent configuration in .claude/agents/accounting-sub-agent.md (claim ACCOUNTING_* from Needs_Action/Accounting/, invoke odoo-accounting skill)
- [ ] T037 [P] [US1] Create odoo-accounting skill in .claude/skills/odoo-accounting/SKILL.md (inputs: vault file with partner/amount/currency/description, workflow: call odoo-mcp create_draft, output: Pending_Approval/ preview)
- [ ] T038 [US1] Add Phase 1 to accounting-sub-agent: Read Dashboard.md, Business_Goals.md, Company_Handbook.md; scan Needs_Action/Accounting/ for ACCOUNTING_INVOICE_* or ACCOUNTING_PAYMENT_*
- [ ] T039 [US1] Add Phase 2 to accounting-sub-agent: Use task-triage to classify file type (invoice vs payment), extract metadata from YAML front-matter (partner, amount, currency PKR, description, due_date)
- [ ] T040 [US1] Add Phase 3 to accounting-sub-agent: Invoke odoo-accounting skill to draft invoice/payment via odoo-mcp create_draft, generate preview with all details, move to Pending_Approval/ACCOUNTING_*
- [ ] T041 [US1] Add Phase 5 to accounting-sub-agent: Log draft_created to Logs/YYYY-MM-DD.jsonl with mcp=odoo-mcp, method=create_draft, params={partner_id, amount, currency}, result={draft_id, preview_url}
- [ ] T042 [US1] Add to approval-recovery-sub-agent Phase 3: For approved ACCOUNTING_* files, call odoo-mcp confirm then post methods, log mcp_call for each, move to Done/Accounting/POSTED_*
- [ ] T043 [US1] Test end-to-end invoice workflow: Create ACCOUNTING_INVOICE_001.md (Client ABC, PKR 50,000, "Consulting services Feb 2026"), verify draft in Odoo, approve, verify posted invoice, check Logs/ and Done/
- [ ] T044 [US1] Test concurrent invoice processing: Create ACCOUNTING_INVOICE_002.md and ACCOUNTING_INVOICE_003.md simultaneously, verify claim-by-move prevents duplicate processing, both complete independently
- [ ] T045 [US1] Test Odoo draft creation failure: Simulate odoo-mcp timeout, verify error logged to Logs/ with error_type=mcp_timeout, file moved to Done/ERROR_* with details

**Checkpoint**: Odoo financial operations fully functional - accounting-sub-agent can draft invoices/payments, approval-recovery-sub-agent posts after human approval, complete audit trail in Logs/

---

## Phase 6: User Story 3 - Weekly Audit and CEO Briefing (Priority: P1)

**Goal**: Automate weekly audit data collection (Sunday 23:00 PKT) and CEO briefing generation (Monday 07:00 PKT)

**Independent Test**: Main orchestrator creates WEEKLY_AUDIT_TRIGGER.md Sunday 23:00 PKT. Finance-auditor-sub-agent claims trigger, collects data from Odoo (revenue), bank CSV (expenses), Done/ (tasks), Social/Summary_* (engagement), flags anomalies (subscriptions >30 days no usage), writes Accounting/Audit_Data_2026-02-15.md. Monday 07:00 PKT, generates Briefings/2026-02-17_Monday_Briefing.md with professional Karachi tone.

### Implementation for User Story 3

- [ ] T046 [P] [US3] Create finance-auditor-sub-agent configuration in .claude/agents/finance-auditor-sub-agent.md (claim WEEKLY_AUDIT_TRIGGER, invoke weekly-audit-engine and ceo-briefing-generator skills)
- [ ] T047 [P] [US3] Create weekly-audit-engine skill in .claude/skills/weekly-audit-engine/SKILL.md (inputs: WEEKLY_AUDIT_TRIGGER, outputs: Accounting/Audit_Data_[date].md with revenue, expenses, tasks, social, anomalies)
- [ ] T048 [P] [US3] Create ceo-briefing-generator skill in .claude/skills/ceo-briefing-generator/SKILL.md (inputs: Audit_Data, Business_Goals.md, Dashboard.md; output: Briefings/YYYY-MM-DD_Monday_Briefing.md)
- [ ] T049 [US3] Add to main-orchestrator Phase 2: Weekly audit trigger logic - check if current day/time is Sunday 23:00 PKT, create WEEKLY_AUDIT_TRIGGER.md in Needs_Action/ if not exists
- [ ] T050 [US3] Add Phase 1 to finance-auditor-sub-agent: Read Dashboard.md, Business_Goals.md, Company_Handbook.md; scan Needs_Action/ for WEEKLY_AUDIT_TRIGGER.md, claim to In_Progress/finance-auditor-sub-agent/
- [ ] T051 [US3] Add Phase 3 to finance-auditor-sub-agent: Invoke weekly-audit-engine skill to collect revenue from odoo-mcp search_records (account.move where state=posted, week range)
- [ ] T052 [US3] Add to weekly-audit-engine: Parse bank CSV from Finance/ folder for expenses and subscriptions (total expenses, subscription costs, last usage dates)
- [ ] T053 [US3] Add to weekly-audit-engine: Scan Done/ folder for task completion (count files, extract created/completed timestamps, calculate avg completion time, flag delayed >5 days)
- [ ] T054 [US3] Add to weekly-audit-engine: Read Social/Summary_*.md files for weekly social metrics (posts made, total reach, engagement rate, potential leads)
- [ ] T055 [US3] Add to weekly-audit-engine: Flag anomalies - subscriptions >30 days no usage (from bank CSV), delayed tasks >expected duration (from Company_Handbook.md), unusual transactions >threshold PKR 25,000
- [ ] T056 [US3] Add to weekly-audit-engine: Write Accounting/Audit_Data_[date].md with all collected data and anomaly flags, log AUDIT_DATA_COLLECTED to Logs/
- [ ] T057 [US3] Add Phase 4 to finance-auditor-sub-agent: Check if current time is Monday 07:00 PKT, invoke ceo-briefing-generator skill if yes
- [ ] T058 [US3] Add to ceo-briefing-generator: Read Accounting/Audit_Data_[date].md, Business_Goals.md, Dashboard.md
- [ ] T059 [US3] Add to ceo-briefing-generator: Generate Executive Summary (revenue change %, task completion rate, social reach growth, bottleneck summary, cost-saving opportunities)
- [ ] T060 [US3] Add to ceo-briefing-generator: Generate Revenue & Financial Performance section (total revenue PKR with % change, receivables, expenses, net profit, key metrics)
- [ ] T061 [US3] Add to ceo-briefing-generator: Generate Tasks & Operational Progress section (completed count, avg time, delayed tasks, top bottleneck with recommendation)
- [ ] T062 [US3] Add to ceo-briefing-generator: Generate Social Media & Lead Generation section (posts by platform, reach, engagement rate, potential leads, top performing post)
- [ ] T063 [US3] Add to ceo-briefing-generator: Generate Proactive Suggestions section from anomalies (cost savings from unused subscriptions, process improvements for bottlenecks, opportunities from high engagement)
- [ ] T064 [US3] Add to ceo-briefing-generator: Generate Business Goals Alignment section (read Business_Goals.md, track progress per goal, flag on track / opportunity / action needed)
- [ ] T065 [US3] Add to ceo-briefing-generator: Write Briefings/YYYY-MM-DD_Monday_Briefing.md with professional Karachi business tone (respectful, formal, concise, culturally aware, cost-conscious PKR amounts)
- [ ] T066 [US3] Add Phase 5 to finance-auditor-sub-agent: Move WEEKLY_AUDIT_TRIGGER to Done/, update Dashboard.md Weekly Audit Status (last audit date, next audit date, briefing generated checkmark)
- [ ] T067 [US3] Test weekly audit trigger: Manually create WEEKLY_AUDIT_TRIGGER.md, verify finance-auditor-sub-agent claims, collects data from Odoo (use odoo-mcp search_records), writes Audit_Data with flagged anomalies
- [ ] T068 [US3] Test CEO briefing generation: Use sample Audit_Data_2026-02-15.md, Business_Goals.md, Dashboard.md; verify Briefings/2026-02-17_Monday_Briefing.md generated with all sections in professional Karachi tone
- [ ] T069 [US3] Test anomaly flagging: Create bank CSV with subscription last used 41 days ago, verify weekly-audit-engine flags in Audit_Data, verify ceo-briefing-generator suggests cancellation in Proactive Suggestions

**Checkpoint**: Weekly audit cycle fully functional - audit runs Sunday night, CEO briefing ready Monday morning with actionable insights, anomaly detection working

---

## Phase 7: User Story 6 - Cross-Domain Coordination via Vault (Priority: P2)

**Goal**: Implement claim-by-move coordination so sub-agents process files in parallel without race conditions or duplicate work

**Independent Test**: Place ACCOUNTING_INVOICE_004.md in Needs_Action/Accounting/ and SOCIAL_linkedin_004.md in Needs_Action/Social/ simultaneously. Verify accounting-sub-agent claims first, social-media-sub-agent claims second, both process independently in parallel, no interference, both log claims to Logs/ with timestamp and claimed_by

### Implementation for User Story 6

- [ ] T070 [US6] Document claim-by-move protocol in .claude/agents/gold-main-orchestrator.md instructions: atomic file move via rename (not copy-delete), first agent to succeed owns file exclusively
- [ ] T071 [US6] Add to all sub-agent Phase 1: Use atomic file move to claim file from Needs_Action/[domain]/ to In_Progress/[agent-name]/, log claim_file to Logs/ with timestamp, agent, file, claimed_by
- [ ] T072 [US6] Add to all sub-agent Phase 1: If file move fails (already claimed by another agent), skip to next item without error, do not retry claim on same file
- [ ] T073 [US6] Add to all sub-agent Phase 5: On error, move file to Done/ERROR_[filename] to release ownership, log error with details, continue to next item
- [ ] T074 [US6] Add to main-orchestrator Phase 3: System health monitoring - scan In_Progress/[all agents]/ for stuck files (>30 min without log activity), flag in Dashboard.md with agent name and duration
- [ ] T075 [US6] Test parallel processing: Create ACCOUNTING_INVOICE_005.md and SOCIAL_linkedin_005.md in respective Needs_Action/ folders at same time, verify both claimed and processed in parallel with no blocking
- [ ] T076 [US6] Test claim collision: Simulate two agents attempting to claim same file (create file, manually move twice), verify second move fails gracefully, first agent processes file, second skips
- [ ] T077 [US6] Test error release: Simulate processing error on ACCOUNTING_INVOICE_006.md, verify file moves to Done/ERROR_* with error details, ownership released, next file can be claimed

**Checkpoint**: Vault coordination working - sub-agents claim files atomically, process in parallel across domains, no duplicate work, errors release ownership cleanly

---

## Phase 8: User Story 2 - Multi-Platform Social Media Management (Priority: P2)

**Goal**: Enable AI Employee to generate platform-specific social media posts (LinkedIn, Facebook, Instagram, Twitter/X) with approval before posting

**Independent Test**: Drop SOCIAL_linkedin_006.md in Needs_Action/Social/ with post topic "Announce Q1 business growth". Verify social-media-sub-agent generates professional LinkedIn content with Karachi hashtags, creates preview in Pending_Approval/, human approves, browser-mcp posts to LinkedIn, file moves to Done/Social/POSTED_*, engagement summary created in Social/Summary_2026-02-15.md

### Implementation for User Story 2

- [ ] T078 [P] [US2] Create social-media-sub-agent configuration in .claude/agents/social-media-sub-agent.md (claim SOCIAL_* from Needs_Action/Social/, invoke multi-social-poster skill)
- [ ] T079 [P] [US2] Create multi-social-poster skill in .claude/skills/multi-social-poster/SKILL.md (inputs: vault file with platform and topic, outputs: Pending_Approval/ preview with platform-specific content)
- [ ] T080 [US2] Add Phase 1 to social-media-sub-agent: Read Dashboard.md, Business_Goals.md, Company_Handbook.md; scan Needs_Action/Social/ for SOCIAL_linkedin_*, SOCIAL_facebook_*, SOCIAL_instagram_*, SOCIAL_x_*
- [ ] T081 [US2] Add Phase 2 to social-media-sub-agent: Use task-triage to classify platform from filename or YAML front-matter (linkedin | facebook | instagram | x), extract topic and post requirements
- [ ] T082 [US2] Add Phase 3 to social-media-sub-agent: Invoke multi-social-poster skill to generate platform-specific content (LinkedIn: professional business-focused 300-500 words, Facebook: conversational 150-300 words, Instagram: visual story 100-150 words + hashtags, Twitter/X: concise <280 chars)
- [ ] T083 [US2] Add to multi-social-poster: For all platforms, include Karachi/Sindh local hashtags when relevant (#KarachiBusinesses, #PakistanStartups, #SindhEntrepreneur)
- [ ] T084 [US2] Add to multi-social-poster: Generate preview with platform, content, hashtags, target audience, estimated reach, move to Pending_Approval/SOCIAL_[platform]_[id].md
- [ ] T085 [US2] Add Phase 5 to social-media-sub-agent: Log draft_created to Logs/ with platform, topic, content length, hashtag count
- [ ] T086 [US2] Add to approval-recovery-sub-agent Phase 3: For approved SOCIAL_* files, call browser-mcp to navigate to platform, fill post form, click publish, log mcp_call, move to Done/Social/POSTED_*
- [ ] T087 [US2] Add Phase 3 to social-media-sub-agent: After posting, generate engagement summary in Social/Summary_[date].md (platform, post title, publish time, reach, engagement rate, potential leads)
- [ ] T088 [US2] Add to multi-social-poster: Enforce maximum 3 posts per day across all platforms (read Done/Social/POSTED_* for today, count, halt if ≥3 with error message)
- [ ] T089 [US2] Test LinkedIn post generation: Create SOCIAL_linkedin_007.md with topic "New service offering - Odoo consulting", verify professional content, Karachi hashtags, preview in Pending_Approval/
- [ ] T090 [US2] Test Instagram post generation: Create SOCIAL_instagram_008.md with topic "Behind the scenes: Team collaboration", verify visual story content <150 words, 5-10 hashtags including #KarachiBusinesses
- [ ] T091 [US2] Test Twitter/X post generation: Create SOCIAL_x_009.md with topic "Quick business tip: Invoice automation", verify concise content <280 chars, relevant hashtags
- [ ] T092 [US2] Test post approval and execution: Approve SOCIAL_linkedin_007.md, verify approval-recovery-sub-agent calls browser-mcp to post to LinkedIn, generates Social/Summary_2026-02-15.md with reach metrics
- [ ] T093 [US2] Test 3 posts per day limit: Create 4 SOCIAL_* files on same day, verify first 3 processed, 4th halted with error "Daily post limit reached (3/day max)"

**Checkpoint**: Social media management fully functional - social-media-sub-agent generates platform-specific content, approval-recovery-sub-agent posts after approval, engagement tracked in summaries

---

## Phase 9: User Story 4 - Error Detection and Recovery (Priority: P2)

**Goal**: Automate error detection, retry transient failures with exponential backoff, flag persistent issues for human review

**Independent Test**: Simulate odoo-mcp timeout on ACCOUNTING_INVOICE_010.md. Verify approval-recovery-sub-agent detects error, logs error_type=mcp_timeout, retries after 1min with retry_attempt=1, logs retry. If fails again, retry after 5min (retry_attempt=2), then 15min (retry_attempt=3). After 3 failures, move to Done/ERROR_* and flag in Dashboard.md Error Log with status=escalated.

### Implementation for User Story 4

- [ ] T094 [P] [US4] Create error-recovery-handler skill in .claude/skills/error-recovery-handler/SKILL.md (inputs: error event, outputs: recovery action - retry | pause | escalate)
- [ ] T095 [US4] Add to approval-recovery-sub-agent Phase 3: Wrap all MCP calls in try/except error handling, log error to Logs/ on exception with error_type, error_message
- [ ] T096 [US4] Add to approval-recovery-sub-agent Phase 3: Invoke error-recovery-handler skill on MCP error to classify error type (transient: mcp_timeout, network_error, temporary_unavailable; persistent: authentication_failure, invalid_params, odoo_config_error)
- [ ] T097 [US4] Add to error-recovery-handler: For transient errors, return recovery_action=retry with exponential backoff schedule: 1min (attempt 1), 5min (attempt 2), 15min (attempt 3)
- [ ] T098 [US4] Add to error-recovery-handler: For persistent errors, return recovery_action=pause (move to Done/ERROR_* with details) or escalate (flag in Dashboard.md for human)
- [ ] T099 [US4] Add to approval-recovery-sub-agent Phase 3: Implement retry logic - sleep for backoff duration, increment retry_attempt, log recovery_attempt to Logs/ with recovery_action=retry, recovery_status=recovering
- [ ] T100 [US4] Add to approval-recovery-sub-agent Phase 3: After 3 failed retries, move file to Done/ERROR_* with all error details, log recovery_status=escalated, update Dashboard.md Error Log
- [ ] T101 [US4] Add to approval-recovery-sub-agent Phase 3: On successful retry, log recovery_status=resolved, continue workflow (confirm/post or navigate/fill/click), move to Done/COMPLETED_*
- [ ] T102 [US4] Add to main-orchestrator Phase 3: Watchdog monitoring - count errors in Logs/ today grouped by error_type, if error rate >threshold (5 errors/hour), flag spike in Dashboard.md Error Log
- [ ] T103 [US4] Add to main-orchestrator Phase 3: Detect constitutional violations - if any agent attempts state-changing MCP without Approved/ file, log CONSTITUTION VIOLATION PREVENTED to Dashboard.md and Logs/, halt affected agent
- [ ] T104 [US4] Test transient error recovery: Simulate odoo-mcp timeout on ACCOUNTING_INVOICE_011.md, verify retry after 1min (attempt 1), mock success, verify recovery_status=resolved and workflow continues
- [ ] T105 [US4] Test persistent error escalation: Simulate odoo authentication_failure on ACCOUNTING_INVOICE_012.md, verify 3 retries with exponential backoff, after 3 failures verify move to Done/ERROR_* and Dashboard.md flag with status=escalated
- [ ] T106 [US4] Test error watchdog: Create 6 errors within 1 hour (simulate MCP timeouts), verify main-orchestrator flags error rate spike in Dashboard.md Error Log
- [ ] T107 [US4] Test constitutional violation detection: Attempt to call odoo-mcp confirm without Approved/ file, verify main-orchestrator logs CONSTITUTION VIOLATION PREVENTED and halts action

**Checkpoint**: Error recovery fully functional - transient errors retry with exponential backoff, persistent errors escalate to human, watchdog monitors system health, constitutional violations blocked

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final testing, documentation, and system validation

- [ ] T108 [P] Create sample vault test files for each workflow: ACCOUNTING_INVOICE_SAMPLE.md, SOCIAL_linkedin_SAMPLE.md, WEEKLY_AUDIT_TRIGGER_SAMPLE.md with realistic data
- [ ] T109 [P] Update Dashboard.md with final template including all sections: Status (Last Active, queue counts), Pending Approvals (with time since draft), Weekly Audit Status, Recent Activity (20 entries), Error Log (24h), System Health (uptime, stuck files, violations)
- [ ] T110 [P] Document agent operational instructions in history/prompts/001-gold-tier-employee/gold-tier-operational-cycle.prompt.md: 5-phase cycle (Observe & Claim → Classify & Delegate → Execute with HITL → Audit & Weekly → Clean, Log & Report)
- [ ] T111 Validate quickstart.md: Follow all setup steps, run end-to-end test workflows, verify each independent test criteria from spec.md user stories
- [ ] T112 Run end-to-end workflow test 1 (US1): Drop ACCOUNTING_INVOICE_TEST_FINAL.md, verify full cycle (claim → draft → approve → post → Done/POSTED_* → Logs/ entry → Dashboard update)
- [ ] T113 Run end-to-end workflow test 2 (US2): Drop SOCIAL_linkedin_TEST_FINAL.md, verify full cycle (claim → generate → approve → post → Done/POSTED_* → Summary_* → Logs/ → Dashboard)
- [ ] T114 Run end-to-end workflow test 3 (US3): Trigger weekly audit (create WEEKLY_AUDIT_TRIGGER.md), verify Audit_Data collection from Odoo/bank/Done/Social, verify CEO briefing generation with Karachi tone
- [ ] T115 Run end-to-end workflow test 4 (US5): Create ACCOUNTING_PAYMENT_TEST.md in Pending_Approval/, leave 25h, verify auto-rejection to Done/REJECTED_*, check Logs/ for timeout_no_approval
- [ ] T116 Run end-to-end workflow test 5 (US6): Drop ACCOUNTING_INVOICE_A.md and SOCIAL_linkedin_B.md simultaneously, verify parallel processing with no collisions, both complete independently
- [ ] T117 Verify constitutional compliance: Check all HITL gates enforced (Odoo confirm/post, social posts require approval), verify claim-by-move prevents duplicates, verify logging complete, verify PKR currency and PKT timezone in all logs
- [ ] T118 Performance validation: Measure invoice draft creation time (<5 min target from Needs_Action/ drop), social post draft time (<10 min target), CEO briefing generation time (<15 min target Monday 07:00 PKT)
- [ ] T119 [P] Security validation: Verify NEVER logging passwords/credentials/tokens, verify Approved/ file check before state-changing MCP calls, verify 24h approval timeout prevents stale approvals
- [ ] T120 Final cleanup: Remove all test files from vault folders (Needs_Action/, In_Progress/, Pending_Approval/, Approved/, Done/), clear test Logs/, remove sample Briefings/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **US7 Logging (Phase 3)**: Depends on Foundational completion - Foundational for US1-US6 (all agents log)
- **US5 HITL (Phase 4)**: Depends on US7 completion - Foundational for US1, US2 (require approval workflow)
- **US1 Odoo Ops (Phase 5)**: Depends on US5, US7 completion - MVP deliverable
- **US3 Weekly Audit (Phase 6)**: Depends on US7 completion, ideally after US1 (needs Odoo data for audit)
- **US6 Vault Coordination (Phase 7)**: Depends on US7 completion - Enables parallel US1, US2, US3
- **US2 Social Media (Phase 8)**: Depends on US5, US7 completion
- **US4 Error Recovery (Phase 9)**: Depends on US7 completion, ideally after US1, US2 (needs workflows to monitor)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

**Foundational Stories** (MUST complete first):
- **User Story 7 (P1) - Logging**: No dependencies on other stories - Foundational for all
- **User Story 5 (P1) - HITL**: Depends on US7 - Foundational for US1, US2

**MVP Story**:
- **User Story 1 (P1) - Odoo Ops**: Depends on US5, US7 - Can start after foundational stories

**Parallel Stories** (can run in parallel after foundational + MVP):
- **User Story 3 (P1) - Weekly Audit**: Depends on US7, ideally US1 for Odoo data
- **User Story 6 (P2) - Vault Coordination**: Depends on US7
- **User Story 2 (P2) - Social Media**: Depends on US5, US7

**Enhancement Story**:
- **User Story 4 (P2) - Error Recovery**: Depends on US7, ideally US1+US2 complete for workflows to monitor

### Within Each User Story

**General pattern**:
- Agent configurations before skill invocations
- Skills before agent phases that invoke them
- MCP server methods before skills that call them
- Logging infrastructure before all actions
- HITL infrastructure before draft/approve workflows

### Parallel Opportunities

**Phase 1 (Setup)**: T002, T003, T004, T005, T006, T007 can run in parallel (different folders/files)

**Phase 2 (Foundational)**:
- T010, T011, T012, T013 (Odoo MCP methods) can run in parallel (different files)
- T017, T018 (skill verification) can run in parallel

**Phase 3 (US7 Logging)**: Most tasks sequential due to logging dependencies

**Phase 5 (US1 Odoo Ops)**: T036, T037 can run in parallel (agent config vs skill definition)

**Phase 6 (US3 Audit)**: T046, T047, T048 can run in parallel (agent config vs 2 skill definitions)

**Phase 8 (US2 Social)**: T078, T079 can run in parallel (agent config vs skill definition)

**Phase 10 (Polish)**: T108, T109, T110, T119 can run in parallel (different files/tasks)

**Cross-Story Parallelization**:
Once US7 and US5 complete, US1, US3, US6 can be worked on in parallel by different team members (different agents/skills/domains)

---

## Parallel Example: User Story 1 (Odoo Operations)

```bash
# Launch agent config and skill definition together (T036, T037):
Task: "Create accounting-sub-agent configuration in .claude/agents/accounting-sub-agent.md"
Task: "Create odoo-accounting skill in .claude/skills/odoo-accounting/SKILL.md"

# Both can proceed in parallel as they edit different files with no dependencies
```

---

## Implementation Strategy

### MVP First (US7 + US5 + US1 Only)

1. Complete Phase 1: Setup (vault structure, base files)
2. Complete Phase 2: Foundational (Odoo MCP server, main orchestrator) - CRITICAL
3. Complete Phase 3: US7 Logging (foundational for all subsequent work)
4. Complete Phase 4: US5 HITL (foundational for US1 approval workflow)
5. Complete Phase 5: US1 Odoo Financial Operations (MVP!)
6. **STOP and VALIDATE**: Test US1 independently with end-to-end workflow
7. Deploy/demo: Drop invoice, draft in Odoo, approve, post, verify Done/ and Logs/

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US7 Logging → All actions auditable
3. Add US5 HITL → Approval gates working
4. Add US1 Odoo Ops → Test independently → **Deploy/Demo (MVP! 🎯)**
5. Add US3 Weekly Audit → Test independently → Deploy/Demo (Executive visibility)
6. Add US6 Vault Coordination → Enable parallel processing
7. Add US2 Social Media → Test independently → Deploy/Demo (Marketing automation)
8. Add US4 Error Recovery → Test independently → Deploy/Demo (System reliability)
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. **Week 1** (Team together): Complete Setup (Phase 1) + Foundational (Phase 2) + US7 Logging (Phase 3)
2. **Week 2** (Team splits):
   - Developer A: US5 HITL + US1 Odoo Ops (MVP critical path)
   - Developer B: US6 Vault Coordination (enables parallelization)
   - Developer C: US3 Weekly Audit (executive reporting)
3. **Week 3** (Team splits):
   - Developer A: US2 Social Media (requires US5 HITL complete)
   - Developer B: US4 Error Recovery (monitors US1, US2 workflows)
   - Developer C: Phase 10 Polish (testing, validation)
4. Stories integrate independently via vault file coordination

---

## Notes

- **[P] tasks** = different files, no dependencies, safe to parallelize
- **[Story] label** maps task to specific user story for traceability
- **Each user story should be independently completable and testable** via its Independent Test criteria
- **Tests are OPTIONAL**: Spec does not explicitly request unit/integration tests - validation via end-to-end workflows
- **Commit after each task or logical group** (e.g., commit after agent config + skill definition pair)
- **Stop at any checkpoint to validate story independently** before proceeding to next priority
- **Avoid**: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Gold-tier system is agent-based**: No traditional code compilation - system operates through agent skill invocations and MCP integrations
- **Critical path**: Odoo MCP server (T008-T016) MUST complete before US1 can start - highest priority blocker
- **Vault structure is foundational**: Setup phase (T001-T007) creates all required folders for claim-by-move coordination
- **Logging is foundational**: US7 (T020-T027) MUST complete before US1-US6 to ensure all actions are auditable
- **HITL is foundational for sensitive actions**: US5 (T028-T035) MUST complete before US1, US2 to enforce approval gates
- **Professional Karachi business tone required**: All CEO briefings, social posts, communications must be respectful, formal, concise, culturally aware, cost-conscious (PKR amounts)
- **Constitutional compliance non-negotiable**: HITL gates, claim-by-move coordination, logging completeness, PKR/PKT standards enforced throughout

---

**Tasks Status**: ✅ **COMPLETE**

**Total Tasks**: 120 tasks across 10 phases

**Task Breakdown by User Story**:
- Setup (Phase 1): 7 tasks
- Foundational (Phase 2): 12 tasks
- US7 Logging (Phase 3): 8 tasks
- US5 HITL (Phase 4): 8 tasks
- US1 Odoo Ops (Phase 5 - MVP): 10 tasks
- US3 Weekly Audit (Phase 6): 24 tasks
- US6 Vault Coordination (Phase 7): 8 tasks
- US2 Social Media (Phase 8): 16 tasks
- US4 Error Recovery (Phase 9): 14 tasks
- Polish (Phase 10): 13 tasks

**Parallel Opportunities**: 15+ tasks marked [P] for parallelization

**MVP Scope**: Phases 1-5 (Setup + Foundational + US7 + US5 + US1) = 45 tasks for minimum viable product

**Next Step**: Begin implementation with `/sp.implement` or manually execute tasks starting with Phase 1
