# Personal AI Employee — Gold Tier

> **Hackathon:** Personal AI Employee — Building Autonomous FTEs in 2026
> **Tier Achieved:** Gold (Bronze + Silver + Gold — 100% complete)
> **Location:** Karachi, Pakistan (PKT — UTC+5)
> **Stack:** Python · Claude Code · Playwright · Obsidian Vault · MCP

An autonomous Digital FTE (Full-Time Equivalent) that manages business operations 24/7: email triage, social media posting, accounting (Odoo ERP), weekly CEO briefing, and error recovery — all with human-in-the-loop approval before every sensitive action.

---

## Live Demo Evidence

| Platform | Status | File |
|----------|--------|------|
| LinkedIn | ✅ POSTED LIVE | `Done/Social/POSTED_LINKEDIN_POST_LIVE_TEST_20260220_210343.md` |
| Facebook | ✅ POSTED LIVE | `Done/Social/POSTED_FACEBOOK_POST_LIVE_TEST_20260220_210343.md` |
| Instagram | ✅ POSTED LIVE | `Done/Social/POSTED_INSTAGRAM_POST_20260220.md` |
| Email (Gmail) | ✅ Sent via MCP | `Done/Email/SENT_EMAIL_001_client-inquiry.md` |
| Odoo ERP | ✅ MCP Connected | `mcp-servers/odoo-mcp/server.py` |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│               EXTERNAL SOURCES                       │
│   Gmail · LinkedIn · Facebook · Instagram · Twitter  │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│            PERCEPTION LAYER (Watchers)               │
│  gmail_watcher.py · filesystem_watcher.py            │
│  process_monitor.py (watchdog with backoff restart)  │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│         OBSIDIAN VAULT (Local Markdown State)        │
│  Needs_Action/ → In_Progress/ → Pending_Approval/   │
│            → Approved/ → Done/                       │
│  Dashboard.md · Logs/ · Plans/ · Briefings/          │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│         REASONING LAYER (Claude Code)                │
│  gold-main-orchestrator · sub-agents (email,         │
│  social, accounting, finance, triage, planner)       │
│  Ralph Wiggum loop (Stop hook — autonomous until     │
│  task moves to Done/)                                │
└──────────┬──────────────────────────┬───────────────┘
           ↓                          ↓
┌──────────────────┐     ┌────────────────────────────┐
│  HUMAN-IN-LOOP   │     │       ACTION LAYER          │
│  Review files in │────▶│  4 MCP Servers (Python):   │
│  Pending_Approval│     │  · email-mcp (Gmail)        │
│  Move to Approved│     │  · browser-mcp (LinkedIn)   │
└──────────────────┘     │  · social-mcp (FB/IG/TW)   │
                         │  · odoo-mcp (ERP/JSON-RPC)  │
                         └────────────────────────────┘
