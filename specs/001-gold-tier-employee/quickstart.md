# Quickstart: Gold-Tier Autonomous AI Employee

**Feature**: 001-gold-tier-employee
**Phase**: 1 (Setup & Testing Guide)
**Date**: 2026-02-15

## Purpose

Provide step-by-step setup instructions and testing procedures for the Gold-Tier Autonomous AI Employee system. Get from zero to working system in under 2 hours.

---

## Prerequisites

**Required Software**:
- Claude Code CLI (Anthropic) - latest version
- Odoo Community 19+ - accessible via local network or VM
- Python 3.11+ - for odoo-mcp server development
- Git - for version control

**Required Accounts**:
- Gmail account (for email-mcp)
- LinkedIn account (optional, for social media)
- Facebook account (optional, for social media)
- Instagram account (optional, for social media)
- Twitter/X account (optional, for social media)

**System Requirements**:
- Windows 10+, macOS 12+, or Linux (Ubuntu 20.04+)
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space (for Odoo + logs + vault)

---

## Step 1: Setup Vault Structure (15 minutes)

Create the folder hierarchy at repository root:

```bash
# Navigate to repository root
cd "/c/Users/Cs/Desktop/AI Employee-"

# Create vault folders
mkdir -p Needs_Action/{Accounting,Social,Finance,Email,Comms}
mkdir -p In_Progress/{accounting-sub-agent,social-media-sub-agent,finance-auditor-sub-agent,approval-sub-agent}
mkdir -p Pending_Approval Approved
mkdir -p Done/{Accounting,Social,Email}
mkdir -p Briefings Accounting Logs Plans

# Create initial files
touch Dashboard.md
touch Business_Goals.md
touch Company_Handbook.md

# Initialize Dashboard.md
cat > Dashboard.md << 'EOF'
# AI Employee Dashboard

**Last Active**: Never (awaiting first cycle)

## Status

- **Pending Approvals**: 0
- **Items in Accounting Queue**: 0
- **Items in Social Queue**: 0
- **Items Processed Today**: 0
- **Errors Today**: 0

## Pending Approvals (Human Action Required)

(none)

## Weekly Audit Status

- **Last Audit**: Never
- **Next Audit**: (will be scheduled on first Sunday 23:00 PKT)
- **CEO Briefing**: Never

## Recent Activity

(no activity yet)

## Error Log (Last 24 Hours)

(no errors)
EOF

echo "✅ Vault structure created successfully"
```

**Verification**:
```bash
# List vault structure
tree -L 2 -d

# Should show:
# .
# ├── Needs_Action/
# │   ├── Accounting/
# │   ├── Social/
# │   ├── Finance/
# │   ├── Email/
# │   └── Comms/
# ├── In_Progress/
# │   ├── accounting-sub-agent/
# │   ├── social-media-sub-agent/
# │   ├── finance-auditor-sub-agent/
# │   └── approval-sub-agent/
# ├── Pending_Approval/
# ├── Approved/
# ├── Done/
# ├── Briefings/
# ├── Accounting/
# ├── Logs/
# ├── Plans/
# ├── Dashboard.md
# ├── Business_Goals.md
# └── Company_Handbook.md
```

---

## Step 2: Configure Agents (30 minutes)

The agent configuration files already exist in `.claude/agents/` from the constitution work. Verify they are present:

```bash
# Check agent files exist
ls -l .claude/agents/

# Should show:
# main-orchestrator.md
# accounting-sub-agent.md
# social-media-sub-agent.md
# finance-auditor-sub-agent.md
# approval-recovery-sub-agent.md
```

**Note**: Agent configurations were created during `/sp.constitution` and contain the 5-phase execution cycle. No additional configuration needed unless customizing behavior.

---

## Step 3: Install Skills (15 minutes)

Verify Gold-tier skills exist in `.claude/skills/`:

```bash
# Check skill files exist
ls -l .claude/skills/*/SKILL.md

# Should show:
# .claude/skills/task-triage/SKILL.md (Silver carry-over)
# .claude/skills/file-handler/SKILL.md (Silver carry-over)
# .claude/skills/odoo-accounting/SKILL.md (Gold - CREATED)
# .claude/skills/multi-social-poster/SKILL.md (Gold - CREATED)
# .claude/skills/ceo-briefing-generator/SKILL.md (Gold - CREATED)
# .claude/skills/weekly-audit-engine/SKILL.md (Gold - CREATED)
```

**Missing Skill**: `error-recovery-handler/SKILL.md` (needs creation - will be done in `/sp.tasks` implementation phase)

