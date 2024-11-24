from playwright.sync_api import Locator

def wait_for_locator_to_be_stable(locator: Locator):
    locator.hover(trial=True)
