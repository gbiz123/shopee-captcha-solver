import asyncio
import logging
import os

from playwright.async_api import Page, async_playwright, expect
from playwright_stealth import stealth_async, StealthConfig
import pytest

from ..asyncplaywrightsolver import AsyncPlaywrightSolver

@pytest.mark.asyncio
async def test_solve_on_register(caplog):
    async with async_playwright() as p:
        mexico_proxy = {
            "server": "45.67.2.115:5689",
            "username": "aupzmsxp",
            "password": "vszgekgiz6ax"
        }
        caplog.set_level(logging.DEBUG)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, proxy=mexico_proxy)
            page = await browser.new_page()
            config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
            await stealth_async(page, config)
            await page.goto("https://shopee.com.mx/buyer/signup?next=https%3A%2F%2Fshopee.com.mx%2F")
            sadcaptcha = AsyncPlaywrightSolver(page, os.environ["API_KEY"], dump_requests=True)
            await page.locator("input[name=phone]").click()
            await page.keyboard.type("55 1254 5678", delay=100)
            await page.locator("form >  button").click()
            await sadcaptcha.solve_captcha_if_present()
            assert await sadcaptcha.captcha_is_not_present()

@pytest.mark.asyncio
async def test_solve_captcha_on_shopee_login(caplog):
    brazil_proxy = {
        "server": "45.67.2.115:5689",
        "username": "aupzmsxp",
        "password": "vszgekgiz6ax"
    }
    caplog.set_level(logging.DEBUG)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
                headless=False,
                proxy=brazil_proxy,
                args=[
                    "--disable-dev-shm-usage", 
                     "--disable-blink-features=AutomationControlled",
                ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
        # devinscrumbo@gmail.com, th.etoughapi1!
        await stealth_async(page, config)
        await page.goto("https://shopee.co.id/")
        sadcaptcha = AsyncPlaywrightSolver(page, os.environ["API_KEY"], dump_requests=True)
        input("Sign in to Google then press enter")
        url = page.url # Refresh the page to avoid detached frame (hacky yes)
        await page.goto(url)
        input("Press enter to refresh the page and solve the captcha")
        await sadcaptcha.solve_captcha_if_present()
        assert await sadcaptcha.captcha_is_not_present()
