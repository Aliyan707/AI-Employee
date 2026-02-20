#!/usr/bin/env python3
"""Watchdog — Process health monitor and auto-restart for AI Employee.

Monitors critical watcher processes and restarts them if they crash.
Implements exponential backoff on repeated failures.

Usage:
    python watchers/watchdog.py

Monitors (configurable via env vars):
    - gmail_watcher.py
    - filesystem_watcher.py

Sends a Dashboard.md alert when a process is restarted.

Based on Section 7 (Error States & Recovery) of Hackathone.md.
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import dotenv
dotenv.load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path(__file__).parent.parent))
GMAIL_CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "")
WATCHERS_DIR = Path(__file__).parent

# Check interval for watchdog (seconds)
WATCHDOG_INTERVAL = int(os.environ.get("WATCHDOG_INTERVAL", "30"))

# Max restart attempts before giving up on a process (resets after RESET_WINDOW_S)
MAX_RESTARTS = int(os.environ.get("MAX_RESTARTS", "5"))
RESET_WINDOW_S = int(os.environ.get("RESET_WINDOW_S", "3600"))  # 1 hour

PKT = timezone(timedelta(hours=5))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [watchdog] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(VAULT_PATH / "Logs" / "watchdog.log", mode="a"),
    ],
)
log = logging.getLogger("watchdog")


# ── Process registry ──────────────────────────────────────────────────────────

class ManagedProcess:
    """A process the watchdog keeps alive."""

    def __init__(self, name: str, cmd: list[str], extra_env: dict | None = None):
        self.name = name
        self.cmd = cmd
        self.extra_env = extra_env or {}
        self.proc: subprocess.Popen | None = None
        self.restart_count = 0
        self.restart_window_start = time.time()
        self.last_restart: float = 0.0
        self.backoff_s = 5  # starts at 5s, doubles each restart up to 300s

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self) -> None:
        env = os.environ.copy()
        env.update(self.extra_env)
        log.info("Starting process: %s  cmd=%s", self.name, " ".join(self.cmd))
        self.proc = subprocess.Popen(
            self.cmd,
            cwd=str(VAULT_PATH),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        self.last_restart = time.time()
        log.info("Started %s (pid=%s)", self.name, self.proc.pid)

    def restart(self) -> bool:
        """Restart with exponential backoff. Returns False if max restarts exceeded."""
        now = time.time()

        # Reset counter if outside the window
        if now - self.restart_window_start > RESET_WINDOW_S:
            self.restart_count = 0
            self.restart_window_start = now
            self.backoff_s = 5

        if self.restart_count >= MAX_RESTARTS:
            log.error(
                "Process %s exceeded max restarts (%d) in %ds — giving up",
                self.name, MAX_RESTARTS, RESET_WINDOW_S,
            )
            return False

        # Kill old process if still somehow running
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

        log.warning(
            "Restarting %s (attempt %d/%d) after %ds backoff",
            self.name, self.restart_count + 1, MAX_RESTARTS, self.backoff_s,
        )
        time.sleep(self.backoff_s)

        self.start()
        self.restart_count += 1
        self.backoff_s = min(self.backoff_s * 2, 300)  # max 5-minute backoff
        return True


# ── Vault helpers ─────────────────────────────────────────────────────────────

def _update_dashboard(message: str) -> None:
    dash = VAULT_PATH / "Dashboard.md"
    ts = datetime.now(PKT).strftime("%Y-%m-%d %H:%M PKT")
    line = f"- {ts}: {message}\n"
    try:
        content = dash.read_text(encoding="utf-8") if dash.exists() else "# Dashboard\n"
        if "## Recent Activity" in content:
            content = content.replace("## Recent Activity\n", f"## Recent Activity\n{line}", 1)
        else:
            content += f"\n## Recent Activity\n{line}"
        dash.write_text(content, encoding="utf-8")
    except Exception as exc:
        log.warning("Dashboard update failed: %s", exc)


def _log_entry(entry: dict) -> None:
    log_dir = VAULT_PATH / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now(PKT).strftime('%Y-%m-%d')}.md"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── Main watchdog loop ────────────────────────────────────────────────────────

def build_processes() -> list[ManagedProcess]:
    """Build the list of processes to monitor."""
    processes = []

    # Gmail watcher — only if credentials exist
    if GMAIL_CREDENTIALS_PATH and Path(GMAIL_CREDENTIALS_PATH).exists():
        processes.append(ManagedProcess(
            name="gmail_watcher",
            cmd=[
                sys.executable,
                str(WATCHERS_DIR / "gmail_watcher.py"),
                str(VAULT_PATH),
                GMAIL_CREDENTIALS_PATH,
            ],
        ))
    else:
        log.warning(
            "Gmail watcher skipped — GMAIL_CREDENTIALS_PATH not set or file missing"
        )

    # FileSystem watcher
    drop_folder = os.environ.get("DROP_FOLDER_PATH", str(VAULT_PATH / "Drop"))
    Path(drop_folder).mkdir(parents=True, exist_ok=True)
    processes.append(ManagedProcess(
        name="filesystem_watcher",
        cmd=[
            sys.executable,
            str(WATCHERS_DIR / "filesystem_watcher.py"),
            str(VAULT_PATH),
            drop_folder,
        ],
    ))

    return processes


def run_watchdog() -> None:
    processes = build_processes()
    if not processes:
        log.error("No processes to monitor — exiting")
        sys.exit(1)

    # Start all processes initially
    for p in processes:
        p.start()

    log.info(
        "Watchdog monitoring %d process(es), checking every %ds",
        len(processes), WATCHDOG_INTERVAL,
    )

    # Graceful shutdown on SIGTERM / SIGINT
    _shutdown = [False]

    def _handle_signal(sig, _frame):
        log.info("Received signal %s — shutting down watchdog", sig)
        _shutdown[0] = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    while not _shutdown[0]:
        time.sleep(WATCHDOG_INTERVAL)

        for p in processes:
            if _shutdown[0]:
                break
            if not p.is_alive():
                exit_code = p.proc.returncode if p.proc else -1
                log.warning(
                    "Process %s died (exit_code=%s) — attempting restart",
                    p.name, exit_code,
                )
                _update_dashboard(
                    f"[WATCHDOG] {p.name} crashed (exit={exit_code}) — restarting..."
                )
                _log_entry({
                    "timestamp": datetime.now(PKT).isoformat(),
                    "agent": "watchdog",
                    "action": "restart",
                    "process": p.name,
                    "exit_code": exit_code,
                    "restart_count": p.restart_count + 1,
                })

                ok = p.restart()
                if ok:
                    _update_dashboard(f"[WATCHDOG] {p.name} restarted (attempt {p.restart_count})")
                else:
                    _update_dashboard(
                        f"[WATCHDOG] ⚠️ {p.name} FAILED permanently — manual intervention needed"
                    )
                    _log_entry({
                        "timestamp": datetime.now(PKT).isoformat(),
                        "agent": "watchdog",
                        "action": "permanent_failure",
                        "process": p.name,
                    })

    # Clean shutdown
    log.info("Stopping all monitored processes...")
    for p in processes:
        if p.proc and p.proc.poll() is None:
            p.proc.terminate()
            try:
                p.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.proc.kill()
            log.info("Stopped %s", p.name)

    log.info("Watchdog shutdown complete")


if __name__ == "__main__":
    # Ensure log directory exists before handler is added
    (VAULT_PATH / "Logs").mkdir(parents=True, exist_ok=True)
    run_watchdog()
