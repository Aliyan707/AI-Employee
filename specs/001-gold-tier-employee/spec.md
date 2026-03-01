# Feature Specification: Gold-Tier Autonomous AI Employee

**Feature Branch**: `001-gold-tier-employee`
**Created**: 2026-02-15
**Status**: Draft
**Input**: User description: "Gold tier scope — 40+ hour autonomous employee deliverable with 4 specialized sub-agents for accounting, social media, finance auditing, and approval/recovery operations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Odoo Financial Operations (Priority: P1)

As a business owner, I need the AI Employee to draft invoices and payments in Odoo ERP so that I can review and approve financial transactions without manually creating records.

**Why this priority**: Financial operations are the most critical business function. Automated draft creation saves 15-20 hours/week while maintaining human oversight over all financial decisions.

**Independent Test**: Can be fully tested by dropping an ACCOUNTING_INVOICE_001.md file in Needs_Action/Accounting/ with invoice details. System should draft the invoice in Odoo, place preview in Pending_Approval/, and upon human approval, post the invoice to Odoo. Delivers immediate value by automating invoice creation workflow.

**Acceptance Scenarios**:

1. **Given** an invoice request file in Needs_Action/Accounting/, **When** Accounting Sub-Agent claims the file, **Then** system drafts invoice in Odoo via odoo-mcp and creates preview in Pending_Approval/
2. **Given** an approved invoice in Approved/, **When** Approval Sub-Agent processes it, **Then** system posts invoice to Odoo and moves file to Done/Accounting/POSTED_*
3. **Given** an Odoo draft creation fails, **When** error occurs, **Then** system logs error to Logs/YYYY-MM-DD.jsonl and moves file to Done/ERROR_* with details
4. **Given** multiple invoice requests, **When** processed concurrently, **Then** each is handled by claim-by-move with no duplicate processing

---

### User Story 2 - Multi-Platform Social Media Management (Priority: P2)

As a business owner, I need the AI Employee to generate platform-specific social media posts for LinkedIn, Facebook, Instagram, and Twitter/X so that I can maintain consistent brand presence across platforms with minimal manual effort.

**Why this priority**: Social media drives customer acquisition and brand awareness. Automating content generation while requiring approval maintains quality and saves 8-10 hours/week.

**Independent Test**: Can be fully tested by placing a SOCIAL_linkedin_001.md file describing desired post topic in Needs_Action/Social/. System should generate platform-appropriate content, place in Pending_Approval/, and upon approval, post via browser-mcp. Delivers value by maintaining social media presence without manual content creation.

**Acceptance Scenarios**:

1. **Given** a social post request for LinkedIn, **When** Social Sub-Agent processes it, **Then** system generates professional business-focused content suitable for LinkedIn audience
2. **Given** a social post request for Instagram, **When** Social Sub-Agent processes it, **Then** system generates visual story-focused content with appropriate hashtags
3. **Given** a social post request for Twitter/X, **When** Social Sub-Agent processes it, **Then** system generates concise content under 280 characters with relevant hashtags
4. **Given** posts are approved and posted, **When** engagement occurs, **Then** system tracks metrics in Social/Summary_[date].md
5. **Given** Karachi/Sindh context, **When** generating content, **Then** system includes local hashtags and cultural awareness

---

### User Story 3 - Weekly Audit and CEO Briefing (Priority: P1)

As a business owner, I need the AI Employee to automatically run weekly audits on Sunday night and generate a comprehensive CEO briefing by Monday morning so that I start each week with clear visibility into revenue, bottlenecks, and actionable recommendations.

**Why this priority**: Executive visibility is critical for informed decision-making. Automated weekly reporting eliminates manual data aggregation (4-6 hours/week) and provides proactive business intelligence.

**Independent Test**: Can be fully tested by Main Orchestrator creating WEEKLY_AUDIT_TRIGGER.md on Sunday at 23:00 PKT. System should collect data from Odoo, bank transactions, Done/ folder, and social summaries, flag anomalies, and generate Monday briefing in Briefings/. Delivers immediate value by providing automated weekly business intelligence.

**Acceptance Scenarios**:

1. **Given** it is Sunday 23:00 PKT, **When** Main Orchestrator triggers audit, **Then** Finance & Auditor Sub-Agent claims trigger and invokes weekly-audit-engine
2. **Given** audit engine is running, **When** collecting data, **Then** system retrieves revenue from Odoo, expenses from bank transactions, task completion from Done/, and social metrics from summaries
3. **Given** audit data is collected, **When** analyzing, **Then** system flags subscriptions with no usage >30 days, delayed tasks, and unusual transactions above threshold
4. **Given** audit completes, **When** Monday 07:00 PKT arrives, **Then** system generates CEO briefing in Briefings/YYYY-MM-DD_Monday_Briefing.md
5. **Given** briefing is generated, **When** reading it, **Then** it contains revenue summary, completed tasks, bottlenecks, proactive suggestions, and social activity in professional Karachi business tone

---

### User Story 4 - Error Detection and Recovery (Priority: P2)

As a business owner, I need the AI Employee to automatically detect errors, retry transient failures, and flag persistent issues so that system reliability is maintained without constant manual intervention.

**Why this priority**: System reliability directly impacts business operations. Automated error recovery reduces downtime and prevents stuck workflows, saving 3-5 hours/week of troubleshooting.

**Independent Test**: Can be fully tested by simulating MCP timeouts or Odoo connection failures. System should detect error, log to Logs/, retry transient failures with exponential backoff, pause persistent issues, and flag critical errors in Dashboard.md. Delivers value by maintaining system health autonomously.

**Acceptance Scenarios**:

1. **Given** an MCP call times out, **When** error occurs, **Then** Approval & Recovery Sub-Agent logs error with retry_attempt=1 and retries after delay
2. **Given** a transient error resolves after retry, **When** recovery succeeds, **Then** system logs recovery_status=resolved and continues workflow
3. **Given** a persistent error fails after 3 retries, **When** max retries exceeded, **Then** system pauses workflow, moves file to Done/ERROR_*, and flags in Dashboard.md
4. **Given** error rates exceed threshold, **When** watchdog detects spike, **Then** system flags in Dashboard.md Error Log and alerts for human review
5. **Given** critical system error, **When** detected, **Then** system halts affected sub-agent and logs CONSTITUTION VIOLATION PREVENTED if applicable

---

### User Story 5 - Human-in-the-Loop Approval Workflow (Priority: P1)

As a business owner, I need all sensitive actions (Odoo posts, social media posts, payments >PKR 100,000) to require my explicit approval before execution so that I maintain control over critical business decisions.

**Why this priority**: Risk management is essential for financial and reputational safety. HITL gates prevent costly errors while allowing automation of preparatory work.

**Independent Test**: Can be fully tested by creating drafts in Pending_Approval/ and verifying that no action executes until file is moved to Approved/. System should never auto-execute state-changing MCP calls without approval. Delivers value by providing safety guardrails for automation.

**Acceptance Scenarios**:

1. **Given** an Odoo invoice draft in Pending_Approval/, **When** human does not approve within 24 hours, **Then** system assumes rejection and moves to Done/REJECTED_*
2. **Given** a social post draft in Pending_Approval/, **When** human moves to Approved/, **Then** Approval Sub-Agent executes browser-mcp posting within approval window (<24 hours)
3. **Given** a payment request >PKR 100,000, **When** drafted, **Then** system MUST flag for HITL approval regardless of other rules
4. **Given** any irreversible action, **When** preparing to execute, **Then** system MUST check for Approved/ file and halt if not present
5. **Given** approval is granted, **When** executing action, **Then** system logs approval_granted with approver and approval_time to audit trail

---

### User Story 6 - Cross-Domain Coordination via Vault (Priority: P2)

As a system operator, I need sub-agents to coordinate exclusively through vault file movements (claim-by-move) so that parallelization is safe, work is never duplicated, and ownership is always clear.

**Why this priority**: Coordination prevents race conditions and duplicate work, ensuring system integrity and efficiency across all sub-agents.

**Independent Test**: Can be fully tested by placing multiple files in Needs_Action/ across different domains (Accounting/, Social/, Finance/). Each sub-agent should claim files in their domain atomically, process independently, and never interfere with other sub-agents' work.

**Acceptance Scenarios**:

1. **Given** a file in Needs_Action/Accounting/, **When** Accounting Sub-Agent claims it, **Then** file moves to In_Progress/accounting-sub-agent/ and is exclusively owned
2. **Given** two sub-agents attempt to claim same file, **When** first succeeds, **Then** second's move operation fails and it skips to next item
3. **Given** a sub-agent is processing a file, **When** error occurs, **Then** sub-agent MUST move file to Done/ERROR_* to release ownership
4. **Given** files across multiple domains, **When** processed in parallel, **Then** each sub-agent works independently with no blocking or interference
5. **Given** all file movements, **When** occurring, **Then** system logs every claim and transition to Logs/YYYY-MM-DD.jsonl

---

### User Story 7 - Comprehensive Audit Logging (Priority: P1)

As a business owner, I need every action, MCP call, approval decision, error, and recovery attempt logged in JSON Lines format so that I have complete auditability and can troubleshoot any issues or review system behavior.

**Why this priority**: Audit trail is legally and operationally critical. Complete logging enables compliance, debugging, performance analysis, and trust in automation.

**Independent Test**: Can be fully tested by performing any workflow (invoice creation, social post, audit cycle) and verifying that Logs/YYYY-MM-DD.jsonl contains structured JSON log entries for every action with all required fields (timestamp PKT, agent, action, file, status, metadata).

**Acceptance Scenarios**:

1. **Given** any sub-agent action, **When** executed, **Then** system logs to Logs/YYYY-MM-DD.jsonl with timestamp (ISO 8601 PKT), agent, action, file, status, metadata
2. **Given** any MCP call, **When** invoked, **Then** system logs with mcp, method, params, result fields
3. **Given** any approval decision, **When** granted, **Then** system logs with approver, approval_time
4. **Given** any error, **When** occurs, **Then** system logs with error_type, error_message, retry_attempt
5. **Given** end of day, **When** reviewing logs, **Then** every file movement, claim, draft, approval, execution, and error is traceable with complete context
6. **Given** Dashboard.md, **When** updated, **Then** it provides human-readable summary of recent activity, pending approvals, weekly audit status, and error log

---

### Edge Cases

