# Implementation Plan: Gold-Tier Autonomous AI Employee

**Branch**: `001-gold-tier-employee` | **Date**: 2026-02-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-gold-tier-employee/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a Gold-Tier Autonomous AI Employee system providing 40+ hours/week of autonomous business operations across four specialized domains (Accounting, Social Media, Finance & Auditing, Approval & Recovery) with mandatory human-in-the-loop gates for sensitive actions.

**Primary Requirement**: Four specialized sub-agents (Accounting, Social Media, Finance & Auditor, Approval & Recovery) coordinate via vault file movements (claim-by-move) to automate Odoo ERP financial operations, multi-platform social media posting, weekly audit cycles with CEO briefing generation, and error recovery with watchdog monitoring. All sensitive actions (Odoo posts, social posts, payments >PKR 100k) require human approval before execution.

**Technical Approach** (from research): Multi-agent system implemented via Claude Code agent configurations (`.claude/agents/*.md`) invoking approved skills (`.claude/skills/*/SKILL.md`) and integrating with external systems via MCP servers (odoo-mcp, browser-mcp, email-mcp). Coordination via file-based vault workflow with atomic file move operations. Logging to JSON Lines format (`Logs/YYYY-MM-DD.jsonl`). No traditional code compilation/deployment—system operates through agent skill invocations and MCP integrations.

## Technical Context

**Agent Platform**: Claude Code (Anthropic CLI) with multi-agent support
**Agent Configurations**: 5 total (Main Orchestrator + 4 specialized sub-agents) defined in `.claude/agents/*.md`
**Agent Skills**: 9 approved skills in `.claude/skills/*/SKILL.md` (task-triage, file-handler, odoo-accounting, multi-social-poster, ceo-briefing-generator, weekly-audit-engine, error-recovery-handler, plus Silver carry-over)
**Integration Layer**: Model Context Protocol (MCP) servers - email-mcp (existing), browser-mcp (existing/extended), odoo-mcp (custom - **NEEDS DEVELOPMENT**)
**Storage**: File-based vault with folder semantics (Needs_Action/, In_Progress/, Pending_Approval/, Approved/, Done/, Briefings/, Accounting/, Logs/, Plans/)
**Coordination**: Claim-by-move atomic file operations (first agent to move file to In_Progress/[agent-name]/ owns it)
**Logging**: JSON Lines format (one JSON object per line) in `Logs/YYYY-MM-DD.jsonl` with required fields (timestamp PKT, agent, action, status, metadata)
**Testing**: End-to-end workflow testing via sample vault files (ACCOUNTING_INVOICE_001.md, SOCIAL_linkedin_001.md, WEEKLY_AUDIT_TRIGGER.md) with validation of state transitions and log entries
**Target Platform**: Local system (Windows/macOS/Linux) with Claude Code CLI installed, Odoo ERP Community 19+ accessible (local/VM), social media accounts configured in browser-mcp
**Project Type**: Multi-agent system (agent configurations + skills + MCP integrations + vault structure)
**Performance Goals**:
- Invoice draft creation <5 min from file drop
- Social post draft <10 min from request
- Weekly CEO briefing generated <15 min (by Monday 07:15 PKT)
- Transient error recovery <15 min (3 retries with exponential backoff)
**Constraints**:
- HITL approval required for ALL Odoo confirm/post, social posts, payments >PKR 100k (no exceptions)
- 24-hour approval timeout (assume rejection if not moved to Approved/)
- Claim-by-move coordination (atomic file moves only, no copy-then-delete)
- PKR currency default, PKT timezone (UTC+5) mandatory
- Professional Karachi business tone required
**Scale/Scope**:
- 4 sub-agents + 1 orchestrator (5 total agents)
- 9 approved skills
- 3 MCP servers (email-mcp, browser-mcp, odoo-mcp)
- 71 functional requirements
- 40+ hours/week automation target

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitutional Reference**: Gold-Tier Constitution v3.0.0 (`.specify/memory/constitution.md`)

### ✅ Compliance Verification

