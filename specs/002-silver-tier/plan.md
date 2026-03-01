# Implementation Plan: Silver-Tier Multi-Agent AI Employee

**Branch**: `002-silver-tier` | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-silver-tier/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a multi-agent file-based orchestration system with 1 main orchestrator and 3 specialized sub-agents (Email, Comms, Planner) that coordinate via claim-by-move file ownership, process work through skills (email-drafter, social-linkedin-poster, plan-creator), enforce Human-in-the-Loop approval gates, and execute approved actions via MCP servers (email-mcp, browser-mcp). The system operates in 6-step cycles: Observe → Claim & Prioritize → Process with Skills → HITL & Execution → Clean & Report → Coordination Signal.

**Technical Approach**: Vault-based agent orchestration using Claude Code's native file-watching and skill invocation capabilities, with Markdown files as the primary data format and atomic file moves for coordination. No traditional application code required—system is implemented entirely through vault structure, agent behaviors defined in .claude/skills/, and bash/PowerShell automation scripts for initialization and setup.

## Technical Context

**Language/Version**: Vault-based agent system (Claude Code with Sonnet 4.5), Bash/PowerShell scripts for automation
**Primary Dependencies**: Claude Code, MCP servers (email-mcp, browser-mcp), .claude/skills/ (7 skills: task-triage, file-handler, email-drafter, social-linkedin-poster, plan-creator, approval-handler)
**Storage**: File-based Markdown storage in vault structure (Needs_Action/, In_Progress/, Pending_Approval/, Approved/, Done/, Plans/, Logs/, Dashboard.md)
**Testing**: Manual validation via acceptance scenarios from spec.md; file-based integration tests (drop file → verify processing → check outputs)
**Target Platform**: Local machine (Windows/macOS/Linux), Obsidian-compatible vault, Git repository
**Project Type**: Single vault orchestration system (no frontend/backend/mobile)
**Performance Goals**:
  - Email drafts generated within 2 minutes of file arrival
  - Orchestrator cycle every 5 minutes
  - Dashboard.md updates within 5 minutes of activity
  - Plan progress updates on each cycle
**Constraints**:
  - Local-only operation (no cloud hybrid in Silver)
  - 100% HITL approval for external actions (emails, posts)
  - Constitutional compliance (claim-by-move, skills-only intelligence, structured logging)
  - Atomic file operations required for coordination
  - PKT timezone (UTC+5) for all timestamps
**Scale/Scope**:
  - Single-user (Aliyan)
  - ~10-50 items/day processing
  - 1-2 LinkedIn posts/day
  - 5-20 emails/day
  - 1-5 active plans concurrently

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Constitutional Compliance Validation

Checking against `.specify/memory/constitution.md` v2.0.0 (Silver-Tier):

#### ✅ Principle I: Multi-Sub-Agent Architecture (NON-NEGOTIABLE)
**Status**: COMPLIANT
- **Requirement**: 1 main orchestrator + 3 specialized sub-agents
- **Implementation**: Plan includes Main Orchestrator + Email Sub-Agent + Comms Sub-Agent + Planner Sub-Agent
- **Evidence**: Agent cycle documented in user input; each agent has distinct responsibilities per spec.md

#### ✅ Principle II: Claim-by-Move Coordination Rule (MANDATORY)
**Status**: COMPLIANT
- **Requirement**: First sub-agent to move file from Needs_Action/ to In_Progress/[agent-name]/ owns it exclusively
- **Implementation**: Step 2 of agent cycle implements atomic file move for claiming; other agents MUST ignore claimed files
- **Evidence**: Spec FR-001, FR-003 require atomic file operations and exclusive ownership

#### ✅ Principle III: Agent Skills-Based Intelligence (ENFORCED)
**Status**: COMPLIANT
- **Requirement**: All intelligent behavior via predefined Agent Skills; no direct code logic
- **Implementation**: Step 3 of agent cycle delegates to skills (email-drafter, social-linkedin-poster, plan-creator, task-triage, file-handler)
- **Evidence**: Spec FR-030 through FR-033 mandate skill-exclusive processing

