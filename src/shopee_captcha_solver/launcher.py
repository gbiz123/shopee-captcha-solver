import logging
import re
import tempfile
from .download_crx import download_extension_to_unpacked, download_extension_to_tempfile

from playwright.sync_api import sync_playwright, BrowserContext, Playwright

LOGGER = logging.getLogger(__name__)

def shopee_solver_context(playwright: Playwright, api_key: str) -> BrowserContext:
    with download_extension_to_unpacked() as ext:
        user_data_dir = tempfile.TemporaryDirectory()
        _patch_extension_file_with_key(ext, api_key)
        ctx = playwright.chromium.launch_persistent_context(
            user_data_dir.name,
            headless=False,
            args=[
                f"--disable-extensions-except={ext}",
                f"--load-extension={ext}",
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',         
                '--disable-web-security',
                '--disable-infobars',  
                '--start-maximized'
            ]
        )
        return ctx

def _patch_extension_file_with_key(extension_dir: str, api_key: str) -> None:
    with open(extension_dir + "/script.js") as f:
        script = f.read()
    script = patch_extension_script_with_key(script, api_key)
    with open(extension_dir + "/script.js", "w") as f:
        _ = f.write(script)
    LOGGER.debug("patched extension file with api key")

def patch_extension_script_with_key(script: str, api_key: str) -> str:
    script = script.replace("return apiKey;", f"return \"{api_key}\";")
    script = script.replace("localStorage.getItem(\"sadCaptchaKey\");", "true;")
    LOGGER.debug("patched extension script with api key")
    return script
