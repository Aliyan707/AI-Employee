---
name: social-linkedin-poster
description: Generate engaging LinkedIn posts to promote business/services (sales lead gen), draft in Pending_Approval/, post via browser-mcp only after human approval. Use for Comms/ tasks or scheduled sales content creation.
---

# LinkedIn Poster Skill

## When to use
Triggered by main orchestrator or comms sub-agent when sales opportunity detected (e.g., WhatsApp "pricing" keyword) or weekly schedule.

## Core Rules
- Posts: value-first, Karachi/Sindh focused, hashtag #AIEmployee #KarachiBusiness #FreelanceAI
- Length: 100–250 words, engaging hook, call-to-action (DM me)
- Always require HITL approval (no auto-posting)
- Include disclaimer if needed: "Generated with AI assistance"
- Log posted content to Logs/linkedin_[date].md

## Workflow
1. Generate post idea/content:
   - Hook: Question or stat (e.g., "Struggling with 24/7 client follow-ups?")
   - Value: Explain benefit (e.g., "My AI Employee handles emails & WhatsApp autonomously")
   - CTA: "DM for a free demo in Karachi"
2. Draft full post + suggested image/text (no actual image gen in Silver)
3. Write to Pending_Approval/SOCIAL_linkedin_[timestamp].md

Example file content:
```markdown
---
platform: linkedin
post_type: sales_promotion
sensitivity: medium
requires_hitl: true
scheduled_for: null
reason: Sales content requires approval before posting
---

# LinkedIn Post Draft

## Hook
Struggling with 24/7 client follow-ups in Karachi's competitive market?

## Body
My AI Employee is here to help! 🤖

I've built an autonomous system that:
✅ Handles WhatsApp & email responses 24/7
✅ Qualifies leads automatically
✅ Routes urgent items to me instantly
✅ Never misses a follow-up

Perfect for freelancers, consultants, and small businesses in Karachi who want to scale without hiring.

## Call to Action
DM me for a free demo and see how it works! 💼

## Hashtags
#AIEmployee #KarachiBusiness #FreelanceAI #AutomationPakistan #AIForBusiness

## Suggested Visual
Text overlay: "24/7 Client Support Without Hiring" + Karachi skyline background

---
Generated with AI assistance
```

4. Wait for user to review Pending_Approval/ and move to Approved/
5. Once in Approved/, use browser-mcp to post to LinkedIn
6. Move posted content to Done/Social/POSTED_linkedin_[timestamp].md
7. Create log entry in Logs/linkedin_[date].md with engagement tracking setup

## Output Format
Always create structured markdown files with YAML frontmatter containing:
- platform (linkedin)
- post_type (sales_promotion, thought_leadership, case_study, engagement, announcement)
- sensitivity (always medium for sales content)
- requires_hitl (always true)
- scheduled_for (ISO datetime or null for immediate)
- reason (why approval needed)

## Content Types

### Sales Promotion
```
Focus: Lead generation, service offers
Tone: Professional but approachable
CTA: "DM me" or "Contact for demo"
```

### Thought Leadership
```
Focus: Industry insights, AI trends in Pakistan
Tone: Expert, helpful
CTA: "Share your thoughts" or "Follow for more"
```

### Case Study
```
Focus: Success stories (anonymized if needed)
Tone: Results-driven, specific
CTA: "Want similar results?"
```

### Engagement
```
Focus: Questions, polls, discussions
Tone: Conversational, community-building
CTA: "Comment below"
```

## Integration Points
- Input: Needs_Action/Comms/SOCIAL_*.md files or triggered by orchestrator
- Pending: Pending_Approval/SOCIAL_linkedin_*.md (for HITL review)
- Approved: Approved/SOCIAL_linkedin_*.md (ready to post)
- Completed: Done/Social/POSTED_linkedin_*.md (posted confirmation)
- Logs: Logs/linkedin_[date].md (engagement tracking)

## Karachi/Pakistan Context
- Highlight local market advantages (time zone, rates, quality)
- Reference Pakistani business culture when relevant
- Use PKT for scheduling and business hours context
- Mention Karachi specifically for local lead generation
- Be mindful of cultural sensitivities

## Best Practices
- Post during peak Pakistan business hours (9 AM - 6 PM PKT)
- Best days: Tuesday-Thursday for B2B content
- Use 3-5 hashtags maximum (avoid spam)
- Always include a clear value proposition
- Keep paragraphs short (1-2 sentences) for readability
- Use emojis sparingly but strategically (✅, 🤖, 💼)

## Content Calendar Suggestions
- Monday: Motivation/Week startup tips
- Tuesday-Thursday: Service promotion/Case studies
- Friday: Community engagement/Questions
- Weekend: Thought leadership/Industry insights

## Error Handling
- If browser-mcp fails to post, move back to Pending_Approval/ with error note
- If LinkedIn shows "too many posts" warning, schedule for next available slot
- If content violates LinkedIn guidelines, flag for revision
- If hashtag research needed, suggest alternatives

## Engagement Tracking
After posting, log to Logs/linkedin_[date].md:
```markdown
---
date: 2026-02-15
post_id: POSTED_linkedin_20260215_093045
status: posted
---

# LinkedIn Post Performance

**Post Type:** sales_promotion
**Posted At:** 2026-02-15 09:30 PKT
**Content:** [First 50 chars...]

## Engagement Metrics (Update manually or via browser-mcp if available)
- Views: TBD
- Reactions: TBD
- Comments: TBD
- Shares: TBD
- Profile Visits: TBD
- DMs Received: TBD

## Follow-up Actions
- [ ] Respond to comments within 2 hours
- [ ] Follow up on DMs from interested leads
- [ ] Track conversion to actual demos/clients
```

## Safety Rules
- Never post without explicit human approval
- Never share client confidential information
- Never make claims that can't be substantiated
- Never engage in spammy behavior (excessive tagging, posting)
- Always maintain professional tone
- Flag any potentially controversial content for extra review

## Examples of Effective Posts

### Example 1: Problem-Solution
```
Hook: "Lost a client because you missed their weekend email?"
Value: AI Employee monitors 24/7, routes urgent items instantly
CTA: "DM me to see how it works"
Hashtags: #AIEmployee #KarachiBusiness #FreelanceAI
```

### Example 2: Social Proof
```
Hook: "Just automated 40 hours/month of email responses"
Value: Share what the system handles automatically
CTA: "Want the same for your business?"
Hashtags: #Automation #ProductivityPakistan #AIForBusiness
```

### Example 3: Value-First
```
Hook: "3 signs you need AI automation in your business:"
Value: List specific pain points and how AI solves them
CTA: "Which one resonates with you?"
Hashtags: #BusinessTips #KarachiEntrepreneurs #AIEmployee
```
