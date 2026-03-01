---
id: 001
title: Create task triage skill
stage: general
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: master
user: Aliyan 707
command: Create skill file
labels: ["skill", "task-triage", "automation"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .claude/skills/task-triage/SKILL.md
tests:
 - none
---

## Prompt

Create skill in .claude/skills/task-triage/SKILL.md

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

## Response snapshot

Successfully created the task-triage skill file at `.claude/skills/task-triage/SKILL.md`.

The skill includes:
- Core classification rules for urgency (high/medium/low)
- Step-by-step workflow for processing incoming items
- Automatic plan creation template for complex tasks
- Dashboard logging requirements
- File movement automation to Done/ folder
- Complete markdown template example for plan files
- Usage examples for common scenarios

The skill can be invoked when processing items in the Needs_Action folder or checking the inbox. It follows Bronze tier constraints (filesystem operations only, no external communications).

## Outcome

- ✅ Impact: Created new skill for automating task triage workflow
- 🧪 Tests: none
- 📁 Files: Created 1 file (.claude/skills/task-triage/SKILL.md)
- 🔁 Next prompts: Create supporting folders (Needs_Action/, Done/, Plans/), test skill invocation
- 🧠 Reflection: Skill provides structured approach to inbox management with clear classification rules and action guidelines

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Test skill with sample task file