1. **✅ Gold-Tier Multi-Sub-Agent Architecture (Principle I)**
   - Implements exactly 4 specialized sub-agents: Accounting, Social Media, Finance & Auditor, Approval & Recovery
   - Implements Main Orchestrator for delegation, weekly audit triggering, monitoring
   - Each agent operates within designated scope (no scope violations)
   - No direct agent-to-agent communication (vault file coordination only)

2. **✅ Claim-by-Move Coordination (Principle II)**
   - First sub-agent to move file from Needs_Action/ to In_Progress/[agent-name]/ owns it exclusively
   - Atomic file move operations (not copy-then-delete)
   - Ownership persists until Pending_Approval/, Approved/, or Done/
   - Error release via Done/ERROR_[filename]

3. **✅ Gold-Tier Agent Skills (Principle III)**
   - EVERY intelligent decision uses approved skills (odoo-accounting, multi-social-poster, ceo-briefing-generator, weekly-audit-engine, error-recovery-handler, task-triage, file-handler)
   - Skills invoked via .claude/skills/[skill-name]/SKILL.md definitions
   - No custom logic bypassing skills

4. **✅ Gold-Tier HITL Gates (Principle IV)**
   - Mandatory approval for ALL Odoo confirm/post actions
   - Mandatory approval for ALL social media posts
   - Mandatory approval for ALL payments or new payees
   - Mandatory approval for ANY action >PKR 100,000 or irreversible
   - Approval workflow: Draft → Pending_Approval/ → (human) → Approved/ → Execute → Done/
   - 24-hour timeout (assume rejection)

5. **✅ Gold-Tier External Integration via MCP (Principle V)**
   - Approved MCP tools: odoo-mcp, browser-mcp, email-mcp (no unknown MCPs)
   - State-changing MCP calls ONLY after Approved/ file exists
   - Read-only queries allowed for monitoring/audit (no approval needed)
   - Pre-execution checklist: file in Approved/, complete payload, acceptable sensitivity, recent timestamp (<24h), no errors

6. **✅ Enhanced JSON Lines Logging (Principle VI)**
   - ALL actions log to Logs/YYYY-MM-DD.jsonl in JSON Lines format
   - Required fields: timestamp (ISO 8601 PKT), agent, action, file, status, metadata
   - Special log types: MCP calls (mcp, method, params, result), approvals (approver, approval_time), errors (error_type, error_message, retry_attempt), recovery (recovery_action, recovery_status)
   - Dashboard.md updated with human-readable summary
   - NEVER log passwords, API keys, credentials, tokens

7. **✅ Professional Karachi Business Tone (Principle VII)**
   - All outputs, logs, drafts, briefings use professional Pakistani business English
   - Respectful, formal, concise, culturally aware
   - Cost-aware (PKR amounts), proactive but not overstepping

8. **✅ Gold-Tier Vault Workflow (Principle VIII)**
   - Folder structure: Needs_Action/[Accounting|Social|Finance|Email|Comms]/, In_Progress/[agent]/, Pending_Approval/, Approved/, Done/, Briefings/, Accounting/, Logs/
   - State transitions: Needs_Action/ → In_Progress/[agent]/ → Pending_Approval/ → Approved/ → Done/
   - Atomic file moves, log every move, update Dashboard.md, immutable Done/ archive

9. **✅ Weekly Audit Cycle (Principle IX)**
   - Sunday 23:00 PKT: Main Orchestrator creates WEEKLY_AUDIT_TRIGGER.md
   - Finance & Auditor Sub-Agent claims, invokes weekly-audit-engine skill
   - Collects: revenue (Odoo), expenses (bank tx), tasks (Done/), social (summaries)
   - Flags: subscriptions >30 days no usage, delayed tasks, unusual transactions
   - Writes Accounting/Audit_Data_[date].md
   - Monday 07:00 PKT: Invokes ceo-briefing-generator, writes Briefings/YYYY-MM-DD_Monday_Briefing.md
   - Logs completion with status: AUDIT_DATA_COLLECTED

