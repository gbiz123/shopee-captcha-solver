import logging
import time
import os

from playwright.sync_api import Page, sync_playwright, expect
from playwright_stealth import stealth_sync, StealthConfig

from ..playwrightsolver import PlaywrightSolver

def test_solve_captcha_on_shopee_register(caplog):
    mexico_proxy = {
        "server": "45.67.2.115:5689",
    }
    caplog.set_level(logging.DEBUG)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, proxy=mexico_proxy)
        page = browser.new_page()
        config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
        stealth_sync(page, config)
        page.goto("https://shopee.com.mx/buyer/signup?next=https%3A%2F%2Fshopee.com.mx%2F")
        sadcaptcha = PlaywrightSolver(page, os.environ["API_KEY"], dump_requests=True)
        page.locator("input[name=phone]").click()
        page.keyboard.type("55 1254 5678", delay=100)
        page.locator("form >  button").click()
        sadcaptcha.solve_captcha_if_present()
        assert sadcaptcha.captcha_is_not_present()

def test_solve_captcha_on_shopee_login(caplog):
    brazil_proxy = {
        "server": "206.232.75.209:6779",
    }
    caplog.set_level(logging.DEBUG)
    with sync_playwright() as p:
        browser = p.chromium.launch(
                headless=False,
                proxy=brazil_proxy,
                args=[
                    "--disable-dev-shm-usage", 
                     "--disable-blink-features=AutomationControlled",
                ]
        )
        context = browser.new_context(
            # user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
        # devinscrumbo@gmail.com, th.etoughapi1!
        stealth_sync(page, config)
        page.goto("https://shopee.com.br/")
        sadcaptcha = PlaywrightSolver(page, os.environ["API_KEY"], dump_requests=True)
        # input("Sign in to Google then press enter")
        # url = page.url # Refresh the page to avoid detached frame (hacky yes)
        # page.goto(url)
        input("Press enter to refresh the page and solve the captcha")
        sadcaptcha.solve_captcha_if_present()
        time.sleep(5)
        assert sadcaptcha.captcha_is_not_present()
