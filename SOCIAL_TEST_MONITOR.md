# 🎯 Social Media Test - Live Monitoring Guide

**Test File Created:** `Needs_Action/Social/POST_LIVE_TEST_20260219_223159.md`
**Agent Responsible:** `gold-social` (Social Media Sub-Agent)
**Expected Duration:** 2-3 minutes (generation + approval workflow)

---

## 📊 Monitoring Dashboard

### Primary Monitor: PM2 Web Interface
```bash
# Already running at:
http://localhost:9615

# Watch the gold-social agent logs in real-time
```

### Secondary Monitor: PM2 CLI
```bash
# Live tail of social media agent
pm2 logs gold-social --lines 50 --raw

# Or all agents together
pm2 logs --lines 20
```

### Tertiary Monitor: JSON Lines Log
```bash
# Watch structured logs
tail -f Logs/social_$(date +%Y%m%d).jsonl | jq -r '[.timestamp, .event, .status] | @tsv'

# Or pretty-print all fields
tail -f Logs/social_$(date +%Y%m%d).jsonl | jq .
```

---

## ⏱️ Expected Timeline

### Phase 1: File Discovery & Claim (0-30 seconds)
**What happens:**
- gold-social agent scans Needs_Action/Social/ folder
- Detects POST_LIVE_TEST_20260219_223159.md
- Claims file by moving to In_Progress/Social/

**Watch for:**
```jsonl
{"timestamp":"2026-02-19T22:32:00+05:00","agent":"gold-social","event":"file_claimed","file":"POST_LIVE_TEST_20260219_223159.md","status":"claimed"}
```

**Verify:**
```bash
ls -la In_Progress/Social/
# Should show: POST_LIVE_TEST_20260219_223159.md
```

---

### Phase 2: Content Generation (30-90 seconds)
**What happens:**
- Agent invokes `/multi-social-poster` skill
- Reads content brief and requirements
- Generates platform-specific posts:
  - LinkedIn: Professional, 150-200 words, ROI-focused
  - Facebook: Friendly, 100-150 words, emojis
  - Twitter/X: Concise, 280 chars or thread
- Applies Karachi-specific hashtags
- Creates draft files in Pending_Approval/Social/

**Watch for:**
```jsonl
{"timestamp":"2026-02-19T22:32:15+05:00","agent":"gold-social","event":"skill_invoked","skill":"multi-social-poster","status":"processing"}
{"timestamp":"2026-02-19T22:32:45+05:00","agent":"gold-social","event":"content_generated","platforms":["linkedin","facebook","twitter"],"status":"success"}
{"timestamp":"2026-02-19T22:33:00+05:00","agent":"gold-social","event":"approval_requested","approval_file":"Pending_Approval/Social/LINKEDIN_POST_20260219_223159.md","status":"pending"}
```

**Verify:**
```bash
ls -la Pending_Approval/Social/
# Should show 3 files:
# - LINKEDIN_POST_20260219_223159.md
# - FACEBOOK_POST_20260219_223159.md
# - TWITTER_POST_20260219_223159.md
```

---

### Phase 3: Human Approval (Manual - You Do This!)
**What you need to do:**
1. Review generated content:
   ```bash
   cat Pending_Approval/Social/LINKEDIN_POST_20260219_223159.md
   cat Pending_Approval/Social/FACEBOOK_POST_20260219_223159.md
   cat Pending_Approval/Social/TWITTER_POST_20260219_223159.md
   ```