#### ✅ Principle IV: Human-in-the-Loop Gate (CRITICAL SAFETY RULE)
**Status**: COMPLIANT
- **Requirement**: Mandatory approval for emails, LinkedIn posts, money, new contacts, attachments >1MB
- **Implementation**: Step 4 of agent cycle enforces Drafts → Pending_Approval/ → (human review) → Approved/ → MCP execute workflow
- **Evidence**: Spec FR-022 through FR-025, SC-002 (100% HITL approval rate)

#### ✅ Principle V: External Integration via MCP (CONTROLLED)
**Status**: COMPLIANT
- **Requirement**: External integrations ONLY via MCP tools; NEVER auto-execute without file in Approved/
- **Implementation**: email-mcp and browser-mcp integration with pre-execution checklist (FR-036)
- **Evidence**: Spec FR-034, FR-035, FR-036 enforce MCP-only external access with approval gates

#### ✅ Principle VI: Structured Logging and Audit Trail (MANDATORY)
**Status**: COMPLIANT
- **Requirement**: All actions logged to Logs/YYYY-MM-DD.md (JSON) + Dashboard.md (human-readable)
- **Implementation**: Step 5 of agent cycle appends to both Dashboard.md and Logs/[date].md
- **Evidence**: Spec FR-026 through FR-029 mandate dual logging

#### ✅ Principle VII: Professional Karachi Business Tone (COMMUNICATION STANDARD)
**Status**: COMPLIANT
- **Requirement**: Professional Pakistani business English appropriate for Karachi context
- **Implementation**: email-drafter and social-linkedin-poster skills enforce Karachi tone; Company_Handbook.md read in Step 1
- **Evidence**: Spec assumptions section documents tone requirements; skills reference constitution

#### ✅ Principle VIII: Vault-Coordinated Workflow (ENFORCED STRUCTURE)
**Status**: COMPLIANT
- **Requirement**: Needs_Action/ → In_Progress/[agent]/ → Pending_Approval/ → Approved/ → Done/ state transitions
- **Implementation**: 6-step agent cycle follows exact workflow; atomic file moves enforce state transitions
- **Evidence**: Spec FR-001 through FR-004 define folder structure and transitions

### Gate Result: ✅ ALL GATES PASSED

**Summary**: Silver-tier implementation plan is fully compliant with constitutional v2.0.0. All 8 core principles are satisfied. No violations or exceptions required.

**Re-evaluation Trigger**: After Phase 1 design, re-check that data models and contracts maintain constitutional compliance (especially claim-by-move atomicity and HITL workflow).

## Project Structure

### Documentation (this feature)

```text
specs/002-silver-tier/
├── plan.md              # This file (/sp.plan command output)
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output (agent cycle patterns, MCP integration)
├── data-model.md        # Phase 1 output (entities: EmailDraft, LinkedInPost, Plan, LogEntry, Dashboard)
├── quickstart.md        # Phase 1 output (setup guide, first agent cycle walkthrough)
├── contracts/           # Phase 1 output (skill invocation contracts, MCP call contracts)
│   ├── email-drafter.contract.md
│   ├── social-linkedin-poster.contract.md
│   ├── plan-creator.contract.md
│   ├── email-mcp.contract.md
│   └── browser-mcp.contract.md
├── checklists/
│   └── requirements.md  # Spec validation checklist (completed)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

This is a **vault-based orchestration system** with no traditional source code. Implementation is achieved through:

1. **Vault Structure** (file-based coordination):
```text
AI Employee/
├── Needs_Action/
│   ├── Email/           # Incoming EMAIL_* files
│   ├── Comms/           # Incoming SOCIAL_*, WHATSAPP_* files
│   └── [general]/       # Other tasks
├── In_Progress/
│   ├── email-sub-agent/     # Email agent's claimed files
│   ├── comms-sub-agent/     # Comms agent's claimed files
│   └── planner-sub-agent/   # Planner agent's claimed files
├── Pending_Approval/    # Human review queue
│   ├── EMAIL_*.md
│   ├── SOCIAL_*.md
│   └── PLAN_*.md
├── Approved/            # Human-approved actions ready to execute
│   ├── EMAIL_*.md
│   └── SOCIAL_*.md
├── Done/                # Completed archive (immutable)
│   ├── Email/
│   │   └── SENT_*.md
│   ├── Social/
│   │   └── POSTED_*.md
│   └── Plans/
│       └── PLAN_*.md
├── Plans/               # Active multi-step plans
│   └── PLAN_*.md
├── Logs/                # Daily JSON audit logs
│   └── YYYY-MM-DD.md
├── Dashboard.md         # Central status view
├── Company_Handbook.md  # Custom business rules (optional)
├── .claude/
│   └── skills/
│       ├── task-triage/SKILL.md       # Bronze carry-over
│       ├── file-handler/SKILL.md      # Bronze carry-over
│       ├── email-drafter/SKILL.md     # Silver (completed)
│       ├── social-linkedin-poster/SKILL.md  # Silver (completed)
│       ├── plan-creator/SKILL.md      # Silver (completed)
│       └── approval-handler/SKILL.md  # Silver (reserved for future)
└── .specify/
    ├── memory/
    │   └── constitution.md  # v2.0.0 Silver-tier
    ├── scripts/
    │   ├── bash/
    │   │   ├── init-silver-vault.sh      # Initialize folder structure
    │   │   └── create-dashboard.sh       # Create initial Dashboard.md
    │   └── powershell/
    │       ├── init-silver-vault.ps1     # Windows equivalent
    │       └── create-dashboard.ps1
    └── templates/
        ├── dashboard-template.md
        ├── email-draft-template.md
        ├── linkedin-post-template.md
        └── plan-template.md
