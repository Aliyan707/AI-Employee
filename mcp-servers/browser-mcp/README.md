# Browser MCP Server (Playwright)

MCP (Model Context Protocol) server for LinkedIn posting via Playwright browser automation. Integrates with the Silver-tier AI Employee vault-based approval workflow.

## Features

- ✅ Playwright browser automation for LinkedIn
- ✅ Persistent session management (saves login state)
- ✅ Automated LinkedIn posting with content validation
- ✅ Pre-execution checklist (content length, hashtags, approval age)
- ✅ Success handling (move to Done/Social/, log, update Dashboard)
- ✅ Failure handling (move back to Pending_Approval/ with error)
- ✅ Complete audit trail (JSON logs + Dashboard updates)
- ✅ HITL approval enforcement (only posts from Approved/ folder)

## Prerequisites

1. **Node.js** v18+ installed
2. **LinkedIn account** with email and password
3. **Vault structure** initialized (Approved/, Done/Social/, Logs/, Dashboard.md)
4. **Chromium browser** (installed automatically via Playwright)

## Installation

```bash
cd mcp-servers/browser-mcp

# Install dependencies
npm install

# Install Playwright browsers
npm run install-browsers

# Copy environment template
cp .env.example .env

# Edit .env with your LinkedIn credentials
nano .env
```

### Configure .env

```bash
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
LINKEDIN_SESSION_PATH=/path/to/linkedin-session
VAULT_PATH=/path/to/AI_Employee_Vault
HEADLESS=true
```

**Security Note**: LinkedIn credentials are stored in .env (excluded from git). Session cookies are saved in LINKEDIN_SESSION_PATH for reuse.

## Configuration in Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "browser-mcp": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-servers/browser-mcp/index.js"],
      "env": {
        "LINKEDIN_EMAIL": "your-email@example.com",
        "LINKEDIN_PASSWORD": "your-password",
        "LINKEDIN_SESSION_PATH": "/absolute/path/to/linkedin-session",
        "VAULT_PATH": "/absolute/path/to/AI_Employee_Vault",
        "HEADLESS": "true"
      }
    }
  }
}
```

**CRITICAL**: Use absolute paths!

## Usage

### From Claude Code Agent

The Comms Sub-Agent calls browser-mcp automatically when an approved LinkedIn post is ready:

```javascript
// Claude Code invokes via MCP protocol:
await mcp.call_tool('post_to_linkedin', {
  file_path: 'Approved/SOCIAL_linkedin_20260215.md'
});
```

### Test LinkedIn Post File Format

**Approved/SOCIAL_linkedin_test.md**:

```markdown
---
platform: linkedin
post_type: sales_promotion
sensitivity: medium
requires_hitl: true
timestamp: 2026-02-15T10:30:00+05:00
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

## Pre-Execution Checklist

browser-mcp validates before posting:

1. ✅ File exists in `Approved/` folder
2. ✅ Platform is `linkedin` in frontmatter
3. ✅ Content is 100-250 words
4. ✅ Hashtags present in content
5. ✅ Approval timestamp <24 hours old
6. ✅ No ERROR flags in file

If validation fails:
- File moved back to `Pending_Approval/`
- Error note appended to file
- Error logged to `Logs/YYYY-MM-DD.md`
- Dashboard flagged with error

## Success Workflow

When post publishes successfully:

1. **Move file**: `Approved/SOCIAL_*.md` → `Done/Social/POSTED_SOCIAL_*.md`
2. **Log success**: Append to `Logs/YYYY-MM-DD.md`:
   ```json
   {
     "timestamp": "2026-02-15T10:35:00+05:00",
     "agent": "browser-mcp",
     "action": "post_to_linkedin",
     "file": "SOCIAL_linkedin_20260215.md",
     "status": "completed",
     "metadata": {
       "platform": "linkedin",
       "word_count": 145,
       "result": "success"
     }
   }
   ```
3. **Update Dashboard**: Add line to Recent Activity:
   ```markdown
   - 2/15/2026, 10:35:00 PKT: [POSTED] LinkedIn post published successfully
   ```

## Failure Workflow

When posting fails:

