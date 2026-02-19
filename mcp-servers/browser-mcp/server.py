#!/usr/bin/env python3
"""Browser MCP Server — Python implementation.

Posts approved content to LinkedIn via Playwright browser automation:
  Approved/SOCIAL_linkedin_*.md → validate → post → Done/Social/POSTED_*.md

Uses: mcp (PyPI), playwright (Python), python-dotenv
"""

import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import dotenv
dotenv.load_dotenv()

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────
VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path(__file__).parent.parent.parent))
LINKEDIN_EMAIL = os.environ.get("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD", "")
SESSION_DIR = Path(
    os.environ.get("LINKEDIN_SESSION_PATH", Path(__file__).parent / "linkedin-session")
)
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT = int(os.environ.get("BROWSER_TIMEOUT", "30000"))

PKT = timezone(timedelta(hours=5))

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [browser-mcp] %(levelname)s %(message)s",
)
log = logging.getLogger("browser-mcp")

mcp = FastMCP("browser-mcp")


# ── File helpers ──────────────────────────────────────────────────────────────

def _parse_social_file(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter + content from vault social markdown file."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        raise ValueError("Missing YAML frontmatter block")
    fm: dict = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([\w-]+):\s*(.+)$", line)
        if kv:
            fm[kv.group(1).strip()] = kv.group(2).strip()
    return fm, m.group(2).strip()


def _validate_social(path: Path, platform: str) -> list[str]:
    """Return list of validation errors (empty = OK to post)."""
    errors: list[str] = []
    if not path.exists():
        return ["File does not exist"]
    if "Approved" not in path.parts:
        errors.append("File must be in the Approved/ folder")
    try:
        fm, content = _parse_social_file(path)
        file_platform = fm.get("platform", "").lower()
        if file_platform != platform:
            errors.append(
                f"Platform mismatch: expected '{platform}', got '{file_platform or 'none'}'"
            )
        if not content or len(content.strip()) < 10:
            errors.append("Post content is too short (minimum 10 characters)")
        if fm.get("error"):
            errors.append("File contains an ERROR flag — resolve before posting")
        if ts := fm.get("timestamp"):
            try:
                approval_dt = datetime.fromisoformat(ts)
                if approval_dt.tzinfo is None:
                    approval_dt = approval_dt.replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - approval_dt).total_seconds() / 3600
                if age_h > 24:
                    errors.append(f"Approval expired ({age_h:.0f}h old, max 24h)")
            except ValueError:
                pass
    except Exception as exc:
        errors.append(f"Parse error: {exc}")
    return errors


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
    pending = VAULT_PATH / "Pending_Approval" / path.name
    try:
        pending.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(pending))
        with pending.open("a", encoding="utf-8") as f:
            f.write(
                f"\n\n## ERROR (browser-mcp)\n{error_msg}\n"
                f"Timestamp: {datetime.now(PKT).isoformat()}\n"
            )
    except Exception as exc:
        log.error("Failed to move file back: %s", exc)


# ── LinkedIn Playwright automation ────────────────────────────────────────────