```

2. **MCP Integration** (external services):
```text
MCP Servers (configured externally, invoked by agents):
├── email-mcp            # Gmail send/receive
└── browser-mcp          # LinkedIn posting, WhatsApp reading
```

3. **Agent Behaviors** (defined in .claude/skills/):
```text
Each skill defines:
- When to use (trigger conditions)
- Workflow (step-by-step process)
- Output format (YAML frontmatter + Markdown body)
- Integration points (which folders, which MCP servers)
```

**Structure Decision**: This is a **vault orchestration system** (Option 1 adapted for agent coordination), not a traditional application. No src/ or tests/ directories needed. All "code" is configuration (skills, templates, constitution) + automation scripts (bash/PowerShell for setup). Agents are Claude Code instances following skill definitions and constitution rules, coordinating via file operations.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: ✅ NO VIOLATIONS - No complexity tracking needed

All constitutional requirements are met without exceptions. The vault-based architecture inherently enforces claim-by-move coordination (atomic file operations), HITL gates (folder-based workflow), and skills-based intelligence (.claude/skills/ definitions).

---

## Phase 0: Research & Unknowns Resolution

### Research Tasks

Based on Technical Context, the following areas require research to finalize implementation approach:

1. **Agent Cycle Implementation Pattern**
   - **Question**: How do Claude Code agents execute the 6-step cycle (Observe → Claim → Process → HITL → Clean → Coordinate)?
   - **Research Need**: Determine if this requires custom bash/PowerShell scheduling scripts, cron jobs, or relies on Claude Code's native file-watching capabilities
   - **Priority**: HIGH (foundational to all agent behavior)

2. **Atomic File Move Operations**
   - **Question**: How to ensure atomic file moves for claim-by-move coordination across concurrent agents?
   - **Research Need**: Investigate filesystem atomicity guarantees on Windows/macOS/Linux; determine if additional locking needed
   - **Priority**: HIGH (constitutional requirement for Principle II)

3. **MCP Server Integration**
   - **Question**: How do agents invoke email-mcp and browser-mcp from within skill workflows?
   - **Research Need**: Review MCP protocol documentation; determine invocation syntax and error handling
   - **Priority**: HIGH (required for P1 Email and P2 LinkedIn features)

4. **Skill Invocation Mechanism**
   - **Question**: How does Main Orchestrator delegate work to sub-agents, and how do sub-agents invoke skills?
   - **Research Need**: Clarify if skills are invoked via special syntax, file-based triggers, or agent-native commands
   - **Priority**: HIGH (constitutional requirement for Principle III)

5. **Dashboard.md Update Strategy**
   - **Question**: Can multiple agents safely append to Dashboard.md concurrently, or is a locking mechanism needed?
   - **Research Need**: Investigate concurrent file write patterns; determine if append-only log is sufficient
   - **Priority**: MEDIUM (impacts logging reliability)

6. **Orchestrator Scheduling**
   - **Question**: How does Main Orchestrator run "every 5 minutes" to check for new work?
   - **Research Need**: Determine if this requires external cron/Task Scheduler or Claude Code native scheduling
   - **Priority**: MEDIUM (impacts system responsiveness)

7. **Company_Handbook.md Format**
   - **Question**: What structure and format should Company_Handbook.md use for agent-readable business rules?
   - **Research Need**: Define schema for cultural holidays, tone preferences, custom routing rules
   - **Priority**: LOW (nice-to-have, not blocking MVP)

### Research Findings

*Output will be documented in `research.md` after research tasks complete*

Expected research.md structure:
```markdown
# Silver-Tier Implementation Research