**Temporary workaround**: Create placeholder until implementation:
```bash
mkdir -p .claude/skills/error-recovery-handler
cat > .claude/skills/error-recovery-handler/SKILL.md << 'EOF'
---
name: error-recovery-handler
description: Detect errors, retry transient, flag persistent. Watchdog monitoring for system health.
---

# Error Recovery Handler Skill (Placeholder)

## When to use
Triggered by Approval & Recovery Sub-Agent when errors detected.

## Workflow
1. Detect error type (transient vs persistent)
2. For transient errors: retry with exponential backoff (1min, 5min, 15min)
3. For persistent errors: pause workflow, move to Done/ERROR_*, flag in Dashboard.md
4. Watchdog: monitor In_Progress/ for stuck files (>30min), flag in Dashboard.md

## Outputs
- Log entries to Logs/YYYY-MM-DD.jsonl (error, recovery_attempt)
- Dashboard.md Error Log updates
- Done/ERROR_* files for persistent failures

(Full implementation pending /sp.tasks phase)
EOF
```

---

## Step 4: Setup MCP Servers (45 minutes)

### 4.1 Odoo MCP Server (Custom - Needs Development)

**Create odoo-mcp server** (simplified for quickstart):

```bash
# Create odoo-mcp directory structure
mkdir -p .claude/mcp-servers/odoo-mcp/methods

# Create Python requirements
cat > .claude/mcp-servers/odoo-mcp/requirements.txt << 'EOF'
odoorpc>=0.10.0
fastapi>=0.110.0
pydantic>=2.6.0
uvicorn>=0.27.0
EOF

# Create config template
cat > .claude/mcp-servers/odoo-mcp/config.json << 'EOF'
{
  "odoo_url": "http://localhost:8069",
  "odoo_db": "my_company",
  "odoo_username": "admin",
  "odoo_password_file": ".env/odoo_password"
}
EOF

# Create password file (NEVER commit to git)
mkdir -p .env
echo "your_odoo_password_here" > .env/odoo_password
echo ".env/" >> .gitignore

# Install Python dependencies
cd .claude/mcp-servers/odoo-mcp
pip install -r requirements.txt
```

**Note**: Full `server.py` and method implementations will be created in `/sp.tasks` implementation phase. For quickstart, odoo-mcp is configured but not yet functional.

### 4.2 Browser MCP Extension

**If browser-mcp already installed**:
- Extend with `social_platforms.json` config file containing LinkedIn, Facebook, Instagram, Twitter/X selectors
- Implementation details in `/sp.tasks` phase

**If browser-mcp NOT installed**:
- Install from: https://github.com/anthropics/mcp-browser
- Follow MCP installation docs

### 4.3 Email MCP

**If email-mcp already installed**:
- Configure with Gmail OAuth2 credentials
- No additional setup needed

**If email-mcp NOT installed**:
- Install from MCP registry: https://github.com/anthropics/mcp-email
- Configure Gmail OAuth2

---

## Step 5: Test Workflows (30 minutes)

### 5.1 Test Accounting Workflow (Odoo Invoice Draft)

**Create test invoice request**:
```bash
cat > Needs_Action/Accounting/ACCOUNTING_INVOICE_001.md << 'EOF'
---
type: ACCOUNTING_INVOICE
id: 001
created: 2026-02-15T10:30:00+05:00
claimed_by: null
status: needs_action
priority: high
partner: "Client ABC"
amount: 50000
currency: PKR
---

# Invoice for Client ABC

## Details

- Service: Web development
- Hours: 40
- Rate: PKR 1,250/hour
- Total: PKR 50,000
- Due: 2026-03-01

## Line Items

1. Web development services (40 hours @ PKR 1,250/hour) = PKR 50,000

Please draft this invoice in Odoo for human review.
EOF
```

**Expected Workflow** (once odoo-mcp is implemented):
1. Accounting Sub-Agent scans Needs_Action/Accounting/, finds ACCOUNTING_INVOICE_001.md
2. Moves file to In_Progress/accounting-sub-agent/ACCOUNTING_INVOICE_001.md (claim)
3. Invokes odoo-accounting skill → calls odoo-mcp create_draft
4. Odoo draft created (ID 456), preview generated
5. Agent moves file to Pending_Approval/ACCOUNTING_INVOICE_001.md with draft preview
6. Human reviews Pending_Approval/, moves to Approved/
7. Approval Sub-Agent detects approved file, calls odoo-mcp confirm/post
8. Invoice posted to Odoo, file moves to Done/Accounting/POSTED_ACCOUNTING_INVOICE_001.md

**Validation**:
- Check Logs/2026-02-15.jsonl for log entries (claim_file, mcp_call, approval_granted, action_executed)
- Check Dashboard.md Recent Activity section
- Verify file transitions: Needs_Action/ → In_Progress/ → Pending_Approval/ → Approved/ → Done/

