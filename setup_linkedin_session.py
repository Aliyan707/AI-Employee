#!/usr/bin/env python3
"""LinkedIn one-time session setup.

Opens a visible Chrome browser. Log into LinkedIn manually.
Session is saved so future postings work without login.

Usage:
  python setup_linkedin_session.py
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("mcp-servers/browser-mcp/.env")
session_dir = Path("mcp-servers/browser-mcp/linkedin-session")
session_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("LinkedIn Session Setup")
print("=" * 60)
print()
print("A Chrome browser window will open.")
print("Please:")
print("  1. Log into LinkedIn with your credentials")
print("  2. Complete any security checks / 2FA")
print("  3. Make sure you reach the LinkedIn feed page")
print("  4. Then come back here and press Ctrl+C to save the session")
print()
print("Session will be saved to:", session_dir)
print()

from playwright.sync_api import sync_playwright

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
    )
    page = ctx.new_page()
    page.goto("https://www.linkedin.com/login")

    print("Browser opened — complete login in the browser window...")
    print("Waiting (up to 5 minutes)...")

    try:
        # Wait for feed page, up to 5 minutes
        page.wait_for_url("**/feed/**", timeout=300000)
        print()
        print("Login detected! Feed page reached.")
        print("Session saved to:", session_dir)
        time.sleep(2)  # Let cookies save
    except KeyboardInterrupt:
        print()
        print("Interrupted by user.")
        print("Current URL:", page.url)
    except Exception as e:
        print(f"Error: {e}")
        print("Current URL:", page.url)
    finally:
        ctx.close()

print()
print("Session setup complete.")
print("You can now run: python post_now.py linkedin <file>")
