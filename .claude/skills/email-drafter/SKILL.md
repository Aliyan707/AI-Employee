---
name: email-drafter
description: Draft professional business emails (replies or outbound), classify sensitivity, request HITL approval via Pending_Approval/ folder if needed, send via email-mcp only after Approved/. Use when processing EMAIL_* files in Needs_Action/Email/ or when user asks to reply/send email.
---

# Email Drafter Skill

## When to use
Triggered by task-triage skill when urgency=high/medium and action=reply or outbound needed.

## Core Rules (Karachi business context)
- Tone: polite, professional, concise, respectful (use "Dear [Name]," "Best regards," or "Warm regards," Aliyan)
- Always reference Company_Handbook.md rules (e.g., no attachments without approval, flag payments)
- Never send without HITL if: new recipient, amount mentioned, attachment, or >1 paragraph
- Log every draft to Logs/email_[timestamp].md

## Workflow
1. Read incoming email content from file.
2. Classify sensitivity: low (info/follow-up), medium (question/request), high (payment/invoice/new contact)
3. Draft response:
   - Subject: Re: [original] or clear new subject
   - Greeting + context recap
   - Clear body (short paragraphs)
   - Call-to-action if needed
   - Signature: Aliyan | Karachi, Pakistan | [your contact]
4. If low sensitivity → write draft directly in file → move to Approved/EMAIL_[id].md (auto-approve simulation for Bronze-like low-risk)
5. If medium/high → write full draft + reason to Pending_Approval/EMAIL_[id].md

Example file content:
```markdown
---
from: sender@example.com
to: recipient@example.com
subject: Re: Invoice Query
sensitivity: medium
requires_hitl: true
reason: Contains financial discussion
---

Dear [Name],

Thank you for your email regarding the invoice query.

[Body of response]

Please let me know if you need any further clarification.

Best regards,
Aliyan
Karachi, Pakistan
[Contact Information]
```

6. Wait for user to review Pending_Approval/ and move to Approved/
7. Once in Approved/, use email-mcp to send the email
8. Move sent email to Done/Email/SENT_[id].md with timestamp
9. Create log entry in Logs/email_[timestamp].md

## Output Format
Always create structured markdown files with YAML frontmatter containing:
- from
- to
- subject
- sensitivity (low/medium/high)
- requires_hitl (true/false)
- reason (if requires_hitl is true)

## Integration Points
- Input: Needs_Action/Email/EMAIL_*.md files
- Pending: Pending_Approval/EMAIL_*.md (for HITL review)
- Approved: Approved/EMAIL_*.md (ready to send)
- Completed: Done/Email/SENT_*.md (sent confirmation)
- Logs: Logs/email_[timestamp].md (audit trail)

## Error Handling
- If email-mcp fails, move back to Pending_Approval/ with error note
- If recipient email invalid, flag for user review
- If attachment referenced but not present, block and request clarification

## Karachi Business Etiquette
- Use formal greetings (avoid casual "Hi" unless established relationship)
- Reference time zones when scheduling (PKT - Pakistan Standard Time)
- Be mindful of cultural holidays (Eid, Ramadan)
- Use "Inshallah" appropriately in future commitments if culturally appropriate
- Keep responses brief but warm

## Examples

### Low Sensitivity (Auto-Approve)
```
Simple acknowledgment, thank you note, meeting confirmation
```

### Medium Sensitivity (HITL Required)
```
Price quotes, scheduling discussions, technical questions, multi-party coordination
```

### High Sensitivity (HITL Required)
```
Payment requests, new business proposals, legal/contract matters, invoice disputes
```
