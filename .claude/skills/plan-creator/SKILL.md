---
name: plan-creator
description: Create/update multi-step Plan_*.md files from complex tasks, break into checkboxes, track progress, request approval if needed. Use when task requires >2 steps or coordination across sub-agents.
---

# Plan Creator Skill

## When to use
Triggered by main orchestrator or planner sub-agent on high-urgency or multi-domain items.

## Core Rules
- Plans must be 3-8 steps (if >8, break into multiple plans)
- Each step must be actionable and testable (checkbox format)
- Always include approval step for sensitive actions
- Update progress on each orchestrator cycle
- Move to Done/ when all checkboxes complete
- Log plan creation/updates to Dashboard.md

## Workflow
1. Read task from Needs_Action/ or Plans/.
2. Break into 3–8 checkboxes (realistic steps)
   Example:
   - [ ] Triage incoming WhatsApp message
   - [ ] Draft LinkedIn post if sales intent
   - [ ] Request approval for posting
   - [ ] Log outcome
3. Write/update Plans/PLAN_[task-id].md
4. If step needs external/MCP → add approval sub-step
5. Update progress on next cycles (check off when Done/)
6. When all checked → move plan to Done/, notify Dashboard.md
7. End with `<status>PLAN_UPDATED</status>`

## Output Format

### Plan File Structure
```markdown
---
plan_id: PLAN_[unique-id]
created: 2026-02-15T10:30:00Z
updated: 2026-02-15T10:30:00Z
status: in_progress
priority: high/medium/low
owner: main-orchestrator
requires_approval: true/false
estimated_steps: 5
completed_steps: 0
---

# Plan: [Clear descriptive title]

## Context
Brief description of what this plan accomplishes and why it's needed.

**Trigger:** [What triggered this plan - e.g., "Email from client requesting quote"]
**Expected Outcome:** [What success looks like - e.g., "Quote sent and logged"]
**Delegated To:** [List of sub-agents involved - e.g., "email-drafter, file-handler"]

## Steps

- [ ] **Step 1:** [Action description]
  - Owner: [sub-agent or main-orchestrator]
  - Estimated time: [if relevant]
  - Dependencies: [if any]
  - Approval needed: Yes/No

- [ ] **Step 2:** [Action description]
  - Owner: [sub-agent or main-orchestrator]
  - Estimated time: [if relevant]
  - Dependencies: Step 1
  - Approval needed: Yes/No

- [ ] **Step 3:** [Action description]
  - Owner: [sub-agent or main-orchestrator]
  - Estimated time: [if relevant]
  - Dependencies: Step 2
  - Approval needed: Yes/No

[Continue for all steps...]

## Progress Log
- 2026-02-15 10:30 - Plan created
- 2026-02-15 10:45 - Step 1 completed
- 2026-02-15 11:00 - Step 2 in progress

## Notes
- [Any important considerations]
- [Risks or blockers]
- [Follow-up actions after completion]

<status>PLAN_UPDATED</status>
```

## Plan Types

### Simple Sequential Plan
```
Steps execute one after another, no branching
Example: Email reply workflow
```

### Parallel Plan
```
Multiple steps can happen simultaneously
Example: Multi-channel outreach (email + LinkedIn)
```

### Conditional Plan
```
Steps depend on outcomes of previous steps
Example: Lead qualification → if qualified, send pricing; if not, nurture
```

### Approval-Required Plan
```
Critical steps that must wait for human approval
Example: Payment processing, new client contracts
```

