from playwright.async_api import Locator

async def wait_for_locator_to_be_stable(locator: Locator):
    await locator.hover(trial=True)
