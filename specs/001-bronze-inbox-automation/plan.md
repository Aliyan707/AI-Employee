# Implementation Plan: Bronze-Tier Inbox Automation

**Branch**: `001-bronze-inbox-automation` | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bronze-inbox-automation/spec.md`

## Summary

Implement a filesystem-only inbox automation system that continuously monitors Needs_Action/, classifies items using two predefined skills (task-triage and file-handler), processes them according to skill workflows, logs all activity to Dashboard.md, and archives completed items to Done/. The system runs in a simple while loop executing a 5-phase cycle: Observe → Classify & Delegate → Execute → Clean up → Report. Target delivery: 8-12 hours of development time.

**Core Architecture**: Event-driven loop with skill delegation pattern. No external dependencies, APIs, or complex frameworks—pure filesystem operations using Claude Code CLI skills.

## Technical Context

**Language/Version**: Bash scripting + Claude Code CLI (claude-sonnet-4-5-20250929)
**Primary Dependencies**:
- Claude Code CLI with Skill tool
- task-triage skill (.claude/skills/task-triage/SKILL.md)
- file-handler skill (.claude/skills/file-handler/SKILL.md)
- Bash 5.x (for file operations and while loop)

**Storage**: Local filesystem (Obsidian vault)
- Needs_Action/ - Incoming items
- Done/ - Processed archive
- Plans/ - Complex task plans
- Dashboard.md - Activity log

**Testing**: Manual validation via Dashboard.md logs and Done/ folder inspection
**Target Platform**: Windows 10/11 with Bash shell (Git Bash or WSL), Karachi timezone (PKT, UTC+5)
**Project Type**: Automation script (not traditional software - no src/ directory needed)
**Performance Goals**:
- Process each item in <30 seconds
- 90%+ classification accuracy
- 100% sensitive keyword detection

**Constraints**:
- Filesystem-only (no network, no external APIs)
- Two skills maximum (task-triage, file-handler)
- Sequential processing (no parallelism)
- Bronze tier: 8-12 hour development window

**Scale/Scope**: Single-user, ~10-50 items/day expected throughput

## Constitution Check

*GATE: Must pass before implementation. Re-check after Phase 1 design.*

✅ **Filesystem-Only Operations** - Implementation uses only local file I/O (read, write, move)
✅ **Inbox Processing Workflow** - 5-phase cycle implements Needs_Action → Done flow
✅ **Limited Skill Set** - Only task-triage and file-handler invoked via Skill tool
✅ **Restricted Write Access** - Writes only to Needs_Action/ (analysis), Plans/ (new plans), Done/ (moves), Dashboard.md (logs)
✅ **Mandatory File Archival** - Phase 4 (Clean up) moves all processed files to Done/
✅ **Activity Logging** - Phase 3 (Execute) appends log to Dashboard.md for every item
✅ **Human Review for Sensitive Items** - Skills flag items with NEEDS_HUMAN_REVIEW
✅ **Professional Pakistani Business Tone** - All outputs use concise, professional language

**Constitution Compliance**: PASS - No violations. All 8 core principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-inbox-automation/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (implementation plan)
├── tasks.md             # Task breakdown (created by /sp.tasks)
├── checklists/
│   └── requirements.md  # Quality validation checklist (completed)
└── contracts/
    ├── skill-interface.md       # Contract between main loop and skills
    └── dashboard-log-format.md  # Log entry format specification
```

### Source Code (repository root)

Since this is an automation workflow rather than traditional software, there is no `src/` directory. The "implementation" consists of:

```text
AI Employee/                    # Repository root (Obsidian vault)
├── .claude/
│   └── skills/
│       ├── task-triage/
│       │   └── SKILL.md        # Existing skill (already implemented)
│       └── file-handler/
│           └── SKILL.md        # Existing skill (already implemented)
│
├── Needs_Action/               # Inbox (incoming items)
├── Done/                       # Archive (processed items)
├── Plans/                      # Task plans (PLAN_*.md files)
├── Dashboard.md                # Activity log and status
├── Company_Handbook.md         # Optional custom rules
│
├── .specify/
│   ├── memory/
│   │   └── constitution.md     # Bronze tier constitution
│   └── scripts/
│       └── bronze-automation-loop.sh  # Main execution loop (TO BE CREATED)
│
└── specs/
    └── 001-bronze-inbox-automation/   # This feature's documentation
```

