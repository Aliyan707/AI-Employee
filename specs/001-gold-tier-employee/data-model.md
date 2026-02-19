# Data Model: Gold-Tier Autonomous AI Employee

**Feature**: 001-gold-tier-employee
**Phase**: 1 (Data Model & Contracts)
**Date**: 2026-02-15

## Purpose

Define core entities, their attributes, relationships, state machines, and validation rules for the Gold-Tier Autonomous AI Employee system.

**Note**: This is NOT a traditional database schema. The "data model" describes file-based entities (Markdown files with YAML front-matter) and their state transitions through the vault folder structure.

---

## Entity Catalog

1. [Vault File](#1-vault-file) - Work item state machine (file moving through folders)
2. [Sub-Agent](#2-sub-agent) - Autonomous processor configuration
3. [Main Orchestrator](#3-main-orchestrator) - Central coordinator configuration
4. [Skill](#4-skill) - Intelligent behavior module definition
5. [MCP Server](#5-mcp-server) - External integration endpoint
6. [Log Entry](#6-log-entry) - Audit record (JSON Lines format)
7. [Audit Data](#7-audit-data) - Weekly business intelligence collection
8. [CEO Briefing](#8-ceo-briefing) - Weekly executive report
9. [Dashboard](#9-dashboard) - Real-time system status view
10. [Approval Workflow](#10-approval-workflow) - HITL gate process

---

## 1. Vault File

**Description**: Work item represented as Markdown file with YAML front-matter. Moves through vault folders to represent state transitions. Claimed and processed by sub-agents.

**Location**: Starts in `Needs_Action/[domain]/`, moves to `In_Progress/[agent]/`, then `Pending_Approval/`, `Approved/`, finally `Done/`

**Filename Convention**: `[TYPE]_[ID].md` or `[TYPE]_[description].md`
- Examples: `ACCOUNTING_INVOICE_001.md`, `SOCIAL_linkedin_002.md`, `WEEKLY_AUDIT_TRIGGER.md`, `EMAIL_client_inquiry.md`

**Structure**:
```markdown
---
# YAML front-matter (metadata)
type: ACCOUNTING_INVOICE | ACCOUNTING_PAYMENT | SOCIAL_linkedin | SOCIAL_facebook | WEEKLY_AUDIT_TRIGGER | EMAIL | etc.
id: 001
created: 2026-02-15T10:30:00+05:00
claimed_by: accounting-sub-agent (null if unclaimed)
status: needs_action | in_progress | pending_approval | approved | completed | rejected | error
priority: high | medium | low (optional, default: medium)
# Type-specific metadata
partner: "Client ABC" (for ACCOUNTING_INVOICE)
amount: 50000 (for ACCOUNTING_INVOICE)
currency: PKR (for ACCOUNTING_INVOICE)
platform: linkedin (for SOCIAL_*)
---

# Markdown body (payload)

[Human-readable description of the work item]

## Details

[Type-specific payload - e.g., invoice line items, social post content, etc.]
```

**State Machine**:
```
Needs_Action/[domain]/[file] → In_Progress/[agent]/[file] → Pending_Approval/[file]
                                                            ↘
                                                             Approved/[file] → Done/[domain]/COMPLETED_[file]
                                                            ↗
                                                           (24h timeout: Done/[domain]/REJECTED_[file])

Error path: Any state → Done/[domain]/ERROR_[file]
```

**State Transitions**:
| From State | To State | Trigger | File Move | Log Action |
|------------|----------|---------|-----------|------------|
| needs_action | in_progress | Agent claims file | Needs_Action/[domain]/[file] → In_Progress/[agent]/[file] | `claim_file` |
| in_progress | pending_approval | Draft created, HITL required | In_Progress/[agent]/[file] → Pending_Approval/[file] | `draft_created` |
| pending_approval | approved | Human moves file | Pending_Approval/[file] → Approved/[file] | `approval_granted` |
| approved | completed | MCP action executed | Approved/[file] → Done/[domain]/COMPLETED_[file] | `action_executed` |
| pending_approval | rejected | 24h timeout OR human decision | Pending_Approval/[file] → Done/[domain]/REJECTED_[file] | `approval_rejected` |
| (any) | error | Exception during processing | [current]/[file] → Done/[domain]/ERROR_[file] | `error_occurred` |

**Validation Rules**:
- Filename MUST match pattern: `[A-Z_]+_[a-zA-Z0-9_-]+\.md`
- YAML front-matter MUST include: type, id (or generated UUID), created (ISO 8601 PKT), status
- File moves MUST be atomic (rename operation, not copy-then-delete)
- Claimed files MUST have `claimed_by` field set to agent name
- Status MUST be one of: needs_action, in_progress, pending_approval, approved, completed, rejected, error

**Relationships**:
- **Created by**: Human (manual file drop) OR Main Orchestrator (WEEKLY_AUDIT_TRIGGER) OR Sub-Agent (error-recovery-handler creating ERROR_* file)
- **Claimed by**: One Sub-Agent (exclusive ownership via In_Progress/[agent]/)
- **Logged in**: Log Entry (every state transition logged to Logs/YYYY-MM-DD.jsonl)
- **Summarized in**: Dashboard (Pending Approvals section, Recent Activity section)

---

## 2. Sub-Agent

**Description**: Specialized autonomous processor with designated domain (Accounting, Social Media, Finance & Auditor, Approval & Recovery). Configured via Markdown file, executes 5-phase cycle.

**Location**: `.claude/agents/[agent-name].md`

**Agent Names** (4 total):
- `accounting-sub-agent` - Odoo ERP integration
- `social-media-sub-agent` - Multi-platform social posting
- `finance-auditor-sub-agent` - Weekly audit + CEO briefing
- `approval-recovery-sub-agent` - HITL workflow + error watchdog

**Configuration Structure**:
```markdown
# [Agent Name] Configuration

**Agent ID**: [agent-name] (used in In_Progress/[agent-name]/ folder)
**Domain**: [Accounting | Social Media | Finance & Auditor | Approval & Recovery]
**Approved Skills**: [comma-separated list of skills this agent may invoke]
**Scan Folders**: [comma-separated list of Needs_Action/ subfolders to monitor]

## Responsibilities

- [Responsibility 1]
- [Responsibility 2]
...

## 5-Phase Execution Cycle

### Phase 1: Observe & Claim
- Read Dashboard.md, Business_Goals.md, Company_Handbook.md
- Scan Needs_Action/[domain]/ for unclaimed files
- Move first unclaimed file to In_Progress/[agent-name]/ (atomic claim)
- Also scan Approved/ for own pending actions

### Phase 2: Classify & Delegate to Skill
- Use task-triage or file-handler to classify file type
- Delegate to domain skill: [skill-name]
- Extract metadata from file YAML front-matter

### Phase 3: Execute with HITL & MCP
- Invoke skill workflow (e.g., odoo-accounting drafts invoice)
- Draft/preview → Pending_Approval/[type]_[id].md
- If file in Approved/, call appropriate MCP (e.g., odoo-mcp confirm/post)
- Generate summaries/contributions as needed

### Phase 4: Audit & Weekly Special
- If WEEKLY_AUDIT_TRIGGER.md exists in Needs_Action/:
  - [Agent-specific audit contribution]
- Move trigger to Done/ when complete

### Phase 5: Clean, Log & Report
- Move completed files to Done/[domain]/
- Append log to Dashboard.md ## Recent Activity
- Append JSON log line to Logs/YYYY-MM-DD.jsonl
- If error detected, invoke error-recovery-handler skill
- Output: <gold-cycle-report agent="[agent-name]">...</gold-cycle-report>

## Constitutional Constraints

- MUST operate only within designated scope (no scope violations)
- MUST NOT communicate with other sub-agents directly (vault file coordination only)
- MUST use approved skills exclusively (no custom logic)
- MUST log every action to Logs/YYYY-MM-DD.jsonl
- MUST enforce HITL gates for sensitive actions (Odoo posts, social posts, payments >PKR 100k)
```

**Attributes**:
- **agent_id** (string): Unique identifier, used in folder names (e.g., "accounting-sub-agent")
- **domain** (enum): Accounting | Social Media | Finance & Auditor | Approval & Recovery
- **approved_skills** (list of string): Skills this agent may invoke
- **scan_folders** (list of string): Needs_Action/ subfolders to monitor
- **responsibilities** (list of string): Human-readable responsibility descriptions

**Validation Rules**:
- Agent ID MUST match pattern: `[a-z-]+`
- Approved skills MUST exist in `.claude/skills/[skill-name]/SKILL.md`
- Scan folders MUST exist in vault structure (`Needs_Action/[folder]/`)
- Agent MUST NOT claim files outside scan folders (constitutional violation)

**Relationships**:
- **Configured in**: `.claude/agents/[agent-name].md`
- **Invokes**: Skill (one or more approved skills)
- **Claims**: Vault File (moves to In_Progress/[agent-name]/)
- **Logs to**: Log Entry (Logs/YYYY-MM-DD.jsonl)
- **Updates**: Dashboard (Dashboard.md after each cycle)
- **Calls**: MCP Server (odoo-mcp, browser-mcp, email-mcp) when executing approved actions

---

## 3. Main Orchestrator

**Description**: Central coordinator that delegates work to sub-agents, triggers weekly audit cycle, monitors stuck items, enforces constitutional compliance. Never performs sub-agent work directly.

**Location**: `.claude/agents/main-orchestrator.md`

**Configuration Structure**:
```markdown
# Main Orchestrator Configuration

**Agent ID**: main-orchestrator
**Role**: Global coordination, delegation, weekly audit triggering, system health monitoring

## Responsibilities

- Scan Needs_Action/ for new items (all subfolders)
- Delegate to appropriate sub-agent (based on file type or folder location)
- Trigger weekly audit cycle (create WEEKLY_AUDIT_TRIGGER.md Sunday 23:00 PKT)
- Monitor In_Progress/ for stuck files (>30 min in same folder without log activity)
- Update Dashboard.md with system-wide status (Pending Approvals count, queue counts, error count)
- Enforce constitutional compliance (halt on violation detection)

## Execution Cycle

### Phase 1: Monitor & Delegate
- Read Dashboard.md
- Scan Needs_Action/[all subfolders]/ for new files
- For each file, determine appropriate sub-agent based on:
  - File type (ACCOUNTING_* → accounting-sub-agent)
  - Folder location (Needs_Action/Social/ → social-media-sub-agent)
- Do NOT claim files directly (sub-agents claim from Needs_Action/)

### Phase 2: Weekly Audit Trigger
- Check if current day/time is Sunday 23:00 PKT
- If yes and WEEKLY_AUDIT_TRIGGER.md not in Needs_Action/, create it:
  ```markdown
  ---
  type: WEEKLY_AUDIT_TRIGGER
  created: 2026-02-15T23:00:00+05:00
  status: needs_action
  ---

  # Weekly Audit Trigger

  This file triggers the weekly audit cycle.

  Finance & Auditor Sub-Agent will:
  1. Claim this file
  2. Invoke weekly-audit-engine skill
  3. Collect data from Odoo, bank CSV, Done/, Social/Summary_*
  4. Flag anomalies (subscriptions >30 days no usage, delayed tasks, unusual tx)
  5. Write Accounting/Audit_Data_[date].md
  6. Invoke ceo-briefing-generator skill Monday 07:00 PKT
  7. Move this trigger to Done/
  ```

### Phase 3: System Health Monitoring
- Scan In_Progress/[all agents]/ for stuck files:
  - Read last log entry timestamp for each file
  - If >30 min since last activity, flag in Dashboard.md
- Count Pending_Approval/ files, update Dashboard.md
- Count errors in Logs/YYYY-MM-DD.jsonl (today), update Dashboard.md Error Log

### Phase 4: Dashboard Update
- Write Dashboard.md with:
  - Last Active: [current timestamp PKT]
  - Pending Approvals: [count + details]
  - Items in queues: [Accounting queue count, Social queue count, etc.]
  - Items Processed Today: [count from Logs/]
  - Errors Today: [count from Logs/ with status=error]
  - Recent Activity: [last 20 log entries, reverse chronological]
  - Weekly Audit Status: [last/next dates, briefing status]

## Constitutional Constraints

- MUST NOT perform sub-agent work directly (delegate only)
- MUST NOT claim files from Needs_Action/ (sub-agents claim)
- MUST trigger weekly audit exactly once per week (Sunday 23:00 PKT)
- MUST halt system on constitutional violation detection
```

**Attributes**:
- **agent_id** (string): "main-orchestrator"
- **audit_trigger_time** (time): Sunday 23:00 PKT (configurable in Company_Handbook.md)
- **stuck_file_threshold** (duration): 30 minutes (configurable)
- **monitoring_enabled** (boolean): true (always)

**Validation Rules**:
- MUST NOT create duplicate WEEKLY_AUDIT_TRIGGER.md (check Needs_Action/ and In_Progress/ before creating)
- MUST log all delegation decisions to Logs/YYYY-MM-DD.jsonl
- Dashboard.md MUST be updated at least once per cycle

**Relationships**:
- **Configured in**: `.claude/agents/main-orchestrator.md`
- **Delegates to**: Sub-Agent (assigns work via file type/folder detection)
- **Triggers**: Vault File (creates WEEKLY_AUDIT_TRIGGER.md)
- **Updates**: Dashboard (Dashboard.md after each cycle)
- **Monitors**: Log Entry (reads Logs/ for stuck file detection, error counting)

---

## 4. Skill

**Description**: Approved intelligent behavior module invoked by sub-agents. Defines inputs, workflow steps, outputs. Modularity ensures testable, auditable behavior.

**Location**: `.claude/skills/[skill-name]/SKILL.md`

**Approved Skills** (9 total):
1. **task-triage** (Silver carry-over): Classify urgency, suggest actions
2. **file-handler** (Silver carry-over): Summarize file content
3. **odoo-accounting** (Gold): Draft/create/post Odoo invoices/payments
4. **multi-social-poster** (Gold): Generate platform-specific social posts
5. **ceo-briefing-generator** (Gold): Generate weekly executive briefing
6. **weekly-audit-engine** (Gold): Collect weekly audit data, flag anomalies
7. **error-recovery-handler** (Gold): Detect errors, retry transient, flag persistent

**Skill Definition Structure**:
```markdown
---
name: [skill-name]
description: [One-sentence description of skill purpose]
---

# [Skill Name] Skill

## When to use
[Trigger conditions - e.g., "Triggered by Accounting Sub-Agent on ACCOUNTING_* files"]

## Inputs
- [Input 1]: [Description, type, source]
- [Input 2]: [Description, type, source]
...

## Workflow
1. [Step 1]
2. [Step 2]
...
N. [Step N]

## Outputs
- [Output 1]: [Description, type, destination]
- [Output 2]: [Description, type, destination]
...

## Error Handling
- [Error scenario 1]: [How to handle]
- [Error scenario 2]: [How to handle]
...

## Logging Requirements
- [What to log]: [Format, destination]
...
```

**Attributes**:
- **name** (string): Skill identifier (e.g., "odoo-accounting")
- **description** (string): One-sentence purpose
- **inputs** (list): Required inputs with types and sources
- **workflow** (list): Ordered steps to execute
- **outputs** (list): Generated outputs with types and destinations
- **error_handling** (list): Error scenarios and handling strategies
- **logging_requirements** (list): What to log and where

**Validation Rules**:
- Skill name MUST match folder name (`.claude/skills/[skill-name]/SKILL.md`)
- Inputs MUST be obtainable from vault files, Dashboard.md, Business_Goals.md, Company_Handbook.md, or MCP servers
- Workflow steps MUST be deterministic and testable
- Outputs MUST specify destination (Pending_Approval/, Done/, Logs/, Dashboard.md, etc.)

**Relationships**:
- **Invoked by**: Sub-Agent (during Phase 2: Classify & Delegate)
- **Reads from**: Vault File, Dashboard, Business_Goals.md, Company_Handbook.md
- **Writes to**: Vault File (Pending_Approval/), Log Entry (Logs/), Dashboard (Dashboard.md)
- **Calls**: MCP Server (if skill requires external integration)

---

## 5. MCP Server

**Description**: External integration endpoint using Model Context Protocol (JSON-RPC over stdio/HTTP). Provides methods for state-changing operations (require approval) and read-only queries (no approval needed).

**Approved MCP Servers** (3 total):
1. **odoo-mcp** (custom, NEEDS DEVELOPMENT): Odoo ERP integration
2. **browser-mcp** (existing/extended): Browser automation for social media
3. **email-mcp** (existing): Gmail integration

**MCP Server Configuration**:
```json
{
  "name": "odoo-mcp",
  "protocol": "stdio",
  "command": "python",
  "args": ["-m", ".claude/mcp-servers/odoo-mcp/server.py"],
  "env": {
    "ODOO_URL": "http://localhost:8069",
    "ODOO_DB": "my_company",
    "ODOO_USERNAME": "admin",
    "ODOO_PASSWORD_FILE": ".env/odoo_password"
  }
}
```

**Methods** (Odoo MCP example):
| Method | Type | Inputs | Outputs | Approval Required? |
|--------|------|--------|---------|-------------------|
| create_draft | State-changing | partner_id, amount, currency, description, due_date | draft_id, preview_url | No (draft creation allowed) |
| confirm | State-changing | draft_id | confirmed_id | **YES** (requires Approved/ file) |
| post | State-changing | draft_id | posted_id, move_id | **YES** (requires Approved/ file) |
| search_records | Read-only | model, domain, fields | records[] | No (audit data collection) |

**Attributes**:
- **name** (string): MCP server identifier (e.g., "odoo-mcp")
- **protocol** (enum): stdio | http
- **command** (string): Executable to run server
- **args** (list of string): Command arguments
- **env** (object): Environment variables (credentials, URLs)
- **methods** (list): Available methods with signatures

**Validation Rules**:
- State-changing methods (create, update, delete, confirm, post, send) MUST check for Approved/ file before execution
- Read-only methods (search, read, get) MAY execute without approval (used for monitoring, audit)
- All MCP calls MUST log to Logs/YYYY-MM-DD.jsonl with mcp, method, params, result fields
- Credentials MUST be stored in environment or separate file (NEVER in MCP config JSON)

**Relationships**:
- **Called by**: Sub-Agent (during Phase 3: Execute with HITL & MCP)
- **Configured in**: Claude Code MCP server config (JSON)
- **Logs to**: Log Entry (every MCP call logged with mcp, method, params, result)
- **Requires**: Vault File in Approved/ (for state-changing methods)

---

## 6. Log Entry

**Description**: Audit record in JSON Lines format (one JSON object per line). Logged to `Logs/YYYY-MM-DD.jsonl` for complete traceability.

**Location**: `Logs/YYYY-MM-DD.jsonl` (one file per day, PKT timezone)

**JSON Schema**: See [contracts/logs.schema.json](contracts/logs.schema.json)

**Required Fields**:
```json
{
  "timestamp": "2026-02-15T14:30:00+05:00",  // ISO 8601 with PKT timezone (+05:00)
  "agent": "accounting-sub-agent",            // Which agent logged this
  "action": "draft_invoice",                  // What action was taken
  "file": "ACCOUNTING_INVOICE_001.md",        // File being processed (if applicable)
  "status": "pending_approval",               // Current status
  "metadata": {                               // Context-specific details (nested JSON)
    "partner": "Client ABC",
    "amount": 50000,
    "currency": "PKR"
  }
}
```

**Special Field Sets** (extend base fields):

**MCP Call Log**:
```json
{
  "timestamp": "2026-02-15T14:40:00+05:00",
  "agent": "approval-sub-agent",
  "action": "mcp_call",
  "file": "ACCOUNTING_INVOICE_001.md",
  "status": "completed",
  "mcp": "odoo-mcp",                          // MCP server name
  "method": "create_draft",                   // Method called
  "params": {"partner_id": 123, "amount": 50000},  // Request params
  "result": {"draft_id": 456, "preview_url": "http://..."}  // Response
}
```

**Approval Log**:
```json
{
  "timestamp": "2026-02-15T14:45:00+05:00",
  "agent": "approval-sub-agent",
  "action": "approval_granted",
  "file": "ACCOUNTING_INVOICE_001.md",
  "status": "approved",
  "approver": "human",                        // Who approved
  "approval_time": "2026-02-15T14:42:00+05:00"  // When approved
}
```

**Error Log**:
```json
{
  "timestamp": "2026-02-15T14:50:00+05:00",
  "agent": "approval-sub-agent",
  "action": "error",
  "file": "ACCOUNTING_INVOICE_001.md",
  "status": "error",
  "error_type": "mcp_timeout",                // Error classification
  "error_message": "Odoo MCP timeout after 30s",  // Error details
  "retry_attempt": 1                          // Retry count (1-3)
}
```

**Recovery Log**:
```json
{
  "timestamp": "2026-02-15T14:51:00+05:00",
  "agent": "approval-sub-agent",
  "action": "recovery_attempt",
  "file": "ACCOUNTING_INVOICE_001.md",
  "status": "recovering",
  "recovery_action": "retry",                 // retry | pause | escalate
  "recovery_status": "resolved"               // recovering | resolved | escalated
}
```

**Validation Rules**:
- Timestamp MUST be ISO 8601 with PKT timezone (+05:00)
- Agent MUST be one of: main-orchestrator, accounting-sub-agent, social-media-sub-agent, finance-auditor-sub-agent, approval-sub-agent
- Action MUST be one of: claim_file, draft_created, approval_granted, action_executed, mcp_call, error, recovery_attempt, etc.
- Status MUST be one of: needs_action, in_progress, pending_approval, approved, completed, rejected, error, recovering
- Metadata MUST be valid JSON object (nested structure allowed)
- MUST NEVER log passwords, API keys, credentials, tokens, Odoo credentials

**Relationships**:
- **Written by**: Sub-Agent (every action logged), Main Orchestrator (delegation, monitoring)
- **Describes**: Vault File (file field references work item), MCP Server (mcp field references server), Skill (action corresponds to skill workflow step)
- **Summarized in**: Dashboard (Recent Activity section shows last 20 log entries)

---

## 7. Audit Data

**Description**: Weekly business intelligence collected Sunday night by Finance & Auditor Sub-Agent via weekly-audit-engine skill. Contains revenue, expenses, tasks, social metrics, and anomaly flags.

**Location**: `Accounting/Audit_Data_[date].md` (temporary file, consumed by CEO briefing generator Monday morning)

**Structure**:
```markdown
---
type: AUDIT_DATA
date: 2026-02-15
week_start: 2026-02-09  // Monday
week_end: 2026-02-15    // Sunday
generated: 2026-02-15T23:10:00+05:00
---

# Weekly Audit Data: 2026-02-09 to 2026-02-15

## Revenue & Receivables (Odoo)

**Total Revenue This Week**: PKR 250,000
**Outstanding Receivables**: PKR 150,000
**New Invoices**: 12
**Paid Invoices**: 8

[Detailed breakdown from Odoo search_records]

## Expenses & Subscriptions (Bank Transactions)

**Total Expenses This Week**: PKR 180,000
**Subscription Costs**: PKR 25,000
**One-Time Expenses**: PKR 155,000

### Active Subscriptions
- Subscription A: PKR 10,000/month (last used: 2026-02-10) ✅
- Subscription B: PKR 15,000/month (last used: 2026-01-05) ⚠️ NO USAGE >30 DAYS

[Parsed from bank CSV file]

## Task Completion (Done/ Folder)

**Tasks Completed This Week**: 15
**Average Completion Time**: 2.3 days
**Delayed Tasks (>5 days)**: 2

[Scanned from Done/ folder with created/completed timestamps]

## Social Media Activity (Social/Summary_*)

**Posts Made**: 5 (2 LinkedIn, 2 Facebook, 1 Instagram)
**Total Reach**: 3,500
**Engagement Rate**: 4.2%
**Potential Leads**: 3

[Aggregated from Social/Summary_*.md files]

## Anomalies Flagged

⚠️ **Subscription B**: No usage detected for 41 days (last used 2026-01-05). Consider canceling to save PKR 15,000/month.

⚠️ **Task vendor-research.md**: Delayed 7 days (expected 3 days). Potential bottleneck in vendor onboarding.

⚠️ **Unusual Transaction**: PKR 85,000 one-time expense on 2026-02-12 (exceeds threshold of PKR 25,000). Category: Equipment purchase. [No action needed if expected]

## Audit Completion

- Data Collected: 2026-02-15 23:01 - 23:10 PKT
- Anomalies Found: 3
- Status: AUDIT_DATA_COLLECTED
```

**Attributes**:
- **date** (date): Sunday date when audit ran (YYYY-MM-DD)
- **week_start** (date): Monday of the week (YYYY-MM-DD)
- **week_end** (date): Sunday of the week (YYYY-MM-DD)
- **generated** (timestamp): When audit completed (ISO 8601 PKT)
- **revenue_total** (number): Total revenue for week (PKR)
- **expenses_total** (number): Total expenses for week (PKR)
- **tasks_completed** (number): Count of completed tasks
- **social_posts** (number): Count of social media posts
- **anomalies** (list): Flagged issues with descriptions

**Validation Rules**:
- Date MUST be Sunday (audit trigger day)
- Week start MUST be Monday, week end MUST be Sunday
- Revenue/expenses MUST be in PKR currency
- Anomaly thresholds defined in Company_Handbook.md (default: subscriptions >30 days no usage, tasks >expected duration, transactions >PKR 25,000)

**Relationships**:
- **Generated by**: Finance & Auditor Sub-Agent (via weekly-audit-engine skill)
- **Sources data from**: MCP Server (odoo-mcp search_records), Bank CSV files, Done/ folder, Social/Summary_* files
- **Consumed by**: CEO Briefing (ceo-briefing-generator skill reads this file Monday morning)
- **Logged in**: Log Entry (audit completion logged with status: AUDIT_DATA_COLLECTED)

---

## 8. CEO Briefing

**Description**: Weekly executive report generated Monday 07:00 PKT by Finance & Auditor Sub-Agent via ceo-briefing-generator skill. Synthesizes audit data, business goals, and dashboard status.

**Location**: `Briefings/YYYY-MM-DD_Monday_Briefing.md`

**Structure**:
```markdown
---
type: CEO_BRIEFING
date: 2026-02-17  // Monday date
week_covered: 2026-02-09 to 2026-02-15
generated: 2026-02-17T07:15:00+05:00
---

# CEO Briefing: Week of 2026-02-09 to 2026-02-15

**Generated**: Monday, 2026-02-17 07:15 PKT

## Executive Summary

This week showed 15% revenue growth (PKR 250,000 vs PKR 217,000 last week). Task completion rate improved to 15 tasks/week. Social media reach grew by 20%. One bottleneck identified: vendor onboarding delayed 7 days. Two proactive cost-saving opportunities flagged.

## Revenue & Financial Performance

**Total Revenue**: PKR 250,000 (↑15% vs last week)
**Outstanding Receivables**: PKR 150,000
**Expenses**: PKR 180,000
**Net Profit This Week**: PKR 70,000

**Key Metrics**:
- New invoices issued: 12
- Invoices paid: 8
- Average payment cycle: 18 days

[Sourced from Accounting/Audit_Data_2026-02-15.md]

## Tasks & Operational Progress

**Tasks Completed**: 15 (avg 2.3 days per task)
**In Progress**: 5
**Delayed Tasks**: 2

**Top Bottleneck**: vendor-research.md delayed 7 days (expected 3 days). Recommendation: Review vendor onboarding process or assign additional resources.

[Sourced from Accounting/Audit_Data_2026-02-15.md + Done/ folder]

## Social Media & Lead Generation

**Posts Published**: 5 (2 LinkedIn, 2 Facebook, 1 Instagram)
**Total Reach**: 3,500 people
**Engagement Rate**: 4.2%
**Potential Leads**: 3

**Top Performing Post**: LinkedIn post on service offering (1,200 reach, 6.5% engagement, 2 leads)

[Sourced from Accounting/Audit_Data_2026-02-15.md + Social/Summary_*.md]

## Proactive Suggestions

1. **Cost Savings**: Subscription B has not been used for 41 days (last used 2026-01-05). Recommend canceling to save PKR 15,000/month (PKR 180,000/year).

2. **Process Improvement**: Vendor onboarding tasks taking 2x expected duration (7 days vs 3 days). Consider streamlining vendor approval process or creating vendor onboarding checklist.

3. **Opportunity**: Social media engagement rate (4.2%) above industry average (2-3%). Recommend increasing posting frequency from 5 to 7-8 posts/week to capitalize on audience engagement.

[Sourced from Accounting/Audit_Data_2026-02-15.md anomalies + Business_Goals.md context]

## Business Goals Alignment

[Read from Business_Goals.md]

**Goal 1**: Increase revenue to PKR 1.5M/month by Q2 2026
- **Status**: On track (current: PKR 1M/month, growth: 15%/week)
- **Action**: Maintain current growth rate + social media lead conversion

**Goal 2**: Reduce operational costs by 20%
- **Opportunity**: Subscription cancellation saves PKR 180,000/year (12% of target)

[Aligned with Business_Goals.md]

## Dashboard Highlights

- Pending Approvals: 2 (1 invoice, 1 social post) - **Action Required**
- System Errors (This Week): 1 (Odoo timeout, resolved via retry)
- Automation Savings: 42 hours/week (invoice drafting: 18h, social posts: 10h, audit/reporting: 6h, email drafting: 8h)

[Sourced from Dashboard.md]

## Next Week Priorities

1. Review vendor onboarding process (address bottleneck)
2. Cancel Subscription B (save PKR 15,000/month)
3. Increase social media posting frequency to 7-8 posts/week
4. Follow up on 3 potential leads from LinkedIn

---

**Professional Karachi Business Tone**: Respectful, formal, concise, culturally aware, cost-conscious (PKR amounts), proactive recommendations.
```

**Attributes**:
- **date** (date): Monday date when briefing generated (YYYY-MM-DD)
- **week_covered** (date range): Monday to Sunday of previous week
- **generated** (timestamp): When briefing completed (ISO 8601 PKT)
- **revenue_summary** (object): Revenue, receivables, expenses, profit
- **tasks_summary** (object): Completed, delayed, bottlenecks
- **social_summary** (object): Posts, reach, engagement, leads
- **proactive_suggestions** (list): Recommended actions (cost savings, process improvements, opportunities)
- **goals_alignment** (list): Business goal progress from Business_Goals.md

**Validation Rules**:
- Date MUST be Monday
- Week covered MUST be previous Mon-Sun
- Tone MUST be professional Karachi business English (respectful, formal, concise, culturally aware)
- All amounts MUST be in PKR currency with comma separators
- Proactive suggestions MUST be actionable (not vague observations)

**Relationships**:
- **Generated by**: Finance & Auditor Sub-Agent (via ceo-briefing-generator skill)
- **Sources data from**: Audit Data (Accounting/Audit_Data_*.md), Business Goals (Business_Goals.md), Dashboard (Dashboard.md)
- **Read by**: Human CEO (Monday morning review for week planning)
- **Archived in**: Briefings/ folder (immutable, historical analysis)

---

## 9. Dashboard

**Description**: Real-time system status view updated by Main Orchestrator and sub-agents. Provides human-readable summary of pending approvals, active work, recent activity, and error log.

**Location**: `Dashboard.md` (repository root)

**Structure**: See contracts/dashboard.schema.md (not JSON, Markdown format)

```markdown
# AI Employee Dashboard

**Last Active**: 2026-02-15 14:50 PKT

## Status

- **Active Plans**: 0
- **Pending Approvals**: 2
- **Items in Accounting Queue**: 3 (Needs_Action/Accounting/)
- **Items in Social Queue**: 1 (Needs_Action/Social/)
- **Items Processed Today**: 15
- **Errors Today**: 1 (recovering)

## Pending Approvals (Human Action Required)

- **ACCOUNTING_INVOICE_001.md** - Invoice for Client ABC (PKR 50,000) - Drafted 20m ago
- **SOCIAL_linkedin_002.md** - Service promotion post - Drafted 15m ago

## Weekly Audit Status

- **Last Audit**: 2026-02-09 (Sunday night)
- **Next Audit**: 2026-02-16 (Sunday night)
- **CEO Briefing**: 2026-02-10 (Monday morning) ✅ Generated

## Recent Activity

- 14:50 [ERROR] odoo-mcp timeout on account.move.post - Recovery attempt 1
- 14:45 [APPROVAL] Human approved ACCOUNTING_INVOICE_001.md
- 14:40 [MCP] odoo-mcp account.move.create → draft_id=456
- 14:35 [CLAIM] accounting-sub-agent claimed ACCOUNTING_INVOICE_001.md
- 14:30 [DRAFT] Social post created for LinkedIn promotion
...
(last 20 entries, reverse chronological)

## Error Log (Last 24 Hours)

- 14:50 [ERROR] mcp_timeout: Odoo MCP timeout after 30s - Status: recovering (retry attempt 1)

## System Health

- Uptime: 99.2% (last 7 days)
- Stuck Files: 0 (In_Progress/ files >30min without activity)
- Constitutional Violations: 0
```

**Attributes**:
- **last_active** (timestamp): Last update time (PKT)
- **pending_approvals_count** (number): Count of files in Pending_Approval/
- **queue_counts** (object): Count of files in Needs_Action/[domain]/ folders
- **processed_today** (number): Count of log entries today with status=completed
- **errors_today** (number): Count of log entries today with status=error
- **recent_activity** (list): Last 20 log entries (reverse chronological)
- **error_log** (list): Last 24 hours of errors with status
- **weekly_audit_status** (object): Last/next audit dates, briefing status
- **stuck_files** (number): Count of In_Progress/ files >30min without log activity

**Validation Rules**:
- MUST be updated after every Main Orchestrator cycle
- MUST be updated after significant sub-agent actions (claim, draft, approval, error)
- Pending Approvals section MUST list files with time since draft (e.g., "Drafted 20m ago")
- Recent Activity MUST be reverse chronological (newest first)
- Error Log MUST include error_type, error_message, status (recovering | escalated)

**Relationships**:
- **Updated by**: Main Orchestrator (every cycle), Sub-Agents (after significant actions)
- **Summarizes**: Vault File (Pending Approvals), Log Entry (Recent Activity, Error Log), Audit Data (Weekly Audit Status)
- **Read by**: Main Orchestrator (system health monitoring), Sub-Agents (Phase 1: Observe), Human (manual review)

---

## 10. Approval Workflow

**Description**: Human-in-the-loop gate process for sensitive actions. Ensures business owner reviews and approves Odoo posts, social media posts, payments >PKR 100k, and irreversible actions before execution.

**States**: Draft created → Pending human review → Approved/Rejected → Executed/Archived

**Workflow Steps**:
1. **Draft Creation** (Sub-Agent):
   - Agent invokes skill (e.g., odoo-accounting) to generate draft
   - Draft includes preview with all details (partner, amount, currency, description for Odoo; platform, content, image for social)
   - Agent writes draft to `Pending_Approval/[TYPE]_[id].md`
   - Agent logs draft_created to Logs/YYYY-MM-DD.jsonl
   - Agent updates Dashboard.md Pending Approvals section

2. **Human Review** (Business Owner):
   - Open Pending_Approval/ folder
   - Read draft file, review details
   - Decision: Approve OR Reject
   - **If Approve**: Move file to `Approved/[TYPE]_[id].md`
   - **If Reject**: Move file to `Done/REJECTED_[TYPE]_[id].md` OR leave in Pending_Approval/ (24h timeout triggers automatic rejection)

3. **Approval Detection** (Approval & Recovery Sub-Agent):
   - Phase 1: Scan Approved/ folder for files
   - For each file in Approved/, check timestamp (<24 hours)
   - Log approval_granted to Logs/YYYY-MM-DD.jsonl with approver="human", approval_time=[file move timestamp]
   - Update Dashboard.md (remove from Pending Approvals)

4. **Action Execution** (Approval & Recovery Sub-Agent):
   - Phase 3: For approved file, invoke appropriate MCP:
     - ACCOUNTING_INVOICE_* → odoo-mcp confirm/post
     - ACCOUNTING_PAYMENT_* → odoo-mcp create/confirm payment
     - SOCIAL_linkedin_* → browser-mcp navigate/fill/click (LinkedIn)
     - SOCIAL_facebook_* → browser-mcp navigate/fill/click (Facebook)
   - Log mcp_call to Logs/YYYY-MM-DD.jsonl with mcp, method, params, result
   - Move file to `Done/[domain]/COMPLETED_[TYPE]_[id].md`
   - Update Dashboard.md Recent Activity

5. **Rejection Handling** (Approval & Recovery Sub-Agent):
   - Phase 1: Scan Pending_Approval/ for files >24 hours old
   - For each timeout file, move to `Done/REJECTED_[TYPE]_[id].md`
   - Log approval_rejected to Logs/YYYY-MM-DD.jsonl with reason="timeout_no_approval", timeout_hours=24
   - Update Dashboard.md (remove from Pending Approvals, add to Recent Activity)

**Timeout**:
- Default: 24 hours (configurable in Company_Handbook.md)
- Counted from draft creation timestamp (file created timestamp in Pending_Approval/)
- After timeout, file automatically moves to Done/REJECTED_*

**File Transitions**:
```
In_Progress/[agent]/[file].md → Pending_Approval/[file].md
                                        ↓
                                  (human reviews)
                                        ↓
                    ┌───────────────────┴────────────────────┐
                    ↓                                         ↓
            Approved/[file].md                    (24h timeout OR human rejects)
                    ↓                                         ↓
    (agent executes MCP action)                  Done/REJECTED_[file].md
                    ↓
    Done/[domain]/COMPLETED_[file].md
```

**Validation Rules**:
- HITL approval REQUIRED for: ALL Odoo confirm/post, ALL social posts, ALL payments/new payees, ANY action >PKR 100k or irreversible
- HITL approval NOT required for: Odoo draft creation (read-only preview), social post draft (preview), file classification (task-triage)
- Approved/ file MUST have timestamp <24 hours (stale approvals rejected)
- Draft file MUST include complete preview (all fields needed for MCP execution)

**Relationships**:
- **Enforces**: Constitutional HITL gates (Principle IV)
- **Involves**: Vault File (draft in Pending_Approval/, approved in Approved/), Sub-Agent (creates draft, executes after approval), Human (reviews and approves/rejects), Log Entry (all steps logged)
- **Monitored by**: Dashboard (Pending Approvals section shows files awaiting review)

---

## Entity Relationship Diagram (Conceptual)

```
[Human] ---creates---> [Vault File]
                            |
                            |---claimed_by---> [Sub-Agent]
                            |                       |
                            |                       |---invokes---> [Skill]
                            |                       |                  |
                            |                       |                  |---calls---> [MCP Server]
                            |                       |
                            |                       |---logs_to---> [Log Entry]
                            |                       |
                            |                       |---updates---> [Dashboard]
                            |
                            |---triggers---> [Approval Workflow]
                            |                       |
                            |                       |---generates---> [CEO Briefing]
                            |
                            |---feeds_into---> [Audit Data]

[Main Orchestrator] ---delegates---> [Sub-Agent]
                   ---triggers---> [Vault File] (WEEKLY_AUDIT_TRIGGER)
                   ---updates---> [Dashboard]
                   ---monitors---> [Log Entry]
```

---

## Validation Summary

**File-Based Constraints**:
- Vault files use YAML front-matter + Markdown body
- File moves MUST be atomic (rename, not copy-delete)
- Claimed files MUST have `claimed_by` field set
- State transitions logged to Logs/YYYY-MM-DD.jsonl

**Agent Constraints**:
- Sub-agents operate only within designated scope
- No direct agent-to-agent communication (vault coordination only)
- EVERY action uses approved skills (no custom logic)
- HITL gates enforced for sensitive actions

**Logging Constraints**:
- ALL actions logged to Logs/YYYY-MM-DD.jsonl (JSON Lines format)
- Required fields: timestamp PKT, agent, action, file, status, metadata
- NEVER log passwords, credentials, API keys, tokens
- Dashboard.md updated after significant transitions

**MCP Constraints**:
- State-changing methods require Approved/ file
- Read-only methods allowed without approval (audit data collection)
- Pre-execution checklist: file in Approved/, complete payload, recent timestamp (<24h), no errors

**Currency & Location Constraints**:
- PKR default currency, formatted "PKR 50,000"
- PKT timezone (UTC+5), ISO 8601 format
- Professional Karachi business tone (respectful, formal, concise, culturally aware)

---

**Data Model Status**: ✅ **COMPLETE**

**Next Phase**: Contracts (API schemas, vault file schemas, log schemas)
