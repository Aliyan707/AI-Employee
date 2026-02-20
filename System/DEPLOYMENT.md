# Silver-Tier AI Employee - Deployment Guide

## Prerequisites

### 1. Software Requirements
- Claude Code CLI installed
- Python 3.11+ (for watchers)
- tmux or terminal multiplexer
- Git (for version control)
- Node.js v24+ (for MCP servers)
- Gmail API credentials (for email monitoring)

### 2. Python Watcher Setup

```bash
cd watchers

# Install dependencies
pip install -r requirements.txt

# Configure watchers
cp config.env.example config.env
# Edit config.env with your paths:
#   VAULT_PATH=/path/to/AI_Employee_Vault
#   GMAIL_CREDENTIALS_PATH=/path/to/gmail-credentials.json
#   DROP_FOLDER_PATH=/path/to/drop-folder
```

**Gmail API Setup** (for Gmail watcher):
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as `gmail-credentials.json`

See `watchers/README.md` for detailed setup instructions.

### 3. MCP Server Configuration

Create or edit `~/.config/claude-code/mcp.json`:
```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["-m", "email_mcp_server"],
      "env": {
        "GMAIL_CREDENTIALS": "/path/to/gmail-credentials.json"
      }
    },
    "browser-mcp": {
      "command": "python",
      "args": ["-m", "browser_mcp_server"],
      "env": {
        "LINKEDIN_SESSION": "/path/to/linkedin-session.json"
      }
    }
  }
}
```

### 3. Vault Structure Initialization

```bash
cd ~/AI_Employee_Vault  # or your vault location

# Create folder structure
mkdir -p Needs_Action/{Email,Comms}
mkdir -p In_Progress/{email-sub-agent,comms-sub-agent,planner-sub-agent}
mkdir -p Pending_Approval Approved
mkdir -p Done/{Email,Social,Plans}
mkdir -p Plans Logs System

# Copy System prompts (already created in System/)
# Ensure .claude/skills/ has all Silver skills

# Create initial files
touch Dashboard.md Company_Handbook.md

# Initialize git (recommended)
git init
git add .
git commit -m "Initial Silver-tier vault structure"
```

## Launch Sequence

### Terminal 0: Watchers (Start First)

```bash
cd watchers

# Option 1: Run with Python launcher (all watchers together)
python run_watchers.py

# Option 2: Run watchers individually for testing
python gmail_watcher.py /path/to/vault /path/to/gmail-credentials.json
python filesystem_watcher.py /path/to/vault /path/to/drop-folder

# Option 3: Production deployment with PM2 (recommended)
pm2 start run_watchers.py --name ai-employee-watchers --interpreter python3

# Monitor watcher status
pm2 logs ai-employee-watchers
```

**Note**: Watchers must be running BEFORE starting Claude Code agents. Watchers create files → Agents process files.

### Terminal 1: Main Orchestrator
```bash
cd ~/AI_Employee_Vault

# Simple loop approach
while true; do
  claude --cwd . --prompt-file System/silver-main.md
  sleep 45  # 45-second cycle
done
```

### Terminal 2: Email Sub-Agent
```bash
cd ~/AI_Employee_Vault

# Using ralph-loop (if available)
ralph-loop "Follow System/Email-Sub.md" \
  --completion-promise "EMAIL_CYCLE_DONE" \
  --max-iterations 12

# OR simple loop
while true; do
  claude --cwd . --prompt-file System/Email-Sub.md
  sleep 60  # 1-minute cycle
done
```

### Terminal 3: Comms Sub-Agent
```bash
cd ~/AI_Employee_Vault

while true; do
  claude --cwd . --prompt-file System/Comms-Sub.md
  sleep 90  # 90-second cycle (slower for LinkedIn posting)
done
```

### Terminal 4: Planner Sub-Agent
```bash
cd ~/AI_Employee_Vault

ralph-loop "Follow System/Planner-Sub.md" \
  --completion-promise "PLAN_CYCLE_COMPLETE" \
  --max-iterations 20

# OR simple loop
while true; do
  claude --cwd . --prompt-file System/Planner-Sub.md
  sleep 120  # 2-minute cycle
done
```

## TMUX Deployment (Recommended)

Use tmux for managing all agents in one session. See System/silver-launch.sh script.

## Test Sequence

### Test 1: Watcher → Email Processing
1. **Start watchers** (Terminal 0)
2. Send yourself an important email with keyword "urgent"
3. **Watch for**: `EMAIL_*.md` appears in `Needs_Action/Email/` (within 2 minutes)
4. **Start Email Sub-Agent** (Terminal 2)
5. **Watch flow**: Needs_Action/Email/ → In_Progress/email-sub-agent/ → Pending_Approval/ → (human moves to) Approved/ → Done/Email/SENT_*
6. **Verify**: Dashboard.md updated, Logs/YYYY-MM-DD.md contains JSON entry

### Test 2: File Drop Processing
1. **Ensure watchers running** (Terminal 0)
2. Drop a PDF file into configured drop folder
3. **Watch for**: `FILE_*.md` appears in `Needs_Action/` (immediate)
4. **Start Main Orchestrator** (Terminal 1) - it will process the file
5. **Verify**: File copied to vault, metadata created, logged

