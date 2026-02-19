# Claude Code MCP Configuration — Gold Tier AI Employee

Add the following to `%APPDATA%\Claude\claude_desktop_config.json`
(Windows path: `C:\Users\Cs\AppData\Roaming\Claude\claude_desktop_config.json`).

**After editing: restart Claude Code to load the new MCP servers.**

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\email-mcp\\server.py"],
      "env": {
        "VAULT_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-",
        "GMAIL_CREDENTIALS_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\email-mcp\\gmail-credentials.json",
        "GMAIL_TOKEN_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\email-mcp\\gmail-token.json"
      }
    },
    "browser-mcp": {
      "command": "python",
      "args": ["C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\browser-mcp\\server.py"],
      "env": {
        "VAULT_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-",
        "LINKEDIN_EMAIL": "YOUR-LINKEDIN-EMAIL",
        "LINKEDIN_PASSWORD": "YOUR-LINKEDIN-PASSWORD",
        "LINKEDIN_SESSION_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\browser-mcp\\linkedin-session",
        "HEADLESS": "true",
        "BROWSER_TIMEOUT": "30000"
      }
    },
    "social-mcp": {
      "command": "python",
      "args": ["C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\social-mcp\\server.py"],
      "env": {
        "VAULT_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-",
        "FB_PAGE_ID": "YOUR-FACEBOOK-PAGE-ID",
        "FB_PAGE_ACCESS_TOKEN": "YOUR-FACEBOOK-PAGE-ACCESS-TOKEN",
        "IG_USER_ID": "YOUR-INSTAGRAM-BUSINESS-ID",
        "IG_ACCESS_TOKEN": "YOUR-INSTAGRAM-ACCESS-TOKEN",
        "TW_BEARER_TOKEN": "YOUR-TWITTER-BEARER-TOKEN",
        "TW_API_KEY": "YOUR-TWITTER-API-KEY",
        "TW_API_SECRET": "YOUR-TWITTER-API-SECRET",
        "TW_ACCESS_TOKEN": "YOUR-TWITTER-ACCESS-TOKEN",
        "TW_ACCESS_SECRET": "YOUR-TWITTER-ACCESS-SECRET"
      }
    },
    "odoo-mcp": {
      "command": "python",
      "args": ["C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\odoo-mcp\\server.py"],
      "env": {
        "VAULT_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-"
      }
    }
  }
}
```

## Tools Available After Configuration

| Server | Tool | Description |
|--------|------|-------------|
| email-mcp | `send_email` | Send approved email via Gmail API |
| browser-mcp | `post_to_linkedin` | Post approved content to LinkedIn |
| social-mcp | `post_to_facebook` | Post to Facebook Page via Graph API |
| social-mcp | `post_to_instagram` | Post to Instagram Business via Graph API |
| social-mcp | `post_to_twitter` | Post tweet via Twitter API v2 |
| social-mcp | `get_social_summary` | Aggregate recent post stats |
| odoo-mcp | `odoo_create_draft_invoice` | Draft invoice in Odoo |
| odoo-mcp | `odoo_confirm_invoice` | Confirm/post invoice (HITL required) |
| odoo-mcp | `odoo_search_invoices` | Search invoices (read-only) |

## Credential Setup Status

| Service | Status |
|---------|--------|
| Gmail API | ⏳ Needs `gmail-credentials.json` from Google Cloud |
| LinkedIn | ⏳ Needs email/password in env + first-run 2FA |
| Facebook | ⏳ Needs FB_PAGE_ID + FB_PAGE_ACCESS_TOKEN |
| Instagram | ⏳ Needs IG_USER_ID + IG_ACCESS_TOKEN |
| Twitter/X | ⏳ Needs all 5 TW_* credentials |
| Odoo | ✅ Configured (see mcp-servers/odoo-mcp/.env) |

## LinkedIn First-Run (2FA Setup)
```bash
# Set HEADLESS=false in env, then run:
cd mcp-servers/browser-mcp
python server.py
# Complete 2FA in browser window that opens
# Session saved to linkedin-session/
# Then set HEADLESS=true and restart Claude Code
```
