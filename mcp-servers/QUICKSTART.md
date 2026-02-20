# MCP Servers - Quick Start Guide

Complete setup guide for email-mcp and browser-mcp servers for the Silver-tier AI Employee system.

## Prerequisites

- ✅ Node.js v18+ installed
- ✅ Gmail API credentials (OAuth 2.0)
- ✅ Watchers running (gmail_watcher.py creates OAuth token)
- ✅ Vault structure initialized

---

## Email MCP Setup (5 minutes)

### 1. Install Dependencies

```bash
cd mcp-servers/email-mcp
npm install
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your paths
nano .env
```

**Required .env values**:
```bash
GMAIL_CREDENTIALS_PATH=/path/to/gmail-credentials.json
GMAIL_TOKEN_PATH=/path/to/System/gmail_token.json  # Created by gmail_watcher
VAULT_PATH=/path/to/AI_Employee_Vault
```

### 3. Verify Gmail Token Exists

The gmail_watcher creates the OAuth token on first run:

```bash
# If token doesn't exist, run watcher first:
cd ../../watchers
python gmail_watcher.py /path/to/vault /path/to/gmail-credentials.json
# This will open browser for OAuth consent and save token
```

### 4. Test MCP Server

```bash
cd ../mcp-servers/email-mcp
npm start
# Should see: [email-mcp] Server ready and listening for requests
# Press Ctrl+C to stop
```

### 5. Configure in Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-servers/email-mcp/index.js"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/absolute/path/to/gmail-credentials.json",
        "GMAIL_TOKEN_PATH": "/absolute/path/to/System/gmail_token.json",
        "VAULT_PATH": "/absolute/path/to/AI_Employee_Vault"
      }
    }
  }
}
```

**CRITICAL**: Use absolute paths, not relative!

---

## Test Email Flow (End-to-End)

### 1. Create Test Email File

```bash
cd /path/to/AI_Employee_Vault

# Create test email in Approved/ (bypassing HITL for testing)
cat > Approved/EMAIL_test_001.md << 'EOF'
---
from: your-email@gmail.com
to: your-email@gmail.com
subject: Test Email from email-mcp
timestamp: $(date -u +"%Y-%m-%dT%H:%M:%S%z")
sensitivity: low
requires_hitl: true
---

This is a test email sent via email-mcp server.

If you receive this, email-mcp is working correctly!

Best regards,
AI Employee (email-mcp)
EOF
```

### 2. Trigger Email Sub-Agent

```bash
# In terminal, start Email Sub-Agent cycle once
claude --cwd . --prompt-file System/Email-Sub.md
```

The agent should:
1. Detect file in Approved/
2. Call email-mcp to send
3. Move file to Done/Email/SENT_EMAIL_test_001.md
4. Update Dashboard.md with success message
5. Log to Logs/YYYY-MM-DD.md

### 3. Verify Success

```bash
# Check email was moved to Done/
ls Done/Email/SENT_*

# Check Dashboard was updated
tail Dashboard.md

# Check logs
tail Logs/$(date +%Y-%m-%d).md

# Check your inbox for the test email!
```

---

## Production Deployment

### Option 1: Manual Agent Cycles

```bash
# Terminal 1: Email Sub-Agent
cd /path/to/vault
while true; do
  claude --cwd . --prompt-file System/Email-Sub.md
  sleep 60
done
```

### Option 2: PM2 Process Management

```bash
# Install PM2
npm install -g pm2

# Start agent
pm2 start --name email-sub-agent \
  --interpreter bash \
  --cwd /path/to/vault \
  -- -c "while true; do claude --cwd . --prompt-file System/Email-Sub.md; sleep 60; done"

# Monitor
pm2 logs email-sub-agent
pm2 list
```

---

## Troubleshooting

### "Gmail authentication required"

```bash
# Run gmail watcher to authenticate
cd watchers
python gmail_watcher.py /path/to/vault /path/to/gmail-credentials.json
```

### "Module not found: @modelcontextprotocol/sdk"

```bash
cd mcp-servers/email-mcp
npm install  # Re-install dependencies
```

### "File must be in Approved/ folder"

- Check file path is correct
- Ensure file is actually in Approved/ (not Pending_Approval/)
- Use relative path from vault root: `Approved/EMAIL_*.md`

### Email sent but file not moved to Done/

- Check vault permissions (agent needs write access)
- Check Done/Email/ directory exists
- Check logs for error: `tail Logs/$(date +%Y-%m-%d).md`

---

## Next Steps

1. ✅ email-mcp working → **MVP complete!**
2. ⏸️ browser-mcp (for LinkedIn) → Implement later (US2)
3. ✅ Start watchers → Automate email detection
4. ✅ Deploy agents → 24/7 email automation

---

## Complete MVP Workflow

```
1. Gmail receives email
        ↓
2. gmail_watcher detects → creates Needs_Action/Email/EMAIL_*.md
        ↓
3. Email Sub-Agent claims file → moves to In_Progress/email-sub-agent/
        ↓
4. Email Sub-Agent invokes email-drafter skill
        ↓
5. Draft created in Pending_Approval/EMAIL_*.md
        ↓
6. Human reviews and moves to Approved/
        ↓
7. Email Sub-Agent detects file in Approved/
        ↓
8. Email Sub-Agent calls email-mcp.send_email()
        ↓
9. email-mcp sends via Gmail API
        ↓
10. File moved to Done/Email/SENT_*.md
        ↓
11. Dashboard updated, logs created
```

**You now have production-ready email automation!** 🎉