**Structure Decision**: No traditional source code structure needed. Implementation is a single Bash script (`bronze-automation-loop.sh`) that orchestrates skill invocation. Skills are already implemented as .claude/skills/*/SKILL.md files. The script reads files, calls skills via Claude Code's Skill tool, and performs file operations.

## Complexity Tracking

No constitution violations. All complexity is justified by Bronze tier requirements.

## Architecture Design

### Core Execution Loop

The system runs as an infinite while loop with a 5-phase cycle:

```text
┌─────────────────────────────────────────────────────────────┐
│                    BRONZE AUTOMATION LOOP                    │
│                    (bronze-automation-loop.sh)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  Phase 1: Observe                     │
        │  • Read Dashboard.md (status)         │
        │  • List files in Needs_Action/        │
        │  • Count pending items                │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  Phase 2: Classify & Delegate         │
        │  For each file in Needs_Action/:      │
        │  • If EMAIL_* → task-triage           │
        │  • If FILE_* → file-handler           │
        │  • Else → task-triage (fallback)      │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  Phase 3: Execute Skill Instructions  │
        │  • Invoke chosen skill via Skill tool │
        │  • Skill writes analysis to file      │
        │  • Skill creates Plan if needed       │
        │  • Append log to Dashboard.md         │
        │  • Output status tag                  │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  Phase 4: Clean Up                    │
        │  • Move processed file to Done/       │
        │  • Handle filename collisions         │
        │  • If no items: output <idle> tag     │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  Phase 5: Report                      │
        │  • Output <cycle-complete> tag        │
        │  • Items processed: N                 │
        │  • Plans created: M                   │
        │  • Human attention needed: yes/no     │
        └──────────────────────────────────────┘
                              │
                              │
                              ▼
                    ┌─────────────────┐
                    │  Sleep or Wait  │
                    │  (if idle)      │
                    └─────────────────┘
                              │
                              │
                    Loop back to Phase 1
```

### Skill Delegation Pattern

```text
Main Loop
    │
    ├─ Reads: file in Needs_Action/
    │
    ├─ Decision: filename pattern
    │     │
    │     ├─ EMAIL_*.md ──────────► Skill: task-triage
    │     │                              │
    │     │                              ├─ Classify: high/medium/low
    │     │                              ├─ Summarize content
    │     │                              ├─ Create Plan if complex + high
    │     │                              ├─ Log to Dashboard.md
    │     │                              └─ Return: status (DONE or NEEDS_HUMAN_REVIEW)
    │     │
    │     ├─ FILE_*.ext ──────────► Skill: file-handler
    │     │                              │
    │     │                              ├─ Identify file type
    │     │                              ├─ Summarize if text
    │     │                              ├─ Categorize (invoice/receipt/note/etc)
    │     │                              ├─ Log to Dashboard.md
    │     │                              └─ Return: status
    │     │
    │     └─ *.md (fallback) ─────► Skill: task-triage
    │
    └─ Move file to Done/
```

### File Naming and Routing Rules

| Pattern | Skill | Example |
|---------|-------|---------|
| `EMAIL_*.md` | task-triage | EMAIL_vendor-inquiry.md |
| `EMAIL_*.*` (non-md) | task-triage | EMAIL_urgent.txt |
| `FILE_*.md` | file-handler | FILE_meeting-notes.md |
| `FILE_*.*` | file-handler | FILE_receipt-jan.pdf |
| `*.md` (no prefix) | task-triage (fallback) | task-follow-up.md |
| `*.*` (no prefix, non-md) | file-handler (fallback) | document.txt |

### Skill Interface Contract

**Input to Skill** (passed via Skill tool):
- Filename (relative path: Needs_Action/[filename])
- Implicit: file content (skill reads it)
- Implicit: Company_Handbook.md (skill reads it first if exists)

**Output from Skill** (skill responsibilities):
1. Append analysis to bottom of file:
   ```markdown
   ---
   ANALYSIS
   Classification: high/medium/low (or Category: invoice/receipt/etc)
   Summary: [3-5 sentences]
   Suggested Action: [brief action]
   Status: DONE or NEEDS_HUMAN_REVIEW
   ---
   ```

2. Create Plan if needed (task-triage only):
   - Location: `Plans/PLAN_[original-filename-without-ext].md`
   - Format: Markdown with checkboxes
   - Condition: classification=high AND multi-step (3+ actions)

3. Append log to Dashboard.md:
   ```markdown
   - YYYY-MM-DD HH:MM [Action] [filename]: [classification/category] – [summary snippet]
   ```

4. Output status tag (for main loop to parse):
   - `<status>DONE</status>` - normal completion
   - `<status>NEEDS_HUMAN_REVIEW</status>` - sensitive item flagged

**Main Loop Responsibilities** (post-skill execution):
- Move processed file from Needs_Action/ to Done/
- Handle filename collisions (append timestamp if needed)
- Track counts (items processed, plans created, review needed)
- Output cycle completion report

### Dashboard.md Structure

The Dashboard.md file serves as the central activity log and status tracker:

```markdown
# AI Employee Dashboard

## Status
- Last Active: YYYY-MM-DD HH:MM
- Items in Queue: N
- Items Processed Today: M
- Constitution Version: 1.0.0

## System Information
- Tier: Bronze (Filesystem-only)
- Location: Karachi, Pakistan (PKT, UTC+5)
- Active Skills: task-triage, file-handler
- Deployment: Obsidian vault on local machine

## Recent Activity
<!-- Logs appended here by skills in reverse chronological order -->
- 2026-02-15 14:30 Triaged EMAIL_vendor-followup.md: medium – Created plan for vendor research
- 2026-02-15 14:28 Handled FILE_receipt-jan.pdf: receipt – PDF flagged for manual review
- 2026-02-15 14:25 Triaged EMAIL_newsletter.md: low – Marketing content archived
...

## Statistics
- Total Items Processed: N
- High Priority: X | Medium: Y | Low: Z
- Files Needing Review: R
- Plans Created: P
```

### Error Handling Strategy

| Error Condition | Detection | Response |
|----------------|-----------|----------|
| Empty file in Needs_Action/ | Skill reads 0 bytes | Log "[ERROR] Empty file", move to Done/ with ERROR_ prefix |
| Corrupted/unreadable file | Skill read failure | Log "[ERROR] Unreadable", move to Done/ with ERROR_ prefix |
| Missing Dashboard.md | Main loop check before log | Create Dashboard.md with template structure |
| Filename collision in Done/ | File exists check before move | Append timestamp: `filename_YYYY-MM-DD-HHMM.ext` |
| Skill invocation failure | Skill tool returns error | Log "[ERROR] Skill failed", move file to Done/ with ERROR_ prefix, continue |
| Company_Handbook.md missing | Skill checks existence | Continue without custom rules (optional file) |

All errors are non-fatal. The main loop continues processing remaining items.

### Sensitive Keyword Detection

**Keywords triggering NEEDS_HUMAN_REVIEW** (case-insensitive):
- Financial: payment, invoice, receipt, bill, charge, refund, bank, credit card, account number
- Urgency: urgent, ASAP, deadline, time-sensitive, immediate
- Security: password, credential, API key, token, secret, private key
- Personal: SSN, personal info, confidential, sensitive

**Handling**:
1. Skill detects keyword in content
2. Skill appends to file:
   ```markdown
   ---
   NEEDS_HUMAN_REVIEW
   Reason: [keyword] detected
   ---
   ```
3. Skill logs to Dashboard with `[HUMAN REVIEW REQUIRED]` flag
4. Skill outputs `<status>NEEDS_HUMAN_REVIEW</status>`
5. Main loop moves file to Done/ with `REVIEW_` prefix: `REVIEW_original-filename.ext`

## Implementation Phases

### Phase 0: Validation (Pre-implementation)

**Objective**: Verify environment readiness and dependencies

**Tasks**:
1. Confirm folder structure exists: Needs_Action/, Done/, Plans/, Dashboard.md
2. Verify .claude/skills/task-triage/SKILL.md exists and is readable
3. Verify .claude/skills/file-handler/SKILL.md exists and is readable
4. Check Dashboard.md has `## Recent Activity` section (create if missing)
5. Test Skill tool invocation manually: `/task-triage` and `/file-handler`
6. Verify Bash environment and file operation permissions

**Deliverable**: Environment checklist (all items ✅)

**Estimated Time**: 30 minutes

### Phase 1: Core Loop Implementation

**Objective**: Create bronze-automation-loop.sh with basic 5-phase cycle

**Tasks**:
1. Create `.specify/scripts/bronze-automation-loop.sh`
2. Implement Phase 1 (Observe):
   - Read Dashboard.md to get current status
   - List all files in Needs_Action/ (filter for .md and other supported types)
   - Count pending items
3. Implement Phase 2 (Classify & Delegate):
   - For each file, determine routing based on filename pattern
   - Store skill choice (task-triage or file-handler)
4. Implement Phase 3 (Execute):
   - Invoke chosen skill via Claude Code Skill tool
   - Capture skill output (parse status tag)
5. Implement Phase 4 (Clean Up):
   - Move processed file from Needs_Action/ to Done/
   - Handle filename collisions with timestamp suffix
   - Output `<idle>` tag if no items remain
6. Implement Phase 5 (Report):
   - Track counts during cycle
   - Output `<cycle-complete>` tag with statistics
7. Wrap phases in `while true` loop with sleep interval (e.g., 60 seconds when idle)

**Deliverable**: Working bronze-automation-loop.sh script

**Estimated Time**: 4-5 hours

### Phase 2: Skill Integration and Testing

**Objective**: Ensure skills work correctly when invoked by main loop

**Tasks**:
1. Create test files in Needs_Action/:
   - EMAIL_test-low.md (low priority, simple content)
   - EMAIL_test-high.md (high priority, multi-step)
   - EMAIL_test-urgent-payment.md (contains "urgent" + "payment" keywords)
   - FILE_test-note.md (text file)
   - FILE_test-receipt.pdf (non-text file)
2. Run bronze-automation-loop.sh and verify:
   - Each file is classified correctly
   - Summaries are written to files
   - Plans are created for high-priority multi-step items
   - Dashboard.md logs are appended correctly
   - Files move to Done/ (or Done/REVIEW_* for sensitive)
   - Status tags output correctly
   - Cycle completion report shows accurate counts
3. Test edge cases:
   - Empty file
   - Missing Dashboard.md (should auto-create)
   - Filename collision in Done/
   - No items in Needs_Action/ (should output <idle>)
4. Verify constitution compliance:
   - No external calls made
   - Only allowed folders written to
   - All items logged to Dashboard
   - All items archived to Done/

**Deliverable**: Test results documented in specs/001-bronze-inbox-automation/test-results.md

**Estimated Time**: 2-3 hours

### Phase 3: Error Handling and Robustness

**Objective**: Ensure system handles errors gracefully without crashing

**Tasks**:
1. Add error detection for:
   - Skill invocation failure
   - File read/write errors
   - Corrupted files
   - Missing required files (except Company_Handbook.md which is optional)
2. Implement ERROR_ prefix handling for problematic files
3. Add [ERROR] logging to Dashboard.md
4. Test error scenarios:
   - Delete Dashboard.md mid-cycle (should recreate)
   - Create corrupted file in Needs_Action/
   - Simulate skill failure (invalid skill name)
   - Cause filename collision
5. Verify loop continues after errors (no crashes)

**Deliverable**: Error-resistant bronze-automation-loop.sh

**Estimated Time**: 1-2 hours

### Phase 4: Documentation and Finalization

**Objective**: Document usage, prepare for handoff

**Tasks**:
1. Create quickstart.md:
   - How to start the automation loop
   - How to stop it (Ctrl+C)
   - How to add items to Needs_Action/
   - How to review Dashboard.md logs
   - How to check Done/ archive
2. Create contracts/skill-interface.md:
   - Document input/output contract between loop and skills
   - Include examples
3. Create contracts/dashboard-log-format.md:
   - Document log entry format
   - Include timestamp format (PKT timezone)
4. Update Dashboard.md template with proper sections
5. Test end-to-end workflow:
   - Start loop
   - Drop 5-10 varied items into Needs_Action/
   - Verify all processed correctly
   - Review Dashboard logs
   - Check Done/ archive

**Deliverable**: Complete documentation suite + working system

**Estimated Time**: 1-2 hours

## Technical Decisions

### TD-001: Simple While Loop vs. File Watcher

**Decision**: Use simple `while true` loop with sleep interval, not filesystem watcher

**Rationale**:
- Bronze tier prioritizes simplicity over efficiency
- File watchers (inotify, fswatch) add dependency complexity
- 60-second polling is acceptable for ~10-50 items/day throughput
- Easier to understand and debug

**Trade-offs**:
- ✅ Simple, portable, no dependencies
- ✅ Easy to start/stop (Ctrl+C)
- ❌ Slight delay in processing (up to 60 seconds)
- ❌ CPU wakes every 60 seconds (negligible impact)

**Alternatives Considered**:
- inotifywait: Rejected (requires installation, Linux-specific)
- fswatch: Rejected (requires installation, complex setup)
- Cron job: Rejected (less responsive, harder to monitor)

---

### TD-002: Skill Invocation Method

**Decision**: Use Claude Code's Skill tool (e.g., `/task-triage`) to invoke skills, not direct SKILL.md parsing

**Rationale**:
- Skills are Claude Code primitives, designed to be invoked via Skill tool
- Skill tool handles context loading and execution
- Avoids re-implementing skill execution logic
- Maintains compatibility with Claude Code ecosystem

**Trade-offs**:
- ✅ Native integration with Claude Code
- ✅ Skills can be updated independently
- ✅ Proper context and tool access for skills
- ❌ Requires Claude Code CLI to be running
- ❌ Cannot run as pure Bash script (depends on Claude)

**Implementation Note**: The bronze-automation-loop.sh script will call Claude Code CLI with skill invocations, not attempt to parse SKILL.md files directly.

---

### TD-003: Status Tag Format

**Decision**: Use XML-style tags for status output: `<status>DONE</status>`, `<idle>...</idle>`, `<cycle-complete>...</cycle-complete>`

**Rationale**:
- Easy to parse in Bash with grep/sed
- Visually distinct from Markdown content
- Extensible (can add attributes if needed)
- Unambiguous delimiters

**Trade-offs**:
- ✅ Simple parsing in shell scripts
- ✅ Clear visual separation
- ✅ Familiar XML-like syntax
- ❌ Slightly verbose (vs. JSON or plain text)

**Format Specification**:
```xml
<status>DONE</status>
<status>NEEDS_HUMAN_REVIEW</status>
<idle>No pending items. Waiting for watcher.</idle>
<cycle-complete>
Items processed: 3
New plans created: 1
Human attention needed: yes
</cycle-complete>
```

---

### TD-004: Timestamp Format for Logs and Collisions

**Decision**: Use `YYYY-MM-DD HH:MM` format for Dashboard logs, `YYYY-MM-DD-HHMM` for filename suffixes

**Rationale**:
- ISO 8601 date format is unambiguous and sortable
- PKT timezone (UTC+5) for Karachi location
- Space separator in logs for readability
- No colons in filename suffixes (Windows compatibility)

**Trade-offs**:
- ✅ Sortable chronologically
- ✅ Unambiguous
- ✅ Windows-compatible filenames
- ❌ Requires timezone handling in Bash

**Implementation**:
```bash
# For Dashboard logs
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
echo "- $TIMESTAMP Triaged $FILENAME: $CLASSIFICATION – $SUMMARY" >> Dashboard.md

# For filename collisions
SUFFIX=$(date '+%Y-%m-%d-%H%M')
mv "Needs_Action/$FILENAME" "Done/${FILENAME%.*}_${SUFFIX}.${FILENAME##*.}"
```

---

### TD-005: Plan Creation Threshold

**Decision**: Create Plans only when BOTH conditions met: (1) classification=high AND (2) multi-step (3+ distinct actions detected)

**Rationale**:
- Avoids plan clutter for simple high-priority items (e.g., single urgent question)
- Plans add value only when multiple coordinated steps needed
- Threshold of 3+ actions is reasonable for "multi-step"

**Trade-offs**:
- ✅ Reduces unnecessary plan files
- ✅ Plans created when genuinely useful
- ❌ Requires skill to count action items (more complex)
- ❌ Edge cases: user might want plan for 2-step task

**Heuristic for "multi-step" detection**:
- Count bullet points, numbered lists, or sentences with action verbs
- If count >= 3, consider multi-step
- Conservative: when in doubt, create plan (false positives acceptable)

---

## Data Model

### Entity: Inbox Item

**Attributes**:
- `filename`: String (e.g., "EMAIL_vendor-inquiry.md")
- `filepath`: String (e.g., "Needs_Action/EMAIL_vendor-inquiry.md")
- `content`: String (full file content)
- `file_type`: String ("text/markdown" or "application/pdf" or "unknown")
- `prefix`: String ("EMAIL_" or "FILE_" or null)
- `created_at`: Timestamp (file creation time)

**Lifecycle**:
1. User drops file into Needs_Action/
2. Main loop detects file in Phase 1
3. Main loop classifies file in Phase 2
4. Skill processes file in Phase 3
5. Main loop moves file to Done/ in Phase 4

---

### Entity: Processed Item (in Done/)

**Attributes**:
- `filename`: String (original or with REVIEW_/ERROR_ prefix)
- `filepath`: String (e.g., "Done/EMAIL_vendor-inquiry.md")
- `classification`: String ("high"/"medium"/"low" or category for files)
- `status`: String ("DONE" or "NEEDS_HUMAN_REVIEW")
- `summary`: String (3-5 sentences from analysis)
- `processed_at`: Timestamp (from Dashboard log)

**Variations**:
- Normal: `Done/EMAIL_vendor-inquiry.md`
- Human review: `Done/REVIEW_EMAIL_urgent-payment.md`
- Error: `Done/ERROR_corrupted-file.md`
- Collision: `Done/EMAIL_vendor-inquiry_2026-02-15-1430.md`

---

### Entity: Plan

**Attributes**:
- `filename`: String (e.g., "PLAN_vendor-rfp.md")
- `filepath`: String (e.g., "Plans/PLAN_vendor-rfp.md")
- `source_file`: String (reference to original item)
- `classification`: String ("high" - plans only for high priority)
- `action_items`: List[String] (checkboxes)
- `created_at`: Timestamp

**Format**:
```markdown
# Plan: Vendor RFP Response

**Source:** Done/EMAIL_vendor-rfp.md
**Classification:** high
**Created:** 2026-02-15 14:30

## Tasks
- [ ] Research vendor requirements
- [ ] Draft technical proposal
- [ ] Review pricing options
- [ ] Schedule follow-up call

## Notes
RFP deadline: 2026-02-20. Requires technical and commercial response.
```

---

### Entity: Activity Log Entry

**Attributes**:
- `timestamp`: String ("YYYY-MM-DD HH:MM" in PKT timezone)
- `action`: String ("Triaged" or "Handled" or "ERROR")
- `filename`: String (original filename)
- `classification`: String (priority or category)
- `summary`: String (brief snippet)
- `flags`: List[String] (e.g., ["HUMAN REVIEW REQUIRED"])

**Format**:
```
- YYYY-MM-DD HH:MM [Action] [filename]: [classification] – [summary]
- 2026-02-15 14:30 Triaged EMAIL_vendor-rfp.md: high – RFP response needed by Feb 20
- 2026-02-15 14:32 Handled FILE_receipt-jan.pdf: receipt – PDF flagged for manual review [HUMAN REVIEW REQUIRED]
- 2026-02-15 14:35 ERROR EMAIL_corrupted.md: unreadable – File moved to Done/ with ERROR prefix
```

---

## Contracts

### Contract: Main Loop ↔ Skill Interface

**File Location**: `specs/001-bronze-inbox-automation/contracts/skill-interface.md`

**Summary**:

**Main Loop Provides**:
1. Filename to process (as argument to Skill tool)
2. Implicit: file exists in Needs_Action/
3. Implicit: Dashboard.md exists with ## Recent Activity section

**Skill Provides**:
1. Appends analysis to bottom of file in Needs_Action/
2. Creates Plan file in Plans/ if conditions met (task-triage only)
3. Appends log entry to Dashboard.md
4. Outputs status tag: `<status>DONE</status>` or `<status>NEEDS_HUMAN_REVIEW</status>`

**Main Loop Consumes**:
1. Reads status tag from skill output
2. Moves processed file to Done/ (with REVIEW_ or ERROR_ prefix if needed)
3. Updates cycle statistics

**Invariants**:
- Skill MUST NOT move or delete files (main loop's responsibility)
- Skill MUST write to exactly 3 locations: file in Needs_Action/ (append), Dashboard.md (append), optionally Plans/ (create)
- Main loop MUST invoke exactly one skill per file
- Main loop MUST move file to Done/ after skill completes (success or failure)

---

### Contract: Dashboard Log Format

**File Location**: `specs/001-bronze-inbox-automation/contracts/dashboard-log-format.md`

**Summary**:

**Format**:
```
- YYYY-MM-DD HH:MM [Action] [filename]: [classification] – [summary] [flags]
```

**Fields**:
- `YYYY-MM-DD HH:MM`: Timestamp in PKT timezone (UTC+5), 24-hour format
- `[Action]`: "Triaged" (task-triage) or "Handled" (file-handler) or "ERROR"
- `[filename]`: Original filename (no path, e.g., "EMAIL_vendor.md")
- `[classification]`: "high"/"medium"/"low" OR category like "receipt"/"project-note"
- `[summary]`: 5-15 word snippet of content or action taken
- `[flags]`: Optional, space-separated (e.g., "[HUMAN REVIEW REQUIRED]")

**Examples**:
```markdown
## Recent Activity
- 2026-02-15 14:30 Triaged EMAIL_vendor-rfp.md: high – RFP response needed by Feb 20
- 2026-02-15 14:32 Handled FILE_receipt-jan.pdf: receipt – PDF flagged for manual review [HUMAN REVIEW REQUIRED]
- 2026-02-15 14:35 Triaged EMAIL_newsletter.md: low – Marketing content archived
- 2026-02-15 14:38 ERROR EMAIL_corrupted.md: unreadable – File moved with ERROR prefix
```

**Ordering**: Reverse chronological (newest first). Main loop OR skills append to top of list (after ## Recent Activity header).

---

## Success Criteria Validation

| Success Criterion | Implementation Approach | Validation Method |
|-------------------|-------------------------|-------------------|
| SC-001: <30 sec per item | Sequential processing, minimal file I/O | Manual timing during Phase 2 testing |
| SC-002: 90%+ classification | Keyword analysis in skills | Review test results (20+ test files) |
| SC-003: 100% sensitive detection | Comprehensive keyword list in skills | Test with 10+ sensitive files (zero misses allowed) |
| SC-004: Complete audit trail | Phase 3 appends log for every item | Verify Dashboard.md has one entry per processed file |
| SC-005: 100% file preservation | Phase 4 moves all files to Done/ | Check Done/ contains all test files after run |
| SC-006: 8-12 hour timeline | Phased implementation plan | Track actual hours in Phase 4 retrospective |
| SC-007: Verification via logs | Dashboard.md is primary interface | User review of logs confirms correct processing |
| SC-008: Edge case handling | Phase 3 error handling implementation | Test all 6 edge cases, verify no crashes |

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Skills not working as expected | Medium | High | Test skills manually before loop integration (Phase 2) |
| File corruption causes crash | Low | Medium | Wrap all file I/O in error handling (Phase 3) |
| Dashboard.md grows too large | Medium | Low | Acceptable for Bronze tier; document rotation strategy for future |
| Filename collisions not handled | Low | Medium | Implement timestamp suffix in Phase 1 |
| Loop consumes too much CPU | Low | Low | Use 60-second sleep when idle |
| Timezone confusion (PKT vs UTC) | Medium | Low | Document timezone clearly, use explicit TZ in date commands |
| User forgets to start loop | Medium | Medium | Document startup in quickstart.md, consider systemd/launchd for auto-start |

---

## Open Questions

**Q1**: Should the loop auto-start on system boot?
- **Answer**: Out of scope for Bronze tier. User manually starts loop. Document in quickstart.md.

**Q2**: How to handle non-.md files in Needs_Action/?
- **Answer**: file-handler skill processes all file types. Non-text files (PDF, images) flagged for manual review.

**Q3**: Should Dashboard.md be automatically rotated/archived when it grows large?
- **Answer**: Not in Bronze tier. Acceptable to let it grow. Document manual rotation procedure for future.

**Q4**: What if Company_Handbook.md has conflicting rules with constitution?
- **Answer**: Constitution supersedes (per Governance section). Skills read handbook as optional guidance only.

**Q5**: Should loop output be logged to a file or just stdout?
- **Answer**: stdout for Bronze tier (user can redirect if desired). Dashboard.md serves as persistent log.

---

## Phase Completion Checklist

### Phase 0: Validation
- [ ] Folder structure verified (Needs_Action/, Done/, Plans/, Dashboard.md)
- [ ] Skills exist and are readable
- [ ] Dashboard.md has ## Recent Activity section
- [ ] Skill tool invocation tested manually
- [ ] Bash environment confirmed

### Phase 1: Core Loop
- [ ] bronze-automation-loop.sh created
- [ ] Phase 1 (Observe) implemented
- [ ] Phase 2 (Classify & Delegate) implemented
- [ ] Phase 3 (Execute) implemented
- [ ] Phase 4 (Clean Up) implemented
- [ ] Phase 5 (Report) implemented
- [ ] While loop wraps all phases
- [ ] Sleep interval added when idle

### Phase 2: Integration & Testing
- [ ] 5+ test files created in Needs_Action/
- [ ] Loop processes all test files correctly
- [ ] Classifications accurate (90%+ pass rate)
- [ ] Summaries written to files
- [ ] Plans created for high+multi-step items
- [ ] Dashboard logs appended correctly
- [ ] Files moved to Done/ or Done/REVIEW_*
- [ ] Status tags output correctly
- [ ] Cycle completion reports accurate

### Phase 3: Error Handling
- [ ] Error detection added for all identified scenarios
- [ ] ERROR_ prefix handling implemented
- [ ] [ERROR] logging to Dashboard works
- [ ] Empty file test passes
- [ ] Corrupted file test passes
- [ ] Missing Dashboard test passes (auto-creates)
- [ ] Filename collision test passes
- [ ] Loop continues after errors (no crashes)

### Phase 4: Documentation
- [ ] quickstart.md created
- [ ] contracts/skill-interface.md created
- [ ] contracts/dashboard-log-format.md created
- [ ] Dashboard.md template updated
- [ ] End-to-end test with 10+ varied items
- [ ] All documentation reviewed for accuracy

---

## Next Steps

After plan approval (`/sp.plan` completion):

1. **Review this plan** - Ensure technical approach aligns with Bronze tier vision
2. **Run `/sp.tasks`** - Generate task breakdown from this plan
3. **Execute tasks** - Implement phases 0-4 sequentially
4. **Test thoroughly** - Validate all success criteria
5. **Document** - Create quickstart and contracts
6. **Deploy** - User starts bronze-automation-loop.sh and monitors Dashboard.md

**Estimated Total Time**: 8-12 hours (matches Bronze tier constraint)
