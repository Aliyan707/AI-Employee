---
name: multi-social-poster
description: Generate platform-appropriate posts for Facebook, Instagram, Twitter/X, draft in Pending_Approval/, post via browser-mcp after approval, generate activity summaries. Use for Social/ tasks or scheduled promotion.
---

# Multi-Social Poster Skill

## When to use
Triggered on Needs_Action/Social/* or weekly content schedule.

## Core Rules
- Tailor content: LinkedIn/FB professional, IG visual/story, X concise
- Always HITL approval
- Include Karachi/Sindh/local hashtags when relevant
- Post max 3×/day across platforms
- Summarize: engagement stats if watcher provides, or just "Posted successfully"

## Platforms & MCP Tools

| Platform | MCP Server | Tool | Notes |
|----------|-----------|------|-------|
| LinkedIn | browser-mcp | `post_to_linkedin` | Session-based, Playwright |
| Facebook | social-mcp | `post_to_facebook` | Graph API, Page token |
| Instagram | social-mcp | `post_to_instagram` | Requires `image_url:` in frontmatter |
| Twitter/X | social-mcp | `post_to_twitter` | ≤280 chars, auto-truncated |

## Required Frontmatter Fields

Every approved social file must have:
```yaml
---
platform: linkedin | facebook | instagram | twitter
timestamp: 2026-02-20T10:00:00+05:00
# Instagram only:
image_url: https://public-url/image.jpg
# Facebook optional:
link: https://optional-link.com
---
```

## Workflow
1. Determine platform(s) from task
2. Generate platform-optimized content:
   - LinkedIn: professional, 150-300 words, 3-5 hashtags
   - Facebook: conversational, 50-200 words, link preview optional
   - Instagram: visual caption, 50-150 words, 5-10 hashtags, image_url required
   - Twitter/X: punchy, ≤280 chars, 2-3 hashtags
3. Draft → Pending_Approval/SOCIAL_[platform]_[id].md with correct frontmatter
4. On file in Approved/ → call the matching MCP tool for that platform
5. After post: create summary file Done/Social/Summary_[date].md with post IDs and stats
6. Call `social-mcp: get_social_summary(days=7)` for weekly performance data
