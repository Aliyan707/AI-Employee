---
id: 008
title: Social Posting Cycle Credential Diagnosis
stage: general
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 001-gold-tier-employee
user: Aliyan
command: social-sub-agent posting cycle (LinkedIn, Facebook, Instagram)
labels: ["social-media", "posting", "facebook", "linkedin", "instagram", "credential-failure", "diagnosis", "hitl"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - Pending_Approval/Social/INSTAGRAM_POST_20260220.md (created - Instagram draft)
  - Approved/Social/INSTAGRAM_POST_20260220.md (created then failed - moved back to Pending_Approval/Social/)
  - Approved/Social/FACEBOOK_POST_LIVE_TEST_20260220_210343.md (clean copy created for retry)
  - mcp-servers/social-mcp/server.py (modified - Facebook login selector fixed, JS click + session validation added)
  - Dashboard.md (modified - posting cycle report + updated next actions)
  - Pending_Approval/Social/LINKEDIN_POST_LIVE_TEST_20260220_210343.md (reorganized from root)
  - Pending_Approval/Social/FACEBOOK_POST_LIVE_TEST_20260220_210343.md (reorganized from root)
tests:
  - LinkedIn post attempted: FAILED (wrong password - LinkedIn rejects credentials)
  - Facebook post attempted: FAILED (password incorrect - confirmed via JS login test)
  - Instagram post attempted: FAILED (image required - platform limitation)
  - Facebook JS login approach: CONFIRMED WORKING APPROACH (but blocked by wrong password)
  - Facebook login button selector: DIAGNOSED (hidden input[type=submit], JS evaluate required)
---

## Prompt

The user wants to start the AI employee to automatically post on Facebook, LinkedIn, and Instagram.

**Approved posts ready to execute (Approved/Social/):**
1. `LINKEDIN_POST_LIVE_TEST_20260220_210343.md` - LinkedIn post about AI Employee business automation
2. `FACEBOOK_POST_LIVE_TEST_20260220_210343.md` - Facebook post about AI Employee
3. `FACEBOOK_POST_20260219_223159.md` - Older Facebook post
4. `TWITTER_POST_20260219_223159.md` - Twitter post
5. `TWITTER_POST_LIVE_TEST_20260220_210343.md` - Twitter thread

**Tasks assigned:**
1. Post LinkedIn via browser-mcp post_to_linkedin
2. Post Facebook via social-mcp post_to_facebook
3. Draft and post Instagram post
4. Update Dashboard.md
5. Generate summary

## Response snapshot

Full posting cycle executed. All three platform attempts failed due to credential issues:

**LinkedIn:** FAILED - "Wrong email or password" from LinkedIn authentication. Session expired and re-login rejected. Root cause: `LINKEDIN_PASSWORD` in `mcp-servers/browser-mcp/.env` is incorrect.

**Facebook:** FAILED - "The password you've entered is incorrect" from Facebook. Additionally diagnosed that Facebook's login button is a CSS-hidden `input[type="submit"]` (no `name` attribute), which was the previous selector failure. Fixed `server.py` to use `JS evaluate` click + `Return` key + session cookie validation. But login still fails due to wrong password. Root cause: `Facebook_PASSWORD` in `mcp-servers/social-mcp/.env` is incorrect.

**Instagram:** FAILED - Instagram requires an image for web posts. Text-only captions cannot be posted via the web interface without an image upload. Root cause: Platform limitation - `image_url` frontmatter field must be set and an image must be present.

**Code fixed in server.py:** Facebook login flow now uses robust multi-method approach (JS evaluate, Return key, selector fallback) and validates session cookies post-login.

**Instagram draft created:** `Pending_Approval/Social/INSTAGRAM_POST_20260220.md` - 163 words, 10 hashtags, professional business tone, DM "AUDIT" CTA. Needs `image_url` in frontmatter before it can be posted.

**Dashboard updated** with full posting cycle report and corrected next actions.

## Outcome

- Impact: All three posting attempts diagnosed and failed. Root cause identified for all three: (1) wrong LinkedIn password, (2) wrong Facebook password, (3) Instagram image requirement. Code improved to be more robust for future attempts.
- Tests: 3 posting attempts (0 succeeded), 2 credential failures confirmed, 1 platform limitation confirmed
- Files: 2 server.py fixes, 1 Instagram draft created, 1 Dashboard.md updated, files reorganized to correct directories
- Next prompts: User must provide correct LinkedIn and Facebook passwords, then agent can retry posting. For Instagram, user must provide an image URL.
- Reflection: Browser automation is brittle when sessions expire - headless browsers are easily detected by modern platforms. Consider implementing session refresh automation or using official APIs (Facebook Graph API, LinkedIn API) instead of Playwright for more reliable posting.

## Evaluation notes (flywheel)

- Failure modes observed: (1) Expired sessions requiring re-login, (2) Incorrect stored credentials, (3) Platform anti-bot detection hiding login buttons, (4) Platform restriction on text-only posts (Instagram)
- Graders run and results (PASS/FAIL): LinkedIn posting - FAIL, Facebook posting - FAIL, Instagram posting - FAIL, Instagram draft creation - PASS, Dashboard update - PASS, server.py fix - PASS
- Prompt variant: social-sub-agent live posting cycle
- Next experiment: After credential fix, retry immediately. Consider switching to Facebook Graph API for production reliability.
