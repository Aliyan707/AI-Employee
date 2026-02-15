#!/bin/bash
# Bronze-Tier Personal AI Employee - Automation Loop
# Location: Karachi, Pakistan (PKT, UTC+5)
# Version: 1.0

set -e  # Exit on error

VAULT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$VAULT_ROOT"

echo "========================================"
echo "Bronze AI Employee - Starting"
echo "Location: Karachi, Pakistan"
echo "Vault: $VAULT_ROOT"
echo "Started: $(date '+%Y-%m-%d %H:%M %Z')"
echo "========================================"
echo ""

# Verify required structure
echo "Verifying vault structure..."
for dir in Needs_Action Done Plans System .claude/skills/task-triage .claude/skills/file-handler; do
    if [ ! -d "$dir" ]; then
        echo "ERROR: Missing required directory: $dir"
        exit 1
    fi
done

if [ ! -f "Dashboard.md" ]; then
    echo "WARNING: Dashboard.md not found. Creating..."
    cat > Dashboard.md <<'EOF'
# AI Employee Dashboard

## Status
- Last Active: (not yet run)
- Items in Queue: 0
- Items Processed Today: 0
- Constitution Version: 1.0.0

## System Information
- Tier: Bronze (Filesystem-only)
- Location: Karachi, Pakistan (PKT, UTC+5)
- Active Skills: task-triage, file-handler
- Deployment: Obsidian vault on local machine

## Recent Activity
<!-- One-line logs in reverse chronological order -->

## Statistics
- Total Items Processed: 0
- High Priority: 0 | Medium: 0 | Low: 0
- Files Needing Review: 0
- Plans Created: 0
EOF
fi

echo "✓ Vault structure verified"
echo ""

# Main automation loop
CYCLE_COUNT=0

while true; do
    CYCLE_COUNT=$((CYCLE_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

    echo "========================================"
    echo "Cycle #$CYCLE_COUNT - $TIMESTAMP"
    echo "========================================"

    # Phase 1: Observe
    echo "Phase 1: Observing..."
    FILE_COUNT=$(find Needs_Action -maxdepth 1 -type f \( -name "*.md" -o -name "EMAIL_*" -o -name "FILE_*" \) 2>/dev/null | wc -l)

    if [ "$FILE_COUNT" -eq 0 ]; then
        echo "<idle>Needs_Action is empty</idle>"
        echo ""
        echo "No items to process. Sleeping 60 seconds..."
        echo ""
        sleep 60
        continue
    fi

    echo "Found $FILE_COUNT file(s) to process"

    # Phase 2-5: Process each file
    # NOTE: In Bronze tier, we rely on Claude Code to execute the skill workflows
    # This script triggers Claude Code with the appropriate context

    echo "Phase 2-5: Processing files..."
    echo "NOTE: Bronze tier uses Claude Code CLI for skill execution"
    echo ""
    echo "Files in queue:"
    ls -1 Needs_Action/
    echo ""
    echo "To process these files, you can either:"
    echo "  1. Run: claude --cwd \"$VAULT_ROOT\" --prompt 'Process all items in Needs_Action/'"
    echo "  2. Use the Claude Code chat and type: 'Process inbox'"
    echo "  3. Or continue this script will monitor for manual processing..."
    echo ""

    # For Bronze tier, we pause here and let the user trigger Claude Code manually
    # A more advanced tier would integrate Claude API calls here

    echo "Waiting for files to be processed (checking every 30 seconds)..."
    echo "Press Ctrl+C to stop monitoring"
    echo ""

    # Monitor loop - check if files are being processed
    WAIT_COUNT=0
    while [ "$FILE_COUNT" -gt 0 ] && [ "$WAIT_COUNT" -lt 20 ]; do
        sleep 30
        WAIT_COUNT=$((WAIT_COUNT + 1))
        NEW_COUNT=$(find Needs_Action -maxdepth 1 -type f \( -name "*.md" -o -name "EMAIL_*" -o -name "FILE_*" \) 2>/dev/null | wc -l)

        if [ "$NEW_COUNT" -lt "$FILE_COUNT" ]; then
            PROCESSED=$((FILE_COUNT - NEW_COUNT))
            echo "  ✓ $PROCESSED file(s) processed, $NEW_COUNT remaining..."
            FILE_COUNT=$NEW_COUNT
        fi

        if [ "$NEW_COUNT" -eq 0 ]; then
            echo "  ✓ All files processed!"
            break
        fi
    done

    if [ "$FILE_COUNT" -gt 0 ]; then
        echo "  Note: $FILE_COUNT file(s) still pending after 10 minutes of monitoring"
        echo "  These may require manual processing or Claude Code invocation"
    fi

    echo ""
    echo "<cycle-complete>"
    echo "Cycle #$CYCLE_COUNT finished at $(date '+%Y-%m-%d %H:%M')"
    echo "</cycle-complete>"
    echo ""
    echo "Starting next cycle in 60 seconds..."
    echo ""
    sleep 60
done
