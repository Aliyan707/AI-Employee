# Silver-Tier AI Employee Setup Guide

**Status**: Both MCP servers implemented and dependencies installed ✅
**MVP Ready**: Email automation + LinkedIn posting
**Estimated Setup Time**: 20-30 minutes

## Quick Start Overview

You now have two MCP servers ready for integration:

1. **email-mcp**: Gmail automation (send emails via Gmail API)
2. **browser-mcp**: LinkedIn automation (post via Playwright browser automation)

## Prerequisites Checklist

- [ ] Node.js v18+ installed ✅ (confirmed)
- [ ] npm installed ✅ (confirmed)
- [ ] Gmail account with API access (requires Google Cloud Console setup)
- [ ] LinkedIn account credentials
- [ ] Claude Code CLI installed

## Setup Steps

### Step 1: Configure Gmail API (email-mcp)

1. **Create Google Cloud Project**:
   - Go to https://console.cloud.google.com/
   - Create new project: "AI Employee Email"
   - Enable Gmail API for the project

2. **Create OAuth 2.0 Credentials**:
   - Navigate to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Email MCP Server"
   - Download JSON file

3. **Save Credentials**:
   ```bash
   # Move downloaded file to:
   C:\Users\Cs\Desktop\AI Employee-\mcp-servers\email-mcp\gmail-credentials.json
   ```

4. **First-time Authorization** (generates token):
   ```bash
   cd "mcp-servers/email-mcp"
   node index.js
   # Browser will open for OAuth consent
   # Approve access
   # Token saved to gmail-token.json automatically
   ```

### Step 2: Configure LinkedIn Credentials (browser-mcp)

1. **Edit .env file**:
   ```bash
   # Open: mcp-servers/browser-mcp/.env
   # Replace these lines with your actual credentials:
   LINKEDIN_EMAIL=your-actual-email@example.com
   LINKEDIN_PASSWORD=your-actual-password
   ```

2. **If you have 2FA enabled**:
   ```bash
   # Set headless mode to false for first login:
   HEADLESS=false

   # Run browser-mcp once manually
   cd "mcp-servers/browser-mcp"
   node index.js

   # Complete 2FA in the visible browser window
   # Session will be saved for future use
   # Then set HEADLESS=true again
   ```

### Step 3: Configure Claude Code MCP Integration

Add both servers to your Claude Code configuration:

**File**: `~/.config/claude-code/mcp.json` (or `%APPDATA%\Claude Code\mcp.json` on Windows)

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "node",
      "args": ["C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\email-mcp\\index.js"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\email-mcp\\gmail-credentials.json",
        "GMAIL_TOKEN_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\email-mcp\\gmail-token.json",
        "VAULT_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-",
        "LOG_LEVEL": "info"
      }
    },
    "browser-mcp": {
      "command": "node",
      "args": ["C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\browser-mcp\\index.js"],
      "env": {
        "LINKEDIN_EMAIL": "your-email@example.com",
        "LINKEDIN_PASSWORD": "your-password",
        "LINKEDIN_SESSION_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\browser-mcp\\linkedin-session",
        "VAULT_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-",
        "HEADLESS": "true",
        "BROWSER_TIMEOUT": "30000"
      }
    }
  }
}
```

**CRITICAL**: Update the LinkedIn credentials in the mcp.json file above!

### Step 4: Restart Claude Code

```bash
# Restart Claude Code to load the MCP servers
# The servers will start automatically when Claude Code launches
```

### Step 5: Verify Installation

Create test files to verify both servers work:

**Test Email** (`Approved/EMAIL_test.md`):

```markdown
---
to: your-test-recipient@example.com
from: your-gmail@example.com
subject: Test Email from AI Employee
sensitivity: low
requires_hitl: false
timestamp: 2026-02-15T12:00:00+05:00
---

Hello,

This is a test email from the AI Employee system.

Best regards,
Aliyan
Karachi, Pakistan
```

**Test LinkedIn Post** (`Approved/SOCIAL_linkedin_test.md`):

```markdown
---
platform: linkedin
post_type: sales_promotion
sensitivity: medium
requires_hitl: true
timestamp: 2026-02-15T12:00:00+05:00
---

