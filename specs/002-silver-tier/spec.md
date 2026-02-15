# Feature Specification: Silver-Tier Multi-Agent AI Employee

**Feature Branch**: `002-silver-tier`
**Created**: 2026-02-15
**Status**: Draft
**Input**: User description: "Silver tier scope — 20–30 hour deliverable with multi-agent coordination, email automation, LinkedIn posting, and multi-step planning capabilities"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Email Processing & Response (Priority: P1) 🎯 MVP

Aliyan receives business emails throughout the day and needs professional responses drafted automatically, with human approval before sending to maintain quality and professionalism.

**Why this priority**: Email is the primary business communication channel. Automating triage and drafting saves 2-3 hours daily while maintaining professional standards through HITL approval.

**Independent Test**: Can be fully tested by dropping an EMAIL_*.md file into Needs_Action/Email/, verifying it gets triaged, drafted, moved to Pending_Approval/, and sent via email-mcp after approval. Delivers immediate value even without other features.

**Acceptance Scenarios**:

1. **Given** a new email file in Needs_Action/Email/, **When** the Email Sub-Agent processes it, **Then** it claims the file (moves to In_Progress/email-sub-agent/), classifies sensitivity (low/medium/high), drafts a professional response, and moves draft to Pending_Approval/
2. **Given** an email draft in Pending_Approval/, **When** Aliyan reviews and moves it to Approved/, **Then** email-mcp sends the email and archives to Done/Email/SENT_*.md with complete audit log
3. **Given** a high-sensitivity email (new contact, money, attachment >1MB), **When** Email Sub-Agent processes it, **Then** it MUST flag for HITL review and MUST NOT auto-approve regardless of content

---

### User Story 2 - LinkedIn Sales Post Generation (Priority: P2)

Aliyan wants to maintain consistent LinkedIn presence for lead generation without spending 30+ minutes daily crafting posts, while ensuring all posts align with professional brand and require approval before publishing.

**Why this priority**: LinkedIn is the primary sales channel for reaching Karachi-based businesses. Automated post generation with HITL approval enables consistent visibility without time investment.

**Independent Test**: Can be tested by triggering daily post generation (or manually dropping a SOCIAL_linkedin_*.md file), verifying professional Karachi-focused content is drafted, moved to Pending_Approval/, and posted via browser-mcp after approval.

**Acceptance Scenarios**:

1. **Given** the system runs daily at scheduled time, **When** Comms Sub-Agent generates LinkedIn post, **Then** it creates 1-2 sales-focused posts with Karachi context (#KarachiBusiness, #AIEmployee), 100-250 words, value-first hooks, and CTA, moves to Pending_Approval/
2. **Given** a LinkedIn post draft in Pending_Approval/, **When** Aliyan reviews and moves to Approved/, **Then** browser-mcp posts to LinkedIn profile and archives to Done/Social/POSTED_*.md
3. **Given** a sales opportunity detected in WhatsApp/Email, **When** Comms Sub-Agent identifies pricing/demo keywords, **Then** it generates relevant LinkedIn post promoting the service

---

### User Story 3 - Multi-Step Plan Creation & Tracking (Priority: P3)

Aliyan needs complex tasks broken into trackable steps with progress monitoring, enabling structured execution of multi-day projects without losing context or missing steps.

**Why this priority**: Complex client projects (onboarding, vendor research, service delivery) require structured planning. Automated plan tracking prevents dropped tasks and provides progress visibility.

**Independent Test**: Can be tested by dropping a complex task file, verifying Planner Sub-Agent creates Plan_*.md with 3-8 checkboxes, tracks progress on each cycle, updates Dashboard.md, and archives to Done/Plans/ when complete.

**Acceptance Scenarios**:

1. **Given** a task requiring >2 steps, **When** Planner Sub-Agent processes it, **Then** it creates Plans/PLAN_[task-id].md with 3-8 actionable checkboxes, clear ownership, and dependencies
2. **Given** an active plan in Plans/, **When** orchestrator runs cycle, **Then** Planner Sub-Agent updates progress (checks off completed steps), logs updates, and updates Dashboard.md with current status
3. **Given** a plan with all checkboxes completed, **When** Planner Sub-Agent detects completion, **Then** it moves plan to Done/Plans/, logs completion, and removes from Dashboard.md active plans section

---

### User Story 4 - Main Orchestrator Coordination (Priority: P0 - Foundation)

The system needs central coordination to delegate work to specialized sub-agents, prevent conflicts, and maintain system-wide visibility and control.

**Why this priority**: FOUNDATIONAL - all other user stories depend on orchestrator delegating work correctly. Must be implemented first.

**Independent Test**: Can be tested by dropping files into Needs_Action/, verifying correct sub-agent claims the file (EMAIL_* → email-sub-agent, SOCIAL_* → comms-sub-agent), Dashboard.md updates with system status, and no duplicate processing occurs.

**Acceptance Scenarios**:

1. **Given** new files in Needs_Action/, **When** Main Orchestrator scans, **Then** it correctly routes EMAIL_* to email-sub-agent, SOCIAL_*/WHATSAPP_* to comms-sub-agent, complex tasks to planner-sub-agent based on content analysis
2. **Given** multiple files arriving simultaneously, **When** sub-agents claim files, **Then** claim-by-move rule ensures exclusive ownership (atomic move to In_Progress/[agent]/), no duplicate processing, all claims logged to Logs/YYYY-MM-DD.md
3. **Given** system is running, **When** orchestrator updates Dashboard.md, **Then** it shows accurate counts (pending approvals, active plans, items in queues), recent activity (reverse chronological), and system status (last active timestamp)

---

### Edge Cases

- **Concurrent file claims**: If two sub-agents attempt to claim the same file simultaneously, atomic file move operations ensure only one succeeds; the other skips and moves to next item
- **MCP service unavailable**: If email-mcp or browser-mcp fails, system logs error, moves file back to Pending_Approval/ with error note, and flags for human review
- **Stale approvals**: If draft sits in Pending_Approval/ for >24 hours without human action, system assumes rejection and archives to Done/REJECTED_*
- **Malformed email/social content**: If draft generation produces invalid format (missing required fields), system flags error, moves to Done/ERROR_*, and logs details for debugging
- **Sub-agent timeout**: If file sits in In_Progress/[agent]/ for >30 minutes without progress, orchestrator logs warning and flags for human investigation (but does NOT override ownership per constitution)
- **Empty Needs_Action/**: System idles gracefully, logs inactivity, maintains Dashboard.md timestamp
- **Large attachment handling**: Emails with attachments >1MB MUST be flagged HITL even if content is low-sensitivity
- **Weekend/holiday posting**: LinkedIn post generation respects cultural calendar (no posts during Eid, Ramadan evening hours)

## Requirements *(mandatory)*

### Functional Requirements

**Multi-Agent Coordination:**

- **FR-001**: System MUST implement claim-by-move coordination where first sub-agent to atomically move file from Needs_Action/ to In_Progress/[agent-name]/ gains exclusive ownership
- **FR-002**: Main Orchestrator MUST scan Needs_Action/ folder at regular intervals (configurable, default every 5 minutes) and delegate work to appropriate sub-agents
- **FR-003**: System MUST prevent duplicate processing via atomic file operations (move, not copy-then-delete)
- **FR-004**: System MUST maintain separation of concerns (Email Sub-Agent MUST NOT process social posts, Comms Sub-Agent MUST NOT process emails, etc.)

**Email Automation:**

- **FR-005**: Email Sub-Agent MUST claim EMAIL_* files from Needs_Action/Email/ and move to In_Progress/email-sub-agent/
- **FR-006**: Email Sub-Agent MUST invoke email-drafter skill to generate professional responses with appropriate Karachi business tone
- **FR-007**: Email Sub-Agent MUST classify email sensitivity (low/medium/high) based on content (keywords: payment, invoice, new contact, attachment size)
- **FR-008**: Email Sub-Agent MUST move all drafts to Pending_Approval/ regardless of sensitivity (no auto-send)
- **FR-009**: System MUST send email via email-mcp ONLY when draft file exists in Approved/ folder
- **FR-010**: System MUST archive sent emails to Done/Email/SENT_[id].md with timestamp and complete audit trail

**LinkedIn Sales Posting:**

- **FR-011**: Comms Sub-Agent MUST claim SOCIAL_linkedin_* files from Needs_Action/Comms/
- **FR-012**: Comms Sub-Agent MUST invoke social-linkedin-poster skill to generate engaging posts (100-250 words, Karachi context, hashtags #AIEmployee #KarachiBusiness #FreelanceAI)
- **FR-013**: Comms Sub-Agent MUST generate 1-2 LinkedIn posts per day at scheduled times (configurable, default: 10 AM and 3 PM PKT)
- **FR-014**: System MUST move all LinkedIn post drafts to Pending_Approval/ (no auto-post)
- **FR-015**: System MUST post to LinkedIn via browser-mcp ONLY when draft file exists in Approved/ folder
- **FR-016**: System MUST archive posted content to Done/Social/POSTED_[id].md with engagement tracking placeholder

**Multi-Step Planning:**

- **FR-017**: Planner Sub-Agent MUST claim complex tasks (requiring >2 steps) from Needs_Action/
- **FR-018**: Planner Sub-Agent MUST invoke plan-creator skill to generate Plans/PLAN_[task-id].md with 3-8 actionable checkboxes
- **FR-019**: Planner Sub-Agent MUST update plan progress on each orchestrator cycle (check off completed steps, update timestamps)
- **FR-020**: Planner Sub-Agent MUST move completed plans (all checkboxes checked) to Done/Plans/
- **FR-021**: Plans MUST include clear ownership assignment (which sub-agent executes each step), dependencies, and approval gates for sensitive actions

**Human-in-the-Loop (HITL):**

- **FR-022**: System MUST require human approval for: any email send, any LinkedIn post, any action involving money, new contacts, attachments >1MB
- **FR-023**: System MUST implement approval workflow: Draft → Pending_Approval/ → (human review) → Approved/ → MCP execute → Done/
- **FR-024**: System MUST NOT execute MCP calls (email-mcp, browser-mcp) without corresponding file in Approved/ folder
- **FR-025**: System MUST timeout approvals after 24 hours (assume rejection, archive to Done/REJECTED_*)

**Logging & Audit:**

- **FR-026**: System MUST log all actions to Logs/YYYY-MM-DD.md in JSON format with fields: timestamp (ISO 8601 + PKT timezone), agent, action, file, status, metadata
- **FR-027**: System MUST update Dashboard.md with human-readable recent activity (reverse chronological, max 20 entries)
- **FR-028**: Dashboard.md MUST display: last active timestamp, pending approvals count, active plans count, items in queues, recent activity log
- **FR-029**: System MUST create Done/ archive entries for all processed items (immutable, no deletion)

**Skills Integration:**

- **FR-030**: System MUST invoke skills via .claude/skills/[skill-name]/SKILL.md definitions (no direct code logic)
- **FR-031**: Email Sub-Agent MUST use email-drafter skill exclusively for email generation
- **FR-032**: Comms Sub-Agent MUST use social-linkedin-poster skill exclusively for LinkedIn content
- **FR-033**: Planner Sub-Agent MUST use plan-creator skill exclusively for plan generation

**MCP Integration:**

- **FR-034**: System MUST integrate with email-mcp for Gmail send/receive operations
- **FR-035**: System MUST integrate with browser-mcp for LinkedIn posting and WhatsApp message reading
- **FR-036**: System MUST validate MCP pre-execution checklist before each call: file in Approved/, complete payload, acceptable sensitivity, recent approval (<24h), no errors
- **FR-037**: System MUST handle MCP failures gracefully (log error, move file back to Pending_Approval/ with error note, flag for human review)

### Key Entities *(include if feature involves data)*

- **Email Draft**: Represents a drafted email response awaiting approval. Attributes: from, to, subject, body, sensitivity (low/medium/high), requires_hitl (always true), reason (why approval needed), timestamp, original_email_reference
- **LinkedIn Post**: Represents a drafted LinkedIn post awaiting approval. Attributes: platform (linkedin), post_type (sales_promotion, thought_leadership, case_study, engagement), content (100-250 words), hashtags, scheduled_for (timestamp or null), sensitivity (medium), requires_hitl (true)
- **Plan**: Represents a multi-step plan for complex task execution. Attributes: plan_id, title, context, steps (array of checkboxes with owner/dependencies/approval_needed), created, updated, status (in_progress/completed/blocked), priority, owner, estimated_steps, completed_steps
- **Log Entry**: Represents a single action in the audit trail. Attributes: timestamp (ISO 8601 + PKT), agent (orchestrator/email-sub-agent/comms-sub-agent/planner-sub-agent), action (claim/draft/send/post/plan/update), file (filename), status (in_progress/pending_approval/approved/completed/error), metadata (JSON)
- **Dashboard**: Represents real-time system status. Attributes: last_active (timestamp), active_plans (count), pending_approvals (count), items_in_email_queue, items_in_comms_queue, items_processed_today, recent_activity (array of log entries)

### Assumptions

- **Scheduling**: Daily LinkedIn post generation occurs at 10 AM and 3 PM PKT (configurable)
- **Orchestrator cycle frequency**: Every 5 minutes (configurable)
- **Approval timeout**: 24 hours (configurable)
- **Stalled work detection**: Files in In_Progress/ for >30 minutes trigger warning (but no automatic override)
- **Attachment size threshold**: 1 MB (configurable)
- **Maximum plan steps**: 8 checkboxes (larger plans broken into multiple)
- **Dashboard activity log limit**: 20 most recent entries
- **Timezone**: All timestamps use PKT (Pakistan Standard Time, UTC+5)
- **Cultural calendar**: System respects Eid, Ramadan holidays for LinkedIn posting (requires Company_Handbook.md configuration)
- **Email tone**: Professional Karachi business English per constitution Principle VII
- **File naming**: EMAIL_[id].md, SOCIAL_linkedin_[id].md, PLAN_[task-name].md, SENT_*, POSTED_*, ERROR_*, REJECTED_*
- **MCP authentication**: Assumes email-mcp and browser-mcp are pre-configured with valid credentials

### Out of Scope (Explicitly Excluded)

- Odoo / accounting integration
- Banking / direct payment processing
- Full weekly CEO briefing generation (only simple plan status updates)
- Cloud hybrid deployment (local-only in Silver)
- Direct agent-to-agent messaging (coordination via files only)
- WhatsApp message sending (read-only monitoring in Silver, sending requires human approval)
- Email auto-reply without approval (all emails require HITL)
- Multi-user / team collaboration features
- Advanced analytics / reporting beyond Dashboard.md
- Mobile app or web UI (vault-only interface)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Email drafts are generated within 2 minutes of file appearing in Needs_Action/Email/
- **SC-002**: 100% of emails and LinkedIn posts require explicit human approval before execution (zero auto-sends or auto-posts)
- **SC-003**: LinkedIn posts are generated consistently 1-2 times per day on weekdays with >90% approval rate (indicating quality drafts)
- **SC-004**: Multi-step plans are updated within 5 minutes of any step completion, maintaining accurate progress tracking
- **SC-005**: Dashboard.md reflects system status in real-time (last active timestamp within 5 minutes of current time during operation)
- **SC-006**: Complete audit trail exists for 100% of actions (every claim, draft, approval, execution logged to Logs/)
- **SC-007**: Zero file ownership conflicts occur (claim-by-move prevents duplicate processing)
- **SC-008**: System saves Aliyan 10-15 hours per week on email triage, drafting, and LinkedIn content creation
- **SC-009**: Aliyan can complete 20-30 hour Silver-tier implementation within estimated timeframe
- **SC-010**: All external actions (email sends, LinkedIn posts) are traceable from Needs_Action → In_Progress → Pending_Approval → Approved → Done with timestamps

### Business Impact

- **BI-001**: Reduces email response time from hours/days to minutes (draft ready for review)
- **BI-002**: Maintains consistent LinkedIn presence without daily 30+ minute time investment
- **BI-003**: Prevents missed client communications through structured planning and tracking
- **BI-004**: Provides complete business communication audit trail for compliance and review
- **BI-005**: Enables scaling of business communication without hiring additional staff