### Test 3: LinkedIn Post Generation
Trigger post generation at 10 AM or 3 PM PKT:
1. **Start Comms Sub-Agent** (Terminal 3)
2. **Watch for**: `SOCIAL_linkedin_*.md` appears in `Pending_Approval/` at scheduled time
3. **Human approval**: Move to `Approved/`
4. **Verify**: Posted to LinkedIn via browser-mcp, moved to `Done/Social/POSTED_*`

### Test 4: Multi-Step Plan
1. Drop a complex task file in `Needs_Action/`
2. **Start Planner Sub-Agent** (Terminal 4)
3. **Verify**: `Plans/PLAN_*.md` created with 3-8 checkboxes
4. **Watch**: Plan updates as sub-steps complete (checkboxes marked)

## Monitoring

### Real-Time Dashboard
```bash
watch -n 5 'cat Dashboard.md'
```

### Logs Tail
```bash
tail -f Logs/$(date +%Y-%m-%d).md | jq .
```

### Active Work
```bash
ls -lah In_Progress/*/
ls -lah Pending_Approval/
```

## Production Checklist

### Infrastructure
- [ ] Vault structure initialized (Needs_Action/, In_Progress/, Pending_Approval/, Approved/, Done/, Plans/, Logs/)
- [ ] Dashboard.md and Company_Handbook.md created
- [ ] Constitution v2.0.0 in .specify/memory/constitution.md
- [ ] Git repository initialized

### Agent Skills
- [ ] All .claude/skills/*.md files present (email-drafter, social-linkedin-poster, plan-creator)
- [ ] Agent prompts created (System/silver-main.md, Email-Sub.md, Comms-Sub.md, Planner-Sub.md)

### Watchers (New)
- [ ] Python dependencies installed (`pip install -r watchers/requirements.txt`)
- [ ] Gmail API credentials configured
- [ ] Drop folder created
- [ ] Watcher config.env created and populated
- [ ] Watchers tested standalone
- [ ] Watchers running via PM2 or launcher script

### MCP Servers
- [ ] email-mcp configured in mcp.json
- [ ] browser-mcp configured in mcp.json (if using LinkedIn posting)
- [ ] MCP servers tested with Claude Code

### Testing
- [ ] Test sequence completed successfully (see below)
- [ ] Watcher → Agent → HITL → MCP flow validated
- [ ] Monitoring dashboards working
- [ ] Logs being written correctly

## Expected Performance

- **Watcher detection**:
  - Gmail: Within 2 minutes of email arrival
  - File drops: Immediate (event-driven)
- **Email drafts**: Generated within 2 minutes of file appearing
- **LinkedIn posts**: 1-2 per day at scheduled times (10 AM, 3 PM PKT)
- **Plan updates**: Every 2-5 minutes for active plans
- **Agent cycles**:
  - Main Orchestrator: Every 45 seconds
  - Email Sub-Agent: Every 60 seconds
  - Comms Sub-Agent: Every 90 seconds
  - Planner Sub-Agent: Every 120 seconds
- **HITL approval**: Human-dependent (check Pending_Approval/)

## Architecture Diagram (With Watchers)

```
External Sources (Gmail, File System)
         ↓
    WATCHERS (Python - Layer 0)
    - Gmail Watcher (120s cycle)
    - FileSystem Watcher (event-driven)
         ↓
    Vault/Needs_Action/
         ↓
    CLAUDE CODE AGENTS (Layer 1)
    - Main Orchestrator (45s)
    - Email Sub-Agent (60s)
    - Comms Sub-Agent (90s)
    - Planner Sub-Agent (120s)
         ↓
    Pending_Approval/ → (Human) → Approved/
         ↓
    MCP SERVERS (Layer 2)
    - email-mcp (send emails)
    - browser-mcp (post to LinkedIn)
         ↓
    Done/ (completed actions)
```

## Troubleshooting

### Watchers Not Detecting

**Gmail Watcher**:
- Check credentials: `ls /path/to/gmail-credentials.json`
- Verify Gmail API enabled in Google Cloud Console
- Check logs: `tail -f Vault/Logs/gmail_watcher.log`
- Test query: Send yourself an email marked as important

**FileSystem Watcher**:
- Check drop folder exists: `ls /path/to/drop-folder`
- Verify permissions: `ls -la /path/to/drop-folder`
- Check logs: `tail -f Vault/Logs/filesystem_watcher.log`
- Test: Drop a file manually

### Agents Not Processing Files

- Verify watchers are running: `pm2 list` or check terminal
- Check file appeared in Needs_Action/: `ls Vault/Needs_Action/Email/`
- Verify agent is running and cycling
- Check agent logs for errors
- Ensure no permission issues on vault folders

### MCP Calls Failing

- Verify MCP servers configured in `~/.config/claude-code/mcp.json`
- Test MCP connection: `claude --list-mcp-servers`
- Check MCP server is running (if separate process)
- Review error logs in Pending_Approval/ files (error notes appended)