def _post_linkedin_sync(content: str) -> None:
    """Post to LinkedIn using Playwright synchronous API."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(SESSION_DIR),
            headless=HEADLESS,
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Asia/Karachi",
        )
        page = ctx.new_page()
        page.set_default_timeout(BROWSER_TIMEOUT)

        try:
            # Check login status
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            if "feed" not in page.url:
                log.info("Session expired — logging in...")
                if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
                    raise RuntimeError(
                        "LINKEDIN_EMAIL and LINKEDIN_PASSWORD required. "
                        "Set them in mcp-servers/browser-mcp/.env"
                    )
                page.goto("https://www.linkedin.com/login")
                page.fill("#username", LINKEDIN_EMAIL)
                page.fill("#password", LINKEDIN_PASSWORD)
                page.click('button[type="submit"]')
                page.wait_for_url("**/feed/**", timeout=20000)
                log.info("Login successful — session saved")

            # Open post composer
            log.info("Opening post composer...")
            composer_selectors = [
                '[data-control-name="share.sharebox_open"]',
                'button:has-text("Start a post")',
                '[class*="share-box-feed-entry__trigger"]',
                'button:has-text("Post")',
            ]
            clicked = False
            for sel in composer_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=5000)
                    btn.click()
                    clicked = True
                    break
                except Exception:
                    continue
            if not clicked:
                raise RuntimeError("Could not find LinkedIn post composer button")

            page.wait_for_timeout(1500)

            # Fill post content
            editor_selectors = [
                '[role="textbox"]',
                '.ql-editor',
                '[contenteditable="true"]',
                '.editor-content',
            ]
            filled = False
            for sel in editor_selectors:
                try:
                    editor = page.locator(sel).first
                    editor.wait_for(timeout=5000)
                    editor.click()
                    editor.fill(content)
                    filled = True
                    break
                except Exception:
                    continue
            if not filled:
                raise RuntimeError("Could not find LinkedIn post text editor")

            page.wait_for_timeout(1000)

            # Click Post / Submit button
            post_selectors = [
                'button:has-text("Post")',
                '[data-control-name="share.post"]',
                'button.share-actions__primary-action',
            ]
            posted = False
            for sel in post_selectors:
                try:
                    btn = page.locator(sel).last
                    btn.wait_for(timeout=5000)
                    btn.click()
                    posted = True
                    break
                except Exception:
                    continue
            if not posted:
                raise RuntimeError("Could not find LinkedIn Post submit button")

            page.wait_for_timeout(3000)
            log.info("LinkedIn post published successfully")

        except PlaywrightTimeout as exc:
            raise RuntimeError(f"Browser timeout during LinkedIn post: {exc}") from exc
        finally:
            ctx.close()


# ── MCP Tool ──────────────────────────────────────────────────────────────────

@mcp.tool()
def post_to_linkedin(file_path: str) -> dict:
    """Post approved content to LinkedIn via Playwright browser automation.

    Reads a Markdown file from Approved/ with YAML frontmatter:
      platform: linkedin  (required)
      timestamp           (optional — checked for 24h expiry)

    On success: moves file to Done/Social/POSTED_<name>.md and logs.
    On failure: moves file back to Pending_Approval/ with error note.

    First-time setup: Set HEADLESS=false in .env, run once to complete 2FA,
    then set HEADLESS=true. Session is saved to linkedin-session/.

    Args:
        file_path: Path to approved social file, relative to vault root or absolute.
    """
    abs_path = Path(file_path) if Path(file_path).is_absolute() else VAULT_PATH / file_path
    filename = abs_path.name

    log.info("Processing LinkedIn post request: %s", filename)

    # 1. Validate
    errors = _validate_social(abs_path, "linkedin")
    if errors:
        err_msg = "\n".join(errors)
        log.error("Validation failed: %s", err_msg)
        _move_back_with_error(abs_path, err_msg)
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "browser-mcp",
            "action": "post_to_linkedin", "file": filename, "status": "validation_error",
            "metadata": {"errors": errors},
        })
        _update_dashboard(f"[ERROR] LinkedIn post validation failed: {filename}")
        return {"success": False, "error": err_msg}

    # 2. Parse content
    _, content = _parse_social_file(abs_path)

    # 3. Post
    try:
        _post_linkedin_sync(content)

        # 4. Move to Done/Social/
        done_dir = VAULT_PATH / "Done" / "Social"
        done_dir.mkdir(parents=True, exist_ok=True)
        dest = done_dir / f"POSTED_{filename}"
        shutil.move(str(abs_path), str(dest))

        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "browser-mcp",
            "action": "post_to_linkedin", "file": filename, "status": "completed",
            "metadata": {"content_length": len(content)},
        })
        _update_dashboard(f"[POSTED] LinkedIn post published: {filename}")

        return {
            "success": True,
            "message": "LinkedIn post published successfully",
            "moved_to": str(dest),
        }

    except Exception as exc:
        log.error("LinkedIn post failed: %s", exc)
        _move_back_with_error(abs_path, str(exc))
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "browser-mcp",
            "action": "post_to_linkedin", "file": filename, "status": "error",
            "metadata": {"error": str(exc)},
        })
        _update_dashboard(f"[ERROR] LinkedIn post failed: {exc}")
        return {"success": False, "error": str(exc)}


if __name__ == "__main__":
    mcp.run()