🚀 Exciting news for Karachi businesses!

Are you spending hours daily on email management? Our AI Employee system automates email drafting, LinkedIn posting, and task planning—while keeping you in full control with human-in-the-loop approval.

✅ Save 5-8 hours/day
✅ Professional responses every time
✅ Complete audit trail
✅ 24/7 automation

Interested in transforming your business operations? Let's connect!

#AIEmployee #KarachiBusiness #FreelanceAI #Automation #Pakistan
```

**From Claude Code, run**:

```javascript
// Test email sending
await mcp.call_tool('send_email', {
  file_path: 'Approved/EMAIL_test.md'
});

// Test LinkedIn posting
await mcp.call_tool('post_to_linkedin', {
  file_path: 'Approved/SOCIAL_linkedin_test.md'
});
```

## Vault Structure

Ensure these directories exist:

```
C:\Users\Cs\Desktop\AI Employee-\
├── Needs_Action/
│   ├── Email/
│   └── Comms/
├── In_Progress/
│   ├── Email/
│   ├── Comms/
│   └── Planner/
├── Pending_Approval/
├── Approved/
├── Done/
│   ├── Email/
│   └── Social/
├── Plans/
├── Logs/
└── Dashboard.md
```

Create missing directories:

```bash
mkdir -p "Needs_Action/Email"
mkdir -p "Needs_Action/Comms"
mkdir -p "In_Progress/Email"
mkdir -p "In_Progress/Comms"
mkdir -p "In_Progress/Planner"
mkdir -p "Pending_Approval"
mkdir -p "Approved"
mkdir -p "Done/Email"
mkdir -p "Done/Social"
mkdir -p "Plans"
mkdir -p "Logs"
touch "Dashboard.md"
```

## Security Checklist

- [ ] `.env` files are in `.gitignore` ✅
- [ ] `gmail-credentials.json` and `gmail-token.json` are in `.gitignore` ✅
- [ ] `linkedin-session/` folder is in `.gitignore` ✅
- [ ] Never commit credentials to git
- [ ] Use environment variables for sensitive data
- [ ] Review `.gitignore` files in both MCP directories

## Troubleshooting

### email-mcp Issues

**"credentials.json not found"**:
- Download OAuth 2.0 credentials from Google Cloud Console
- Save as `mcp-servers/email-mcp/gmail-credentials.json`

**"Token expired or invalid"**:
- Delete `gmail-token.json`
- Run `node index.js` manually to re-authorize

**"Gmail API not enabled"**:
- Go to Google Cloud Console
- Enable Gmail API for your project

### browser-mcp Issues

**"Login failed"**:
- Verify LinkedIn credentials in `.env`
- If 2FA enabled, set `HEADLESS=false` and login manually first
- Check `linkedin-session/` folder permissions

**"Chromium not installed"**:
- Run: `npm run install-browsers` in `mcp-servers/browser-mcp/`

**"Content validation failed"**:
- Ensure post is 100-250 words
- Include hashtags (#)
- Check approval timestamp is <24 hours old

## Next Steps

After setup is complete:

1. **Test both MCP servers** with the test files above
2. **Set up Skills** (email-drafter, social-linkedin-poster, etc.)
3. **Deploy orchestrator** to start the full AI Employee system
4. **Monitor Dashboard.md** for real-time status
5. **Review Logs/** for audit trail

## Additional Resources

- **email-mcp**: See `mcp-servers/email-mcp/README.md` for detailed Gmail API setup
- **browser-mcp**: See `mcp-servers/browser-mcp/README.md` for LinkedIn automation details
- **MCP Quickstart**: See `mcp-servers/QUICKSTART.md` for 5-minute setup guide
- **MVP Status**: See `MVP_STATUS.md` for implementation status and metrics

## Support

For issues or questions:
1. Check README.md files in each MCP server directory
2. Review Troubleshooting section above
3. Check MCP server logs in console output
4. Verify vault structure and file permissions

---

**Silver-Tier AI Employee System**
**Author**: Aliyan
**Location**: Karachi, Pakistan
**Timezone**: PKT (UTC+5)
**Status**: MVP Ready ✅
