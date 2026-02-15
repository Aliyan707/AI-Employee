# Feature Specification: Bronze-Tier Inbox Automation

**Feature Branch**: `001-bronze-inbox-automation`
**Created**: 2026-02-15
**Status**: Draft
**Input**: User description: "Bronze tier inbox automation system - filesystem-only, 8-12 hour deliverable"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Process Incoming Email Tasks (Priority: P1)

As a user, I need incoming email items automatically triaged so I can quickly understand what requires my attention without manually reviewing every item.

**Why this priority**: This is the core MVP functionality. Email processing is the primary use case for inbox automation and delivers immediate value by reducing manual triage time.

**Independent Test**: Can be fully tested by dropping an EMAIL_*.md file into Needs_Action/, running the automation, and verifying the file is classified, summarized, logged to Dashboard, and moved to Done/.

**Acceptance Scenarios**:

1. **Given** an EMAIL_vendor-inquiry.md file in Needs_Action/ with content asking for product information, **When** the automation runs, **Then** the file is classified as "medium" priority, a summary is added to the file, a log entry is created in Dashboard.md, and the file is moved to Done/
2. **Given** an EMAIL_urgent-payment.md file containing the word "urgent" and "payment", **When** the automation runs, **Then** the file is classified as "high" priority, flagged with NEEDS_HUMAN_REVIEW status, logged to Dashboard with [HUMAN REVIEW REQUIRED] flag, and moved to Done/ with REVIEW_ prefix
3. **Given** an EMAIL_newsletter.md file with marketing content, **When** the automation runs, **Then** the file is classified as "low" priority, summarized, logged to Dashboard, and moved to Done/

---

### User Story 2 - Process Dropped Files (Priority: P2)

As a user, I need files I drop into the system automatically analyzed and categorized so I can maintain an organized archive without manual filing.

**Why this priority**: Complements email processing by handling generic file drops (documents, notes, research). Extends the system's utility beyond emails.

**Independent Test**: Can be fully tested by dropping a FILE_meeting-notes.md into Needs_Action/, running the automation, and verifying it's summarized, categorized, logged, and archived.

**Acceptance Scenarios**:

1. **Given** a FILE_receipt-jan.pdf in Needs_Action/, **When** the automation runs, **Then** the file is identified as non-text, marked for manual review, categorized as "receipt", logged to Dashboard, and moved to Done/
2. **Given** a FILE_project-notes.md with text content about a project, **When** the automation runs, **Then** the file is read, summarized in 3-5 sentences, categorized as "project-note", logged to Dashboard, and moved to Done/
3. **Given** a large FILE_research-paper.md (>500 lines), **When** the automation runs, **Then** a separate summary_research-paper.md file is created in Needs_Action/, the original is moved to Done/, and both are logged to Dashboard

---

### User Story 3 - Create Action Plans for Complex Items (Priority: P3)

As a user, I need complex high-priority items automatically converted into actionable plans so I can efficiently tackle multi-step tasks without additional planning overhead.

**Why this priority**: Adds value on top of basic classification by creating structured next steps for complex items. Lower priority because simple classification is often sufficient.

**Independent Test**: Can be fully tested by creating a high-priority EMAIL with multiple action items, running the automation, and verifying a PLAN_*.md file is created in Plans/ with checkboxes.

**Acceptance Scenarios**:

1. **Given** an EMAIL_vendor-rfp.md classified as "high" with 3+ distinct action items, **When** the automation runs, **Then** a PLAN_vendor-rfp.md file is created in Plans/ with checkboxes for each action, the original email is moved to Done/, and both are logged to Dashboard
2. **Given** an EMAIL_simple-question.md classified as "high" but containing only a single question, **When** the automation runs, **Then** no plan is created (not complex enough), the email is processed normally and moved to Done/
3. **Given** an EMAIL_meeting-request.md classified as "medium" (not high priority), **When** the automation runs, **Then** no plan is created regardless of complexity, item is processed normally

---

### User Story 4 - Activity Logging and Status Tracking (Priority: P1)

As a user, I need all automation activities logged to a Dashboard so I can review what was processed and track system activity over time.

**Why this priority**: Essential for transparency, debugging, and building trust in the automation. Without logging, users cannot verify correct operation.

**Independent Test**: Can be fully tested by processing any item and verifying Dashboard.md is updated with a one-line log entry in the correct format with timestamp.

**Acceptance Scenarios**:

1. **Given** Dashboard.md exists with a ## Recent Activity section, **When** an EMAIL_test.md is processed, **Then** a new line is appended: "- YYYY-MM-DD HH:MM Triaged EMAIL_test.md: [priority] – [summary]"
2. **Given** multiple items are processed in sequence, **When** all processing completes, **Then** Dashboard.md contains one log entry per item in reverse chronological order (newest first)
3. **Given** an item processing fails with an error, **When** the automation handles the error, **Then** Dashboard.md is updated with "[ERROR]" prefix and the file is moved to Done/ with ERROR_ prefix

---

### Edge Cases

- **Empty or corrupted file**: What happens when a file in Needs_Action/ is empty, corrupted, or unreadable?
  - System should log error to Dashboard, move file to Done/ with ERROR_ prefix, and continue processing other items

