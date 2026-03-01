# Social MCP Server

Gold-tier AI Employee — Facebook, Instagram, and Twitter/X posting via MCP.

## Tools

| Tool | Platform | API |
|------|----------|-----|
| `post_to_facebook` | Facebook Page | Meta Graph API v19 |
| `post_to_instagram` | Instagram Business | Meta Graph API v19 |
| `post_to_twitter` | Twitter/X | API v2 via tweepy |
| `get_social_summary` | All platforms | Reads Done/Social/ |

## Setup

### 1. Install dependencies
```bash
cd mcp-servers/social-mcp
pip install -r requirements.txt
```

### 2. Configure credentials
```bash
cp .env.example .env
# Edit .env with your API credentials
```

### 3. Add to Claude Code mcp.json

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "social-mcp": {
      "command": "python",
      "args": ["C:\\Users\\Cs\\Desktop\\AI Employee-\\mcp-servers\\social-mcp\\server.py"],
      "env": {
        "VAULT_PATH": "C:\\Users\\Cs\\Desktop\\AI Employee-",
        "FB_PAGE_ID": "your-page-id",
        "FB_PAGE_ACCESS_TOKEN": "your-token",
        "IG_USER_ID": "your-ig-id",
        "IG_ACCESS_TOKEN": "your-ig-token",
        "TW_API_KEY": "your-key",
        "TW_API_SECRET": "your-secret",
        "TW_ACCESS_TOKEN": "your-access-token",
        "TW_ACCESS_SECRET": "your-access-secret"
      }
    }
  }
}
```

## File Format

Create approved social post files in `Approved/` with this format:

### Facebook
```markdown
---
platform: facebook
link: https://optional-link.com
timestamp: 2026-02-20T10:00:00+05:00
---

Your Facebook post content here. Can be longer and include emojis 🚀

#hashtag1 #hashtag2
```

### Instagram
```markdown
---
platform: instagram
image_url: https://your-public-image.com/photo.jpg
timestamp: 2026-02-20T10:00:00+05:00
---

Your Instagram caption here. Instagram requires an image_url.

#karachi #business #pakistan
```

### Twitter/X
```markdown
---
platform: twitter
timestamp: 2026-02-20T10:00:00+05:00
---

Your tweet here (max 280 chars). Longer content is auto-truncated.
#AI #Pakistan
```

## Credential Setup Guides

### Facebook Page Access Token
1. Go to [Meta for Developers](https://developers.facebook.com)
2. Create an App → Business type
3. Add "Facebook Login" and "Pages" products
4. Go to Graph API Explorer → select your app + page
5. Add permission: `pages_manage_posts`, `pages_read_engagement`
6. Generate token → use as `FB_PAGE_ACCESS_TOKEN`
7. Get your Page ID from Page Settings → About

### Instagram Business Account
1. Convert your Instagram to a Business or Creator account
2. Connect it to your Facebook Page
3. In your Meta App, add Instagram Graph API product
4. Get Instagram User ID via: `GET /me?fields=id,name&access_token=<token>`
5. Use same token as `IG_ACCESS_TOKEN`

### Twitter / X API
1. Apply at [developer.twitter.com](https://developer.twitter.com)
2. Create a project and app
3. Set App Permissions to "Read and Write"
4. Generate OAuth 1.0a User Access Tokens
5. Copy all 5 values to `.env`

## Security
- Never commit `.env` to git (already in `.gitignore`)
- All tokens are environment variables only
- 24-hour approval expiry prevents stale posts
