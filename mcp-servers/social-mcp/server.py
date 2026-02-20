#!/usr/bin/env python3
"""Social MCP Server — Facebook, Instagram, and Twitter/X integration.

Gold-tier AI Employee social posting tools:
  post_to_facebook   — Playwright browser automation (email/password login)
  post_to_instagram  — Playwright browser automation (email/password login)
  post_to_twitter    — Twitter API v2 via tweepy
  get_social_summary — Aggregate recent post stats from Done/Social/

All tools follow the vault HITL workflow:
  Approved/SOCIAL_<platform>_*.md → validate → post → Done/Social/POSTED_*.md

Uses: mcp (PyPI), playwright (Python), tweepy, python-dotenv
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

import tweepy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────
VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path(__file__).parent.parent.parent))

# Facebook (browser-based)
FB_EMAIL = os.environ.get("Facebook_EMAIL", "")
FB_PASSWORD = os.environ.get("Facebook_PASSWORD", "")
FB_SESSION_DIR = Path(os.environ.get(
    "FB_SESSION_PATH", Path(__file__).parent / "facebook-session"
))

# Instagram (browser-based)
IG_EMAIL = os.environ.get("Instagram__EMAIL", "") or os.environ.get("Instagram_EMAIL", "")
IG_PASSWORD = os.environ.get("Instagram_PASSWORD", "")
IG_SESSION_DIR = Path(os.environ.get(
    "IG_SESSION_PATH", Path(__file__).parent / "instagram-session"
))

# Twitter / X
TW_BEARER_TOKEN = os.environ.get("TW_BEARER_TOKEN", "")
TW_API_KEY = os.environ.get("TW_API_KEY", "")
TW_API_SECRET = os.environ.get("TW_API_SECRET", "")
TW_ACCESS_TOKEN = os.environ.get("TW_ACCESS_TOKEN", "")
TW_ACCESS_SECRET = os.environ.get("TW_ACCESS_SECRET", "")

HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT = int(os.environ.get("BROWSER_TIMEOUT", "30000"))
PKT = timezone(timedelta(hours=5))

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [social-mcp] %(levelname)s %(message)s",
)
log = logging.getLogger("social-mcp")

mcp = FastMCP("social-mcp")


# ── Shared file helpers ───────────────────────────────────────────────────────

def _parse_file(path: Path) -> tuple[dict, str]:
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


def _validate(path: Path, platform: str) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return ["File does not exist"]
    if "Approved" not in path.parts:
        errors.append("File must be in the Approved/ folder")
    try:
        fm, content = _parse_file(path)
        file_platform = fm.get("platform", "").lower()
        if file_platform != platform:
            errors.append(
                f"Platform mismatch: expected '{platform}', got '{file_platform or 'none'}'"
            )
        if not content or len(content.strip()) < 5:
            errors.append("Post content is too short")
        if fm.get("error"):
            errors.append("File contains an ERROR flag")
        if ts := fm.get("timestamp"):
            try:
                dt = datetime.fromisoformat(ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                if age_h > 24:
                    errors.append(f"Approval expired ({age_h:.0f}h old, max 24h)")
            except ValueError:
                pass
    except Exception as exc:
        errors.append(f"Parse error: {exc}")
    return errors


# ── Vault helpers ─────────────────────────────────────────────────────────────

def _done_dir() -> Path:
    d = VAULT_PATH / "Done" / "Social"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _move_back_with_error(path: Path, error_msg: str) -> None:
    pending = VAULT_PATH / "Pending_Approval" / path.name
    try:
        pending.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(pending))
        with pending.open("a", encoding="utf-8") as f:
            f.write(
                f"\n\n## ERROR (social-mcp)\n{error_msg}\n"
                f"Timestamp: {datetime.now(PKT).isoformat()}\n"
            )
    except Exception as exc:
        log.error("Move back failed: %s", exc)


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


# ── Facebook (Playwright) ─────────────────────────────────────────────────────

def _post_facebook_browser(content: str) -> str:
    """Post to Facebook personal profile/page via Playwright. Returns 'posted'."""
    if not FB_EMAIL or not FB_PASSWORD:
        raise RuntimeError(
            "Facebook_EMAIL and Facebook_PASSWORD required in mcp-servers/social-mcp/.env"
        )
    FB_SESSION_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(FB_SESSION_DIR),
            headless=HEADLESS,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = ctx.new_page()
        page.set_default_timeout(BROWSER_TIMEOUT)

        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Login if needed
            if "login" in page.url or page.locator('[name="email"]').is_visible():
                log.info("Facebook: logging in...")
                page.fill('[name="email"]', FB_EMAIL)
                page.fill('[name="pass"]', FB_PASSWORD)
                page.wait_for_timeout(500)
                # Facebook login button is input[type="submit"] (may be CSS-hidden)
                # Try multiple approaches in order
                clicked = False
                # 1. Try JS click on submit (works even when visually hidden)
                try:
                    page.evaluate('document.querySelector("input[type=submit]").click()')
                    clicked = True
                    log.info("Facebook: clicked login via JS evaluate")
                except Exception:
                    pass
                # 2. Try Enter key on password field
                if not clicked:
                    try:
                        page.locator('[name="pass"]').press("Return")
                        clicked = True
                        log.info("Facebook: submitted login via Return key")
                    except Exception:
                        pass
                # 3. Try visible button selectors
                if not clicked:
                    for sel in ['[name="login"]', 'button[type="submit"]']:
                        try:
                            btn = page.locator(sel).first
                            btn.wait_for(timeout=3000)
                            btn.click()
                            clicked = True
                            log.info("Facebook: clicked login via '%s'", sel)
                            break
                        except Exception:
                            continue
                if not clicked:
                    raise RuntimeError("Could not find Facebook login button")
                page.wait_for_timeout(5000)
                # Verify login succeeded by checking for session cookies
                cookies = page.context.cookies()
                session_ok = any(
                    c.get('name', '') in ('c_user', 'xs') for c in cookies
                    if 'facebook.com' in c.get('domain', '')
                )
                if not session_ok and page.locator('[name="email"]').is_visible():
                    raise RuntimeError(
                        "Facebook login failed — check Facebook_EMAIL and Facebook_PASSWORD in .env"
                    )
                log.info("Facebook: login complete")

            # Navigate to home feed
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Click "What's on your mind?" composer
            composer_selectors = [
                '[aria-label="What\'s on your mind?"]',
                'div[role="button"]:has-text("What\'s on your mind")',
                '[data-pagelet="FeedComposer"] div[role="button"]',
            ]
            opened = False
            for sel in composer_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=5000)
                    btn.click()
                    opened = True
                    log.info("Facebook: opened composer via '%s'", sel)
                    break
                except Exception:
                    continue

            if not opened:
                # Try clicking on the text input area directly
                page.locator('[placeholder*="mind"]').first.click()

            page.wait_for_timeout(1500)

            # Type content in the post editor
            editor = page.locator('[contenteditable="true"][role="textbox"]').first
            editor.wait_for(timeout=8000)
            editor.click()
            editor.fill(content)
            page.wait_for_timeout(1000)

            # Click Post button
            post_btn = page.locator(
                'div[aria-label="Post"]:not([aria-disabled="true"]), '
                'button:has-text("Post"):not([disabled])'
            ).last
            post_btn.wait_for(timeout=8000)
            post_btn.click()
            page.wait_for_timeout(3000)

            log.info("Facebook: post published successfully")
            return "posted"

        except PlaywrightTimeout as exc:
            raise RuntimeError(f"Facebook browser timeout: {exc}") from exc
        finally:
            ctx.close()


@mcp.tool()
def post_to_facebook(file_path: str) -> dict:
    """Post approved content to Facebook via browser automation.

    Uses Playwright with a persistent session (no re-login required after first run).
    File must be in Approved/ with YAML frontmatter: platform: facebook

    On success: moves file to Done/Social/POSTED_<name>.md and logs.
    On failure: moves file back to Pending_Approval/ with error note.

    Args:
        file_path: Path to approved social file, relative to vault root or absolute.
    """
    abs_path = Path(file_path) if Path(file_path).is_absolute() else VAULT_PATH / file_path
    filename = abs_path.name

    errors = _validate(abs_path, "facebook")
    if errors:
        err_msg = "\n".join(errors)
        _move_back_with_error(abs_path, err_msg)
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_facebook", "file": filename, "status": "validation_error",
            "metadata": {"errors": errors},
        })
        _update_dashboard(f"[ERROR] Facebook validation failed: {filename}")
        return {"success": False, "error": err_msg}

    _, content = _parse_file(abs_path)

    try:
        _post_facebook_browser(content)
        dest = _done_dir() / f"POSTED_{filename}"
        shutil.move(str(abs_path), str(dest))
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_facebook", "file": filename, "status": "completed",
            "metadata": {"content_length": len(content)},
        })
        _update_dashboard(f"[POSTED] Facebook post published: {filename}")
        return {"success": True, "message": "Facebook post published", "moved_to": str(dest)}

    except Exception as exc:
        log.error("Facebook post failed: %s", exc)
        _move_back_with_error(abs_path, str(exc))
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_facebook", "file": filename, "status": "error",
            "metadata": {"error": str(exc)},
        })
        _update_dashboard(f"[ERROR] Facebook post failed: {exc}")
        return {"success": False, "error": str(exc)}


# ── Instagram (Playwright) ────────────────────────────────────────────────────

def _post_instagram_browser(caption: str) -> str:
    """Post to Instagram via Playwright browser automation. Returns 'posted'."""
    if not IG_EMAIL or not IG_PASSWORD:
        raise RuntimeError(
            "Instagram_EMAIL and Instagram_PASSWORD required in mcp-servers/social-mcp/.env"
        )
    IG_SESSION_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(IG_SESSION_DIR),
            headless=HEADLESS,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            locale="en-US",
        )
        page = ctx.new_page()
        page.set_default_timeout(BROWSER_TIMEOUT)

        try:
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Login if needed
            if page.locator('input[name="username"]').is_visible():
                log.info("Instagram: logging in...")
                page.fill('input[name="username"]', IG_EMAIL)
                page.fill('input[name="password"]', IG_PASSWORD)
                page.click('button[type="submit"]')
                page.wait_for_timeout(4000)
                # Handle "Save login info" prompt
                try:
                    page.locator('button:has-text("Not now"), button:has-text("Not Now")').first.click()
                    page.wait_for_timeout(1000)
                except Exception:
                    pass
                # Handle notifications prompt
                try:
                    page.locator('button:has-text("Not Now")').first.click()
                    page.wait_for_timeout(1000)
                except Exception:
                    pass
                log.info("Instagram: login complete")

            # Click the + (New Post) button
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            new_post_selectors = [
                'svg[aria-label="New post"]',
                '[aria-label="New post"]',
                'a[href="/create/style/"]',
                'svg[aria-label="Plus"]',
            ]
            found = False
            for sel in new_post_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=5000)
                    btn.click()
                    found = True
                    log.info("Instagram: opened new post via '%s'", sel)
                    break
                except Exception:
                    continue

            if not found:
                # Try direct navigation to create page
                page.goto("https://www.instagram.com/create/style/", wait_until="domcontentloaded")
                page.wait_for_timeout(2000)

            page.wait_for_timeout(1500)

            # Instagram requires an image to create a post
            # For text-only posts, we use the caption field in the post dialog
            # Look for file input or caption
            caption_area = page.locator('textarea[aria-label*="caption"], div[contenteditable="true"]').first
            try:
                caption_area.wait_for(timeout=5000)
                caption_area.click()
                caption_area.fill(caption)
                page.wait_for_timeout(1000)

                # Try to find and click Share button
                share_btn = page.locator('button:has-text("Share"), button:has-text("Post")').last
                share_btn.wait_for(timeout=8000)
                share_btn.click()
                page.wait_for_timeout(3000)
                log.info("Instagram: post published successfully")
                return "posted"
            except Exception:
                # Instagram text-only posts not supported without image
                raise RuntimeError(
                    "Instagram requires an image for posts. "
                    "Add an image_url to the frontmatter or use image upload. "
                    "Instagram text-only posts are not supported via web."
                )

        except PlaywrightTimeout as exc:
            raise RuntimeError(f"Instagram browser timeout: {exc}") from exc
        finally:
            ctx.close()


@mcp.tool()
def post_to_instagram(file_path: str) -> dict:
    """Post approved content to Instagram via browser automation.

    Note: Instagram requires an image for feed posts. The post body serves
    as the caption. Add image_url in frontmatter for image context.

    File must be in Approved/ with YAML frontmatter: platform: instagram

    On success: moves file to Done/Social/POSTED_<name>.md and logs.
    On failure: moves file back to Pending_Approval/ with error note.

    Args:
        file_path: Path to approved social file, relative to vault root or absolute.
    """
    abs_path = Path(file_path) if Path(file_path).is_absolute() else VAULT_PATH / file_path
    filename = abs_path.name

    errors = _validate(abs_path, "instagram")
    if errors:
        err_msg = "\n".join(errors)
        _move_back_with_error(abs_path, err_msg)
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_instagram", "file": filename, "status": "validation_error",
            "metadata": {"errors": errors},
        })
        _update_dashboard(f"[ERROR] Instagram validation failed: {filename}")
        return {"success": False, "error": err_msg}

    _, content = _parse_file(abs_path)

    try:
        _post_instagram_browser(content)
        dest = _done_dir() / f"POSTED_{filename}"
        shutil.move(str(abs_path), str(dest))
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_instagram", "file": filename, "status": "completed",
            "metadata": {"content_length": len(content)},
        })
        _update_dashboard(f"[POSTED] Instagram post published: {filename}")
        return {"success": True, "message": "Instagram post published", "moved_to": str(dest)}

    except Exception as exc:
        log.error("Instagram post failed: %s", exc)
        _move_back_with_error(abs_path, str(exc))
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_instagram", "file": filename, "status": "error",
            "metadata": {"error": str(exc)},
        })
        _update_dashboard(f"[ERROR] Instagram post failed: {exc}")
        return {"success": False, "error": str(exc)}


# ── Twitter / X ───────────────────────────────────────────────────────────────

def _twitter_client() -> tweepy.Client:
    missing = [
        name for var, name in [
            (TW_API_KEY, "TW_API_KEY"), (TW_API_SECRET, "TW_API_SECRET"),
            (TW_ACCESS_TOKEN, "TW_ACCESS_TOKEN"), (TW_ACCESS_SECRET, "TW_ACCESS_SECRET"),
        ]
        if not var or var.startswith("YOUR_")
    ]
    if missing:
        raise RuntimeError(
            f"Missing Twitter API credentials: {', '.join(missing)}. "
            "Apply at developer.twitter.com and set them in mcp-servers/social-mcp/.env"
        )
    return tweepy.Client(
        bearer_token=TW_BEARER_TOKEN or None,
        consumer_key=TW_API_KEY,
        consumer_secret=TW_API_SECRET,
        access_token=TW_ACCESS_TOKEN,
        access_token_secret=TW_ACCESS_SECRET,
    )


@mcp.tool()
def post_to_twitter(file_path: str) -> dict:
    """Post approved content to Twitter/X via API v2 (tweepy).

    Content > 280 chars is auto-truncated with '...'.
    File must be in Approved/ with YAML frontmatter: platform: twitter

    Requires TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET in .env.

    Args:
        file_path: Path to approved social file, relative to vault root or absolute.
    """
    abs_path = Path(file_path) if Path(file_path).is_absolute() else VAULT_PATH / file_path
    filename = abs_path.name

    errors = _validate(abs_path, "twitter")
    if errors:
        err_msg = "\n".join(errors)
        _move_back_with_error(abs_path, err_msg)
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_twitter", "file": filename, "status": "validation_error",
            "metadata": {"errors": errors},
        })
        _update_dashboard(f"[ERROR] Twitter validation failed: {filename}")
        return {"success": False, "error": err_msg}

    _, content = _parse_file(abs_path)
    truncated = False
    if len(content) > 280:
        content = content[:277] + "..."
        truncated = True
        log.warning("Tweet truncated to 280 chars")

    try:
        client = _twitter_client()
        response = client.create_tweet(text=content)
        tweet_id = response.data.id
        log.info("Twitter post published: %s", tweet_id)

        dest = _done_dir() / f"POSTED_{filename}"
        shutil.move(str(abs_path), str(dest))
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_twitter", "file": filename, "status": "completed",
            "metadata": {"tweet_id": tweet_id, "truncated": truncated},
        })
        _update_dashboard(f"[POSTED] Twitter/X post published: {tweet_id}")
        return {"success": True, "tweet_id": tweet_id, "truncated": truncated, "moved_to": str(dest)}

    except Exception as exc:
        log.error("Twitter post failed: %s", exc)
        _move_back_with_error(abs_path, str(exc))
        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_twitter", "file": filename, "status": "error",
            "metadata": {"error": str(exc)},
        })
        _update_dashboard(f"[ERROR] Twitter/X post failed: {exc}")
        return {"success": False, "error": str(exc)}


# ── Summary ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_social_summary(days: int = 7) -> dict:
    """Return a summary of recent social posts from Done/Social/.

    Counts posts by platform over the last N days. Used for CEO Briefing.

    Args:
        days: Number of past days to include (default: 7).
    """
    done_dir = VAULT_PATH / "Done" / "Social"
    if not done_dir.exists():
        return {"total": 0, "platforms": {}, "files": [], "period_days": days}

    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    counts: dict[str, int] = {
        "facebook": 0, "instagram": 0, "twitter": 0, "linkedin": 0, "other": 0,
    }
    files: list[str] = []

    for f in done_dir.glob("POSTED_*.md"):
        if f.stat().st_mtime >= cutoff:
            files.append(f.name)
            name_lower = f.name.lower()
            matched = False
            for platform in ("facebook", "instagram", "twitter", "linkedin"):
                if platform in name_lower:
                    counts[platform] += 1
                    matched = True
                    break
            if not matched:
                counts["other"] += 1

    return {
        "total": len(files),
        "platforms": {k: v for k, v in counts.items() if v > 0},
        "files": sorted(files),
        "period_days": days,
    }


if __name__ == "__main__":
    mcp.run()
