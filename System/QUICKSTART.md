# Bronze AI Employee - Quick Start Guide

## What This Does

The Bronze AI Employee automatically processes items in your `Needs_Action/` folder, classifies them, summarizes them, logs activity to Dashboard.md, and archives them to `Done/`.

**Capabilities:**
- Email triage (EMAIL_* files)
- File handling (FILE_* files)
- Priority classification (high/medium/low)
- Automatic summarization
- Human review flagging for sensitive items
- Activity logging
- Safe archival

**Limitations (Bronze Tier):**
- Filesystem only (no emails, APIs, or payments)
- Manual invocation (not fully automated)
- Two skills only (task-triage, file-handler)

---

## Setup (One-Time)

### 1. Verify Vault Structure

```bash
cd ~/path/to/AI_Employee_Vault

# Should have these folders/files:
# Needs_Action/
# Done/
# Plans/
# Dashboard.md
# System/Company_Handbook.md
# .claude/skills/task-triage/SKILL.md
# .claude/skills/file-handler/SKILL.md
```

If anything is missing, create it:

```bash
mkdir -p Needs_Action Done Plans System
mkdir -p .claude/skills/task-triage
mkdir -p .claude/skills/file-handler
```

### 2. Verify Dashboard.md Exists

If `Dashboard.md` doesn't exist, it will be created automatically on first run.

---

## How to Use

### Method 1: Manual Processing (Recommended for Bronze)

1. **Drop files into Needs_Action/**
   ```bash
   # Email example:
   cp ~/Downloads/vendor-email.txt Needs_Action/EMAIL_vendor-inquiry.md

   # File example:
   cp ~/Documents/meeting-notes.md Needs_Action/FILE_meeting-notes.md
   ```

2. **Open Claude Code and process**

   In your Claude Code chat:
   ```
   Process all items in Needs_Action/
   ```

   Or be specific:
   ```
   Process the file Needs_Action/EMAIL_vendor-inquiry.md using task-triage
   ```

3. **Review results**
   - Check `Dashboard.md` for activity log
   - Check `Done/` for archived files
   - Check `Done/REVIEW_*` for items needing your attention

---

### Method 2: Automated Loop (Advanced)

**Option A: Simple Bash Loop**

```bash
cd ~/path/to/AI_Employee_Vault

while true; do
  echo "Checking inbox at $(date)"

  # Count files in Needs_Action
  count=$(ls -1 Needs_Action/ 2>/dev/null | wc -l)

  if [ "$count" -gt 0 ]; then
    echo "Found $count file(s) to process"
    echo "Open Claude Code and type: Process all items in Needs_Action/"
    echo "Waiting 2 minutes for processing..."
    sleep 120
  else
    echo "Inbox empty. Sleeping 60 seconds..."
    sleep 60
  fi
done
```

**Option B: Use Automation Script**

```bash
chmod +x .specify/scripts/bronze-automation-loop.sh
./.specify/scripts/bronze-automation-loop.sh
```

---

## Testing

### Create Test Files

```bash
# Test 1: Low priority newsletter
cat > Needs_Action/EMAIL_test-newsletter.md <<EOF
# Tech Newsletter
Weekly updates and news. No action required.
EOF

# Test 2: Medium priority inquiry
cat > Needs_Action/EMAIL_test-inquiry.md <<EOF
# Customer Inquiry
Customer asking about our services. Please respond.
EOF

# Test 3: High priority + sensitive (should trigger review)
cat > Needs_Action/EMAIL_test-urgent-payment.md <<EOF
# URGENT Payment Required
Invoice #123 for PKR 50,000 is overdue. Please process payment immediately.
Account: 9876543210
EOF

# Test 4: File to handle
cat > Needs_Action/FILE_test-notes.md <<EOF
# Meeting Notes
Discussion about project timeline and deliverables.
EOF
```

### Process Test Files

In Claude Code:
```
Process all items in Needs_Action/
```

### Verify Results

```bash
# Check Dashboard
cat Dashboard.md

# Check Done folder
ls -la Done/

# Should see:
# - EMAIL_test-newsletter.md (archived normally)
# - EMAIL_test-inquiry.md (archived normally)
# - REVIEW_EMAIL_test-urgent-payment.md (flagged for review)
# - FILE_test-notes.md (archived normally)
```

---

## File Naming Conventions

| Prefix | Skill Used | Example |
|--------|------------|---------|
| `EMAIL_*` | task-triage | `EMAIL_vendor-inquiry.md` |
| `FILE_*` | file-handler | `FILE_meeting-notes.md` |
| No prefix (.md) | task-triage | `task-follow-up.md` |
| No prefix (other) | file-handler | `document.txt` |

---

## Understanding the Dashboard

```markdown
## Recent Activity
- 2026-02-15 07:00 Triaged EMAIL_vendor.md: medium – Product inquiry
- 2026-02-15 07:00 Handled FILE_notes.md: project-note – Meeting summary
```

**Format:**
```
- [timestamp] [Action] [filename]: [classification/category] – [summary]
```

**Flags:**
- `[HUMAN REVIEW REQUIRED]` - Sensitive item, check Done/REVIEW_* file

---

## Human Review Items

Files in `Done/REVIEW_*` need your attention:

```bash
# List items needing review
ls Done/REVIEW_*

# Read a flagged item
cat Done/REVIEW_EMAIL_urgent-payment.md
```

**Common reasons for review:**
- Contains keywords: payment, invoice, urgent, deadline
- Financial documents (receipts, bills)
- Contains credentials or sensitive info

**After reviewing:**
1. Take appropriate action (pay invoice, respond to email, etc.)
2. Keep file in Done/ for audit trail
3. Optionally rename to remove REVIEW_ prefix once handled

---

## Troubleshooting

### Files not being processed?

1. Check file is in `Needs_Action/`
2. Verify Claude Code is running
3. Check Dashboard.md for error logs
4. Look for `Done/ERROR_*` files

### Dashboard.md not updating?

1. Verify it has `## Recent Activity` section
2. Check file permissions (should be writable)
3. Review error messages in terminal

### Skills not working?

1. Verify skills exist:
   ```bash
   ls .claude/skills/task-triage/SKILL.md
   ls .claude/skills/file-handler/SKILL.md
   ```
2. Check skill documentation is readable

---

## Daily Workflow

1. **Morning:** Check Dashboard.md for overnight activity
2. **Throughout day:** Drop items into Needs_Action/
3. **As needed:** Process inbox via Claude Code
4. **Evening:** Review Done/REVIEW_* items requiring attention
5. **Weekly:** Archive old items from Done/ if needed

---

## Tips

- **Be specific with filenames**: `EMAIL_vendor-q4-proposal.md` is better than `EMAIL_1.md`
- **One item per file**: Don't batch multiple emails into one file
- **Use Markdown for emails**: Convert emails to .md format for best processing
- **Check REVIEW items daily**: Don't let sensitive items pile up
- **Monitor Dashboard statistics**: Track processing trends

---

## Support

- **Constitution**: `.specify/memory/constitution.md` - Core rules
- **Skills**: `.claude/skills/*/SKILL.md` - Workflow documentation
- **Company Handbook**: `System/Company_Handbook.md` - Custom rules

---

**Version**: 1.0
**Location**: Karachi, Pakistan
**Timezone**: PKT (UTC+5)
**Last Updated**: 2026-02-15
