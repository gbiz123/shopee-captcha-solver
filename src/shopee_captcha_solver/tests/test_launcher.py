import os
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from playwright_stealth import stealth_sync, stealth_async, StealthConfig

import pytest
from shopee_captcha_solver.launcher import make_async_playwright_solver_context, make_playwright_solver_context, make_undetected_chromedriver_solver


def test_launch_uc_solver():
    solver = make_undetected_chromedriver_solver(
        os.environ["API_KEY"],
        headless=False
    )
    input("waiting for enter")
    solver.close()

def test_launch_browser_with_crx():
    with sync_playwright() as p:
        ctx = make_playwright_solver_context(
            p,
            os.environ["API_KEY"],
            headless=False
        )
        page = ctx.new_page()
        stealth_config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
        stealth_sync(page, stealth_config)
        input("waiting for enter")

@pytest.mark.asyncio
async def test_launch_browser_with_asyncpw():
    async with async_playwright() as p:
        ctx = await make_async_playwright_solver_context(
            p,
            os.environ["API_KEY"],
            headless=False
        )
        page = await ctx.new_page()
        stealth_config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
        await stealth_async(page, stealth_config)
        input("waiting for enter")