## Integration Points
- Input: Needs_Action/[category]/*.md files
- Active Plans: Plans/PLAN_*.md (in-progress plans)
- Completed: Done/Plans/PLAN_*.md (finished plans)
- Dashboard: Dashboard.md (summary of active plans)
- Logs: Logs/plan_[date].md (plan execution audit trail)

## Step Complexity Guidelines

### ✅ Good Steps (Actionable & Testable)
```
- [ ] Read email content from Needs_Action/Email/EMAIL_001.md
- [ ] Draft response using email-drafter skill
- [ ] Move draft to Pending_Approval/EMAIL_001.md
- [ ] Wait for approval (human moves to Approved/)
- [ ] Send email via email-mcp
```

### ❌ Bad Steps (Too Vague)
```
- [ ] Handle email
- [ ] Process request
- [ ] Do the thing
```

### ❌ Bad Steps (Too Granular)
```
- [ ] Open file
- [ ] Read line 1
- [ ] Read line 2
- [ ] Parse sender address
```

## Progress Tracking

### Updating Plans
On each orchestrator cycle:
1. Read all Plans/PLAN_*.md files
2. Check if any steps can be completed
3. Update checkboxes: `- [ ]` → `- [x]`
4. Add timestamp to Progress Log
5. Update `updated` field in frontmatter
6. Increment `completed_steps` counter

### Completion Criteria
When ALL checkboxes are checked:
1. Update status to "completed"
2. Move file to Done/Plans/PLAN_[id].md
3. Update Dashboard.md to remove from active plans
4. Create summary log entry in Logs/plan_[date].md
5. Check if any follow-up plans are needed

## Approval Workflow Integration

### When to Require Approval
- Financial actions (payments, invoices)
- External communications (emails, social posts)
- File operations on sensitive data
- New client/vendor interactions
- Changes to automation rules

### How to Add Approval Steps
```markdown
- [ ] **Step 3:** Draft response email
  - Owner: email-drafter
  - Approval needed: Yes
  - Approval gate: Move to Pending_Approval/, wait for user to move to Approved/

- [ ] **Step 4:** [APPROVAL GATE] Wait for human approval
  - Owner: human
  - Check: File exists in Approved/ folder
  - If rejected: Revise and return to Step 3

- [ ] **Step 5:** Send approved email
  - Owner: email-mcp
  - Dependencies: Step 4 approved
  - Approval needed: No (already approved)
```

## Error Handling

### Plan Failures
If a step fails:
1. Mark step with `- [!]` (failed indicator)
2. Add error note to Progress Log
3. Update status to "blocked"
4. Create escalation note in Pending_Approval/ESCALATION_[plan-id].md
5. Wait for human intervention

### Plan Adjustments
If requirements change mid-plan:
1. Add new step or modify existing
2. Log change in Progress Log
3. Update `updated` timestamp
4. Notify Dashboard.md of plan change

## Dashboard Integration

Update Dashboard.md active plans section:
```markdown
## Active Plans (3)

1. **PLAN_email-quote-001** - 3/5 steps complete - Priority: High
   - Next: Wait for approval on quote email
   - Updated: 2 mins ago

2. **PLAN_linkedin-post-002** - 1/4 steps complete - Priority: Medium
   - Next: Draft LinkedIn post content
   - Updated: 15 mins ago

3. **PLAN_client-followup-003** - 0/3 steps complete - Priority: Low
   - Next: Read client request from Needs_Action
   - Updated: 30 mins ago
```

## Examples

### Example 1: Simple Email Reply Plan
```markdown
---
plan_id: PLAN_email-001
status: in_progress
priority: high
estimated_steps: 4
completed_steps: 2
---

# Plan: Reply to Client Invoice Query

## Steps
- [x] Read email from Needs_Action/Email/EMAIL_001.md
- [x] Draft response using email-drafter skill
- [ ] Move to Pending_Approval and wait for human review
- [ ] Send via email-mcp once approved

<status>PLAN_UPDATED</status>
```

### Example 2: Multi-Channel Sales Outreach
```markdown
---
plan_id: PLAN_sales-outreach-001
status: in_progress
priority: medium
estimated_steps: 6
completed_steps: 1
---

# Plan: Sales Lead Follow-up (Multi-Channel)

## Steps
- [x] Analyze WhatsApp pricing inquiry
- [ ] Draft LinkedIn post about service
- [ ] Draft follow-up email to lead
- [ ] Submit both for approval
- [ ] Post to LinkedIn once approved
- [ ] Send email once approved

<status>PLAN_UPDATED</status>
```

### Example 3: Complex Client Onboarding
```markdown
---
plan_id: PLAN_onboard-client-001
status: in_progress
priority: high
estimated_steps: 8
completed_steps: 0
requires_approval: true
---

# Plan: Onboard New Client - Acme Corp

## Steps
- [ ] Create client folder structure
- [ ] Draft welcome email
- [ ] Prepare contract template
- [ ] [APPROVAL] Review contract with human
- [ ] Send contract via email
- [ ] Wait for signed contract return
- [ ] Update CRM/tracking system
- [ ] Send project kickoff details

<status>PLAN_UPDATED</status>
```

## Best Practices

### ✅ Do
- Keep steps atomic and testable
- Include approval gates for sensitive actions
- Log all progress updates
- Use clear, specific language
- Estimate realistic timeframes
- Link to related files/tasks

### ❌ Don't
- Create plans with >8 steps (break into multiple)
- Skip approval steps for external actions
- Leave steps vague or ambiguous
- Forget to update progress on each cycle
- Create duplicate plans for same task
- Mix unrelated tasks in one plan

## Metrics to Track
- Total plans created per day
- Average completion time
- Approval wait times
- Failed steps (for improvement)
- Most common plan types

## Status Codes
Use in final line of each plan update:
- `<status>PLAN_CREATED</status>` - New plan created
- `<status>PLAN_UPDATED</status>` - Progress updated
- `<status>PLAN_COMPLETED</status>` - All steps done
- `<status>PLAN_BLOCKED</status>` - Waiting on external dependency
- `<status>PLAN_FAILED</status>` - Unrecoverable error
- `<status>PLAN_CANCELLED</status>` - No longer needed