### 5.2 Test Social Media Workflow (LinkedIn Post)

**Create test LinkedIn post request**:
```bash
cat > Needs_Action/Social/SOCIAL_linkedin_001.md << 'EOF'
---
type: SOCIAL_linkedin
id: 001
created: 2026-02-15T11:00:00+05:00
claimed_by: null
status: needs_action
priority: medium
platform: linkedin
---

# LinkedIn Post: Announce New Service

## Topic
Announce our new web development services focused on Karachi businesses.

## Key Points
- Professional website development
- Karachi-based team
- Affordable pricing (PKR rates)
- Quick turnaround (2-3 weeks)

## Tone
Professional, business-focused, Karachi-aware

## Hashtags (Optional)
#WebDevelopment #Karachi #BusinessServices #Pakistan

Please generate a professional LinkedIn post draft.
EOF
```

**Expected Workflow** (once browser-mcp is extended):
1. Social Media Sub-Agent scans Needs_Action/Social/, finds SOCIAL_linkedin_001.md
2. Claims file → In_Progress/social-media-sub-agent/
3. Invokes multi-social-poster skill → generates LinkedIn-appropriate content:
   ```
   Excited to announce our new web development services tailored for Karachi businesses!

   We offer:
   ✅ Professional website development
   ✅ Local Karachi-based team
   ✅ Affordable PKR pricing
   ✅ Quick 2-3 week turnaround

   Looking to establish your online presence? Let's connect!

   #WebDevelopment #Karachi #BusinessServices #Pakistan
   ```
4. Agent moves file to Pending_Approval/SOCIAL_linkedin_001.md with generated content
5. Human reviews, moves to Approved/
6. Approval Sub-Agent calls browser-mcp to post to LinkedIn
7. Post published, file moves to Done/Social/POSTED_SOCIAL_linkedin_001.md

**Validation**:
- Verify content is professional, Karachi-aware, uses PKR context
- Check Logs/ for mcp_call entries (browser-mcp navigate, fill, click)
- Verify LinkedIn post appears in feed

### 5.3 Test Weekly Audit Cycle

**Manual trigger for testing** (instead of waiting for Sunday 23:00 PKT):
```bash
cat > Needs_Action/WEEKLY_AUDIT_TRIGGER.md << 'EOF'
---
type: WEEKLY_AUDIT_TRIGGER
created: 2026-02-15T15:00:00+05:00
status: needs_action
---

# Weekly Audit Trigger (Manual Test)

This file triggers the weekly audit cycle.

Finance & Auditor Sub-Agent will:
1. Claim this file
2. Invoke weekly-audit-engine skill
3. Collect data from Odoo, bank CSV, Done/, Social/Summary_*
4. Flag anomalies
5. Write Accounting/Audit_Data_[date].md
6. Invoke ceo-briefing-generator skill
7. Generate Briefings/[date]_Monday_Briefing.md
8. Move this trigger to Done/
EOF
```

**Expected Workflow**:
1. Finance & Auditor Sub-Agent claims WEEKLY_AUDIT_TRIGGER.md
2. Invokes weekly-audit-engine skill
3. Collects data (Odoo revenue via odoo-mcp search_records, bank CSV parsing, Done/ folder scan, Social/Summary_* aggregation)
4. Flags anomalies (subscriptions >30 days, unusual transactions)
5. Writes Accounting/Audit_Data_2026-02-15.md
6. Invokes ceo-briefing-generator skill
7. Reads Business_Goals.md, Audit_Data, Dashboard.md
8. Generates Briefings/2026-02-17_Monday_Briefing.md (if Monday)
9. Logs completion with status: AUDIT_DATA_COLLECTED
10. Moves trigger to Done/