10. **✅ Currency and Location Standards (Principle X)**
    - PKR default currency, formatted "PKR 50,000" with comma separators
    - PKT timezone (UTC+5), ISO 8601 format "2026-02-15T14:30:00+05:00"
    - Karachi business context: hours 09:00-18:00 PKT Mon-Fri, 09:00-14:00 PKT Sat, Pakistani holidays awareness

### 🚫 No Violations Detected

All requirements align with Gold-Tier Constitution v3.0.0. No complexity justification needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-gold-tier-employee/
├── spec.md              # Feature specification (created by /sp.specify)
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── vault-files.schema.json       # Vault file format schemas
│   ├── odoo-mcp.api.json              # Odoo MCP server API contract
│   ├── browser-mcp.api.json           # Browser MCP server API contract
│   └── logs.schema.json               # JSON Lines log schema
├── checklists/          # Quality validation checklists
│   └── requirements.md  # Spec quality checklist (created by /sp.specify)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Agent Configurations (repository root)

```text
.claude/
├── agents/
│   ├── main-orchestrator.md           # Main Orchestrator configuration
│   ├── accounting-sub-agent.md        # Accounting Sub-Agent configuration
│   ├── social-media-sub-agent.md      # Social Media Sub-Agent configuration
│   ├── finance-auditor-sub-agent.md   # Finance & Auditor Sub-Agent configuration
│   └── approval-recovery-sub-agent.md # Approval & Recovery Sub-Agent configuration
│
├── skills/
│   ├── task-triage/SKILL.md           # Task triage and classification skill (Silver carry-over)
│   ├── file-handler/SKILL.md          # File content analysis skill (Silver carry-over)
│   ├── odoo-accounting/SKILL.md       # Odoo ERP integration skill (Gold - CREATED)
│   ├── multi-social-poster/SKILL.md   # Multi-platform social posting skill (Gold - CREATED)
│   ├── ceo-briefing-generator/SKILL.md # CEO briefing generation skill (Gold - CREATED)
│   ├── weekly-audit-engine/SKILL.md   # Weekly audit data collection skill (Gold - CREATED)
│   └── error-recovery-handler/SKILL.md # Error detection & recovery skill (Gold - NEEDS CREATION)
│
└── mcp-servers/
    └── odoo-mcp/                      # Custom Odoo MCP server (NEEDS DEVELOPMENT)
        ├── server.py                  # MCP server implementation
        ├── odoo_client.py             # Odoo JSON-RPC client
        ├── methods/
        │   ├── create_draft.py        # Draft invoice/payment/journal
        │   ├── confirm.py             # Confirm draft record
        │   ├── post.py                # Post to ledger
        │   └── search_records.py      # Read financial data
        └── config.json                # Odoo connection configuration
```

### Vault Structure (repository root)

```text
Needs_Action/
├── Accounting/          # ACCOUNTING_* files (invoice/payment requests)
├── Social/              # SOCIAL_* files (post requests)
├── Finance/             # Bank transaction CSV files
├── Email/               # EMAIL_* files (email drafts/requests)
└── Comms/               # WHATSAPP_* files (WhatsApp message processing)

In_Progress/
├── accounting-sub-agent/     # Files claimed by Accounting Sub-Agent
├── social-sub-agent/         # Files claimed by Social Media Sub-Agent
├── finance-auditor-sub-agent/# Files claimed by Finance & Auditor Sub-Agent
└── approval-sub-agent/       # Files claimed by Approval & Recovery Sub-Agent

Pending_Approval/        # Drafts awaiting human review
├── ACCOUNTING_*.md      # Odoo draft previews
├── SOCIAL_*.md          # Social post previews
└── [other]

Approved/                # Human-approved actions ready to execute
├── ACCOUNTING_*.md      # Approved Odoo operations
├── SOCIAL_*.md          # Approved social posts
└── [other]

Done/                    # Completed archive (immutable)
├── Accounting/
│   └── POSTED_*.md      # Posted Odoo records
├── Social/
│   └── POSTED_*.md      # Posted social content
└── [other]

Briefings/               # Weekly CEO briefings
└── YYYY-MM-DD_Monday_Briefing.md

Accounting/              # Financial data
├── Current_Month.md     # Monthly financial summary
└── Audit_Data_[date].md # Temporary weekly audit data

Logs/                    # Daily JSON Lines logs
└── YYYY-MM-DD.jsonl     # JSON Lines audit log

Plans/                   # Active multi-step plans (if using plan-creator)
└── PLAN_*.md

Dashboard.md             # Central status view (human-readable)
Business_Goals.md        # Business objectives for CEO briefing context (optional)
Company_Handbook.md      # Custom rules, approval thresholds, anomaly limits (optional)
```

