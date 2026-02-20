---
id: 002
title: Create file handler skill
stage: general
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: master
user: Aliyan 707
command: Create skill file
labels: ["skill", "file-handler", "automation", "file-processing"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .claude/skills/file-handler/SKILL.md
tests:
 - none
---

## Prompt

Create skill in .claude/skills/file-handler/SKILL.md ---
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
Input file: Needs_Action/FILE_receipt-2026-02.pdf

Output in file or console:

## Response snapshot

Successfully created the file-handler skill file at `.claude/skills/file-handler/SKILL.md`.

The skill includes:
- Core rules for file processing with Bronze tier constraints (text/Markdown focus)
- Category suggestions: invoice, receipt, project-note, research, junk, other
- Step-by-step workflow for analyzing and processing files
- Three detailed examples:
  1. Text/Markdown file processing with summary
  2. Non-text file (PDF) handling with manual review flag
  3. Large text file with separate summary creation
- Dashboard logging for activity tracking
- Integration notes with task-triage skill
- Usage examples for batch and single file processing
- Automatic file movement to Done/ folder

The skill uses FILE_* prefix convention to identify files for processing and complements the task-triage skill for comprehensive inbox management.

## Outcome

- ✅ Impact: Created file processing skill for automated file intake and categorization
- 🧪 Tests: none
- 📁 Files: Created 1 file (.claude/skills/file-handler/SKILL.md)
- 🔁 Next prompts: Test with sample files, integrate with task-triage workflow
- 🧠 Reflection: Skill provides clear file processing workflow with examples for different file types and integrates well with existing task-triage skill

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Test file handler with various file types and sizes
