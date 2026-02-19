#!/usr/bin/env python3
"""Email MCP Server — Python implementation.

Sends approved emails via Gmail API with full HITL vault workflow:
  Approved/EMAIL_*.md → validate → send → Done/Email/SENT_*.md

Uses: mcp (PyPI), google-api-python-client, python-dotenv
"""

import base64
import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from pathlib import Path

import dotenv
dotenv.load_dotenv()

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────
VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path(__file__).parent.parent.parent))
GMAIL_CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "")
GMAIL_TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "")

PKT = timezone(timedelta(hours=5))

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [email-mcp] %(levelname)s %(message)s",
)
log = logging.getLogger("email-mcp")

mcp = FastMCP("email-mcp")


# ── Gmail helpers ─────────────────────────────────────────────────────────────

def _gmail_service():
    """Return an authenticated Gmail service. Raises if token missing."""
    token_path = GMAIL_TOKEN_PATH or str(VAULT_PATH / "System" / "gmail_token.json")
    if not Path(token_path).exists():
        raise RuntimeError(
            "Gmail token not found. Run watchers/gmail_watcher.py first to complete OAuth."
        )
    creds = Credentials.from_authorized_user_file(token_path)
    return build("gmail", "v1", credentials=creds)


def _parse_email_file(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter + body from vault email markdown file."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        raise ValueError("Invalid email file: missing YAML frontmatter block")
    fm: dict = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([\w-]+):\s*(.+)$", line)
        if kv:
            fm[kv.group(1).strip()] = kv.group(2).strip()
    return fm, m.group(2).strip()


def _validate(path: Path) -> list[str]:
    """Return list of validation errors (empty list = OK to send)."""
    errors: list[str] = []
    if not path.exists():
        return ["File does not exist"]
    # Must live in Approved/
    if "Approved" not in path.parts:
        errors.append("File must be in the Approved/ folder")
    try:
        fm, body = _parse_email_file(path)
        for field in ("to", "from", "subject"):
            if not fm.get(field):
                errors.append(f"Missing required frontmatter field: {field}")
        if not body:
            errors.append("Email body is empty")
        if ts := fm.get("timestamp"):
            try:
                approval_dt = datetime.fromisoformat(ts)
                if approval_dt.tzinfo is None:
                    approval_dt = approval_dt.replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - approval_dt).total_seconds() / 3600
                if age_h > 24:
                    errors.append(f"Approval expired ({age_h:.0f}h old, max 24h)")
            except ValueError:
                pass  # unparseable timestamp — skip age check
        if fm.get("error") or "ERROR:" in body:
            errors.append("File contains an ERROR flag — resolve before sending")
    except Exception as exc:
        errors.append(f"Parse error: {exc}")
    return errors


def _send_gmail(to: str, subject: str, body: str, from_addr: str) -> str:
    """Send via Gmail API. Returns the sent message ID."""
    svc = _gmail_service()
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to
    msg["from"] = from_addr
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
    return result["id"]


# ── Vault helpers ─────────────────────────────────────────────────────────────

def _log_entry(entry: dict) -> None:
    log_dir = VAULT_PATH / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now(PKT).strftime('%Y-%m-%d')}.md"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


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


def _move_back_with_error(path: Path, error_msg: str) -> None:
    """Return file to Pending_Approval/ with error note appended."""
    pending = VAULT_PATH / "Pending_Approval" / path.name
    try:
        pending.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(pending))
        with pending.open("a", encoding="utf-8") as f:
            f.write(
                f"\n\n## ERROR (email-mcp)\n{error_msg}\n"
                f"Timestamp: {datetime.now(PKT).isoformat()}\n"
            )
    except Exception as exc:
        log.error("Failed to move file back to Pending_Approval/: %s", exc)


# ── MCP Tool ──────────────────────────────────────────────────────────────────

@mcp.tool()
def send_email(file_path: str) -> dict:
    """Send an approved email via Gmail API.

    Reads a Markdown file from Approved/ with YAML frontmatter fields:
      to, from, subject  (required)
      timestamp          (optional — checked for 24h expiry)

    On success: moves file to Done/Email/SENT_<name>.md and logs.
    On failure: moves file back to Pending_Approval/ with error note.

    Args:
        file_path: Path to approved email file, relative to vault root or absolute.
    """
    abs_path = Path(file_path) if Path(file_path).is_absolute() else VAULT_PATH / file_path
    filename = abs_path.name

    log.info("Processing send request: %s", filename)

    # 1. Validate
    errors = _validate(abs_path)
    if errors:
        err_msg = "\n".join(errors)
        log.error("Validation failed: %s", err_msg)
        _move_back_with_error(abs_path, err_msg)
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "email-mcp",
            "action": "send_email", "file": filename, "status": "validation_error",
            "metadata": {"errors": errors},
        })
        _update_dashboard(f"[ERROR] Email validation failed: {filename}")
        return {"success": False, "error": err_msg}

    # 2. Parse
    fm, body = _parse_email_file(abs_path)
    to, from_addr, subject = fm["to"], fm["from"], fm["subject"]

    # 3. Send
    try:
        msg_id = _send_gmail(to, subject, body, from_addr)
        log.info("Sent OK — message_id=%s to=%s", msg_id, to)

        # 4. Move to Done/Email/
        done_dir = VAULT_PATH / "Done" / "Email"
        done_dir.mkdir(parents=True, exist_ok=True)
        dest = done_dir / f"SENT_{filename}"
        shutil.move(str(abs_path), str(dest))

        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "email-mcp",
            "action": "send_email", "file": filename, "status": "completed",
            "metadata": {"to": to, "subject": subject, "message_id": msg_id},
        })
        _update_dashboard(f'[SENT] Email to {to}: "{subject}"')

        return {
            "success": True,
            "message": f"Email sent to {to}",
            "message_id": msg_id,
            "moved_to": str(dest),
        }

    except Exception as exc:
        log.error("Send failed: %s", exc)
        _move_back_with_error(abs_path, str(exc))
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "email-mcp",
            "action": "send_email", "file": filename, "status": "error",
            "metadata": {"to": to, "subject": subject, "error": str(exc)},
        })
        _update_dashboard(f"[ERROR] Failed to send email to {to}: {exc}")
        return {"success": False, "error": str(exc)}


if __name__ == "__main__":
    mcp.run()