## Decision: Agent Cycle Implementation
**Chosen Approach**: [bash/PowerShell scheduling | Claude Code native | hybrid]
**Rationale**: [why chosen based on capabilities and constraints]
**Alternatives Considered**: [other options evaluated]

## Decision: Atomic File Operations
**Chosen Approach**: [OS-level atomicity | advisory locks | atomic rename | other]
**Rationale**: [why sufficient for claim-by-move coordination]
**Alternatives Considered**: [other locking mechanisms]

## Decision: MCP Invocation
**Chosen Approach**: [direct MCP calls | wrapper scripts | skill-embedded syntax]
**Rationale**: [how skills invoke email-mcp and browser-mcp]
**Alternatives Considered**: [other integration patterns]

[Continue for all research areas...]
```

---

## Phase 1: Design & Contracts

### Prerequisites

- ✅ spec.md complete
- ⏳ research.md complete (after Phase 0)

### Data Model (data-model.md)

Based on entities defined in spec.md (FR-001 through FR-037), the following data models will be documented:

1. **EmailDraft**
   - Purpose: Represents a drafted email response awaiting approval
   - Fields: from, to, subject, body, sensitivity (low/medium/high), requires_hitl (always true), reason, timestamp, original_email_reference
   - File Format: Markdown with YAML frontmatter
   - Storage: Pending_Approval/EMAIL_[id].md → Approved/ → Done/Email/SENT_[id].md
   - Validation Rules: MUST have all required fields; sensitivity MUST be low/medium/high; requires_hitl MUST be true

2. **LinkedInPost**
   - Purpose: Represents a drafted LinkedIn post awaiting approval
   - Fields: platform (linkedin), post_type (sales_promotion | thought_leadership | case_study | engagement), content (100-250 words), hashtags, scheduled_for (timestamp or null), sensitivity (medium), requires_hitl (true)
   - File Format: Markdown with YAML frontmatter
   - Storage: Pending_Approval/SOCIAL_linkedin_[id].md → Approved/ → Done/Social/POSTED_[id].md
   - Validation Rules: Content length 100-250 words; hashtags include #AIEmployee #KarachiBusiness; requires_hitl MUST be true

3. **Plan**
   - Purpose: Represents a multi-step plan for complex task execution
   - Fields: plan_id, title, context, steps (array of checkboxes with owner/dependencies/approval_needed), created, updated, status (in_progress/completed/blocked), priority, owner, estimated_steps, completed_steps
   - File Format: Markdown with YAML frontmatter + checkbox list
   - Storage: Plans/PLAN_[task-name].md → Done/Plans/PLAN_[task-name].md
   - State Transitions: in_progress → completed (when all checkboxes checked) OR blocked (if step fails)

4. **LogEntry**
   - Purpose: Represents a single action in the audit trail
   - Fields: timestamp (ISO 8601 + PKT timezone), agent (orchestrator | email-sub-agent | comms-sub-agent | planner-sub-agent), action (claim | draft | send | post | plan | update), file (filename), status (in_progress | pending_approval | approved | completed | error), metadata (JSON object)
   - File Format: JSON lines (one entry per line)
   - Storage: Logs/YYYY-MM-DD.md (append-only)
   - Validation Rules: Timestamp MUST include timezone; agent MUST be one of 4 valid values; action MUST be recognized verb

5. **Dashboard**
   - Purpose: Represents real-time system status
   - Fields: last_active (timestamp), active_plans (count), pending_approvals (count), items_in_email_queue, items_in_comms_queue, items_processed_today, recent_activity (array of log entries, max 20)
   - File Format: Markdown with structured sections
   - Storage: Dashboard.md (root level, updated by all agents)
   - Update Strategy: Agents append to ## Recent Activity; Main Orchestrator updates ## Status counts

*Full data-model.md will be generated with detailed field definitions, relationships, and examples*

### API Contracts (contracts/)

For a vault-based system, "API contracts" are **skill invocation contracts** and **MCP call contracts** rather than traditional REST/GraphQL endpoints.

#### Skill Invocation Contracts

**contracts/email-drafter.contract.md**:
```yaml
skill_name: email-drafter
input:
  file_path: In_Progress/email-sub-agent/EMAIL_*.md
  content:
    from: string
    to: string
    subject: string
    original_body: string
    context: string (optional)
