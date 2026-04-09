"""
OpenClaw - Automation tool for claiming DigitalOcean credits
from the GitHub Student Developer Education Pack.

Usage:
    python claim_digitalocean.py --username <github_username> --password <github_password>
    or set GITHUB_USERNAME and GITHUB_PASSWORD environment variables.
    Credentials can also be entered interactively when omitted.
"""

import argparse
import getpass
import os
import sys
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


GITHUB_LOGIN_URL = "https://github.com/login"
EDUCATION_PACK_URL = "https://education.github.com/pack/offers"
DIGITALOCEAN_OFFER_NAME = "DigitalOcean"

# Timeout constants (milliseconds)
LOGIN_ERROR_TIMEOUT_MS = 3000
OFFER_SELECTOR_TIMEOUT_MS = 5000

# Browser keep-open duration after a successful run (seconds)
POST_CLAIM_WAIT_SECONDS = 15


def parse_args():
    parser = argparse.ArgumentParser(
        description="Claim DigitalOcean credits from the GitHub Student Developer Pack."
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("GITHUB_USERNAME", ""),
        help="GitHub username (or set GITHUB_USERNAME env var)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("GITHUB_PASSWORD", ""),
        help="GitHub password (or set GITHUB_PASSWORD env var)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (no visible window)",
    )
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=500,
        help="Slow down Playwright operations by the specified milliseconds (default: 500)",
    )
    return parser.parse_args()


def is_digitalocean_url(url: str) -> bool:
    """Return True only when *url* belongs to the digitalocean.com domain."""
    try:
        hostname = urlparse(url).hostname or ""
        return hostname == "digitalocean.com" or hostname.endswith(".digitalocean.com")
    except ValueError:
        return False


def login_to_github(page, username: str, password: str) -> None:
    """Log into GitHub with the provided credentials."""
    print("[*] Navigating to GitHub login page...")
    page.goto(GITHUB_LOGIN_URL)
    page.wait_for_load_state("networkidle")

    print("[*] Entering credentials...")
    page.fill("#login_field", username)
    page.fill("#password", password)
    page.click('[name="commit"]')
    page.wait_for_load_state("networkidle")

    # Handle two-factor authentication prompt if present
    if "two-factor" in page.url or "two_factor" in page.url:
        print(
            "[!] Two-factor authentication required.\n"
            "    Please complete 2FA in the browser window, then press Enter to continue..."
        )
        input()
        page.wait_for_load_state("networkidle")

    # Check for login errors
    error_selector = ".flash-error, #js-flash-container .flash-error"
    try:
        page.wait_for_selector(error_selector, timeout=LOGIN_ERROR_TIMEOUT_MS)
        error_text = page.inner_text(error_selector)
        print(f"[!] Login failed: {error_text.strip()}")
        sys.exit(1)
    except PlaywrightTimeoutError:
        pass  # No error shown — login succeeded

    print("[+] Successfully logged in to GitHub.")


def navigate_to_education_pack(page) -> None:
    """Navigate to the GitHub Education Pack offers page."""
    print("[*] Navigating to GitHub Education Pack offers page...")
    page.goto(EDUCATION_PACK_URL)
    page.wait_for_load_state("networkidle")

    # If redirected to login, we need to authenticate first
    if "github.com/login" in page.url:
        print("[!] Redirected to login — please log in first.")
        sys.exit(1)

    print("[+] Reached Education Pack offers page.")


def find_and_claim_digitalocean(page) -> None:
    """Locate the DigitalOcean offer card and click to claim it."""
    print(f"[*] Searching for {DIGITALOCEAN_OFFER_NAME} offer...")

    # The offers page lists partner offers; locate the DigitalOcean entry.
    # GitHub Education Pack uses offer cards — try common selectors.
    offer_selectors = [
        f'[data-partner-name="{DIGITALOCEAN_OFFER_NAME}"]',
        f'[aria-label*="{DIGITALOCEAN_OFFER_NAME}"]',
        f'a[href*="digitalocean"]',
    ]

    offer_element = None
    for selector in offer_selectors:
        try:
            offer_element = page.wait_for_selector(selector, timeout=OFFER_SELECTOR_TIMEOUT_MS)
            if offer_element:
                break
        except PlaywrightTimeoutError:
            continue

    # Fallback: search by visible text
    if not offer_element:
        try:
            offer_element = page.get_by_text(DIGITALOCEAN_OFFER_NAME, exact=False).first
        except (PlaywrightTimeoutError, AttributeError):
            pass

    if not offer_element:
        print(f"[!] Could not find the {DIGITALOCEAN_OFFER_NAME} offer on the page.")
        print("    Make sure you have an active GitHub Student/Teacher verification.")
        sys.exit(1)

    print(f"[+] Found {DIGITALOCEAN_OFFER_NAME} offer. Clicking to claim...")
    offer_element.click()
    page.wait_for_load_state("networkidle")

    # Check if we landed on the DigitalOcean redemption / offer page
    if is_digitalocean_url(page.url) or "claim" in page.url:
        print(
            "[+] Redirected to DigitalOcean — follow the on-screen instructions to\n"
            "    complete your account setup and redeem the credits."
        )
    else:
        print(f"[+] Claim action triggered. Current URL: {page.url}")


def main() -> None:
    args = parse_args()

    username = args.username
    password = args.password

    # Prompt interactively if credentials were not supplied
    if not username:
        username = input("GitHub username: ").strip()
    if not password:
        password = getpass.getpass("GitHub password: ")

    if not username or not password:
        print("[!] GitHub credentials are required.")
        sys.exit(1)

    slow_mo = max(0, min(args.slow_mo, 5000))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless, slow_mo=slow_mo)
        context = browser.new_context()
        page = context.new_page()

        try:
            login_to_github(page, username, password)
            navigate_to_education_pack(page)
            find_and_claim_digitalocean(page)

            print(
                "\n[+] Done! If the DigitalOcean offer page opened, complete the\n"
                "    registration there to finish claiming your credits."
            )

            # Keep the browser open briefly so the user can see the result
            if not args.headless:
                print(
                    f"[*] Keeping browser open for {POST_CLAIM_WAIT_SECONDS} seconds "
                    "so you can review the result..."
                )
                time.sleep(POST_CLAIM_WAIT_SECONDS)

        except PlaywrightTimeoutError as exc:
            print(f"[!] Timed out waiting for a page element: {exc}")
            sys.exit(1)
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
