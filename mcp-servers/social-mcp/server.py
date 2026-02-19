#!/usr/bin/env python3
"""Social MCP Server — Facebook, Instagram, and Twitter/X integration.

Gold-tier AI Employee social posting tools:
  post_to_facebook   — Meta Graph API (Page posts)
  post_to_instagram  — Meta Graph API (IG Business/Creator media posts)
  post_to_twitter    — Twitter API v2 via tweepy
  get_social_summary — Aggregate recent post stats from Done/Social/

All tools follow the vault HITL workflow:
  Approved/SOCIAL_<platform>_*.md → validate → post → Done/Social/POSTED_*.md

Uses: mcp (PyPI), tweepy, requests, python-dotenv
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

import requests
import tweepy
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────
VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path(__file__).parent.parent.parent))

# Meta (Facebook + Instagram)
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
IG_USER_ID = os.environ.get("IG_USER_ID", "")         # Instagram Business account ID
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")

# Twitter / X
TW_BEARER_TOKEN = os.environ.get("TW_BEARER_TOKEN", "")
TW_API_KEY = os.environ.get("TW_API_KEY", "")
TW_API_SECRET = os.environ.get("TW_API_SECRET", "")
TW_ACCESS_TOKEN = os.environ.get("TW_ACCESS_TOKEN", "")
TW_ACCESS_SECRET = os.environ.get("TW_ACCESS_SECRET", "")

META_GRAPH_URL = "https://graph.facebook.com/v19.0"
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
    """Parse YAML frontmatter + body from vault social markdown file."""
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
    """Return list of validation errors (empty = OK to post)."""
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


# ── Facebook ──────────────────────────────────────────────────────────────────

def _post_facebook_api(message: str, link: str = "") -> str:
    """POST to Facebook Page feed. Returns post ID."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        raise RuntimeError(
            "FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN are required. "
            "Set them in mcp-servers/social-mcp/.env"
        )
    url = f"{META_GRAPH_URL}/{FB_PAGE_ID}/feed"
    data: dict = {"message": message, "access_token": FB_PAGE_ACCESS_TOKEN}
    if link:
        data["link"] = link
    resp = requests.post(url, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json().get("id", "unknown")


@mcp.tool()
def post_to_facebook(file_path: str) -> dict:
    """Post approved content to a Facebook Page via Meta Graph API.

    File must be in Approved/ with YAML frontmatter:
      platform: facebook  (required)
      link: <url>         (optional — adds link preview)

    On success: moves file to Done/Social/POSTED_<name>.md and logs.
    On failure: moves file back to Pending_Approval/ with error note.

    Setup: create a Meta App with pages_manage_posts permission and generate
    a Page Access Token. Set FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN in .env.

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

    fm, content = _parse_file(abs_path)
    link = fm.get("link", "")

    try:
        post_id = _post_facebook_api(content, link)
        log.info("Facebook post published: %s", post_id)

        dest = _done_dir() / f"POSTED_{filename}"
        shutil.move(str(abs_path), str(dest))

        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_facebook", "file": filename, "status": "completed",
            "metadata": {"post_id": post_id},
        })
        _update_dashboard(f"[POSTED] Facebook post published: {post_id}")
        return {"success": True, "post_id": post_id, "moved_to": str(dest)}

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


# ── Instagram ─────────────────────────────────────────────────────────────────

def _post_instagram_api(caption: str, image_url: str) -> str:
    """Post to Instagram Business via Meta Graph API (2-step: create + publish)."""
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        raise RuntimeError(
            "IG_USER_ID and IG_ACCESS_TOKEN required. "
            "Requires an Instagram Business/Creator account linked to a Facebook Page."
        )
    if not image_url:
        raise RuntimeError(
            "Instagram requires a public image_url in the file frontmatter. "
            "Add 'image_url: https://...' to the approved file."
        )

    # Step 1: Create media container
    create_resp = requests.post(
        f"{META_GRAPH_URL}/{IG_USER_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": IG_ACCESS_TOKEN},
        timeout=30,
    )
    create_resp.raise_for_status()
    container_id = create_resp.json()["id"]
    log.info("Instagram media container created: %s", container_id)

    # Step 2: Publish container
    pub_resp = requests.post(
        f"{META_GRAPH_URL}/{IG_USER_ID}/media_publish",
        data={"creation_id": container_id, "access_token": IG_ACCESS_TOKEN},
        timeout=30,
    )
    pub_resp.raise_for_status()
    return pub_resp.json().get("id", "unknown")


@mcp.tool()
def post_to_instagram(file_path: str) -> dict:
    """Post approved content to Instagram via Meta Graph API.

    Requires an Instagram Business or Creator account connected to a Facebook Page.
    Instagram requires an image — add image_url to frontmatter.

    File must be in Approved/ with YAML frontmatter:
      platform: instagram   (required)
      image_url: <url>      (required — must be a public HTTPS URL)

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

    fm, content = _parse_file(abs_path)
    image_url = fm.get("image_url", "")

    try:
        post_id = _post_instagram_api(content, image_url)
        log.info("Instagram post published: %s", post_id)

        dest = _done_dir() / f"POSTED_{filename}"
        shutil.move(str(abs_path), str(dest))

        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_instagram", "file": filename, "status": "completed",
            "metadata": {"post_id": post_id, "image_url": image_url},
        })
        _update_dashboard(f"[POSTED] Instagram post published: {post_id}")
        return {"success": True, "post_id": post_id, "moved_to": str(dest)}

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
        if not var
    ]
    if missing:
        raise RuntimeError(
            f"Missing Twitter API credentials: {', '.join(missing)}. "
            "Apply for Twitter API access at developer.twitter.com and set them in .env"
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
    """Post approved content to Twitter/X via API v2.

    Tweet content must be ≤ 280 characters. Content longer than 280 chars
    will be auto-truncated with '...' and a warning is logged.

    File must be in Approved/ with YAML frontmatter:
      platform: twitter   (required)

    On success: moves file to Done/Social/POSTED_<name>.md and logs.
    On failure: moves file back to Pending_Approval/ with error note.

    Setup: apply at developer.twitter.com, create an app with Read+Write
    permissions, generate OAuth 1.0a access tokens, set TW_* vars in .env.

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

    # Enforce 280-char limit
    truncated = False
    if len(content) > 280:
        content = content[:277] + "..."
        truncated = True
        log.warning("Tweet truncated to 280 characters")

    try:
        client = _twitter_client()
        response = client.create_tweet(text=content)
        tweet_id = response.data["id"]
        log.info("Twitter post published: %s", tweet_id)

        dest = _done_dir() / f"POSTED_{filename}"
        shutil.move(str(abs_path), str(dest))

        _log_entry({
            "timestamp": datetime.now(PKT).isoformat(), "agent": "social-mcp",
            "action": "post_to_twitter", "file": filename, "status": "completed",
            "metadata": {"tweet_id": tweet_id, "truncated": truncated},
        })
        _update_dashboard(f"[POSTED] Twitter/X post published: {tweet_id}")
        return {
            "success": True,
            "tweet_id": tweet_id,
            "truncated": truncated,
            "moved_to": str(dest),
        }

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


# ── Summary tool ──────────────────────────────────────────────────────────────

@mcp.tool()
def get_social_summary(days: int = 7) -> dict:
    """Return a summary of recent social posts from Done/Social/.

    Counts posts by platform over the last N days by scanning POSTED_*.md
    filenames and log entries. Used by the CEO Briefing and weekly audit.

    Args:
        days: Number of past days to include in the summary (default: 7).
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
