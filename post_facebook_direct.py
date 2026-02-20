#!/usr/bin/env python3
"""Post to Facebook via Playwright.

Opens a visible browser. Complete login/2FA if prompted.
Session is saved for future runs.

Usage:
  python post_facebook_direct.py <file>
"""
import os
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv("mcp-servers/social-mcp/.env")

VAULT_PATH = Path("C:/Users/Cs/Desktop/AI Employee-")
PKT = timezone(timedelta(hours=5))
FB_SESSION = Path("mcp-servers/social-mcp/fb-session")
email = os.environ.get("Facebook_EMAIL", "")
password = os.environ.get("Facebook_PASSWORD", "")


def extract_post_content(md_text: str) -> str:
    m = re.search(r"## Post Content\s*\n+(.*?)(?:\n---\n|\Z)", md_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m2 = re.match(r"^---\n.*?\n---\n(.*)", md_text, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    return md_text.strip()


def post_to_facebook(file_path: Path) -> bool:
    from playwright.sync_api import sync_playwright, TimeoutError as PTimeout

    md_text = file_path.read_text(encoding="utf-8")
    content = extract_post_content(md_text)
    print(f"Content length: {len(content)} chars")
    print(f"Preview: {content[:100]}...")
    print(f"FB Email: {email}")

    FB_SESSION.mkdir(parents=True, exist_ok=True)
    Path("Logs").mkdir(exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(FB_SESSION),
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled"],
        )

        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page = ctx.new_page()
        page.set_default_timeout(60000)

        # Navigate to Facebook
        print("Navigating to Facebook...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        current_url = page.url
        print(f"Current URL: {current_url}")
        page.screenshot(path="Logs/fb_initial.png")

        # Login if needed — check for presence of email/password fields (works at both /login and /)
        email_field = None
        for sel in ["input[name='email']", "#email", "input[type='email']",
                    "input[placeholder*='Email']", "input[placeholder*='email']",
                    "input[placeholder*='mobile']"]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    email_field = sel
                    break
            except Exception:
                continue

        if email_field or "login" in current_url:
            print(f"Login form detected (field: {email_field})...")
            try:
                # Fill email
                if email_field:
                    page.fill(email_field, email)
                else:
                    page.get_by_placeholder("Email address or mobile number").fill(email)
                page.wait_for_timeout(700)
                # Fill password
                for psel in ["input[name='pass']", "#pass", "input[type='password']",
                             "input[placeholder*='Password']", "input[placeholder*='password']"]:
                    try:
                        if page.locator(psel).count() > 0:
                            page.fill(psel, password)
                            break
                    except Exception:
                        continue
                page.wait_for_timeout(700)
                # Submit
                for bsel in ["button[name='login']", "button[type='submit']:has-text('Log in')",
                             "button:has-text('Log in')", "[data-testid='royal_login_button']"]:
                    try:
                        if page.locator(bsel).count() > 0:
                            page.click(bsel)
                            break
                    except Exception:
                        continue
                print("Credentials submitted. Waiting for login (up to 3 min)...")
                page.wait_for_timeout(6000)
                print(f"After login URL: {page.url}")
                page.screenshot(path="Logs/fb_after_login.png")
            except Exception as e:
                print(f"Login error: {e}")

        # Check for 2FA / extra verification
        current_url = page.url
        if "checkpoint" in current_url or "two_step" in current_url or "login" in current_url:
            print(f"Security check at: {current_url}")
            print("Complete verification in the browser window (up to 3 minutes)...")
            try:
                page.wait_for_url("**/home.php**", timeout=180000)
            except PTimeout:
                try:
                    page.wait_for_function(
                        "() => window.location.href.includes('facebook.com') && "
                        "!window.location.href.includes('login') && "
                        "!window.location.href.includes('checkpoint')",
                        timeout=60000
                    )
                except Exception:
                    pass

        page.wait_for_timeout(4000)
        current_url = page.url
        print(f"Post-login URL: {current_url}")
        page.screenshot(path="Logs/fb_feed.png")

        # Navigate to home/feed
        if "home.php" not in current_url and "facebook.com" in current_url:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

        # Find the post composer
        print("Looking for post composer...")
        page.screenshot(path="Logs/fb_before_composer.png")

        opened = False

        # Method 1: "What's on your mind" placeholder
        for selector in [
            "[placeholder*=\"What's on your mind\"]",
            "[aria-label*=\"What's on your mind\"]",
            "div[role='button']:has-text(\"What's on your mind\")",
            "span:has-text(\"What's on your mind\")",
        ]:
            try:
                el = page.locator(selector).first
                el.wait_for(timeout=5000)
                el.click()
                opened = True
                print(f"  Composer via: {selector}")
                break
            except Exception:
                continue

        if not opened:
            # Try clicking the story/status update area at the top
            try:
                page.click("div[data-pagelet='FeedUnit_0']", timeout=5000)
                opened = True
                print("  Composer via FeedUnit")
            except Exception:
                pass

        if not opened:
            # Scan all divs/spans with "mind" text
            try:
                els = page.locator("text=What's on your mind").all()
                if els:
                    els[0].click()
                    opened = True
                    print(f"  Composer via text scan ({len(els)} matches)")
            except Exception:
                pass

        if not opened:
            page.screenshot(path="Logs/fb_composer_fail.png")
            html = page.content()
            with open("Logs/fb_page_html.txt", "w", encoding="utf-8") as f:
                f.write(html[:8000])
            raise RuntimeError("Could not open Facebook post composer — check Logs/fb_composer_fail.png")

        page.wait_for_timeout(2000)
        page.screenshot(path="Logs/fb_composer_open.png")

        # Type the content
        print("Typing post content...")
        textbox_selectors = [
            "div[role='textbox']",
            "[contenteditable='true']",
            "[aria-label*=\"What's on your mind\"]",
        ]
        filled = False
        for sel in textbox_selectors:
            try:
                tb = page.locator(sel).last
                tb.wait_for(timeout=5000)
                tb.click()
                page.wait_for_timeout(500)
                page.keyboard.type(content, delay=15)
                filled = True
                print(f"  Filled via: {sel}")
                break
            except Exception:
                continue

        if not filled:
            raise RuntimeError("Could not type into Facebook post editor")

        page.wait_for_timeout(2000)
        page.screenshot(path="Logs/fb_post_ready.png")

        # Click Post button
        print("Submitting post...")
        post_selectors = [
            "div[aria-label='Post']",
            "[data-testid='react-composer-post-button']",
            "button:has-text('Post')",
        ]
        posted = False
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

        if not posted:
            # Try get_by_role
            try:
                btn = page.get_by_role("button", name=re.compile("^Post$", re.I))
                btn.click(timeout=5000)
                posted = True
                print("  Posted via role button")
            except Exception:
                pass

        if not posted:
            raise RuntimeError("Could not click Post button")

        page.wait_for_timeout(5000)
        page.screenshot(path="Logs/fb_posted.png")
        print("Facebook post published!")
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
        print("Usage: python post_facebook_direct.py <file>")
        sys.exit(1)

    fp = Path(sys.argv[1]) if Path(sys.argv[1]).is_absolute() else VAULT_PATH / sys.argv[1]
    if not fp.exists():
        print(f"ERROR: File not found: {fp}")
        sys.exit(1)

    try:
        ok = post_to_facebook(fp)
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