- **Filename collision in Done/**: What happens when moving a file to Done/ but a file with that name already exists?
  - System should append timestamp to filename: original-name_YYYY-MM-DD-HHMM.ext before moving

- **Missing Dashboard.md**: What happens if Dashboard.md doesn't exist when trying to log an activity?
  - System should create Dashboard.md with proper structure before appending log entry

- **Keyword false positives**: What happens when a file contains "urgent" but isn't actually urgent (e.g., "not urgent")?
  - System should still flag for human review (conservative approach - better safe than sorry)

- **Mixed file types**: What happens when a FILE_*.md has both FILE_ prefix and email-like content?
  - file-handler skill takes precedence (prefix-based routing is primary)

- **No items in Needs_Action/**: What happens when the automation runs but Needs_Action/ is empty?
  - System should complete silently without errors, optionally log "No items to process"

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST scan Needs_Action/ folder and identify all .md files for processing
- **FR-002**: System MUST route files starting with EMAIL_ prefix to task-triage skill
- **FR-003**: System MUST route files starting with FILE_ prefix to file-handler skill
- **FR-004**: System MUST classify every processed item as high, medium, or low urgency based on keyword analysis
- **FR-005**: System MUST detect sensitive keywords (payment, invoice, urgent, deadline, password, credential, bank, etc.) and flag items with NEEDS_HUMAN_REVIEW
- **FR-006**: System MUST write a summary (3-5 sentences for text files) and classification at the bottom of each processed file
- **FR-007**: System MUST create Plans/PLAN_*.md files for high-priority items that require multiple steps
- **FR-008**: System MUST append a one-line log entry to Dashboard.md under ## Recent Activity for every processed item
- **FR-009**: System MUST move every processed file from Needs_Action/ to Done/ after processing
- **FR-010**: System MUST output <status>DONE</status> or <status>NEEDS_HUMAN_REVIEW</status> at the end of processing each item
- **FR-011**: System MUST handle filename collisions in Done/ by appending timestamp
- **FR-012**: System MUST handle errors gracefully by logging to Dashboard with [ERROR] prefix and moving problematic files to Done/ with ERROR_ prefix
- **FR-013**: System MUST process items sequentially (FIFO order) not in parallel
- **FR-014**: System MUST never send emails, make API calls, process payments, or perform any external actions beyond filesystem operations
- **FR-015**: System MUST read Company_Handbook.md (if exists) before processing any items to load custom rules

### Key Entities

- **Inbox Item**: Any .md file in Needs_Action/ folder; has properties: filename, content, classification (high/medium/low), category (for files), status (DONE/NEEDS_HUMAN_REVIEW)

- **Task Item**: Inbox item with EMAIL_ prefix or email-like content; processed by task-triage skill; may generate a Plan

- **File Item**: Inbox item with FILE_ prefix; processed by file-handler skill; has category (invoice, receipt, project-note, research, junk, other)

- **Plan**: Markdown file in Plans/ folder created for complex high-priority items; contains checkboxes for action items, source reference, classification, creation date

- **Activity Log**: One-line entry in Dashboard.md documenting processing of an item; format: "- YYYY-MM-DD HH:MM [Action] [filename]: [classification/category] – [summary]"

- **Dashboard**: Central Dashboard.md file containing Status section, Recent Activity log, and Statistics; updated after every processing operation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can drop items into Needs_Action/ and have them fully processed (classified, summarized, logged, archived) in under 30 seconds per item
- **SC-002**: System correctly classifies 90%+ of items as high/medium/low priority based on content and keywords
- **SC-003**: System achieves 100% sensitive item detection (zero false negatives for payment/invoice/credential keywords)
- **SC-004**: Dashboard.md maintains complete audit trail with one log entry per processed item, viewable in chronological order
- **SC-005**: Done/ folder serves as searchable archive with 100% of processed items preserved
- **SC-006**: System operates for 8-12 hours of development time to reach production readiness
- **SC-007**: Users can verify automation correctness by reviewing Dashboard logs without needing to check individual files
- **SC-008**: System handles edge cases (empty files, collisions, errors) without crashing or losing data

## Scope

### In Scope

- Processing .md files in Needs_Action/ folder
- Classification of items into high/medium/low urgency
- Summarization of text content (3-5 sentences)
- Categorization of files (invoice, receipt, project-note, research, junk, other)
- Detection of sensitive keywords with human review flagging
- Creation of simple Plans/ for complex high-priority items
- Logging all activities to Dashboard.md
- Archiving processed items to Done/ folder
- Error handling with ERROR_ prefix
- Filename collision handling with timestamps
- Reading Company_Handbook.md for custom rules
- Sequential processing (FIFO)
- Status output (<status>DONE</status> or <status>NEEDS_HUMAN_REVIEW</status>)

### Out of Scope (Bronze Tier Limitations)

- Sending emails or WhatsApp messages
- MCP servers or external integrations
- Payment processing or approval workflows
- Weekly briefing generation
- Multiple parallel agents (Ralph Wiggum loop architecture)
- Social media posting (Odoo or other platforms)
- Processing non-Markdown files (PDFs, images, etc.) beyond flagging for manual review
- Automated responses or communications
- Cloud sync or remote storage
- Advanced NLP or sentiment analysis
- Machine learning models
- User authentication or multi-user support

## Assumptions

- Needs_Action/, Done/, Plans/, and Dashboard.md folders/files exist (created during setup)
- Files in Needs_Action/ are placed manually by user (no automated intake)
- Obsidian vault is located on local machine in Karachi (timezone PKT, UTC+5)
- System runs in single-user mode (Aliyan 707)
- Company_Handbook.md is optional; system works without it
- Users prefer conservative flagging (false positives acceptable for NEEDS_HUMAN_REVIEW)
- FIFO processing order is acceptable (no priority queue needed for Bronze tier)
- Summary length of 3-5 sentences is sufficient for most items
- Text files are UTF-8 encoded Markdown
- System date/time is accurate for logging purposes

## Dependencies

- Obsidian vault with filesystem access
- Claude Code CLI with task-triage and file-handler skills installed
- .specify/memory/constitution.md (Bronze-tier constitution) defining operational rules
- Bash shell environment for file operations
- Git repository for version control (optional but recommended)

## Open Questions

None. All requirements are clearly defined within Bronze tier constraints.
