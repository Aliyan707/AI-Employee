#!/usr/bin/env python3
"""Post to LinkedIn/Facebook using undetected-chromedriver (stealth mode).

Bypasses bot detection. Uses selenium with undetected Chrome.

Usage:
  python post_stealth.py linkedin <file>
  python post_stealth.py facebook <file>
"""
import os
import re
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

VAULT_PATH = Path("C:/Users/Cs/Desktop/AI Employee-")
PKT = timezone(timedelta(hours=5))
Path("Logs").mkdir(exist_ok=True)


def extract_post_content(md_text: str) -> str:
    m = re.search(r"## Post Content\s*\n+(.*?)(?:\n---\n|\Z)", md_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m2 = re.match(r"^---\n.*?\n---\n(.*)", md_text, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    return md_text.strip()


def wait_for_element(driver, selectors, timeout=30):
    """Try multiple selectors, return first found element."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import selenium.common.exceptions as ex

    end_time = time.time() + timeout
    while time.time() < end_time:
        for sel in selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    return el
            except Exception:
                pass
        time.sleep(0.5)
    return None


def post_linkedin(file_path: Path) -> bool:
    load_dotenv("mcp-servers/browser-mcp/.env")
    email = os.environ.get("LINKEDIN_EMAIL", "")
    password = os.environ.get("LINKEDIN_PASSWORD", "")

    md_text = file_path.read_text(encoding="utf-8")
    content = extract_post_content(md_text)
    print(f"[LinkedIn] Content: {len(content)} chars")
    print(f"  Email: {email}")

    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # Session directory
    session_dir = Path("mcp-servers/browser-mcp/linkedin-session-uc")
    session_dir.mkdir(parents=True, exist_ok=True)

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={session_dir}")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,720")

    driver = uc.Chrome(options=options, headless=False)
    driver.set_page_load_timeout(30)
    wait = WebDriverWait(driver, 30)

    try:
        print("  Navigating to LinkedIn...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(4)

        current_url = driver.current_url
        print(f"  URL: {current_url}")

        if "/feed/" not in current_url or "login" in current_url:
            print("  Logging in...")
            driver.get("https://www.linkedin.com/login")
            time.sleep(2)

            # Fill email
            driver.find_element(By.ID, "username").send_keys(email)
            time.sleep(0.5)
            driver.find_element(By.ID, "password").send_keys(password)
            time.sleep(0.5)
            driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

            print("  Waiting for login (up to 3 min - complete any 2FA)...")
            try:
                wait.until(lambda d: "/feed/" in d.current_url and "login" not in d.current_url)
                print("  Logged in!")
            except Exception:
                print(f"  Timeout - URL: {driver.current_url}")
                print("  Complete login manually in browser window (2 min)...")
                for _ in range(120):
                    if "/feed/" in driver.current_url:
                        print("  Manual login detected!")
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError("Login timeout")
        else:
            print("  Already logged in!")

        # Take screenshot
        driver.save_screenshot("Logs/li_uc_feed.png")
        time.sleep(3)

        # Find composer
        print("  Opening post composer...")
        composer = None
        for sel in [
            'button:contains("Start a post")',
            '.share-box-feed-entry__trigger',
        ]:
            pass  # CSS :contains not supported

        # Try XPath
        from selenium.webdriver.common.by import By
        try:
            el = driver.find_element(By.XPATH, '//*[contains(text(), "Start a post")]')
            el.click()
            composer = el
            print("  Composer opened (XPath)")
        except Exception:
            pass

        if not composer:
            # Try clicking the share box input area
            try:
                el = driver.find_element(By.CSS_SELECTOR, '[data-control-name="share.sharebox_open"]')
                el.click()
                composer = el
                print("  Composer opened (data-control-name)")
            except Exception:
                pass

        if not composer:
            # Take screenshot to debug
            driver.save_screenshot("Logs/li_uc_composer_fail.png")
            raise RuntimeError("Could not open LinkedIn composer — see Logs/li_uc_composer_fail.png")

        time.sleep(2)

        # Find editor
        print("  Typing content...")
        editor = None
        for sel in ["[role='textbox']", ".ql-editor", "[contenteditable='true']"]:
            try:
                editor = driver.find_element(By.CSS_SELECTOR, sel)
                break
            except Exception:
                pass

        if not editor:
            raise RuntimeError("Could not find post editor")

        editor.click()
        time.sleep(0.5)
        # Type in chunks
        chunk_size = 100
        for i in range(0, len(content), chunk_size):
            editor.send_keys(content[i:i+chunk_size])
            time.sleep(0.05)

        time.sleep(2)

        # Submit
        print("  Submitting...")
        for sel in [
            "button.share-actions__primary-action",
            "[data-control-name='share.post']",
        ]:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                btn.click()
                print(f"  Posted via: {sel}")
                break
            except Exception:
                pass

        time.sleep(5)
        driver.save_screenshot("Logs/li_uc_posted.png")
        print("  LinkedIn post published!")

    except Exception as e:
        print(f"  ERROR: {e}")
        try:
            driver.save_screenshot("Logs/li_uc_error.png")
        except Exception:
            pass
        driver.quit()
        return False

    driver.quit()

    done_dir = VAULT_PATH / "Done" / "Social"
    done_dir.mkdir(parents=True, exist_ok=True)
    dest = done_dir / f"POSTED_{file_path.name}"
    shutil.move(str(file_path), str(dest))
    print(f"  Moved to: {dest}")
    return True


def post_facebook(file_path: Path) -> bool:
    load_dotenv("mcp-servers/social-mcp/.env")
    email_addr = os.environ.get("Facebook_EMAIL", "")
    password = os.environ.get("Facebook_PASSWORD", "")

    md_text = file_path.read_text(encoding="utf-8")
    content = extract_post_content(md_text)
    print(f"[Facebook] Content: {len(content)} chars")
    print(f"  Email: {email_addr}")

    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    session_dir = Path("mcp-servers/social-mcp/fb-session-uc")
    session_dir.mkdir(parents=True, exist_ok=True)

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={session_dir}")
    options.add_argument("--window-size=1280,800")

    driver = uc.Chrome(options=options, headless=False)
    driver.set_page_load_timeout(30)

    try:
        print("  Navigating to Facebook...")
        driver.get("https://www.facebook.com/")
        time.sleep(4)

        current_url = driver.current_url
        print(f"  URL: {current_url}")
        driver.save_screenshot("Logs/fb_uc_initial.png")

        # Login check
        try:
            email_field = driver.find_element(By.CSS_SELECTOR, "input[name='email']")
            print("  Login form found — logging in...")
            email_field.clear()
            email_field.send_keys(email_addr)
            time.sleep(0.5)

            pass_field = driver.find_element(By.CSS_SELECTOR, "input[name='pass']")
            pass_field.clear()
            pass_field.send_keys(password)
            time.sleep(0.5)

            # Click login button
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[name='login']")
            login_btn.click()

            print("  Waiting for login (up to 3 min)...")
            for _ in range(180):
                url = driver.current_url
                if "login" not in url and "checkpoint" not in url:
                    print(f"  Logged in! URL: {url}")
                    break
                time.sleep(1)
            else:
                print(f"  Login stuck at: {driver.current_url}")
                print("  Complete login manually in the browser window (2 min)...")
                for _ in range(120):
                    url = driver.current_url
                    if "login" not in url and "checkpoint" not in url:
                        print("  Manual login complete!")
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError("Login timeout")
        except Exception as login_err:
            if "email" in str(login_err).lower() or "find_element" in str(login_err):
                print("  Already logged in (no email field found)")
            else:
                raise

        time.sleep(3)
        driver.save_screenshot("Logs/fb_uc_feed.png")

        # Find and click composer
        print("  Looking for post composer...")
        composer_clicked = False

        # Try XPath for "What's on your mind"
        for xpath in [
            '//*[@placeholder="What\'s on your mind?"]',
            '//*[@placeholder="What\'s on your mind"]',
            '//*[contains(@aria-label, "What\'s on your mind")]',
            '//*[@data-pagelet="FeedUnit_0"]//*[@role="button"]',
        ]:
            try:
                el = driver.find_element(By.XPATH, xpath)
                el.click()
                composer_clicked = True
                print(f"  Composer via xpath: {xpath[:60]}")
                break
            except Exception:
                pass

        if not composer_clicked:
            driver.save_screenshot("Logs/fb_uc_composer_fail.png")
            raise RuntimeError("Could not open FB composer — see Logs/fb_uc_composer_fail.png")

        time.sleep(2)

        # Type content
        print("  Typing content...")
        from selenium.webdriver.common.by import By
        textbox = None
        for sel in ["div[role='textbox']", "[contenteditable='true']"]:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in reversed(els):  # usually the last one is the composer
                    if el.is_displayed():
                        textbox = el
                        break
                if textbox:
                    break
            except Exception:
                pass

        if not textbox:
            raise RuntimeError("Could not find FB text editor")

        textbox.click()
        time.sleep(0.5)
        for i in range(0, len(content), 100):
            textbox.send_keys(content[i:i+100])
            time.sleep(0.05)

        time.sleep(2)

        # Submit
        print("  Submitting...")
        for xpath in [
            '//div[@aria-label="Post"]',
            '//button[normalize-space()="Post"]',
        ]:
            try:
                btn = driver.find_element(By.XPATH, xpath)
                btn.click()
                print(f"  Posted!")
                break
            except Exception:
                pass

        time.sleep(5)
        driver.save_screenshot("Logs/fb_uc_posted.png")
        print("  Facebook post published!")

    except Exception as e:
        print(f"  ERROR: {e}")
        try:
            driver.save_screenshot("Logs/fb_uc_error.png")
        except Exception:
            pass
        driver.quit()
        return False

    driver.quit()

    done_dir = VAULT_PATH / "Done" / "Social"
    done_dir.mkdir(parents=True, exist_ok=True)
    dest = done_dir / f"POSTED_{file_path.name}"
    shutil.move(str(file_path), str(dest))
    print(f"  Moved to: {dest}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python post_stealth.py <platform> <file>")
        sys.exit(1)

    platform = sys.argv[1].lower()
    file_arg = sys.argv[2]
    fp = Path(file_arg) if Path(file_arg).is_absolute() else VAULT_PATH / file_arg

    if not fp.exists():
        print(f"File not found: {fp}")
        sys.exit(1)

    if platform == "linkedin":
        ok = post_linkedin(fp)
    elif platform == "facebook":
        ok = post_facebook(fp)
    else:
        print(f"Unknown platform: {platform}")
        ok = False

    sys.exit(0 if ok else 1)
