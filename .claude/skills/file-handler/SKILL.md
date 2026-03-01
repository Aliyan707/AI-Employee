---
name: file-handler
description: Analyze and process dropped or incoming files in Needs_Action/. Summarize content (text), suggest category/action, move to Done when handled. Use when file starts with FILE_ or when user asks to process dropped files / inbox items.
---

# File Handler Skill

## Core Rules
- Read Company_Handbook.md for any file-type rules
- Goal: understand file quickly → decide fate → clean up
- Supported in Bronze: text/Markdown files mostly (no heavy binary processing)
- Categories to suggest: invoice, receipt, project-note, research, junk, other
- Actions: summarize, extract key points, categorize (add tag in filename or note), archive (move to Done/)
- Update Dashboard.md: "- [timestamp] Handled file [name]: [category] – [summary snippet]"
- End with file moved to Done/

## Step-by-Step Workflow
1. Identify file type from name/content
2. If text/Markdown → read and summarize in 3–5 sentences
3. If non-text (pdf/image) → note "non-text file – manual review suggested"
4. Suggest category & action
5. Write summary + suggestion at bottom of the file (or create summary_*.md if large)
6. Move original file to Done/
7. Append log to Dashboard.md → ## Recent Activity

## Examples

### Example 1: Text/Markdown File
**Input file:** Needs_Action/FILE_meeting-notes-2026-02.md

**Output in file or console:**
```markdown
---
FILE ANALYSIS
Category: project-note
Processed: 2026-02-15
---

Summary: Meeting notes from Q1 planning session covering budget allocation,
team assignments, and project timeline. Key decision: prioritize feature A
over B due to customer demand. Action items assigned to 3 team members.

Suggested Action: Archive as project documentation
Category: project-note
```

**Dashboard update:** `- 2026-02-15 14:30 Handled file meeting-notes-2026-02.md: project-note – Q1 planning decisions and assignments`

**File moved to:** Done/FILE_meeting-notes-2026-02.md

### Example 2: Non-text File
**Input file:** Needs_Action/FILE_receipt-2026-02.pdf

**Output:**
```markdown
---
FILE ANALYSIS
Category: receipt
Processed: 2026-02-15
---

Summary: Non-text file (PDF) – manual review suggested
File appears to be a receipt based on naming convention.

Suggested Action: Manual review for financial processing
Category: receipt
Note: Create summary_receipt-2026-02.md if details are extracted manually
```

**Dashboard update:** `- 2026-02-15 14:32 Handled file receipt-2026-02.pdf: receipt – PDF file flagged for manual review`

**File moved to:** Done/FILE_receipt-2026-02.pdf

### Example 3: Large Text File
**Input file:** Needs_Action/FILE_research-paper-draft.md (large file)

**Action:** Create separate summary file

**Output:** Create Needs_Action/summary_research-paper-draft.md:
```markdown
# Summary: research-paper-draft.md

**Category:** research
**Processed:** 2026-02-15
**Original file:** Done/FILE_research-paper-draft.md

## Summary
[3-5 sentence summary of the research paper]

## Key Points
- Point 1
- Point 2
- Point 3

## Suggested Action
Archive original, keep summary for reference

## Next Steps
- [ ] Review findings with team
- [ ] Extract methodology section for reuse
```

**Dashboard update:** `- 2026-02-15 14:35 Handled file research-paper-draft.md: research – Created summary, archived original`

## Integration with Task Triage
- File handler focuses on FILE_* prefixed items
- Task triage handles general .md task items
- Both update Dashboard.md
- Both move processed items to Done/
- Can work together: file handler processes file → creates task → task triage handles the task

## Usage
User: "Process the dropped files"
→ Find all FILE_* in Needs_Action/
→ Process each following workflow steps 1-7
→ Report summary of all files handled

User: "Handle FILE_invoice-jan.txt"
→ Read specific file
→ Follow workflow for that file
→ Move to Done/ when complete
