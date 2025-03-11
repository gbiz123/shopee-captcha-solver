import os
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync, StealthConfig

from shopee_captcha_solver.launcher import shopee_solver_context

def test_launch_browser_with_crx():
    with sync_playwright() as p:
        ctx = shopee_solver_context(p, os.environ["API_KEY"])
        page = ctx.new_page()
        stealth_config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
        stealth_sync(page, stealth_config)
        input("waiting for enter")
