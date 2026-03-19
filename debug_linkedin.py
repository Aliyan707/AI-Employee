#!/usr/bin/env python3
"""Debug LinkedIn page state - non-interactive."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("mcp-servers/browser-mcp/.env")
email = os.environ.get("LINKEDIN_EMAIL", "")
password = os.environ.get("LINKEDIN_PASSWORD", "")
session_dir = Path("mcp-servers/browser-mcp/linkedin-session")

from playwright.sync_api import sync_playwright

Path("Logs").mkdir(exist_ok=True)

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        str(session_dir),
        headless=True,
        viewport={"width": 1280, "height": 720},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="en-US",
    )
    page = ctx.new_page()
    page.set_default_timeout(30000)

    print("Navigating to LinkedIn feed...")
    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    print(f"Current URL: {page.url}")
    print(f"Page title: {page.title()}")

    page.screenshot(path="Logs/linkedin_debug.png", full_page=False)
    print("Screenshot saved to Logs/linkedin_debug.png")

    # Find all buttons
    buttons = page.locator("button").all()
    print(f"\nFound {len(buttons)} buttons on page:")
    for i, btn in enumerate(buttons[:25]):
        try:
            txt = (btn.text_content() or "").strip()
            aria = btn.get_attribute("aria-label") or ""
            cls = (btn.get_attribute("class") or "")[:60]
            if txt or aria:
                print(f"  [{i}] text='{txt[:50]}' aria='{aria[:40]}' class='{cls}'")
        except Exception:
            pass

    print("\nSearching for 'Start a post':")
    try:
        els = page.locator("text=Start a post").all()
        print(f"  Found {len(els)} matches")
        for i, el in enumerate(els):
            tag = el.evaluate("el => el.tagName")
            cls = el.get_attribute("class") or ""
            print(f"  [{i}] <{tag}> class='{cls[:60]}'")
    except Exception as e:
        print(f"  Error: {e}")

    # Print page HTML excerpt (first 3000 chars around "start" keywords)
    try:
        html = page.content()
        idx = html.lower().find("start a post")
        if idx >= 0:
            print(f"\nHTML around 'start a post' (pos {idx}):")
            print(html[max(0,idx-200):idx+400])
    except Exception as e:
        print(f"HTML search error: {e}")

    ctx.close()
    print("\nDone.")