**Structure Decision**: Multi-agent system structure (not traditional code project). Agents are configured via `.claude/agents/*.md` files, invoke approved skills from `.claude/skills/*/SKILL.md`, coordinate via vault file movements, and integrate with external systems via MCP servers. No compilation/deployment—system operates through Claude Code agent runtime with MCP integrations.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. Constitution Check ✅ PASSED. This section is not applicable.*

## Phase 0: Research & Design Decisions

See [research.md](research.md) for detailed findings.

**Key Decisions**:

1. **Odoo MCP Server Technology Stack**: Python 3.11+ with `odoo-rpc` library for JSON-RPC client, FastAPI for MCP server implementation, Pydantic for schema validation
   - **Rationale**: Python ecosystem has mature Odoo integration libraries (odoo-rpc, erppeek). FastAPI provides async MCP server with built-in OpenAPI docs. Pydantic ensures type-safe request/response handling.
   - **Alternatives Considered**: Node.js (rejected due to less mature Odoo libraries), direct XML-RPC (rejected in favor of odoo-rpc abstraction)

2. **Browser MCP Extension Approach**: Extend existing browser-mcp with social media platform support (LinkedIn, Facebook, Instagram, Twitter/X)
   - **Rationale**: Leverage existing browser automation infrastructure. Add platform-specific selectors and workflows rather than building from scratch.
   - **Alternatives Considered**: Puppeteer/Playwright direct (rejected to maintain MCP architecture), platform APIs (rejected due to strict rate limits and approval processes)

3. **Agent Execution Pattern**: 5-phase cycle (Observe & Claim → Classify & Delegate → Execute with HITL → Audit & Weekly → Clean, Log & Report)
   - **Rationale**: Standardized pattern ensures consistent behavior across all sub-agents. Atomic claim-by-move prevents race conditions. Skill delegation maintains modularity.
   - **Alternatives Considered**: Event-driven webhooks (rejected for Gold-tier; polling simpler for local deployment), cron-based scheduling (rejected; on-demand processing more responsive)

4. **Logging Format**: JSON Lines (.jsonl) with one JSON object per line
   - **Rationale**: Line-by-line parseable for streaming analysis. Standard format supported by log aggregators (jq, logstash). Append-only safe for concurrent writes.
   - **Alternatives Considered**: Structured JSON arrays (rejected; requires file rewrite on append), plain text logs (rejected; not machine-parseable), SQLite (rejected; over-engineered for local deployment)

5. **Vault Coordination**: Atomic file move operations via filesystem APIs
   - **Rationale**: Filesystem move operations are atomic at OS level (on same filesystem). Simple, no external coordination service needed. Natural ownership semantics.
   - **Alternatives Considered**: File locking (rejected; complex deadlock scenarios), database queue (rejected; over-engineered), Redis pub/sub (rejected; external dependency)

6. **Error Recovery Strategy**: Exponential backoff retry (1min, 5min, 15min) for transient errors, pause and flag for persistent errors after 3 failures
   - **Rationale**: Transient errors (network timeouts, temporary service unavailability) typically resolve within minutes. Exponential backoff prevents thundering herd. 3-retry limit prevents infinite loops.
   - **Alternatives Considered**: Linear backoff (rejected; too aggressive), circuit breaker pattern (rejected; over-engineered for Gold-tier), no retry (rejected; reduces reliability)