- **What happens when Odoo server is unreachable?** System detects connection error, logs to Logs/ with error_type="odoo_connection_failure", retries with exponential backoff (1min, 5min, 15min), and after 3 failures flags in Dashboard.md for human intervention. File remains in In_Progress/ until resolved or moved to ERROR_.
- **What happens when browser-mcp fails to post to social platform?** System logs error, checks if transient (network timeout) or persistent (authentication failure). For transient, retries up to 3 times. For persistent, moves to Done/ERROR_* and flags for human review with specific error details.
- **What happens when approval sits in Pending_Approval/ for >24 hours?** System assumes rejection, moves file to Done/REJECTED_*, logs rejection with reason="timeout_no_approval", and updates Dashboard.md to remove from Pending Approvals list.
- **What happens when multiple domains need same data simultaneously?** Each sub-agent reads shared files (Business_Goals.md, Company_Handbook.md, Dashboard.md) independently. No locking required for read-only access. Only files being claimed/processed follow exclusive ownership.
- **What happens when Sunday audit trigger fails?** If Finance & Auditor Sub-Agent cannot claim WEEKLY_AUDIT_TRIGGER.md or errors during data collection, system logs error, moves trigger to Done/ERROR_WEEKLY_AUDIT_[date].md, and notifies via Dashboard.md that Monday briefing will be missing. Human can manually trigger next week.
- **What happens when vault folders are missing?** Main Orchestrator startup validates required folder structure exists (Needs_Action/*, In_Progress/*, Pending_Approval/, Approved/, Done/, Briefings/, Accounting/, Logs/). If missing, logs error and halts with clear message listing missing folders.
- **What happens when file has malformed content?** Sub-agent attempting to parse file detects invalid format, logs error with specifics (missing required fields, invalid JSON, etc.), moves to Done/ERROR_* with error details in filename or log, and continues to next item.

## Requirements *(mandatory)*

### Functional Requirements

#### Sub-Agent Architecture

- **FR-001**: System MUST implement exactly four specialized sub-agents: Accounting Sub-Agent, Social Media Sub-Agent, Finance & Auditor Sub-Agent, Approval & Recovery Sub-Agent
- **FR-002**: System MUST implement Main Orchestrator that delegates work, triggers weekly audit, monitors stuck items, and enforces constitutional compliance
- **FR-003**: Each sub-agent MUST operate only within its designated scope as defined in constitution
- **FR-004**: Sub-agents MUST NOT communicate directly; all coordination MUST occur via vault file movements
- **FR-005**: Main Orchestrator MUST scan Needs_Action/ every cycle for new items and delegate to appropriate sub-agent

#### Accounting Operations

- **FR-006**: Accounting Sub-Agent MUST claim ACCOUNTING_* files from Needs_Action/Accounting/
- **FR-007**: Accounting Sub-Agent MUST invoke odoo-accounting skill to draft invoices, payments, and journal entries
- **FR-008**: Accounting Sub-Agent MUST use odoo-mcp to create draft records in Odoo (NEVER confirm/post without approval)
- **FR-009**: Accounting Sub-Agent MUST move all drafts to Pending_Approval/ with complete preview including partner, amount, currency (PKR default), description, due date
- **FR-010**: After approval, Approval Sub-Agent MUST execute odoo-mcp confirm/post from Approved/ files only
- **FR-011**: All Odoo operations MUST log to Logs/YYYY-MM-DD.jsonl including mcp, method, params, result

#### Social Media Operations

- **FR-012**: Social Media Sub-Agent MUST claim SOCIAL_* files from Needs_Action/Social/
- **FR-013**: Social Media Sub-Agent MUST invoke multi-social-poster skill for platform-specific content generation
- **FR-014**: Social Media Sub-Agent MUST tailor content per platform: LinkedIn/Facebook (professional), Instagram (visual story), Twitter/X (concise <280 chars)
- **FR-015**: Social Media Sub-Agent MUST include Karachi/Sindh local hashtags when relevant
- **FR-016**: Social Media Sub-Agent MUST move all draft posts to Pending_Approval/SOCIAL_[platform]_[id].md
- **FR-017**: After approval, Approval Sub-Agent MUST execute browser-mcp posting from Approved/ files only
- **FR-018**: Social Media Sub-Agent MUST generate engagement summaries in Social/Summary_[date].md after posting
- **FR-019**: System MUST enforce maximum 3 posts per day across all platforms

#### Weekly Audit Cycle

- **FR-020**: Main Orchestrator MUST create WEEKLY_AUDIT_TRIGGER.md in Needs_Action/ every Sunday at 23:00 PKT
- **FR-021**: Finance & Auditor Sub-Agent MUST claim trigger and invoke weekly-audit-engine skill
- **FR-022**: Weekly audit MUST collect: revenue & receivables (Odoo via odoo-mcp), expenses & subscriptions (bank transactions), task completion rate (Done/ folder), social reach/posts (Social/Summary_*)
- **FR-023**: Weekly audit MUST flag anomalies: subscriptions no usage >30 days, delayed tasks >expected duration, unusual transactions >threshold (defined in Company_Handbook.md)
- **FR-024**: Weekly audit MUST write findings to temporary Accounting/Audit_Data_[date].md
- **FR-025**: Finance & Auditor Sub-Agent MUST invoke ceo-briefing-generator skill Monday 07:00 PKT
- **FR-026**: CEO briefing MUST read: Business_Goals.md, Accounting/Audit_Data_[date].md, Dashboard.md
- **FR-027**: CEO briefing MUST include: revenue summary (Odoo + bank tx in PKR), completed tasks (Done/), bottlenecks (delayed plans/flagged items), proactive suggestions (unused subscriptions/cost leaks), social activity (posts made/potential leads)
- **FR-028**: CEO briefing MUST be written to Briefings/YYYY-MM-DD_Monday_Briefing.md in professional Karachi business tone
- **FR-029**: Audit completion MUST log to Logs/YYYY-MM-DD.jsonl with status: AUDIT_DATA_COLLECTED

#### Error Recovery

- **FR-030**: Approval & Recovery Sub-Agent MUST monitor Pending_Approval/ folder for items needing execution
- **FR-031**: Approval & Recovery Sub-Agent MUST execute MCP calls ONLY for files in Approved/
- **FR-032**: Approval & Recovery Sub-Agent MUST invoke error-recovery-handler skill when errors detected
- **FR-033**: System MUST retry transient errors (network timeouts, temporary service unavailability) with exponential backoff: 1min, 5min, 15min
- **FR-034**: System MUST pause persistent errors after 3 retry attempts and move file to Done/ERROR_* with error details
- **FR-035**: System MUST flag critical errors in Dashboard.md Error Log with error_type, error_message, status (recovering | escalated)
- **FR-036**: Approval & Recovery Sub-Agent MUST perform watchdog monitoring for system health: error rates, stuck files (In_Progress/ >30min)
- **FR-037**: System MUST log all errors with error_type, error_message, retry_attempt, recovery_action, recovery_status

#### Human-in-the-Loop Approval

- **FR-038**: System MUST require human approval before ALL Odoo confirm/post actions (no exceptions)
- **FR-039**: System MUST require human approval before ALL social media posts (no exceptions)
- **FR-040**: System MUST require human approval before ALL payments or new payee additions (no exceptions)
- **FR-041**: System MUST require human approval for ANY action >PKR 100,000 or irreversible operations
- **FR-042**: System MUST require human approval for first contact to new recipients (email/LinkedIn)
- **FR-043**: System MUST check Approved/ folder before executing any state-changing MCP call; if file not present, MUST halt and log error
- **FR-044**: System MUST assume rejection if file remains in Pending_Approval/ >24 hours without approval
- **FR-045**: System MUST log all approval decisions with approver, approval_time, file

#### Vault Coordination

- **FR-046**: System MUST implement claim-by-move: first sub-agent to move file from Needs_Action/ to In_Progress/[agent-name]/ becomes sole owner
- **FR-047**: Sub-agents MUST use atomic file move operations (not copy-then-delete)
- **FR-048**: If file move fails (already claimed), sub-agent MUST skip to next item without error
- **FR-049**: Sub-agent ownership MUST persist until file moves to Pending_Approval/, Approved/, or Done/
- **FR-050**: On error, sub-agent MUST move file to Done/ERROR_[filename] to release ownership
- **FR-051**: System MUST log all file claims to Logs/YYYY-MM-DD.jsonl with timestamp, agent, file, claimed_by

#### Audit Logging

- **FR-052**: System MUST log ALL actions to Logs/YYYY-MM-DD.jsonl in JSON Lines format (one JSON object per line)
- **FR-053**: Every log entry MUST include: timestamp (ISO 8601 with PKT timezone +05:00), agent, action, file (if applicable), status, metadata (context-specific as JSON object)
- **FR-054**: MCP call logs MUST include: mcp, method, params, result
- **FR-055**: Approval logs MUST include: approver, approval_time
- **FR-056**: Error logs MUST include: error_type, error_message, retry_attempt
- **FR-057**: Recovery logs MUST include: recovery_action, recovery_status
- **FR-058**: System MUST update Dashboard.md with: Last Active (PKT), Pending Approvals (count + details), Weekly Audit Status (last/next dates), Recent Activity (reverse chronological, max 20), Error Log (last 24h)
- **FR-059**: System MUST NEVER log passwords, API keys, credentials, tokens, or Odoo credentials

#### MCP Integration

- **FR-060**: System MUST integrate with email-mcp (Gmail) for email read/send operations
- **FR-061**: System MUST integrate with browser-mcp for LinkedIn, Facebook, Instagram, Twitter/X posting
- **FR-062**: System MUST integrate with odoo-mcp (custom) exposing: create_draft, confirm, post, search_records methods
- **FR-063**: System MUST allow read-only MCP queries without approval (monitoring, audit data collection)
- **FR-064**: System MUST require Approved/ file before ANY state-changing MCP call (post, confirm, send)
- **FR-065**: System MUST only invoke approved MCP tools (email-mcp, browser-mcp, odoo-mcp); NEVER invoke unknown MCPs

#### Currency and Location

- **FR-066**: System MUST use PKR (Pakistani Rupee) as default currency for all financial amounts
- **FR-067**: System MUST format currency as "PKR 50,000" with comma separators for amounts >999
- **FR-068**: System MUST use PKT (Pakistan Standard Time, UTC+5) for all timestamps
- **FR-069**: System MUST format timestamps as ISO 8601: "2026-02-15T14:30:00+05:00" in logs, "2026-02-15 14:30 PKT" for human-readable
- **FR-070**: System MUST apply Karachi business context: business hours 09:00-18:00 PKT Mon-Fri, 09:00-14:00 PKT Sat, awareness of Pakistani holidays
- **FR-071**: All communications MUST use professional Karachi business tone: respectful, formal, concise, culturally aware

### Key Entities

- **Sub-Agent**: Specialized autonomous agent with distinct responsibilities (Accounting, Social Media, Finance & Auditor, Approval & Recovery). Each operates independently, claims files from designated Needs_Action/ subdirectory, processes via approved skills, coordinates through vault file movements only.

- **Main Orchestrator**: Central coordinator that delegates work to sub-agents, triggers weekly audit cycle, monitors system health (stuck files, error rates), updates Dashboard.md, enforces constitutional compliance. Never performs sub-agent work directly.

- **Vault File**: Work item represented as Markdown file moving through states: Needs_Action/ → In_Progress/[agent]/ → Pending_Approval/ → Approved/ → Done/. Filename prefix indicates type (ACCOUNTING_*, SOCIAL_*, EMAIL_*, etc.). Content includes structured metadata and payload.

- **MCP Server**: External service integration via Model Context Protocol. Three servers: email-mcp (Gmail), browser-mcp (social platforms), odoo-mcp (Odoo ERP). Provides methods for read-only queries (allowed without approval) and state-changing operations (require Approved/ file).

- **Skill**: Approved intelligent behavior module invoked by sub-agents. Nine total: task-triage, file-handler, odoo-accounting, multi-social-poster, ceo-briefing-generator, weekly-audit-engine, error-recovery-handler. Defined in .claude/skills/[skill-name]/SKILL.md.

- **Audit Data**: Weekly business intelligence collected Sunday night: revenue (Odoo), expenses (bank tx), tasks (Done/), social (summaries), anomaly flags (unused subscriptions, delays, unusual tx). Written to Accounting/Audit_Data_[date].md, consumed by CEO briefing generator Monday morning.

- **CEO Briefing**: Weekly executive report generated Monday 07:00 PKT in Briefings/YYYY-MM-DD_Monday_Briefing.md. Contains: revenue summary (PKR), completed tasks, bottlenecks, proactive suggestions (cost leaks, subscription waste), social activity (posts, engagement, leads). Professional Karachi business tone.

- **Approval Workflow**: Human-in-the-loop gate for sensitive actions. Flow: Draft created → Pending_Approval/ → (human reviews) → Approved/ → (agent executes) → Done/*_COMPLETED_*. Timeout: 24 hours (assume rejection). Logged: approver, approval_time, file.

- **Error Record**: Logged error with retry/recovery tracking. Fields: timestamp (PKT), agent, error_type (mcp_timeout, odoo_connection_failure, etc.), error_message, retry_attempt (1-3), recovery_action (retry | pause | escalate), recovery_status (recovering | resolved | escalated). Transient errors retry with backoff; persistent errors pause and flag.

- **Dashboard**: Central status view (Dashboard.md) updated after significant transitions. Sections: Status (Last Active, Pending Approvals count, queue counts, processed count, error count), Pending Approvals (detailed list for human), Weekly Audit Status (last/next dates, briefing status), Recent Activity (20 recent actions, reverse chronological), Error Log (last 24h errors with status).

- **Log Entry**: JSON Lines record in Logs/YYYY-MM-DD.jsonl. Required fields: timestamp (ISO 8601 PKT), agent, action (claim | draft | send | post | mcp_call | approval_granted | error | recovery_attempt), file (if applicable), status (in_progress | pending_approval | approved | completed | error | recovering), metadata (nested JSON with context-specific details).

## Success Criteria *(mandatory)*

### Measurable Outcomes

#### Automation and Efficiency

- **SC-001**: Business owner saves minimum 40 hours per week on manual tasks (invoice creation, social media posting, data aggregation, report generation)
- **SC-002**: Odoo invoice drafts are created within 5 minutes of file appearing in Needs_Action/Accounting/
- **SC-003**: Social media posts are drafted within 10 minutes of request appearing in Needs_Action/Social/
- **SC-004**: Weekly CEO briefing is generated and available in Briefings/ by Monday 07:15 PKT (15 min after trigger)
- **SC-005**: 95% of workflows complete without human intervention beyond required approvals

#### Reliability and Error Handling

- **SC-006**: System automatically recovers from 90% of transient errors (network timeouts, temporary service unavailability) within 15 minutes
- **SC-007**: No action executes without approval when HITL gate is constitutionally mandated
- **SC-008**: Zero duplicate processing of files due to claim-by-move coordination
- **SC-009**: All errors are logged with complete context (error_type, error_message, retry_attempt) for debugging
- **SC-010**: System uptime >99% (excluding planned Odoo/MCP server maintenance)

#### Audit and Compliance

- **SC-011**: 100% of actions, MCP calls, approvals, errors, and recoveries are logged to Logs/YYYY-MM-DD.jsonl
- **SC-012**: All log entries include required fields (timestamp PKT, agent, action, status, metadata) with no missing data
- **SC-013**: All financial amounts are logged in PKR currency with proper formatting
- **SC-014**: All timestamps are in PKT timezone (UTC+5) with ISO 8601 format
- **SC-015**: Audit trail enables complete reconstruction of any workflow from Needs_Action/ to Done/

#### Business Intelligence

- **SC-016**: Weekly audit successfully identifies 100% of subscriptions with no usage >30 days
- **SC-017**: Weekly audit flags 90% of unusual transactions based on Company_Handbook.md thresholds
- **SC-018**: CEO briefing provides actionable insights (bottlenecks, cost leaks, suggestions) in 100% of weeks
- **SC-019**: Social media engagement summaries accurately track posts, reach, and potential leads

#### User Experience

- **SC-020**: Business owner can review and approve pending items from Dashboard.md in under 10 minutes per day
- **SC-021**: Error notifications in Dashboard.md provide clear, actionable information (what failed, why, next steps)
- **SC-022**: CEO briefing uses professional Karachi business tone with culturally appropriate language
- **SC-023**: 100% of approvals are granted or rejected within 24 hours (manual human action)

## Assumptions

1. **Odoo ERP Setup**: Assumes Odoo Community 19+ is installed and accessible via local network or VM. Odoo database credentials are available in environment configuration. Company is already set up in Odoo with chart of accounts, partners, and products configured.

2. **MCP Server Availability**: Assumes odoo-mcp custom MCP server is developed and exposes required methods (create_draft, confirm, post, search_records). Assumes browser-mcp supports LinkedIn, Facebook, Instagram, Twitter/X navigation and posting. Assumes email-mcp (Gmail) is configured with appropriate OAuth2 credentials.

3. **Vault Folder Structure**: Assumes vault folders exist at project root: Needs_Action/[Accounting|Social|Finance|Email|Comms]/, In_Progress/[accounting-sub-agent|social-sub-agent|finance-auditor-sub-agent|approval-sub-agent]/, Pending_Approval/, Approved/, Rejected/, Done/[Accounting|Social|*]/, Briefings/, Accounting/, Logs/, Plans/. Assumes Dashboard.md, Business_Goals.md, Company_Handbook.md files exist or can be created.

4. **Bank Transaction Access**: Assumes bank transaction data (CSV or similar) is manually downloaded and placed in designated location for Finance & Auditor Sub-Agent to parse. Automated banking API integration is out of scope for Gold-tier.

5. **Social Media Credentials**: Assumes business owner has active accounts on LinkedIn, Facebook, Instagram, Twitter/X with credentials configured in browser-mcp for automated posting after approval.

6. **Company_Handbook.md Thresholds**: Assumes Company_Handbook.md exists and defines: approval thresholds (e.g., payments >PKR 50,000 require dual approval), unusual transaction thresholds for audit flags (e.g., >PKR 25,000 single transaction), subscription usage monitoring period (default 30 days).

7. **Weekly Audit Timing**: Assumes business operates on standard Monday-Sunday week. Audit triggers Sunday 23:00 PKT, briefing generates Monday 07:00 PKT. Timing is configurable but defaults to these values.

8. **Karachi Business Context**: Assumes business operates in Karachi, Pakistan with awareness of local business hours (09:00-18:00 PKT Mon-Fri, 09:00-14:00 PKT Sat), Pakistani national holidays, Islamic calendar events (Eid, Ramadan), and local business customs.

9. **Human Availability**: Assumes business owner reviews Pending_Approval/ folder at least once per day (typically morning and afternoon). 24-hour approval timeout assumes human checks within this window.

10. **Error Recovery Scope**: Assumes transient errors (network timeouts, temporary service unavailability) resolve within 15 minutes (covered by 3 retries with backoff). Persistent errors (authentication failures, Odoo configuration errors) require human intervention.

11. **Data Retention**: Assumes Done/ folder is immutable archive (never deleted). Logs/ folder retains daily YYYY-MM-DD.jsonl files indefinitely for compliance. Briefings/ folder retains all weekly briefings for historical analysis.

12. **Skill Definitions**: Assumes all approved skills have corresponding .claude/skills/[skill-name]/SKILL.md files defining their behavior, inputs, outputs, and workflows. Skills are invoked via Claude Code skill system.

## Dependencies

### External Systems

- **Odoo ERP Community 19+**: Required for accounting operations (invoices, payments, journal entries, financial data). Must be accessible via network (local or VM).
- **Gmail Account**: Required for email-mcp integration. Must have OAuth2 configured.
- **LinkedIn Business Account**: Required for professional social media posting.
- **Facebook Business Account**: Required for social media posting (optional if not using Facebook).
- **Instagram Business Account**: Required for visual social media posting (optional if not using Instagram).
- **Twitter/X Account**: Required for microblogging social media posting (optional if not using Twitter/X).

### MCP Servers

- **email-mcp**: Existing MCP server for Gmail integration (read inbox, send email).
- **browser-mcp**: Existing or extended MCP server for browser automation (navigate, fill forms, click buttons) on social media platforms.
- **odoo-mcp**: Custom MCP server (must be developed) exposing Odoo JSON-RPC methods: create_draft (create draft invoice/payment), confirm (confirm draft), post (post to ledger), search_records (read financial data for audit).

### Constitution and Skills

- **Gold-Tier Constitution v3.0.0**: System behavior is governed by constitution at .specify/memory/constitution.md. All sub-agent responsibilities, HITL gates, MCP execution rules, logging requirements, and vault workflow defined constitutionally.
- **Approved Skills**: odoo-accounting, multi-social-poster, ceo-briefing-generator, weekly-audit-engine, error-recovery-handler (must exist in .claude/skills/).

### Data Sources

- **Business_Goals.md**: Defines business objectives and KPIs for CEO briefing context.
- **Company_Handbook.md**: Defines approval thresholds, unusual transaction limits, subscription monitoring rules.
- **Bank Transaction Files**: Manually downloaded CSV/Excel files placed in designated folder for expense parsing.

## Out of Scope

The following are explicitly **not** included in Gold-Tier:

1. **Cloud/Local Hybrid Architecture**: Gold-tier operates entirely on local system with local Odoo instance. Cloud deployment, hybrid vault sync, or remote agent coordination is Platinum-tier.

2. **Direct Agent-to-Agent Communication**: Sub-agents coordinate exclusively via vault file hand-offs. No direct messaging, shared state, or protocol-based communication between agents.

3. **Automated Banking API Payments**: Bank transaction data must be manually downloaded. Automated payment execution via banking APIs is out of scope.

4. **Advanced Inter-Agent Protocol**: No sophisticated multi-agent protocols (negotiation, consensus, distributed coordination). Simple claim-by-move file ownership is the coordination mechanism.

5. **Production-Grade Odoo Infrastructure**: Local or VM Odoo deployment is sufficient. Production HTTPS, load balancing, database clustering, automated backups are not required for Gold-tier.

6. **Real-Time Collaboration Features**: No real-time multi-user features, simultaneous editing, or collaborative approval workflows. Single business owner human-in-the-loop model.

7. **Mobile Application**: No mobile app for approvals or monitoring. Dashboard.md and Pending_Approval/ folder accessed via desktop file browser or editor.

8. **Advanced Analytics Dashboard**: CEO briefing provides weekly summary. No interactive charts, trend analysis, or business intelligence dashboard UI.

9. **Multi-Currency Support**: PKR is the only supported currency. Foreign currency conversion or multi-currency accounting is out of scope.

10. **Automated Social Media Engagement**: System posts content after approval but does not auto-reply to comments, auto-like, auto-follow, or engage with other users' content.

11. **Email Auto-Response**: System can draft email replies but requires approval before sending. No auto-responders, vacation messages, or automated email workflows without HITL.

12. **Custom Reporting Beyond Weekly Briefing**: Weekly CEO briefing is the only automated report. Ad-hoc reports, monthly/quarterly summaries, or custom report generation requires manual data extraction from logs.
