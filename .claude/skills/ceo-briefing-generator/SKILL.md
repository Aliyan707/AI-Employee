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
