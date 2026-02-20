#!/usr/bin/env python3
"""Direct social media poster — extracts post content and publishes.

Usage:
  python post_now.py linkedin <file>
  python post_now.py facebook <file>
  python post_now.py twitter <file>
"""
import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

VAULT_PATH = Path("C:/Users/Cs/Desktop/AI Employee-")
PKT = timezone(timedelta(hours=5))


def extract_post_content(md_text: str) -> str:
    """Extract only the post body from between '## Post Content' and next '---' separator."""
    # Try to find the ## Post Content section
    m = re.search(r"## Post Content\s*\n+(.*?)(?:\n---\n|\Z)", md_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: strip frontmatter and return rest
    m2 = re.match(r"^---\n.*?\n---\n(.*)", md_text, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    return md_text.strip()


def extract_twitter_tweets(md_text: str) -> list[str]:
    """Extract individual tweet texts from code blocks in the Twitter thread file."""
    tweets = re.findall(r"```\n(.*?)\n```", md_text, re.DOTALL)
    return [t.strip() for t in tweets if t.strip()]


def move_to_done(file_path: Path, platform: str) -> Path:
    done_dir = VAULT_PATH / "Done" / "Social"
    done_dir.mkdir(parents=True, exist_ok=True)
    dest = done_dir / f"POSTED_{file_path.name}"
    shutil.move(str(file_path), str(dest))
    print(f"  Moved to: {dest}")
    return dest


def post_linkedin(file_path: Path) -> bool:
    load_dotenv("mcp-servers/browser-mcp/.env")
    email = os.environ.get("LINKEDIN_EMAIL", "")
    password = os.environ.get("LINKEDIN_PASSWORD", "")
    session_dir = Path(os.environ.get(
        "LINKEDIN_SESSION_PATH",
        "mcp-servers/browser-mcp/linkedin-session"
    ))
    headless = False  # Always visible for posting so user can handle 2FA/captcha

    md_text = file_path.read_text(encoding="utf-8")
    content = extract_post_content(md_text)
    print(f"\n[LinkedIn] Posting ({len(content)} chars)...")
    print(f"  Preview: {content[:80]}...")
    print(f"  Session dir: {session_dir}")
    print(f"  Headless: {headless}")

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PTimeout

        session_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                str(session_dir),
                headless=headless,
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
            page.set_default_timeout(60000)

            print("  Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            current_url = page.url
            is_logged_in = (
                "/feed/" in current_url and
                "login" not in current_url and
                "session_redirect" not in current_url
            )

            if not is_logged_in:
                print(f"  Need login (current URL: {current_url})")
                page.goto("https://www.linkedin.com/login")
                page.wait_for_timeout(1500)
                page.fill("#username", email)
                page.wait_for_timeout(500)
                page.fill("#password", password)
                page.wait_for_timeout(500)
                page.click('button[type="submit"]')
                print("  Credentials submitted — waiting for login (up to 90s for 2FA/CAPTCHA)...")
                try:
                    page.wait_for_url("**/feed/**", timeout=90000)
                    print("  Login successful!")
                except PTimeout:
                    # May be stuck on verification step — check URL
                    curr = page.url
                    print(f"  Timeout — current URL: {curr}")
                    if "checkpoint" in curr or "challenge" in curr:
                        print("  Security check detected — manual completion needed (120s)...")
                        page.wait_for_url("**/feed/**", timeout=120000)
                    else:
                        raise RuntimeError(f"Login did not reach feed. URL: {curr}")
                    print("  Login completed!")
            else:
                print("  Already logged in (session active)")

            # Open post composer
            print("  Opening post composer...")
            page.wait_for_timeout(3000)  # Extra wait for feed to fully load
            composer_selectors = [
                'button:has-text("Start a post")',
                '[class*="share-box-feed-entry__trigger"]',
                '[data-control-name="share.sharebox_open"]',
                'button[class*="artdeco-button"]:has-text("Post")',
                '.feed-shared-update-v2__control-menu-trigger',
                '[aria-label="Start a post"]',
                'span:has-text("Start a post")',
                'div.share-box-feed-entry__top-bar',
                # Try clicking the text box area at the top of the feed
                'button.share-creation-state__placeholder-btn',
            ]
            clicked = False
            for sel in composer_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=5000)
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    clicked = True
                    print(f"  Composer opened via: {sel}")
                    break
                except Exception:
                    continue
            if not clicked:
                # Last resort: try clicking the "What's on your mind" text in the top card
                try:
                    page.locator("text=What's on your mind").click(timeout=5000)
                    clicked = True
                    print("  Composer opened via text click")
                except Exception:
                    pass
            if not clicked:
                raise RuntimeError("Could not open LinkedIn post composer")

            page.wait_for_timeout(2000)

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
                    editor.wait_for(timeout=8000)
                    editor.click()
                    # Use keyboard to type (more reliable than fill for contenteditable)
                    page.keyboard.type(content, delay=5)
                    filled = True
                    print(f"  Content filled via: {sel}")
                    break
                except Exception:
                    continue
            if not filled:
                raise RuntimeError("Could not fill LinkedIn post editor")

            page.wait_for_timeout(1500)

            # Submit
            post_btn_selectors = [
                'button.share-actions__primary-action',
                'button[data-control-name="share.post"]',
                '.share-box_actions button:has-text("Post")',
                'button:has-text("Post"):not([disabled])',
            ]
            posted = False
            for sel in post_btn_selectors:
                try:
                    btn = page.locator(sel).last
                    btn.wait_for(timeout=8000)
                    btn.click()
                    posted = True
                    print(f"  Post submitted via: {sel}")
                    break
                except Exception:
                    continue
            if not posted:
                raise RuntimeError("Could not find LinkedIn Post submit button")

            page.wait_for_timeout(4000)
            ctx.close()

        print("  LinkedIn post PUBLISHED successfully!")
        move_to_done(file_path, "linkedin")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def post_facebook(file_path: Path) -> bool:
    load_dotenv("mcp-servers/social-mcp/.env")
    headless = False  # Always visible
    fb_email = os.environ.get("Facebook_EMAIL", "")
    fb_password = os.environ.get("Facebook_PASSWORD", "")

    fb_session = Path("mcp-servers/social-mcp/fb-session")
    fb_session.mkdir(parents=True, exist_ok=True)

    md_text = file_path.read_text(encoding="utf-8")
    content = extract_post_content(md_text)
    print(f"\n[Facebook] Posting ({len(content)} chars)...")
    print(f"  Preview: {content[:80]}...")

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PTimeout

        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                str(fb_session),
                headless=headless,
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                args=["--disable-blink-features=AutomationControlled"],
            )
            ctx.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )
            page = ctx.new_page()
            page.set_default_timeout(60000)

            print("  Navigating to Facebook...")
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            current_url = page.url
            is_logged_in = (
                "facebook.com" in current_url and
                "login" not in current_url and
                page.locator("[aria-label='Home']").count() > 0 or
                page.locator("[data-pagelet='FeedUnit_0']").count() > 0
            )

            # Auto-login if session expired
            if not is_logged_in and page.locator("input[name='email']").count() > 0:
                print("  Session expired — auto-filling credentials...")
                page.fill("input[name='email']", fb_email)
                page.wait_for_timeout(500)
                page.fill("input[name='pass']", fb_password)
                page.wait_for_timeout(500)
                # Submit via Enter key (most reliable across FB login page variants)
                page.keyboard.press("Enter")
                print("  Credentials submitted — waiting for login (up to 90s for 2FA/CAPTCHA)...")
                try:
                    page.wait_for_function(
                        """() => {
                            const url = window.location.href;
                            const noLoginForm = document.querySelector('input[name="email"]') === null;
                            const notLoginPage = !url.includes('/login') && !url.includes('login.php');
                            return notLoginPage && noLoginForm;
                        }""",
                        timeout=90000
                    )
                    page.wait_for_timeout(3000)  # Extra wait for feed to render
                    print("  Facebook login completed!")
                except PTimeout:
                    curr = page.url
                    if "checkpoint" in curr or "two_step" in curr or "save-device" in curr:
                        print(f"  Security check at {curr} — waiting 120s for manual completion...")
                        try:
                            page.wait_for_function(
                                "() => document.querySelector('[role=\"feed\"]') !== null || "
                                "document.querySelector('[aria-label=\"Home\"]') !== null",
                                timeout=120000
                            )
                            print("  Security check passed!")
                        except PTimeout:
                            print("  Security check timeout — run: python setup_social_sessions.py facebook")
                            return False
                    else:
                        print(f"  Login timeout — URL: {curr}")
                        print("  Run: python setup_social_sessions.py facebook")
                        return False

            # Look for post composer
            print("  Looking for post composer...")
            composer_selectors = [
                '[aria-label="What\'s on your mind"]',
                '[placeholder="What\'s on your mind"]',
                'div[role="button"]:has-text("What\'s on your mind")',
                'span:has-text("What\'s on your mind")',
            ]
            clicked = False
            for sel in composer_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=10000)
                    btn.click()
                    clicked = True
                    print(f"  Composer opened via: {sel}")
                    break
                except Exception:
                    continue
            if not clicked:
                raise RuntimeError("Could not open Facebook post composer")

            page.wait_for_timeout(1500)

            # Type content
            textbox_selectors = [
                '[aria-label="What\'s on your mind"]',
                'div[role="textbox"]',
                '[contenteditable="true"]',
            ]
            filled = False
            for sel in textbox_selectors:
                try:
                    tb = page.locator(sel).last
                    tb.wait_for(timeout=5000)
                    tb.click()
                    page.keyboard.type(content, delay=10)
                    filled = True
                    print(f"  Content filled via: {sel}")
                    break
                except Exception:
                    continue
            if not filled:
                raise RuntimeError("Could not fill Facebook post textbox")

            page.wait_for_timeout(1000)

            # Submit
            post_btn_selectors = [
                'div[aria-label="Post"]',
                'button:has-text("Post")',
                '[data-testid="react-composer-post-button"]',
            ]
            posted = False
            for sel in post_btn_selectors:
                try:
                    btn = page.locator(sel).last
                    btn.wait_for(timeout=8000)
                    btn.click()
                    posted = True
                    print(f"  Post submitted via: {sel}")
                    break
                except Exception:
                    continue
            if not posted:
                raise RuntimeError("Could not submit Facebook post")

            page.wait_for_timeout(4000)
            ctx.close()

        print("  Facebook post PUBLISHED successfully!")
        move_to_done(file_path, "facebook")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def post_instagram(file_path: Path, image_path: Path) -> bool:
    """Post to Instagram via Playwright — requires an image file."""
    load_dotenv("mcp-servers/social-mcp/.env")
    ig_email    = os.environ.get("Instagram__EMAIL", "") or os.environ.get("Instagram_EMAIL", "")
    ig_password = os.environ.get("Instagram_PASSWORD", "")
    headless    = False  # Always visible so user can handle 2FA

    ig_session = Path("mcp-servers/social-mcp/instagram-session")
    ig_session.mkdir(parents=True, exist_ok=True)

    if not image_path.exists():
        print(f"\n[Instagram] ERROR: Image file not found: {image_path}")
        return False

    md_text = file_path.read_text(encoding="utf-8")
    caption = extract_post_content(md_text)
    # Instagram captions: keep to ~2200 chars
    if len(caption) > 2200:
        caption = caption[:2197] + "..."

    print(f"\n[Instagram] Posting ({len(caption)} chars caption)...")
    print(f"  Image: {image_path}")
    print(f"  Preview: {caption[:80]}...")

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PTimeout

        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                str(ig_session),
                headless=headless,
                viewport={"width": 1080, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                args=["--disable-blink-features=AutomationControlled"],
            )
            ctx.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )
            page = ctx.new_page()
            page.set_default_timeout(60000)

            # Check logged-in state by going to home feed
            print("  Checking Instagram login state...")
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            current_url = page.url
            # We're logged in if we're at the home feed (not redirected to login/accounts)
            is_logged_in = (
                "instagram.com" in current_url
                and "/accounts/" not in current_url
                and "/login" not in current_url
                and page.locator('input[name="username"]').count() == 0
                and page.locator('input[name="Mobile number or email"]').count() == 0
                # Confirm feed elements exist
                and (
                    page.locator('[aria-label="Home"]').count() > 0
                    or page.locator('nav[role="navigation"]').count() > 0
                    or page.locator('svg[aria-label="Instagram"]').count() > 0
                )
            )

            if not is_logged_in:
                print("  Not logged in — going to login page...")
                page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
                # Screenshot to see what login page looks like
                page.screenshot(path="Logs/ig_login_page.png")
                print("  Screenshot: Logs/ig_login_page.png")
                # Wait for the login form text input
                try:
                    page.locator('input[type="text"]').first.wait_for(timeout=10000)
                except Exception:
                    page.screenshot(path="Logs/ig_login_timeout.png")
                    raise RuntimeError("Could not reach Instagram login form — try manual setup first")
                print("  Filling credentials...")
                # Instagram login: "Mobile number, username or email" = input[type="text"]
                page.fill('input[type="text"]', ig_email)
                page.wait_for_timeout(500)
                page.fill('input[type="password"]', ig_password)
                page.wait_for_timeout(500)
                page.keyboard.press("Enter")
                print("  Credentials submitted — waiting (up to 90s for 2FA/CAPTCHA)...")
                try:
                    page.wait_for_function(
                        "() => !window.location.href.includes('/login') && "
                        "!window.location.href.includes('/accounts/')",
                        timeout=90000
                    )
                    page.wait_for_timeout(3000)
                    print("  Login complete!")
                except PTimeout:
                    curr = page.url
                    if any(k in curr for k in ["challenge", "two_step", "verify", "checkpoint"]):
                        print(f"  Security check at {curr} — complete in browser (120s)...")
                        page.wait_for_function(
                            "() => !window.location.href.includes('/accounts/')",
                            timeout=120000
                        )
                        page.wait_for_timeout(3000)
                        print("  Security check passed!")
                    else:
                        raise RuntimeError(f"Login failed, URL: {curr}")
                # Navigate to home feed after login
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
            else:
                print("  Already logged in (session active)")

            # Dismiss "Save login info?" / "Turn on notifications?" dialogs
            for btn_text in ["Not Now", "Not now", "Skip"]:
                try:
                    page.locator(f'button:has-text("{btn_text}")').first.click(timeout=3000)
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

            # Press Escape to dismiss any stale overlay first
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)

            # Navigate directly to create/select page (most reliable)
            print("  Navigating to Instagram create page...")
            page.goto("https://www.instagram.com/create/select/", wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
            page.screenshot(path="Logs/ig_create_page.png")
            print("  Screenshot: Logs/ig_create_page.png")

            # Upload image via "Select from computer" button on the create page
            print("  Looking for upload button...")
            try:
                select_btn = page.locator(
                    'button:has-text("Select from computer"), '
                    'button:has-text("Select From Computer"), '
                    'div[role="button"]:has-text("Select from computer")'
                ).first
                select_btn.wait_for(timeout=15000)
                print("  Found upload button, triggering file chooser...")
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    select_btn.click()
                fc_info.value.set_files(str(image_path.resolve()))
                print("  Image uploaded via 'Select from computer'!")
            except Exception as e1:
                print(f"  Button method failed ({e1}) — trying JS file input injection...")
                # Try directly setting hidden file input (some IG versions expose this)
                try:
                    page.evaluate(
                        """
                        const input = document.querySelector('input[type="file"]');
                        if (!input) throw new Error('no file input found');
                        """
                    )
                    inp = page.locator('input[type="file"]').first
                    inp.evaluate("el => el.style.display = 'block'")
                    inp.set_input_files(str(image_path.resolve()))
                    print("  Image uploaded via exposed file input!")
                except Exception as e2:
                    page.screenshot(path="Logs/ig_upload_final_fail.png")
                    raise RuntimeError(f"All upload methods failed: {e1} | {e2}")
            page.wait_for_timeout(3000)
            print("  Image upload complete!")

            # Click through crop/filter steps
            for step_label in ["Next", "OK", "Select crop"]:
                try:
                    page.locator(f'button:has-text("{step_label}")').last.click(timeout=5000)
                    page.wait_for_timeout(2000)
                    print(f"  Clicked '{step_label}'")
                except Exception:
                    pass

            # Next → to filters screen
            try:
                page.locator('button:has-text("Next")').last.click(timeout=6000)
                page.wait_for_timeout(2000)
                print("  Moved to filters step")
            except Exception:
                pass

            # Next → to caption screen
            try:
                page.locator('button:has-text("Next")').last.click(timeout=6000)
                page.wait_for_timeout(2000)
                print("  Moved to caption step")
            except Exception:
                pass

            # Screenshot before filling caption
            page.screenshot(path="Logs/ig_caption_page.png")
            print("  Screenshot: Logs/ig_caption_page.png")

            # Fill caption
            print("  Filling caption...")
            caption_selectors = [
                '[aria-label="Write a caption..."]',
                '[aria-label*="caption"]',
                'div[role="textbox"]',
                '[contenteditable="true"]',
                'textarea',
            ]
            filled = False
            for sel in caption_selectors:
                try:
                    cap = page.locator(sel).first
                    cap.wait_for(timeout=8000)
                    cap.click()
                    page.keyboard.type(caption, delay=5)
                    filled = True
                    print(f"  Caption filled via: {sel}")
                    break
                except Exception:
                    continue
            if not filled:
                page.screenshot(path="Logs/ig_caption_fail.png")
                raise RuntimeError("Could not find Instagram caption field")

            page.wait_for_timeout(1000)

            # Share
            print("  Sharing post...")
            share_selectors = [
                'button:has-text("Share")',
                '[type="button"]:has-text("Share")',
                'div[role="button"]:has-text("Share")',
            ]
            shared = False
            for sel in share_selectors:
                try:
                    btn = page.locator(sel).last
                    btn.wait_for(timeout=8000)
                    btn.click()
                    shared = True
                    print(f"  Share clicked via: {sel}")
                    break
                except Exception:
                    continue
            if not shared:
                raise RuntimeError("Could not find Instagram Share button")

            # Wait for post to complete
            page.wait_for_timeout(6000)
            ctx.close()

        print("  Instagram post PUBLISHED successfully!")
        move_to_done(file_path, "instagram")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def post_twitter(file_path: Path) -> bool:
    load_dotenv("mcp-servers/social-mcp/.env")
    bearer = os.environ.get("TW_BEARER_TOKEN", "")
    api_key = os.environ.get("TW_API_KEY", "")

    if "YOUR_TWITTER" in bearer or "YOUR_TWITTER" in api_key:
        print("\n[Twitter] SKIPPED — credentials not configured (TW_* vars are placeholder)")
        print("  Add real Twitter API keys to mcp-servers/social-mcp/.env to enable Twitter posting")
        return False

    md_text = file_path.read_text(encoding="utf-8")
    tweets = extract_twitter_tweets(md_text)
    print(f"\n[Twitter] Posting thread ({len(tweets)} tweets)...")

    try:
        import tweepy
        client = tweepy.Client(
            bearer_token=bearer,
            consumer_key=api_key,
            consumer_secret=os.environ.get("TW_API_SECRET", ""),
            access_token=os.environ.get("TW_ACCESS_TOKEN", ""),
            access_token_secret=os.environ.get("TW_ACCESS_SECRET", ""),
        )
        last_id = None
        for i, tweet in enumerate(tweets, 1):
            print(f"  Tweeting {i}/{len(tweets)}: {tweet[:60]}...")
            resp = client.create_tweet(text=tweet, in_reply_to_tweet_id=last_id)
            last_id = resp.data.id
            print(f"  Tweet {i} posted (id={last_id})")

        print("  Twitter thread PUBLISHED successfully!")
        move_to_done(file_path, "twitter")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python post_now.py <platform> <file> [image_file]")
        print("  platform: linkedin | facebook | instagram | twitter | all")
        sys.exit(1)

    platform = sys.argv[1].lower()
    file_arg = sys.argv[2]
    file_path = Path(file_arg) if Path(file_arg).is_absolute() else VAULT_PATH / file_arg

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    if platform == "linkedin":
        ok = post_linkedin(file_path)
    elif platform == "facebook":
        ok = post_facebook(file_path)
    elif platform == "instagram":
        img_arg = sys.argv[3] if len(sys.argv) > 3 else str(VAULT_PATH / "Files/ig_post_20260220.png")
        img_path = Path(img_arg) if Path(img_arg).is_absolute() else VAULT_PATH / img_arg
        ok = post_instagram(file_path, img_path)
    elif platform == "twitter":
        ok = post_twitter(file_path)
    elif platform == "all":
        print("=== AI Employee — Social Media Posting ===")
        li_file = VAULT_PATH / "Approved/Social/LINKEDIN_POST_LIVE_TEST_20260220_210343.md"
        fb_file = VAULT_PATH / "Approved/Social/FACEBOOK_POST_LIVE_TEST_20260220_210343.md"
        tw_file = VAULT_PATH / "Approved/Social/TWITTER_POST_LIVE_TEST_20260220_210343.md"
        results = {}
        if li_file.exists():
            results["linkedin"] = post_linkedin(li_file)
        if fb_file.exists():
            results["facebook"] = post_facebook(fb_file)
        if tw_file.exists():
            results["twitter"] = post_twitter(tw_file)
        print("\n=== Results ===")
        for p, r in results.items():
            print(f"  {p}: {'SUCCESS' if r else 'FAILED/SKIPPED'}")
        ok = all(results.values())
    else:
        print(f"Unknown platform: {platform}")
        ok = False

    sys.exit(0 if ok else 1)
