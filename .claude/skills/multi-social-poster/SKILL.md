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

## Workflow
1. Determine platform(s) from task
2. Generate content:
   - FB/IG: longer + image suggestion
   - X: <280 chars + link/hashtags
3. Draft + preview → Pending_Approval/SOCIAL_[platform]_[id].md
4. On Approved/ → call browser-mcp (navigate, fill, post)
5. After post: create summary file Social/Summary_[date].md
