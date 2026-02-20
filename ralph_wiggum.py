#!/usr/bin/env python3
"""Ralph Wiggum — Autonomous task completion loop for Gold-tier AI Employee.

Named after the pattern described in Hackathone.md Section 2D.
Keeps Claude working until a task file is confirmed moved to /Done.

Usage:
    python ralph_wiggum.py --prompt "Process all files in Needs_Action/" \\
                            --task-id "TASK_001" \\
                            --max-iterations 10

How it works:
    1. Creates a state file in /Flags/ with the task ID and prompt
    2. Launches `claude` with the prompt
    3. After Claude exits, checks if the task has landed in /Done
    4. If NOT in /Done: re-invokes Claude with the same prompt (up to max_iterations)
    5. If in /Done: exits successfully
    6. State file is cleaned up on success or max-iteration abort

The stop hook (.claude/hooks/ralph_wiggum_stop.py) integrates with Claude
Code's Stop event to perform the same check inside the Claude process.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

PKT = timezone(timedelta(hours=5))

VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path(__file__).parent))
FLAGS_DIR = VAULT_PATH / "Flags"
DONE_DIR = VAULT_PATH / "Done"
LOGS_DIR = VAULT_PATH / "Logs"


def _log(msg: str) -> None:
    ts = datetime.now(PKT).strftime("%Y-%m-%d %H:%M:%S PKT")
    print(f"[ralph-wiggum] {ts}  {msg}", flush=True)


def _write_state(task_id: str, prompt: str, iteration: int) -> Path:
    """Write current loop state to Flags/<task_id>.json."""
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "task_id": task_id,
        "prompt": prompt,
        "iteration": iteration,
        "started_at": datetime.now(PKT).isoformat(),
        "status": "in_progress",
    }
    state_file = FLAGS_DIR / f"{task_id}.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state_file


def _clear_state(state_file: Path) -> None:
    try:
        state_file.unlink(missing_ok=True)
    except Exception:
        pass


def _task_in_done(task_id: str) -> bool:
    """Return True if any file matching the task_id exists under Done/."""
    if not DONE_DIR.exists():
        return False
    for f in DONE_DIR.rglob(f"*{task_id}*"):
        return True
    return False


def _promise_detected(output: str) -> bool:
    """Return True if Claude output contains the completion promise tag."""
    return "<promise>TASK_COMPLETE</promise>" in output


def _append_audit_log(task_id: str, status: str, iterations: int) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{datetime.now(PKT).strftime('%Y-%m-%d')}.md"
    entry = {
        "timestamp": datetime.now(PKT).isoformat(),
        "agent": "ralph-wiggum",
        "task_id": task_id,
        "status": status,
        "iterations_used": iterations,
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run_loop(prompt: str, task_id: str, max_iterations: int = 10) -> int:
    """
    Main Ralph Wiggum loop.

    Returns exit code: 0 = task complete, 1 = max iterations reached, 2 = error.
    """
    _log(f"Starting loop for task_id='{task_id}', max_iterations={max_iterations}")
    _log(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

    state_file = _write_state(task_id, prompt, 0)

    for iteration in range(1, max_iterations + 1):
        _log(f"--- Iteration {iteration}/{max_iterations} ---")

        # Update state file
        _write_state(task_id, prompt, iteration)

        # Build claude invocation
        # Uses `claude` CLI with --print flag for non-interactive mode
        cmd = [
            "claude",
            "--print",
            "--no-conversation",
            prompt,
        ]

        _log(f"Invoking: {' '.join(cmd[:3])} ...")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(VAULT_PATH),
                capture_output=False,
                text=True,
                timeout=300,  # 5-minute timeout per iteration
            )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            _log(f"TIMEOUT on iteration {iteration} — re-injecting")
            time.sleep(5)
            continue
        except FileNotFoundError:
            _log("ERROR: 'claude' CLI not found in PATH. Is Claude Code installed?")
            _clear_state(state_file)
            return 2

        _log(f"Claude exited with code {exit_code}")

        # Check completion: file-based (reliable)
        if _task_in_done(task_id):
            _log(f"SUCCESS: task '{task_id}' found in Done/ — loop complete")
            _clear_state(state_file)
            _append_audit_log(task_id, "completed", iteration)
            return 0

        # Check completion: promise-based (simple fallback)
        # Note: with --print mode, stdout is the conversation output
        # We check stdout via the process output if captured
        _log(f"Task not yet in Done/ — continuing to iteration {iteration + 1}")
        time.sleep(3)  # brief pause before retry

    # Exhausted iterations
    _log(f"MAX ITERATIONS ({max_iterations}) reached — aborting loop for '{task_id}'")
    _clear_state(state_file)
    _append_audit_log(task_id, "max_iterations_reached", max_iterations)
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum — autonomous task completion loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--prompt", "-p", required=True,
        help="The prompt/instruction for Claude to execute each iteration",
    )
    parser.add_argument(
        "--task-id", "-t", required=True,
        help="Unique task identifier used to detect completion in Done/",
    )
    parser.add_argument(
        "--max-iterations", "-n", type=int, default=10,
        help="Maximum number of Claude invocations before giving up (default: 10)",
    )
    args = parser.parse_args()

    exit_code = run_loop(
        prompt=args.prompt,
        task_id=args.task_id,
        max_iterations=args.max_iterations,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