**Validation**:
- Verify Accounting/Audit_Data_*.md exists and contains revenue, expenses, tasks, social metrics, anomalies
- Verify Briefings/*_Monday_Briefing.md exists and uses professional Karachi business tone
- Check Logs/ for audit completion entry

---

## Step 6: Monitor System (Ongoing)

### 6.1 Dashboard Monitoring

**Check Dashboard.md** (updated after every agent cycle):
```bash
cat Dashboard.md

# Look for:
# - Last Active: (should be recent, within last few minutes)
# - Pending Approvals: (count of items needing human review)
# - Recent Activity: (last 20 log entries, reverse chronological)
# - Error Log: (any errors in last 24 hours)
```

### 6.2 Log Analysis

**View today's logs**:
```bash
# Get today's date in PKT (YYYY-MM-DD format)
TODAY=$(TZ=Asia/Karachi date +%Y-%m-%d)

# View logs
cat Logs/${TODAY}.jsonl | jq '.'

# Filter by agent
cat Logs/${TODAY}.jsonl | jq 'select(.agent == "accounting-sub-agent")'

# Filter by action
cat Logs/${TODAY}.jsonl | jq 'select(.action == "mcp_call")'

# Count errors today
cat Logs/${TODAY}.jsonl | jq 'select(.status == "error")' | wc -l
```

### 6.3 Approval Queue Review

**Check pending approvals** (human action required):
```bash
# List files awaiting approval
ls -lh Pending_Approval/

# Review a specific approval
cat Pending_Approval/ACCOUNTING_INVOICE_001.md

# Approve (move to Approved/)
mv Pending_Approval/ACCOUNTING_INVOICE_001.md Approved/

# Reject (move to Done/REJECTED_*)
mv Pending_Approval/SOCIAL_linkedin_002.md Done/Social/REJECTED_SOCIAL_linkedin_002.md
```

---

## Troubleshooting

### Problem: Agents not claiming files from Needs_Action/

**Diagnosis**:
- Check Claude Code is running (agents are invoked by Claude Code runtime)
- Verify agent configuration files exist in `.claude/agents/`
- Check file format (YAML front-matter + Markdown body)

**Solution**:
```bash
# Verify agent configs
ls .claude/agents/*.md

# Check file format
head -20 Needs_Action/Accounting/ACCOUNTING_INVOICE_001.md

# Ensure YAML front-matter is valid (three dashes on line 1, YAML content, three dashes closing)
```

### Problem: MCP calls failing (odoo-mcp, browser-mcp)

**Diagnosis**:
- Check MCP server is running (odoo-mcp, browser-mcp)
- Verify MCP configuration (config.json, credentials)
- Check Logs/ for error_type (mcp_timeout, odoo_connection_failure, etc.)

**Solution**:
```bash
# Test Odoo connection
curl http://localhost:8069/web/database/list

# Check odoo-mcp config
cat .claude/mcp-servers/odoo-mcp/config.json

# Verify Odoo password file exists
cat .env/odoo_password

# Test browser-mcp
# (depends on browser-mcp installation - follow browser-mcp docs)
```

### Problem: Approvals timing out (24 hours)

**Diagnosis**:
- Check Pending_Approval/ for files >24 hours old
- Verify human reviewed and forgot to move to Approved/

**Solution**:
- Review file in Pending_Approval/
- If approval still valid, move to Approved/ manually:
  ```bash
  mv Pending_Approval/ACCOUNTING_INVOICE_001.md Approved/
  ```
- If rejection intended, move to Done/REJECTED_*:
  ```bash
  mv Pending_Approval/ACCOUNTING_INVOICE_001.md Done/Accounting/REJECTED_ACCOUNTING_INVOICE_001.md
  ```

### Problem: Weekly audit not triggering

**Diagnosis**:
- Check Main Orchestrator is creating WEEKLY_AUDIT_TRIGGER.md on Sunday 23:00 PKT
- Verify current day/time is Sunday 23:00 PKT (or later)

**Solution**:
- Manually create trigger for testing (see Step 5.3 above)
- Check Main Orchestrator configuration for weekly audit trigger logic
- Verify timezone is set to PKT (UTC+5)

---

## Next Steps

**After Quickstart**:
1. Run `/sp.tasks` to generate implementation task list (odoo-mcp server development, browser-mcp extension, error-recovery-handler skill)
2. Implement tasks in dependency order (odoo-mcp → agents → skills → end-to-end testing)
3. Configure Business_Goals.md with your business objectives (used by CEO briefing generator)
4. Configure Company_Handbook.md with approval thresholds, anomaly limits, custom rules
5. Set up bank transaction CSV auto-download (manual for Gold-tier; automation in Platinum-tier)

**Production Checklist**:
- [ ] Odoo ERP accessible and configured (company, chart of accounts, partners, products)
- [ ] All social media accounts logged in (LinkedIn, Facebook, Instagram, Twitter/X)
- [ ] Gmail OAuth2 configured for email-mcp
- [ ] Business_Goals.md defined
- [ ] Company_Handbook.md configured (approval thresholds, anomaly limits)
- [ ] First CEO briefing generated successfully
- [ ] Error recovery tested (simulate Odoo timeout, verify retry logic)
- [ ] Vault backup strategy in place (Done/ folder is immutable archive - backup weekly)

**Estimated Time to Production**:
- Quickstart setup: 2 hours (this guide)
- Implementation tasks (/sp.tasks): 40-60 hours (odoo-mcp, browser-mcp extension, testing)
- **Total**: 42-62 hours to fully operational Gold-tier system

---

**Quickstart Status**: ✅ **COMPLETE**

**Next Phase**: `/sp.tasks` (generate implementation task list)
