#!/usr/bin/env python3
"""One-time social media session setup.

Opens visible browser windows for each platform.
Log in manually. Sessions are saved for automated posting.

Usage:
  python setup_social_sessions.py          # Setup all platforms
  python setup_social_sessions.py linkedin # LinkedIn only
  python setup_social_sessions.py facebook # Facebook only
"""
import sys
import time
from pathlib import Path

VAULT_PATH = Path("C:/Users/Cs/Desktop/AI Employee-")
LINKEDIN_SESSION = VAULT_PATH / "mcp-servers/browser-mcp/linkedin-session"
FACEBOOK_SESSION = VAULT_PATH / "mcp-servers/social-mcp/fb-session"


def setup_linkedin():
    print("\n" + "=" * 60)
    print("LINKEDIN SESSION SETUP")
    print("=" * 60)
    print()
    print("A Chrome browser will open at LinkedIn.")
    print("1. Enter your email and password")
    print("2. Complete any 2FA/security verification")
    print("3. Wait until you see the LinkedIn feed")
    print("4. Come back here - it will detect login automatically")
    print()
    LINKEDIN_SESSION.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(LINKEDIN_SESSION),
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        page = ctx.new_page()
        page.goto("https://www.linkedin.com/login")

        print("Browser opened at LinkedIn login page.")
        print("Waiting for you to complete login (up to 5 minutes)...")

        try:
            page.wait_for_url("**/feed/**", timeout=300000)
            print()
            print("LinkedIn login successful! Session saved.")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nInterrupted.")
        except Exception as e:
            print(f"Timeout or error: {e}")
            print(f"Current URL: {page.url}")
        finally:
            ctx.close()


def setup_facebook():
    print("\n" + "=" * 60)
    print("FACEBOOK SESSION SETUP")
    print("=" * 60)
    print()
    print("A Chrome browser will open at Facebook.")
    print("1. Enter your email and password")
    print("2. Complete any 2FA/security verification")
    print("3. Wait until you see the Facebook feed/home")
    print("4. Come back here - it will detect login automatically")
    print()
    FACEBOOK_SESSION.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(FACEBOOK_SESSION),
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
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        page = ctx.new_page()
        page.goto("https://www.facebook.com/login")

        print("Browser opened at Facebook login page.")
        print("Waiting for you to complete login (up to 5 minutes)...")

        try:
            # Facebook may redirect to various URLs after login
            page.wait_for_function(
                """() => {
                    const url = window.location.href;
                    return url.includes('facebook.com') &&
                           !url.includes('/login') &&
                           !url.includes('checkpoint') &&
                           (url.includes('/home') || url.includes('?sk=') ||
                            document.querySelector('[aria-label="Home"]') !== null ||
                            document.querySelector('[data-pagelet="FeedUnit_0"]') !== null);
                }""",
                timeout=300000
            )
            print()
            print("Facebook login successful! Session saved.")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nInterrupted.")
        except Exception as e:
            print(f"Timeout or error: {e}")
            print(f"Current URL: {page.url}")
        finally:
            ctx.close()


def post_after_setup(platform: str, file_path: Path):
    """After sessions are set up, post directly."""
    import subprocess
    script = VAULT_PATH / "post_now.py"
    print(f"\nPosting to {platform}...")
    result = subprocess.run(
        ["python", str(script), platform, str(file_path)],
        cwd=str(VAULT_PATH)
    )
    return result.returncode == 0


if __name__ == "__main__":
    platform = sys.argv[1] if len(sys.argv) > 1 else "all"

    print()
    print("AI Employee — Social Media Session Setup")
    print("=" * 60)
    print("This script sets up authenticated sessions for automated posting.")
    print("You will log in manually once. Sessions are saved for future use.")
    print()

    if platform in ("all", "linkedin"):
        setup_linkedin()

    if platform in ("all", "facebook"):
        setup_facebook()

    print()
    print("=" * 60)
    print("Session setup complete!")
    print()
    print("Now run posting:")
    print("  python post_now.py linkedin Approved/Social/LINKEDIN_POST_LIVE_TEST_20260220_210343.md")
    print("  python post_now.py facebook Approved/Social/FACEBOOK_POST_LIVE_TEST_20260220_210343.md")
    print()
    print("Or post all at once:")
    print("  python post_now.py all dummy")