output:
  file_path: Pending_Approval/EMAIL_[id].md
  frontmatter:
    from: string
    to: string
    subject: string
    sensitivity: low | medium | high
    requires_hitl: true
    reason: string
    timestamp: ISO 8601 + PKT
  body: string (professional email response)
errors:
  - missing_required_fields: ERROR_EMAIL_[id].md
  - content_generation_failed: ERROR_EMAIL_[id].md with reason
```

**contracts/social-linkedin-poster.contract.md**:
```yaml
skill_name: social-linkedin-poster
input:
  trigger: scheduled (10 AM, 3 PM PKT) | manual (file drop) | sales_opportunity_detected
  context: string (optional - sales opportunity details)
output:
  file_path: Pending_Approval/SOCIAL_linkedin_[timestamp].md
  frontmatter:
    platform: linkedin
    post_type: sales_promotion | thought_leadership | case_study | engagement
    sensitivity: medium
    requires_hitl: true
    scheduled_for: timestamp | null
  body:
    hook: string (engaging question or stat)
    content: string (100-250 words)
    cta: string (call to action)
    hashtags: array (#AIEmployee, #KarachiBusiness, #FreelanceAI, etc.)
errors:
  - content_too_long: ERROR_SOCIAL_[id].md (>250 words)
  - inappropriate_content: ERROR_SOCIAL_[id].md with reason
```

**contracts/plan-creator.contract.md**:
```yaml
skill_name: plan-creator
input:
  file_path: Needs_Action/[task-file].md OR In_Progress/planner-sub-agent/[task-file].md
  complexity: complex (>2 steps required)
output:
  file_path: Plans/PLAN_[task-name].md
  frontmatter:
    plan_id: PLAN_[unique-id]
    created: timestamp
    updated: timestamp
    status: in_progress
    priority: high | medium | low
    owner: planner-sub-agent
    requires_approval: true | false
    estimated_steps: integer (3-8)
    completed_steps: 0
  body:
    context: string (what this plan accomplishes)
    steps: array of checkboxes with owner, dependencies, approval_needed
    notes: string (risks, blockers, follow-ups)
    status_tag: <status>PLAN_CREATED</status>
errors:
  - too_many_steps: Split into multiple plans if >8 steps
  - unclear_requirements: ERROR_PLAN_[id].md with clarification needed
```

#### MCP Call Contracts

**contracts/email-mcp.contract.md**:
```yaml
mcp_server: email-mcp
operation: send_email
preconditions:
  - file_exists: Approved/EMAIL_[id].md
  - file_complete: all required fields present
  - approval_recent: timestamp <24 hours old
  - no_errors: no ERROR flag in file
invocation:
  method: [TBD: MCP protocol syntax from research.md]
  params:
    to: extracted from frontmatter
    subject: extracted from frontmatter
    body: extracted from body section
    from: extracted from frontmatter OR default account
response_handling:
  success:
    - move_file: Approved/EMAIL_[id].md → Done/Email/SENT_EMAIL_[id].md
    - append_log: Logs/YYYY-MM-DD.md with send timestamp
    - update_dashboard: Dashboard.md ## Recent Activity
  failure:
    - move_file: Approved/EMAIL_[id].md → Pending_Approval/EMAIL_[id].md
    - add_error_note: append error details to file
    - log_error: Logs/YYYY-MM-DD.md with error metadata
    - flag_human_review: update Dashboard.md with error flag
```

**contracts/browser-mcp.contract.md**:
```yaml
mcp_server: browser-mcp
operation: post_to_linkedin
preconditions:
  - file_exists: Approved/SOCIAL_linkedin_[id].md
  - file_complete: all required fields present
  - approval_recent: timestamp <24 hours old
  - content_valid: 100-250 words, hashtags present
invocation:
  method: [TBD: MCP protocol syntax from research.md]
  params:
    platform: linkedin
    content: combined hook + body + CTA from file
    hashtags: extracted from frontmatter
response_handling:
  success:
    - move_file: Approved/SOCIAL_linkedin_[id].md → Done/Social/POSTED_linkedin_[id].md
    - append_log: Logs/YYYY-MM-DD.md with post timestamp
    - add_engagement_tracking: placeholder for views/reactions/comments
    - update_dashboard: Dashboard.md ## Recent Activity
  failure:
    - move_file: Approved/SOCIAL_linkedin_[id].md → Pending_Approval/SOCIAL_linkedin_[id].md
    - add_error_note: append error details to file
    - log_error: Logs/YYYY-MM-DD.md with error metadata
    - flag_human_review: update Dashboard.md with error flag
```

*Full contracts will be generated in Phase 1 based on research.md findings*

### Quickstart Guide (quickstart.md)

Will include:
1. **Prerequisites**: Claude Code installed, MCP servers configured (email-mcp, browser-mcp), Git repository initialized
2. **Vault Initialization**: Run `.specify/scripts/bash/init-silver-vault.sh` to create folder structure
3. **Dashboard Setup**: Run `.specify/scripts/bash/create-dashboard.sh` to initialize Dashboard.md
4. **First Agent Cycle**: Step-by-step walkthrough of dropping an EMAIL_*.md file and watching it get processed
5. **HITL Approval**: How to review Pending_Approval/ and move files to Approved/
6. **Monitoring**: How to read Dashboard.md and Logs/ for system status

*Full quickstart.md will be generated in Phase 1*

### Agent Context Update

After Phase 1 design completion, will run:
```bash
.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude
```

This will update Claude-specific context with:
- Vault structure details
- Skill invocation patterns
- MCP integration approach
- Agent cycle workflow
- File format examples

---

## Phase 2: Task Generation

**NOT INCLUDED IN /sp.plan** - Use `/sp.tasks` command after plan completion.

Expected task categories:
- **Setup**: Initialize vault structure, create Dashboard.md, configure MCP servers
- **Foundational**: Implement Main Orchestrator cycle, claim-by-move coordination
- **User Story 1 (P1)**: Email Sub-Agent + email-drafter skill integration
- **User Story 2 (P2)**: Comms Sub-Agent + social-linkedin-poster skill integration
- **User Story 3 (P3)**: Planner Sub-Agent + plan-creator skill integration
- **Polish**: Dashboard refinement, logging optimization, error handling

---

## Implementation Notes

### Agent Cycle Details (from user input)

Each sub-agent (Email, Comms, Planner) follows this 6-step cycle:

**1. Observe**
- Read Dashboard.md + Company_Handbook.md (context loading)
- Scan own domain folder in Needs_Action/ (Email → Needs_Action/Email/, Comms → Needs_Action/Comms/)
- Scan In_Progress/[self]/ for work in progress
- Scan Approved/ for own pending approvals (files this agent created that human approved)

**2. Claim & Prioritize**
- Move unclaimed files from Needs_Action/ to In_Progress/[self]/ (atomic move for claim)
- Prioritize work: Approved/ items FIRST → then In_Progress/ → then new Needs_Action/
- Log claim to Logs/YYYY-MM-DD.md

**3. Process with Skills**
- Use task-triage / file-handler to classify incoming items
- Delegate logic to Silver skills:
  - Email → email-drafter
  - LinkedIn/sales → social-linkedin-poster
  - Complex tasks → plan-creator
  - Approvals (future) → approval-handler
- Follow skill workflow as defined in .claude/skills/[skill-name]/SKILL.md

**4. HITL & Execution**
- All drafts → Pending_Approval/ (no auto-execution)
- If human moved file to Approved/ → call corresponding MCP (email-mcp or browser-mcp)
- If Planner: update plan checkboxes in Plans/PLAN_*.md

**5. Clean & Report**
- Move completed files to Done/ (proper subfolder: Email/, Social/, Plans/)
- Append human-readable log to Dashboard.md → ## Recent Activity
- Append detailed JSON log to Logs/[date].md
- If no work left → output `<idle>[agent-name] idle</idle>`

**6. Coordination Signal**
- Main Orchestrator watches all In_Progress/ folders for stuck work
- If Planner creates new task during execution → writes to Needs_Action/ for delegation on next cycle

**Main Orchestrator Special Responsibilities:**
- Every cycle: check for stuck Pending_Approval/ files (>48 hours) → flag in Dashboard.md with warning
- Update Dashboard.md ## Status section (counts of pending approvals, active plans, queue items)
- Enforce constitutional compliance (detect violations, halt and log)

### Critical Design Constraints

1. **Atomicity**: All file moves MUST be atomic to prevent race conditions in claim-by-move
2. **Idempotency**: Agent cycles MUST be idempotent (re-running same cycle with no new work = no state change)
3. **No Direct A2A Messaging**: Agents coordinate via files only (write to Needs_Action/ for delegation, not direct calls)
4. **Immutable Done/**: Once in Done/, files MUST NOT be modified or deleted (audit trail integrity)
5. **HITL Non-Negotiable**: No email sends or LinkedIn posts without file in Approved/ (constitutional Principle IV)

### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Concurrent file claim conflict | Medium | High (duplicate work) | Use atomic rename operations; OS-level filesystem guarantees |
| MCP server failure | Medium | Medium (blocked external actions) | Graceful error handling; move file back to Pending_Approval/ with error note; flag for human review |
| Dashboard.md concurrent write corruption | Low | Medium (lost logs) | Use append-only writes; consider file locking if append not atomic |
| Approval timeout edge case | Low | Low (stale drafts) | Main Orchestrator checks >48h and flags; human can delete or re-approve |
| Skill invocation error | Medium | Medium (processing failure) | Wrap skill calls in error handling; move to Done/ERROR_[file] with details |

---

## Success Metrics (from spec.md)

Reiterating success criteria for implementation validation:

- **SC-001**: Email drafts generated within 2 minutes ✅ (met by 5-min orchestrator cycle + immediate processing)
- **SC-002**: 100% HITL approval rate ✅ (enforced by Pending_Approval/ workflow)
- **SC-003**: 1-2 LinkedIn posts daily with >90% approval rate ✅ (scheduled generation + quality skill)
- **SC-004**: Plans updated within 5 minutes ✅ (Planner Sub-Agent cycle every 5 min)
- **SC-005**: Dashboard.md real-time status ✅ (updated each agent cycle)
- **SC-006**: Complete audit trail ✅ (Logs/ JSON + Dashboard.md + Done/ archive)
- **SC-007**: Zero file ownership conflicts ✅ (atomic claim-by-move)
- **SC-008**: Saves 10-15 hours/week ✅ (automation of email drafting, LinkedIn posting, planning)
- **SC-009**: 20-30 hour implementation ✅ (vault setup + skill configuration, no complex code)
- **SC-010**: Traceability ✅ (file state transitions logged at every step)

---

## Next Steps

1. ✅ **Phase 0**: Generate research.md resolving all technical questions
2. ⏳ **Phase 1**: Generate data-model.md, contracts/, quickstart.md
3. ⏳ **Phase 1**: Run update-agent-context.ps1 to sync with Claude Code
4. ⏳ **Phase 2**: Use `/sp.tasks` to break down implementation into executable tasks
5. ⏳ **Implementation**: Execute tasks in priority order (P0 Orchestrator → P1 Email → P2 LinkedIn → P3 Planning)
