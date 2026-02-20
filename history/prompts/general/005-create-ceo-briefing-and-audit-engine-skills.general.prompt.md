---
id: 005
title: Create CEO Briefing and Audit Engine Skills
stage: general
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: 002-silver-tier
user: Cs
command: manual
labels: ["skills", "configuration", "audit", "reporting", "ceo-briefing"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/ceo-briefing-generator/SKILL.md
  - .claude/skills/weekly-audit-engine/SKILL.md
tests:
  - none
---

## Prompt

create skill in .claude/skills/odoo-accounting/SKILL.md

---
name: ceo-briefing-generator
description: Generate Monday Morning CEO Briefing from Business_Goals.md, recent tasks, bank tx, Odoo data, social activity. Write to Briefings/YYYY-MM-DD.md. Use on weekly audit trigger (Sunday night).
---

# CEO Briefing Generator Skill

## When to use
Triggered by Main Orchestrator or Finance/Auditor sub-agent on WEEKLY_AUDIT_TRIGGER.md

## Workflow
1. Read: Business_Goals.md, Accounting/Current_Month.md, Logs/, Dashboard.md recent
2. Collect:
   - Revenue: from Odoo + bank tx
   - Completed tasks: from Done/
   - Bottlenecks: delayed plans or flagged items
   - Proactive suggestions: unused subscriptions, cost leaks
   - Social: posts made, potential leads
3. Write Briefings/YYYY-MM-DD_Monday_Briefing.md using template structure:

---

Create skill in .claude/skills/weekly-audit-engine/SKILL.md
---
name: weekly-audit-engine
description: Collect data from all domains for weekly audit (revenue, tasks, costs, subscriptions, social). Flag anomalies. Use in Finance/Auditor or Accounting sub-agents on audit trigger.
---

# Weekly Audit Engine Skill

## Workflow
1. On trigger: scan Accounting/, Done/, Logs/, Social/Summary_*
2. Compute:
   - Revenue & receivables (Odoo)
   - Expenses & subscriptions (parse tx)
   - Task completion rate
   - Social reach/posts
3. Flag issues:
   - Subscription no usage >30 days
   - Delayed tasks > expected
   - Unusual tx (> threshold)
4. Write findings to temporary Audit_Data_[date].md
5. Pass to ceo-briefing-generator
6. Log audit run to Logs/
7. End: <status>AUDIT_DATA_COLLECTED</status>

## Response snapshot

Created two complementary skill configuration files for executive reporting and data analysis:
1. `.claude/skills/ceo-briefing-generator/SKILL.md` - Synthesizes multi-domain data into weekly CEO briefing (revenue, tasks, costs, social activity, proactive recommendations)
2. `.claude/skills/weekly-audit-engine/SKILL.md` - Collects and analyzes data across all business domains, flags anomalies, feeds data to briefing generator

These skills work together: audit engine runs Sunday nights to collect data, then passes findings to briefing generator for Monday morning executive summary.

## Outcome

- ✅ Impact: Added executive-level reporting automation to AI Employee system with data-driven insights and anomaly detection
- 🧪 Tests: none (configuration files)
- 📁 Files: Created 2 new skill files enabling weekly audit workflow and CEO briefing generation
- 🔁 Next prompts: Create briefing template structure, define anomaly thresholds, test with sample data
- 🧠 Reflection: Skills integrate with existing vault structure (Done/, Logs/, Accounting/, Social/) and follow established weekly trigger pattern. CEO briefing generator consumes audit engine output for comprehensive reporting.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Define CEO briefing template format and audit anomaly threshold values