```

---

## Tier Achievements

### Bronze ✅ 100%
- `Dashboard.md` — real-time business status dashboard
- `Company_Handbook.md` — rules of engagement for the AI
- Folder structure: `Needs_Action/`, `Done/`, `Inbox/`, `Plans/`, `Logs/`
- Gmail watcher + filesystem watcher
- Claude Code read/write integration throughout
- Agent Skills: `task-triage`, `file-handler`

### Silver ✅ 100%
- LinkedIn auto-posting for business lead generation (live post confirmed)
- Plan.md reasoning loop (`Plans/PLAN_techcorp_rfp_response.md`)
- HITL approval workflow: `Pending_Approval/` → `Approved/` → execution
- Multiple watchers: `gmail_watcher.py` + `filesystem_watcher.py`
- One working MCP server (email-mcp for Gmail)
- Scheduling via Ralph Wiggum autonomous loop
- Agent Skills: `email-drafter`, `social-linkedin-poster`, `plan-creator`

### Gold ✅ 100%
- Full cross-domain integration: email + social + accounting + finance
- **Odoo Community** accounting via JSON-RPC MCP server (invoices, payments, reports)
- **Facebook** posting live via Playwright browser automation
- **Instagram** posting live with branded 1080×1080 image (Pillow-generated)
- **Twitter/X** posting via tweepy API
- Social summaries generated per platform
- 4 MCP servers (email, browser, social, odoo)
- Weekly CEO Briefing skill + Weekly Audit Engine
- Error recovery: `process_monitor.py` watchdog with exponential backoff
- Audit logging: `Logs/YYYY-MM-DD.md`
- Ralph Wiggum loop (`ralph_wiggum.py` + `.claude/hooks/ralph_wiggum_stop.py`)
- Architecture documentation in `CLAUDE.md`, MCP_CONFIG.md, PHR history
- Agent Skills: `odoo-accounting`, `multi-social-poster`, `ceo-briefing-generator`, `weekly-audit-engine`

---

## Project Structure

```
AI Employee-/
├── Dashboard.md                  # Real-time business status
├── Company_Handbook.md           # AI rules of engagement
├── ralph_wiggum.py               # Autonomous task loop
├── post_now.py                   # Direct social posting engine
├── generate_ig_image.py          # Branded Instagram image generator
│
├── mcp-servers/
│   ├── email-mcp/server.py       # Gmail via Google API
│   ├── browser-mcp/server.py     # LinkedIn via Playwright
│   ├── social-mcp/server.py      # Facebook/Instagram/Twitter
│   └── odoo-mcp/server.py        # Odoo ERP via JSON-RPC
│
├── watchers/
│   ├── base_watcher.py           # Abstract watcher template
│   ├── gmail_watcher.py          # Gmail unread monitor
│   ├── filesystem_watcher.py     # Drop-folder file monitor
│   ├── process_monitor.py        # Watchdog with exponential backoff
│   └── run_watchers.py           # Start all watchers
│
├── .claude/
│   ├── agents/                   # Orchestrator + sub-agent definitions
│   ├── skills/                   # 12 Agent Skills (SKILL.md each)
│   └── hooks/ralph_wiggum_stop.py # Stop hook for autonomous loop
│
├── Needs_Action/                 # Incoming tasks (watchers write here)
├── In_Progress/                  # Claimed tasks (prevents double-work)
├── Pending_Approval/             # Awaiting human review
├── Approved/                     # Human-approved, ready to execute
├── Done/                         # Completed tasks
│   ├── Email/
│   └── Social/
├── Plans/                        # Plan.md reasoning artifacts
├── Briefings/                    # Weekly CEO briefing output
├── Logs/                         # Audit logs (YYYY-MM-DD.md)
├── Files/                        # Generated assets (images, etc.)
└── System/
    ├── Company_Handbook.md
    ├── QUICKSTART.md
    └── DEPLOYMENT.md
```

---

## Agent Skills (12 total)

| Skill | Purpose |
|-------|---------|
| `task-triage` | Classify and prioritize incoming Needs_Action items |
| `file-handler` | Process dropped files (PDF, CSV, text) |
| `email-drafter` | Draft professional emails, HITL before send |
| `social-linkedin-poster` | LinkedIn sales posts with approval workflow |
| `multi-social-poster` | FB + IG + Twitter + summary generation |
| `plan-creator` | Multi-step Plan.md breakdown with checkboxes |
| `odoo-accounting` | Odoo invoices, payments, journal entries via MCP |
| `ceo-briefing-generator` | Monday Morning CEO Briefing from all data sources |
| `weekly-audit-engine` | Collect revenue, tasks, costs, anomalies |
| `email-drafter` | Business email drafts with tone-matching |
| `task-triage` | Urgent triage + routing to correct sub-agent |
| `file-handler` | File intake, categorisation, summarisation |

---

## Setup

### Prerequisites

- Python 3.13+
- Claude Code (Pro subscription or API key)
- Playwright (`pip install playwright && playwright install chromium`)
- Pillow (`pip install pillow`)
- Google Cloud project with Gmail API enabled
- Odoo Community 19+ (self-hosted, optional)

### 1. Clone and configure environment

```bash
git clone https://github.com/Aliyan707/AI-Employee.git
cd "AI Employee-"
```

Create `.env` files for each MCP server (never commit these):

**`mcp-servers/browser-mcp/.env`**
```bash
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password
HEADLESS=false
BROWSER_TIMEOUT=60000
VAULT_PATH=C:/path/to/AI Employee-
```

**`mcp-servers/social-mcp/.env`**
```bash
Facebook_EMAIL=your@email.com
Facebook_PASSWORD=your_password
Instagram__EMAIL=your@email.com
Instagram_PASSWORD=your_password
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...
HEADLESS=false
```

**`mcp-servers/email-mcp/.env`**
```bash
GMAIL_CREDENTIALS_PATH=path/to/credentials.json
GMAIL_TOKEN_PATH=path/to/token.json
```

**`mcp-servers/odoo-mcp/.env`**
```bash
ODOO_URL=http://localhost:8069
ODOO_DB=your_db
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password
```

### 2. Install Python dependencies

```bash
pip install playwright pillow python-dotenv mcp tweepy google-api-python-client google-auth-oauthlib
playwright install chromium
```

### 3. Start watchers

```bash
python watchers/run_watchers.py
```

### 4. Start the Ralph Wiggum autonomous loop

```bash
python ralph_wiggum.py
```

Or run Claude Code with the orchestrator:

```bash
claude --dangerously-skip-permissions
```

---

## Posting to Social Media

The primary posting engine is `post_now.py` (direct Playwright, no MCP required):

```bash
# Post to LinkedIn
python post_now.py linkedin Approved/Social/MY_POST.md

