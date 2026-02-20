---
name: task-triage
description: Triage incoming tasks from Needs_Action folder. Classify urgency, suggest actions, create simple plan if needed, move to Done when complete. Use when processing new .md files in Needs_Action/ or when user asks to check inbox / process pending items.
---

# Task Triage Skill

## Core Rules
- Always read Company_Handbook.md first for any custom rules (politeness, flags for approval, etc.)
- Classify every incoming item as:
  - high (contains words: urgent, payment, invoice, asap, deadline)
  - medium (question, request, follow-up)
  - low (newsletter, spam, info only)
- Suggest 1–3 next actions (e.g. reply needed? archive? summarize? flag for human?)
- If action is simple → do it (summarize, categorize, move file)
- If complex or sensitive → write a short Plan_*.md in Plans/ folder with checkboxes
- Update Dashboard.md with a one-line log: "- [timestamp] Triaged [filename]: [classification] – [action taken]"
- Always move processed file to Done/ folder when finished
- Never send emails, make payments, or post publicly (Bronze: filesystem only)

## Step-by-Step Workflow
1. Read the current file in Needs_Action/ (or the one referenced)
2. Extract key info: type (email/file/note), sender/subject if available, main content
3. Apply classification above
4. Write classification + suggested actions at bottom of the file (or new note)
5. If plan needed → create Plans/PLAN_[original-filename-without-ext].md
   Example content:
   ```markdown
   # Plan: [Original Task Name]

   **Source:** Needs_Action/[filename]
   **Classification:** [high/medium/low]
   **Created:** [date]

   ## Tasks
   - [ ] Research [topic/question]
   - [ ] Draft response/summary
   - [ ] Flag for human review if needed
   - [ ] Update Dashboard
   - [ ] Move to Done/

   ## Notes
   [Any additional context or considerations]
   ```
6. Update Dashboard.md with summary line
7. Move original file to Done/[filename]
8. Report completion with: classification, actions taken, plan created (if any)

## Example Usage
User: "Check the inbox"
→ Read all files in Needs_Action/
→ Process each following steps 1-8
→ Report summary of all items triaged

User: "Process the vendor-inquiry.md file"
→ Read Needs_Action/vendor-inquiry.md
→ Follow steps 1-8 for that specific file