1. **Move file back**: `Approved/SOCIAL_*.md` → `Pending_Approval/SOCIAL_*.md`
2. **Append error**: Add to file:
   ```markdown
   ## ERROR (browser-mcp)
   Failed to post to LinkedIn: Login required or network error
   Timestamp: 2026-02-15T10:35:00+05:00
   ```
3. **Log error**: Append to `Logs/YYYY-MM-DD.md`
4. **Flag Dashboard**: Add error line for human review

## Troubleshooting

### "Login required or network error"

**Problem**: LinkedIn session expired or credentials invalid

**Solution**:
1. Delete linkedin-session folder
2. Restart browser-mcp (will re-login)
3. Check LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env
4. If 2FA enabled, login manually first time:
   - Set HEADLESS=false in .env
   - Run browser-mcp
   - Complete 2FA when prompted
   - Session will be saved for future use

### "Content too short/long (X words, minimum 100/maximum 250)"

**Problem**: Post doesn't meet LinkedIn content guidelines

**Solution**:
1. Edit post content in Pending_Approval/
2. Ensure 100-250 words
3. Have human re-approve (move to Approved/)

### "Missing required hashtags"

**Problem**: Post must include hashtags for visibility

**Solution**:
1. Add hashtags to post: `#AIEmployee #KarachiBusiness #FreelanceAI`
2. Re-approve after editing

### "Approval expired (>24 hours old)"

**Problem**: Draft approved too long ago

**Solution**:
1. Move file back to Pending_Approval/
2. Human reviews again
3. Move to Approved/ with fresh timestamp

### Browser won't start

**Problem**: Playwright browsers not installed

**Solution**:
```bash
cd mcp-servers/browser-mcp
npm run install-browsers
```

## Security Considerations

1. **Never commit credentials**:
   - Add `.env` to `.gitignore` ✅ (already done)
   - Add `linkedin-session/` to `.gitignore` ✅
   - Store credentials securely

2. **Session security**:
   - linkedin-session folder contains cookies/auth tokens
   - Set restrictive permissions: `chmod 700 linkedin-session`
   - Don't share session folder

3. **HITL enforcement**:
   - browser-mcp ONLY posts from `Approved/` folder
   - Pre-execution checklist prevents bypass
   - No auto-post capability

4. **LinkedIn Terms of Service**:
   - This is automation for personal/business use
   - Don't spam or violate LinkedIn policies
   - Keep posting frequency reasonable (1-2 posts/day)

## Architecture Integration

```
Comms Sub-Agent (scheduled or triggered)
         ↓
Comms Sub-Agent invokes social-linkedin-poster skill
         ↓
  Pending_Approval/SOCIAL_linkedin_*.md (awaits human review)
         ↓
  Human reviews and moves to Approved/
         ↓
Comms Sub-Agent detects file in Approved/
         ↓
  📱 browser-mcp.post_to_linkedin() (THIS SERVER)
         ↓
  Playwright opens LinkedIn, posts content
         ↓
  Done/Social/POSTED_SOCIAL_*.md
```

## Headless vs Headed Mode

**Headless (HEADLESS=true)**: Browser runs invisibly in background
- Faster, no GUI
- Good for production 24/7 operation
- Can't see what browser is doing

**Headed (HEADLESS=false)**: Browser window visible
- Useful for debugging
- Can watch browser interactions
- Complete 2FA manually
- Good for initial setup

Set in .env:
```bash
HEADLESS=false  # Show browser window
HEADLESS=true   # Run invisibly
```

## Logs

browser-mcp logs to:
- **Console**: Real-time operation messages
- **Vault Logs**: `Logs/YYYY-MM-DD.md` (JSON audit trail)
- **Dashboard**: `Dashboard.md` Recent Activity

## Development

```bash
# Run in development mode with auto-reload
npm run dev

# Run with visible browser (for debugging)
HEADLESS=false npm start
```

## Known Limitations

- **LinkedIn UI changes**: If LinkedIn updates their UI, selectors may need updating
- **2FA**: First login may require manual intervention if 2FA enabled
- **Rate limiting**: LinkedIn may rate-limit if posting too frequently
- **Session expiry**: LinkedIn sessions expire periodically, requiring re-login

## License

MIT

---

**Part of**: Silver-tier AI Employee Multi-Agent System
**Dependencies**: Playwright, MCP SDK, Vault structure
**Integrates with**: Comms Sub-Agent, social-linkedin-poster skill
