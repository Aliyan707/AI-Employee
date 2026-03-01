#!/usr/bin/env python3
"""Ralph Wiggum Stop Hook — Claude Code Stop event handler.

Registered in .claude/settings.json under hooks.Stop.
When Claude tries to stop, this hook checks if the active task is complete.
If not, it exits with code 2 to block the stop and injects a continuation prompt.

Claude Code Stop hook contract:
  - Receives JSON on stdin with current state information
  - Exit code 0 = allow Claude to stop (task complete)
  - Exit code 2 = block stop, stdout is injected as next user message
  - Exit code 1 = allow stop (error in hook — fail open)

Configuration in .claude/settings.json:
  {
    "hooks": {
      "Stop": [{
        "matcher": "",
        "hooks": [{
          "type": "command",
          "command": "python .claude/hooks/ralph_wiggum_stop.py"
        }]
      }]
    }
  }
"""

import json
import os
import sys
from pathlib import Path

VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path(__file__).parent.parent.parent))
FLAGS_DIR = VAULT_PATH / "Flags"
DONE_DIR = VAULT_PATH / "Done"


def _read_stdin_state() -> dict:
    """Read JSON state from stdin (Claude Code passes hook data via stdin)."""
    try:
        raw = sys.stdin.read()
        if raw.strip():
            return json.loads(raw)
    except Exception:
        pass
    return {}


def _active_task_id() -> str | None:
    """Find the active Ralph Wiggum task ID from Flags/ directory."""
    if not FLAGS_DIR.exists():
        return None
    for flag_file in FLAGS_DIR.glob("*.json"):
        try:
            data = json.loads(flag_file.read_text(encoding="utf-8"))
            if data.get("status") == "in_progress":
                return data.get("task_id")
        except Exception:
            continue
    return None


def _task_in_done(task_id: str) -> bool:
    """Return True if any file matching the task_id exists under Done/."""
    if not DONE_DIR.exists():
        return False
    for _ in DONE_DIR.rglob(f"*{task_id}*"):
        return True
    return False


def main() -> None:
    _read_stdin_state()  # Consume stdin even if unused

    task_id = _active_task_id()

    if task_id is None:
        # No active Ralph Wiggum task — allow normal stop
        sys.exit(0)

    if _task_in_done(task_id):
        # Task complete — allow stop
        sys.exit(0)

    # Task NOT complete — block stop and inject continuation prompt
    continuation = (
        f"The task '{task_id}' is not yet complete — it has not appeared in the Done/ folder. "
        "Continue working until the task file is moved to Done/. "
        "Check Needs_Action/ for remaining items, process them, and update the Dashboard."
    )
    print(continuation, end="")
    sys.exit(2)


if __name__ == "__main__":
    main()