# Post to Facebook
python post_now.py facebook Approved/Social/MY_POST.md

# Post to Instagram (requires image_url in frontmatter)
python post_now.py instagram Approved/Social/MY_POST.md

# Post to Twitter/X
python post_now.py twitter Approved/Social/MY_POST.md
```

### Social Post File Format

```markdown
---
platform: linkedin
post_type: sales_promotion
sensitivity: medium
requires_hitl: true
timestamp: 2026-02-20T21:00:00+05:00
---

Your post content here...

#KarachiBusiness #AIEmployee #Automation
```

---

## Human-in-the-Loop (HITL) Workflow

All sensitive actions require human approval before execution:

```
1. AI drafts action → Pending_Approval/ACTION.md
2. Human reviews dashboard (Dashboard.md)
3. Human moves file to Approved/
4. Agent detects file → executes via MCP
5. Result logged → file moved to Done/
```

**Auto-approve thresholds (Company_Handbook.md):**
- Emails to known contacts ✅
- Reading/creating files ✅

**Always require approval:**
- Any payment (all amounts)
- Social media posts
- New email contacts
- Odoo invoice posting

---

## Ralph Wiggum (Autonomous Loop)

The Stop hook (`ralph_wiggum_stop.py`) intercepts Claude's exit and re-injects the prompt until a task file lands in `Done/`:

```
Claude starts task
     ↓
Claude tries to exit
     ↓
Stop hook: Is task in Done/?
  NO → re-inject prompt (keep working)
  YES → allow exit (task complete)
```

Register the hook in `.claude/settings.json`:
```json
{
  "hooks": {
    "Stop": [{ "matcher": "", "hooks": [{"type": "command", "command": "python .claude/hooks/ralph_wiggum_stop.py"}] }]
  }
}
```

---

## Watchdog Process Monitor

`watchers/process_monitor.py` keeps all watcher scripts alive with exponential backoff restart:

```bash
python watchers/process_monitor.py
```

Monitors: `gmail_watcher`, `filesystem_watcher`. Restarts on crash. Logs all events to `Dashboard.md`.

---

## Weekly CEO Briefing

Triggers every Sunday at 18:00 PKT. Generates `Briefings/YYYY-MM-DD.md` covering:

- Revenue MTD vs target
- Completed tasks
- Bottlenecks (tasks overdue)
- Social media performance
- Odoo accounting summary
- Proactive cost-optimization suggestions

Run manually:
```bash
# In Claude Code session:
/ceo-briefing-generator
```

---

## Security

- All credentials in `.env` files (never committed — `.gitignore` enforced)
- Session cookies stored locally (`linkedin-session/`, `fb-session/`, `instagram-session/`)
- HITL mandatory for every external write action
- Audit trail in `Logs/YYYY-MM-DD.md` for every action
- Approval files expire after 24 hours (re-approval required)
- No secrets ever enter the Obsidian vault markdown files

---

## Credential Handling (Security Disclosure)

| Secret | Storage | Rotation |
|--------|---------|----------|
| LinkedIn password | `mcp-servers/browser-mcp/.env` | Monthly |
| Facebook/Instagram password | `mcp-servers/social-mcp/.env` | Monthly |
| Twitter API keys | `mcp-servers/social-mcp/.env` | Quarterly |
| Gmail OAuth token | `mcp-servers/email-mcp/token.json` | Auto-refresh |
| Odoo credentials | `mcp-servers/odoo-mcp/.env` | Monthly |

All `.env` files and session directories are in `.gitignore`.

---

## Hackathon Tier Declaration

**Tier: Gold**

| Tier | Status |
|------|--------|
| Bronze | ✅ 100% |
| Silver | ✅ 100% |
| Gold | ✅ 100% |
| Platinum | Not attempted |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Reasoning engine | Claude Code (claude-sonnet-4-6) |
| Vault / dashboard | Obsidian (local Markdown) |
| Browser automation | Playwright (Python) |
| Email | Google Gmail API (`google-api-python-client`) |
| Twitter/X | tweepy v4 |
| ERP | Odoo Community 19+ (JSON-RPC) |
| Image generation | Pillow (PIL) |
| MCP framework | `mcp` PyPI (FastMCP) |
| Process management | Custom `process_monitor.py` + PM2-compatible |
| Config | `python-dotenv` |

---

## Author

**Aliyan** — Karachi, Pakistan
GitHub: [github.com/Aliyan707/AI-Employee](https://github.com/Aliyan707/AI-Employee)

---

*Built for the Personal AI Employee Hackathon 0 — Panaversity 2026*
