#!/usr/bin/env python3
"""Post to LinkedIn using Playwright with improved anti-detection.

Requires a saved session from setup_linkedin_session.py.
"""
import os
import re
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv("mcp-servers/browser-mcp/.env")

VAULT_PATH = Path("C:/Users/Cs/Desktop/AI Employee-")
PKT = timezone(timedelta(hours=5))
session_dir = Path("mcp-servers/browser-mcp/linkedin-session")
email = os.environ.get("LINKEDIN_EMAIL", "")
password = os.environ.get("LINKEDIN_PASSWORD", "")


def extract_post_content(md_text: str) -> str:
    """Extract only the post body from between '## Post Content' and next '---' separator."""
    m = re.search(r"## Post Content\s*\n+(.*?)(?:\n---\n|\Z)", md_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: strip frontmatter
    m2 = re.match(r"^---\n.*?\n---\n(.*)", md_text, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    return md_text.strip()


def post_to_linkedin(file_path: Path) -> bool:
    from playwright.sync_api import sync_playwright, TimeoutError as PTimeout

    md_text = file_path.read_text(encoding="utf-8")
    content = extract_post_content(md_text)
    print(f"Content length: {len(content)} chars")
    print(f"Preview: {content[:100]}...")

    session_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(session_dir),
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Asia/Karachi",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # Remove automation indicators
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

        page = ctx.new_page()
        page.set_default_timeout(60000)

        # Navigate to feed
        print("Navigating to LinkedIn...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        current_url = page.url
        print(f"Current URL: {current_url}")

        # Login if needed
        if "/feed/" not in current_url or "login" in current_url:
            print("Session expired — logging in...")
            print("(Browser window is open — complete any security checks)")
            page.goto("https://www.linkedin.com/login")
            page.wait_for_timeout(1500)

            # Fill credentials
            page.fill("#username", email)
            page.wait_for_timeout(800)
            page.fill("#password", password)
            page.wait_for_timeout(800)
            page.click('button[type="submit"]')

            print("Waiting for login to complete (up to 3 minutes)...")
            try:
                page.wait_for_url("**/feed/**", timeout=180000)
                print("Logged in successfully!")
            except PTimeout:
                print(f"Login timeout. Current URL: {page.url}")
                print("Please complete login manually in the browser window...")
                # Wait more
                page.wait_for_url("**/feed/**", timeout=120000)
                print("Login completed!")
        else:
            print("Session active!")

        # Wait for feed to load fully
        page.wait_for_timeout(4000)
        print(f"On feed page: {page.url}")

        # Take screenshot
        Path("Logs").mkdir(exist_ok=True)
        page.screenshot(path="Logs/linkedin_feed.png")
        print("Feed screenshot saved to Logs/linkedin_feed.png")

        # Find and click the post composer
        print("Looking for post composer...")

        # Try multiple approaches to open the composer
        opened = False

        # Method 1: Look for the share-box text input placeholder
        try:
            el = page.locator("[placeholder*='mind']").first
            el.wait_for(timeout=5000)
            el.click()
            opened = True
            print("  Method 1 (placeholder) worked")
        except Exception:
            pass

        # Method 2: aria-label contains "mind"
        if not opened:
            try:
                el = page.locator("[aria-label*='mind']").first
                el.wait_for(timeout=5000)
                el.click()
                opened = True
                print("  Method 2 (aria-label mind) worked")
            except Exception:
                pass

        # Method 3: "Start a post" button text (exact)
        if not opened:
            try:
                el = page.get_by_role("button", name=re.compile(r"Start a post", re.I)).first
                el.wait_for(timeout=5000)
                el.click()
                opened = True
                print("  Method 3 (button name regex) worked")
            except Exception:
                pass

        # Method 4: Try share box trigger class
        if not opened:
            try:
                page.wait_for_selector(".share-box-feed-entry__trigger", timeout=5000)
                page.click(".share-box-feed-entry__trigger")
                opened = True
                print("  Method 4 (share-box-feed-entry__trigger) worked")
            except Exception:
                pass

        # Method 5: Any button containing "start" text case-insensitive
        if not opened:
            buttons = page.locator("button").all()
            for btn in buttons:
                try:
                    txt = (btn.text_content() or "").strip().lower()
                    if "start" in txt and "post" in txt:
                        btn.click()
                        opened = True
                        print(f"  Method 5 (button scan): '{txt}'")
                        break
                except Exception:
                    continue

        # Method 6: Screenshot + HTML dump for debugging
        if not opened:
            page.screenshot(path="Logs/linkedin_feed_debug.png")
            html_snippet = page.content()[:5000]
            with open("Logs/linkedin_page_html.txt", "w") as f:
                f.write(html_snippet)
            print("  Debug screenshot: Logs/linkedin_feed_debug.png")
            print("  Page HTML saved: Logs/linkedin_page_html.txt")
            raise RuntimeError("Could not open LinkedIn post composer — see debug files")

        page.wait_for_timeout(2500)

        # Fill the post content
        print("Filling post content...")
        page.screenshot(path="Logs/linkedin_composer.png")

        filled = False
        editor_selectors = [
            '[role="textbox"]',
            '.ql-editor',
            '[contenteditable="true"]',
        ]
        for sel in editor_selectors:
            try:
                editor = page.locator(sel).first
                editor.wait_for(timeout=8000)
                editor.click()
                page.wait_for_timeout(500)
                # Type in chunks to avoid issues
                page.keyboard.type(content, delay=10)
                filled = True
                print(f"  Content filled via: {sel}")
                break
            except Exception:
                continue

        if not filled:
            raise RuntimeError("Could not fill post editor")

        page.wait_for_timeout(2000)
        page.screenshot(path="Logs/linkedin_post_ready.png")

        # Click the Post button
        print("Submitting post...")
        posted = False
        post_selectors = [
            'button.share-actions__primary-action',
            'button[data-control-name="share.post"]',
        ]
        for sel in post_selectors:
            try:
                btn = page.locator(sel).last
                btn.wait_for(timeout=5000)
                btn.click()
                posted = True
                print(f"  Posted via: {sel}")
                break
            except Exception:
                continue

        # Fallback: find Post button by role + name
        if not posted:
            try:
                btn = page.get_by_role("button", name=re.compile("^Post$", re.I)).last
                btn.wait_for(timeout=5000)
                btn.click()
                posted = True
                print("  Posted via role=button name=Post")
            except Exception:
                pass

        if not posted:
            # One more fallback: dump all visible buttons
            buttons = page.locator("button").all()
            for btn in buttons:
                try:
                    txt = (btn.text_content() or "").strip()
                    if txt.strip().lower() == "post":
                        btn.click()
                        posted = True
                        print(f"  Posted via button scan: '{txt}'")
                        break
                except Exception:
                    continue

        if not posted:
            raise RuntimeError("Could not find LinkedIn Post submit button")

        page.wait_for_timeout(5000)
        page.screenshot(path="Logs/linkedin_posted.png")
        print("Post published!")
        ctx.close()

    # Move to Done
    done_dir = VAULT_PATH / "Done" / "Social"
    done_dir.mkdir(parents=True, exist_ok=True)
    dest = done_dir / f"POSTED_{file_path.name}"
    shutil.move(str(file_path), str(dest))
    print(f"File moved to: {dest}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python post_linkedin_direct.py <file>")
        sys.exit(1)

    fp = Path(sys.argv[1]) if Path(sys.argv[1]).is_absolute() else VAULT_PATH / sys.argv[1]
    if not fp.exists():
        print(f"ERROR: File not found: {fp}")
        sys.exit(1)

    try:
        ok = post_to_linkedin(fp)
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
