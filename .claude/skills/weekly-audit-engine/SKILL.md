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