2. Check quality criteria:
   - [ ] Platform-appropriate tone
   - [ ] Karachi hashtags included (#KarachiBusinesses, etc.)
   - [ ] Clear value proposition
   - [ ] No typos or grammar errors
   - [ ] Call-to-action present
   - [ ] Professional brand voice

3. Approve by moving to Approved/:
   ```bash
   # Approve LinkedIn post
   mv Pending_Approval/Social/LINKEDIN_POST_20260219_223159.md Approved/Social/

   # Approve Facebook post
   mv Pending_Approval/Social/FACEBOOK_POST_20260219_223159.md Approved/Social/

   # Approve Twitter post
   mv Pending_Approval/Social/TWITTER_POST_20260219_223159.md Approved/Social/
   ```

   Or approve all at once:
   ```bash
   mv Pending_Approval/Social/*_20260219_223159.md Approved/Social/
   ```

**Expected duration:** 1-3 minutes (your review time)

---

### Phase 4: Posting Execution (0-60 seconds after approval)
**What happens:**
- Approval & Recovery agent detects approved files
- Invokes browser-mcp to post content
- Posts to each platform sequentially:
  1. LinkedIn (via browser automation)
  2. Facebook (via browser automation)
  3. Twitter/X (via browser automation)
- Logs posting results
- Moves completed files to Done/Social/

**Watch for:**
```jsonl
{"timestamp":"2026-02-19T22:35:00+05:00","agent":"gold-approval","event":"approval_detected","files":3,"status":"processing"}
{"timestamp":"2026-02-19T22:35:15+05:00","agent":"gold-approval","event":"platform_post","platform":"linkedin","status":"success","post_url":"https://linkedin.com/..."}
{"timestamp":"2026-02-19T22:35:30+05:00","agent":"gold-approval","event":"platform_post","platform":"facebook","status":"success","post_url":"https://facebook.com/..."}
{"timestamp":"2026-02-19T22:35:45+05:00","agent":"gold-approval","event":"platform_post","platform":"twitter","status":"success","post_url":"https://twitter.com/..."}
{"timestamp":"2026-02-19T22:36:00+05:00","agent":"gold-approval","event":"task_completed","task":"social_post","files_completed":3,"status":"done"}
```

**Verify:**
```bash
ls -la Done/Social/
# Should show 3 completed files with _POSTED suffix
```

---

## 🎯 Expected Results

### Platform-Specific Content

**LinkedIn Post (Professional):**
- Opening hook about business automation challenges
- Statistics: "Save 85% of admin time"
- Services breakdown (Odoo, social media, invoices, email)
- ROI focus: "Starting at PKR 50,000/month"
- Hashtags: #BusinessAutomation #KarachiBusinesses #AIEmployee #DigitalTransformation
- Call-to-action: Free consultation offer
- Length: 150-200 words

**Facebook Post (Friendly):**
- Conversational tone with emojis (🤖 💼 ⚡)
- Focus on pain points (manual admin work)
- Simple solution presentation
- Community focus (Karachi businesses)
- Hashtags: #KarachiBusinesses #BusinessAutomation #PakistanTech
- Call-to-action: "Message us for details"
- Length: 100-150 words

**Twitter/X Post (Concise):**
Option 1 - Single tweet (280 chars):
```
🤖 Tired of manual invoices, emails & admin work?

We build AI employees for Karachi businesses.
✅ Odoo integration
✅ Social automation
✅ Email management

Save 85% of admin time. Starting PKR 50k/mo.

DM for free consultation 👇
#KarachiBusinesses #AIEmployee
```

Option 2 - Thread (3-4 tweets):
```
1/ 🤖 Your business doesn't need more staff. It needs an AI employee.

We help Karachi businesses automate:
• Invoice processing
• Social media
• Email management
• Financial reporting

2/ Real impact: 85% reduction in admin time.
Complete Odoo ERP integration.
Platform-specific social content.
Autonomous email handling.

3/ Not just tools—a complete AI employee that works 24/7.

Starts at PKR 50,000/month.

DM us for a free automation audit 👇
#KarachiBusinesses #BusinessAutomation
```

---

## 📈 Performance Metrics

### Time Comparison
| Task | Manual Process | AI Employee | Time Saved |
|------|---------------|-------------|------------|
| Research & ideation | 15-20 min | 0 min | 20 min |
| LinkedIn draft | 10-15 min | 30 sec | 14 min |
| Facebook adaptation | 8-10 min | 30 sec | 9 min |
| Twitter version | 5-7 min | 30 sec | 6 min |
| Final review | 5 min | 2 min | 3 min |
| **TOTAL** | **45-60 min** | **~5 min** | **~50 min** |

### Business Impact (Monthly)
- **Posts per week:** 3 promotional posts × 3 platforms = 9 posts
- **Time saved per week:** 50 min × 3 = 150 minutes (2.5 hours)
- **Time saved per month:** 10 hours
- **Cost savings:** 10 hours × PKR 2,000/hour = **PKR 20,000/month**
- **ROI:** System cost PKR 50,000, saves PKR 20,000 + improves consistency + 24/7 operation

---

## 🔍 Troubleshooting

### Issue: Agent Not Claiming File
**Symptoms:** File stays in Needs_Action/Social/ for >60 seconds

**Check:**
```bash
pm2 status gold-social
pm2 logs gold-social --lines 50
```

**Fixes:**
- Restart agent: `pm2 restart gold-social`
- Check file permissions: `ls -la Needs_Action/Social/`
- Verify agent prompt: `cat System/Social-Sub-Gold.md`

---

### Issue: Content Generation Fails
**Symptoms:** No files appear in Pending_Approval/Social/

**Check:**
```bash
pm2 logs gold-social --lines 100 --err
cat Logs/social_$(date +%Y%m%d).jsonl | jq 'select(.status=="error")'
```

**Fixes:**
- Verify `/multi-social-poster` skill exists: `ls .claude/skills/multi-social-poster/`
- Check skill configuration: `cat .claude/skills/multi-social-poster/SKILL.md`
- Restart agent: `pm2 restart gold-social`

---

### Issue: Posting Fails After Approval
**Symptoms:** Files in Approved/Social/ but not posted

**Check:**
```bash
pm2 status gold-approval
pm2 logs gold-approval --lines 50
```

**Fixes:**
- Verify browser-mcp is running: Check mcp.json configuration
- Check platform credentials: Ensure social media accounts are logged in
- Manual fallback: Copy content and post manually, then move to Done/

---

## ✅ Success Criteria

- [ ] File claimed within 30 seconds
- [ ] 3 platform-specific posts generated (LinkedIn, Facebook, Twitter)
- [ ] All posts include Karachi hashtags (#KarachiBusinesses, etc.)
- [ ] Tone appropriate for each platform
- [ ] Clear call-to-action in all posts
- [ ] No grammar/spelling errors
- [ ] Posted successfully to all platforms (or ready for manual posting)
- [ ] Files moved to Done/Social/ with completion metadata
- [ ] All actions logged in social_YYYYMMDD.jsonl

---

## 🎓 What This Demonstrates

### Gold-Tier Capabilities
1. **Autonomous Content Creation:** AI generates platform-specific content without templates
2. **Multi-Platform Optimization:** Same message adapted for LinkedIn, Facebook, Twitter
3. **Local Context:** Karachi hashtags and Pakistan business focus
4. **HITL Approval Workflow:** Human oversight before public posting
5. **Constitutional Safety:** Never posts without explicit approval
6. **Structured Logging:** Full audit trail of content generation and posting
7. **Error Recovery:** Approval agent retries and logs failures

### Business Value
- **Consistency:** Brand voice maintained across platforms
- **Speed:** 50 minutes → 5 minutes (90% time savings)
- **Quality:** AI follows platform best practices automatically
- **Scalability:** Can handle 100+ posts/month without additional overhead
- **Compliance:** Full approval workflow for brand safety

---

## 🚀 Next Steps After This Test

1. **Test Email Management:**
   - Create `Needs_Action/Email/EMAIL_REPLY_TEST.md`
   - Watch email-drafter skill generate professional replies
   - Test HITL approval for sensitive communications

2. **Test Finance Audit:**
   - Drop bank CSV in `Needs_Action/Finance/`
   - Watch weekly-audit-engine process transactions
   - Review anomaly detection and subscription monitoring

3. **Trigger Weekly CEO Briefing:**
   ```bash
   # Simulate Sunday 23:00 PKT trigger
   touch Plans/WEEKLY_AUDIT_TRIGGER.md

   # Watch finance-auditor and accounting agents compile data
   # Check Briefings/ folder for generated report
   ```

4. **Full Integration Test:**
   - Create invoice → accounting workflow
   - Generate social post → social media workflow
   - Reply to email → email workflow
   - All running simultaneously via main orchestrator

---

**Ready to start? Open PM2 web interface and watch the magic happen!** ✨

```bash
# Monitoring command (open in new terminal)
pm2 logs gold-social --lines 50 --raw --timestamp

# Or use PM2 web interface
# Already running at: http://localhost:9615
```

---

**Test started at:** 2026-02-19 22:31:59 PKT
**File location:** `Needs_Action/Social/POST_LIVE_TEST_20260219_223159.md`
**Monitor at:** http://localhost:9615