7. **Approval Timeout**: 24 hours (assume rejection if not moved to Approved/)
   - **Rationale**: Business owner reviews Pending_Approval/ once per day (morning/afternoon). 24-hour window accommodates weekends and time off. Prevents indefinite stalled workflows.
   - **Alternatives Considered**: No timeout (rejected; workflows can stall indefinitely), shorter timeout like 4 hours (rejected; too aggressive for weekend/holiday coverage)

8. **Weekly Audit Timing**: Sunday 23:00 PKT trigger, Monday 07:00 PKT briefing generation
   - **Rationale**: Sunday night allows full week (Mon-Sun) data collection. Monday morning briefing ready before business day starts (09:00 PKT). Gives CEO weekend to review and plan week.
   - **Alternatives Considered**: Friday evening audit (rejected; doesn't capture weekend work), real-time continuous metrics (rejected; over-engineered for weekly cadence)

## Phase 1: Data Model & Contracts

See [data-model.md](data-model.md) for entity details and [contracts/](contracts/) for API schemas.

**Core Entities**:

1. **Vault File** (work item state machine):
   - States: Needs_Action → In_Progress → Pending_Approval → Approved → Done
   - Filename prefix indicates type: ACCOUNTING_*, SOCIAL_*, EMAIL_*, etc.
   - Content: YAML front-matter (metadata) + Markdown body (payload)

2. **Sub-Agent** (autonomous processor):
   - Configuration: .claude/agents/[agent-name].md (name, scope, skills, domain)
   - Execution: 5-phase cycle per iteration
   - Coordination: Claim-by-move via In_Progress/[agent-name]/

3. **Skill** (intelligent behavior module):
   - Definition: .claude/skills/[skill-name]/SKILL.md (inputs, workflow, outputs)
   - Invocation: Agent reads SKILL.md, follows workflow, generates output
   - Approved skills: 9 total (task-triage, file-handler, odoo-accounting, multi-social-poster, ceo-briefing-generator, weekly-audit-engine, error-recovery-handler, plus 2 Silver carry-over)

4. **MCP Server** (external integration):
   - Protocol: Model Context Protocol (JSON-RPC over stdio/HTTP)
   - Methods: create_draft, confirm, post, search_records (odoo-mcp), navigate, fill, click (browser-mcp), read_inbox, send (email-mcp)
   - Configuration: Server-specific config (Odoo URL/credentials, browser profiles, Gmail OAuth)

5. **Log Entry** (audit record):
   - Format: JSON Lines (one JSON object per line)
   - Required fields: timestamp (ISO 8601 PKT), agent, action, file, status, metadata
   - Special fields: MCP calls (mcp, method, params, result), approvals (approver, approval_time), errors (error_type, error_message, retry_attempt)

6. **Audit Data** (weekly business intelligence):
   - Collection: Sunday 23:00 PKT via weekly-audit-engine skill
   - Sources: Odoo (revenue/receivables), bank CSV (expenses/subscriptions), Done/ (tasks), Social/Summary_* (engagement)
   - Anomalies flagged: subscriptions >30 days no usage, delayed tasks, unusual transactions (>threshold from Company_Handbook.md)

7. **CEO Briefing** (executive report):
   - Generation: Monday 07:00 PKT via ceo-briefing-generator skill
   - Inputs: Business_Goals.md, Accounting/Audit_Data_[date].md, Dashboard.md
   - Sections: Revenue summary (PKR), Completed tasks, Bottlenecks, Proactive suggestions, Social activity
   - Output: Briefings/YYYY-MM-DD_Monday_Briefing.md (professional Karachi tone)

**API Contracts**:

- **Vault File Schema**: See [contracts/vault-files.schema.json](contracts/vault-files.schema.json)
- **Odoo MCP API**: See [contracts/odoo-mcp.api.json](contracts/odoo-mcp.api.json) (create_draft, confirm, post, search_records methods)
- **Browser MCP API**: See [contracts/browser-mcp.api.json](contracts/browser-mcp.api.json) (navigate, fill, click, wait methods)
- **JSON Lines Log Schema**: See [contracts/logs.schema.json](contracts/logs.schema.json) (required fields + special field sets)

## Quickstart

See [quickstart.md](quickstart.md) for detailed setup and testing instructions.

**Quick Start Summary**:

1. **Prerequisites**: Claude Code CLI installed, Odoo Community 19+ accessible (local/VM), social media accounts configured
2. **Setup Vault Structure**: Create folder hierarchy (Needs_Action/, In_Progress/, Pending_Approval/, Approved/, Done/, Briefings/, Accounting/, Logs/)
3. **Configure Agents**: Create 5 agent configuration files in `.claude/agents/*.md`
4. **Install Skills**: Ensure 9 approved skills exist in `.claude/skills/*/SKILL.md`
5. **Setup MCP Servers**: Configure odoo-mcp (custom), browser-mcp (extended), email-mcp (existing)
6. **Test Workflows**: Drop sample files (ACCOUNTING_INVOICE_001.md, SOCIAL_linkedin_001.md, WEEKLY_AUDIT_TRIGGER.md), observe state transitions and log entries
7. **Monitor**: Check Dashboard.md for status, Pending_Approval/ for items needing review, Logs/ for audit trail

## Implementation Phases (Post-Planning)

**Note**: This plan document is created by `/sp.plan` and stops here. Actual implementation tasks are generated by `/sp.tasks` command in `tasks.md`.

**Next Command**: `/sp.tasks` to generate dependency-ordered implementation tasks

**Expected Task Categories**:
1. Vault structure setup (create folders, initialize files)
2. Agent configuration files (5 agents in `.claude/agents/*.md`)
3. Skill definitions (1 missing: error-recovery-handler in `.claude/skills/error-recovery-handler/SKILL.md`)
4. Odoo MCP server development (Python server, Odoo client, 4 methods)
5. Browser MCP extension (add social platform support)
6. Testing workflows (end-to-end validation with sample files)
7. Documentation (Company_Handbook.md, Business_Goals.md templates)

**Estimated Complexity**: Medium-High (20-30 tasks across 7 categories, 40-60 hours total implementation time)

**Critical Path**: Odoo MCP server development (prerequisite for accounting workflows) → Agent configurations → Skill definitions → End-to-end testing

## Constitution Re-Check (Post-Design)

*GATE: Re-verify after Phase 1 design complete.*

**Status**: ✅ **PASSED** - All Phase 1 design decisions align with Gold-Tier Constitution v3.0.0

**Specific Validations**:

1. ✅ **Data Model** aligns with constitutional entities (Sub-Agent, Skill, MCP Server, Vault File, Log Entry, Audit Data, CEO Briefing)
2. ✅ **API Contracts** enforce HITL gates (Odoo confirm/post require Approved/ file, browser-mcp posting requires Approved/ file)
3. ✅ **Logging Schema** includes all required fields (timestamp PKT, agent, action, file, status, metadata) plus special field sets
4. ✅ **Vault File Schema** enforces state transitions (Needs_Action → In_Progress → Pending_Approval → Approved → Done) and filename conventions
5. ✅ **Audit Data Collection** follows weekly cycle (Sunday 23:00 PKT → Monday 07:00 PKT) with anomaly flagging
6. ✅ **Currency/Location Standards** enforced in schemas (PKR currency validation, PKT timezone in timestamps, Karachi context in briefing tone guidelines)

**No violations introduced during design phase.**

---

**Plan Status**: ✅ **COMPLETE** (Phases 0-1)

**Next Step**: Run `/sp.tasks` to generate implementation task list with dependencies

**Generated Artifacts**:
- ✅ plan.md (this file)
- ✅ research.md (Phase 0 decisions)
- ✅ data-model.md (Phase 1 entities)
- ✅ contracts/ (Phase 1 API schemas)
- ✅ quickstart.md (Phase 1 setup guide)

**Ready for**: Implementation task generation (`/sp.tasks`)
