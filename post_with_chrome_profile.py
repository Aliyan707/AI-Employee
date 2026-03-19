#!/usr/bin/env python3
"""Post to social media using the user's existing Chrome profile.

Uses the user's real Chrome profile (already logged in to FB/LinkedIn).
This bypasses bot detection completely.

Usage:
  python post_with_chrome_profile.py linkedin <file>
  python post_with_chrome_profile.py facebook <file>
"""
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

VAULT_PATH = Path("C:/Users/Cs/Desktop/AI Employee-")
PKT = timezone(timedelta(hours=5))

# Chrome's default user data directory on Windows
CHROME_USER_DATA = Path("C:/Users/Cs/AppData/Local/Google/Chrome/User Data")
CHROME_PROFILE = "Default"  # or "Profile 1" etc.

# We copy the profile to a temp dir to avoid locking issues
TEMP_PROFILE_BASE = Path(tempfile.gettempdir()) / "chrome_playwright_profile"


def extract_post_content(md_text: str) -> str:
    m = re.search(r"## Post Content\s*\n+(.*?)(?:\n---\n|\Z)", md_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m2 = re.match(r"^---\n.*?\n---\n(.*)", md_text, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    return md_text.strip()


def copy_chrome_profile():
    """Copy Chrome profile to temp dir to avoid locking conflicts."""
    import shutil as sh
    src = CHROME_USER_DATA / CHROME_PROFILE
    dst = TEMP_PROFILE_BASE / CHROME_PROFILE

    if dst.exists():
        sh.rmtree(str(dst), ignore_errors=True)
    TEMP_PROFILE_BASE.mkdir(parents=True, exist_ok=True)

    # Copy only the essential files for session (Cookies, Local Storage, etc.)
    essential_dirs = ["Cookies", "Local Storage", "Session Storage",
                      "Extension State", "databases", "Web Data",
                      "Network Action Predictor", "Visited Links"]
    essential_files = ["Cookies", "Cookies-journal", "Web Data", "Web Data-journal",
                       "Local State", "Secure Preferences"]

    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        try:
            dest_item = dst / item.name
            if item.is_file():
                sh.copy2(str(item), str(dest_item))
            elif item.is_dir() and item.name in ["Local Storage", "Session Storage",
                                                   "Extension State", "Databases"]:
                sh.copytree(str(item), str(dest_item), dirs_exist_ok=True)
        except Exception:
            pass  # Skip locked files

    return TEMP_PROFILE_BASE


def post_linkedin(file_path: Path) -> bool:
    from playwright.sync_api import sync_playwright, TimeoutError as PTimeout

    md_text = file_path.read_text(encoding="utf-8")
    content = extract_post_content(md_text)
    print(f"[LinkedIn] Content: {len(content)} chars")
    print(f"  Preview: {content[:80]}...")

    print("  Copying Chrome profile...")
    profile_dir = copy_chrome_profile()
    print(f"  Profile copied to: {profile_dir}")

    Path("Logs").mkdir(exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            channel="chrome",  # Use real Chrome, not Chromium
            viewport={"width": 1280, "height": 720},
            args=[
                "--disable-blink-features=AutomationControlled",
                f"--profile-directory={CHROME_PROFILE}",
            ],
        )

        page = ctx.new_page()
        page.set_default_timeout(60000)

        print("  Navigating to LinkedIn feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        current_url = page.url
        print(f"  URL: {current_url}")
        page.screenshot(path="Logs/li_chrome_profile.png")

        if "/feed/" not in current_url or "login" in current_url:
            print("  Not logged in — please log in manually in the browser window (up to 3 min)...")
            try:
                page.wait_for_url("**/feed/**", timeout=180000)
            except PTimeout:
                print("  Login timeout.")
                ctx.close()
                return False

        # Find post composer
        print("  Opening post composer...")
        page.wait_for_timeout(3000)

        opened = False
        for sel in [
            'button:has-text("Start a post")',
            "[placeholder*='mind']",
            "[aria-label*='mind']",
            '[class*="share-box-feed-entry__trigger"]',
        ]:
            try:
                el = page.locator(sel).first
                el.wait_for(timeout=5000)
                el.click()
                opened = True
                print(f"  Composer opened via: {sel}")
                break
            except Exception:
                continue

        if not opened:
            try:
                page.locator("text=What's on your mind").click(timeout=5000)
                opened = True
            except Exception:
                pass

        if not opened:
            page.screenshot(path="Logs/li_composer_fail.png")
            raise RuntimeError("Could not open LinkedIn composer — see Logs/li_composer_fail.png")

        page.wait_for_timeout(2000)

        # Type content
        print("  Typing content...")
        for sel in ["[role='textbox']", ".ql-editor", "[contenteditable='true']"]:
            try:
                editor = page.locator(sel).first
                editor.wait_for(timeout=5000)
                editor.click()
                page.keyboard.type(content, delay=8)
                print(f"  Filled via: {sel}")
                break
            except Exception:
                continue

        page.wait_for_timeout(2000)

        # Submit
        print("  Submitting...")
        for sel in [
            "button.share-actions__primary-action",
            "button[data-control-name='share.post']",
        ]:
            try:
                btn = page.locator(sel).last
                btn.wait_for(timeout=5000)
                btn.click()
                print(f"  Posted via: {sel}")
                break
            except Exception:
                continue

        page.wait_for_timeout(5000)
        page.screenshot(path="Logs/li_posted.png")
        ctx.close()

    done_dir = VAULT_PATH / "Done" / "Social"
    done_dir.mkdir(parents=True, exist_ok=True)
    dest = done_dir / f"POSTED_{file_path.name}"
    shutil.move(str(file_path), str(dest))
    print(f"  File moved to Done: {dest}")
    return True


def post_facebook(file_path: Path) -> bool:
    from playwright.sync_api import sync_playwright, TimeoutError as PTimeout

    md_text = file_path.read_text(encoding="utf-8")
    content = extract_post_content(md_text)
    print(f"[Facebook] Content: {len(content)} chars")
    print(f"  Preview: {content[:80]}...")

    print("  Copying Chrome profile...")
    profile_dir = copy_chrome_profile()

    Path("Logs").mkdir(exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            channel="chrome",
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = ctx.new_page()
        page.set_default_timeout(60000)

        print("  Navigating to Facebook...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        current_url = page.url
        print(f"  URL: {current_url}")
        page.screenshot(path="Logs/fb_chrome_profile.png")

        # Check login state
        if "login" in current_url or page.locator("input[name='email']").count() > 0:
            print("  Not logged in — please log in in the browser window (3 min)...")
            try:
                page.wait_for_function(
                    """() => !window.location.href.includes('/login') &&
                             !window.location.href.includes('checkpoint') &&
                             document.querySelector('[aria-label="Home"]') !== null""",
                    timeout=180000
                )
            except PTimeout:
                print("  Login timeout.")
                ctx.close()
                return False

        # Find composer
        print("  Looking for post composer...")
        opened = False
        for sel in [
            "[placeholder*=\"What's on your mind\"]",
            "[aria-label*=\"What's on your mind\"]",
            "div[role='button']:has-text(\"What's on your mind\")",
        ]:
            try:
                el = page.locator(sel).first
                el.wait_for(timeout=5000)
                el.click()
                opened = True
                print(f"  Composer via: {sel}")
                break
            except Exception:
                continue

        if not opened:
            try:
                page.locator("text=What's on your mind").click(timeout=5000)
                opened = True
            except Exception:
                pass

        if not opened:
            page.screenshot(path="Logs/fb_composer_fail2.png")
            raise RuntimeError("Could not open Facebook composer")

        page.wait_for_timeout(2000)

        # Type content
        print("  Typing content...")
        for sel in ["div[role='textbox']", "[contenteditable='true']"]:
            try:
                tb = page.locator(sel).last
                tb.wait_for(timeout=5000)
                tb.click()
                page.keyboard.type(content, delay=15)
                print(f"  Filled via: {sel}")
                break
            except Exception:
                continue

        page.wait_for_timeout(2000)

        # Submit
        print("  Submitting...")
        for sel in ["div[aria-label='Post']", "button:has-text('Post')"]:
            try:
                btn = page.locator(sel).last
                btn.wait_for(timeout=5000)
                btn.click()
                print(f"  Posted via: {sel}")
                break
            except Exception:
                continue

        page.wait_for_timeout(5000)
        page.screenshot(path="Logs/fb_posted.png")
        ctx.close()

    done_dir = VAULT_PATH / "Done" / "Social"
    done_dir.mkdir(parents=True, exist_ok=True)
    dest = done_dir / f"POSTED_{file_path.name}"
    shutil.move(str(file_path), str(dest))
    print(f"  File moved to Done: {dest}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python post_with_chrome_profile.py <platform> <file>")
        sys.exit(1)

    platform = sys.argv[1].lower()
    file_arg = sys.argv[2]
    fp = Path(file_arg) if Path(file_arg).is_absolute() else VAULT_PATH / file_arg

    if not fp.exists():
        print(f"ERROR: File not found: {fp}")
        sys.exit(1)

    if platform == "linkedin":
        ok = post_linkedin(fp)
    elif platform == "facebook":
        ok = post_facebook(fp)
    else:
        print(f"Unknown platform: {platform}")
        ok = False

    sys.exit(0 if ok else 1)
