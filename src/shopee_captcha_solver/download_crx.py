import io
import os
from collections.abc import Generator
import zipfile
from contextlib import contextmanager
from io import BufferedWriter, FileIO
import tempfile
import requests
import logging

LOGGER = logging.getLogger(__name__)

# https://stackoverflow.com/questions/7184793/how-to-download-a-crx-file-from-the-chrome-web-store-for-a-given-id
EXTENSION_ID = "beojaiildognffpjmpiamfofnplkdfih"
CHROME_EXT_DOWNLOAD_URL = f"https://clients2.google.com/service/update2/crx?response=redirect&prodversion=126.0.6478.270&acceptformat=crx2,crx3&x=id%3D{EXTENSION_ID}%26uc"

@contextmanager
def download_extension_to_tempfile() -> Generator[BufferedWriter, None, None]:
    r = requests.get(CHROME_EXT_DOWNLOAD_URL)
    LOGGER.debug("downloaded chrome extension from " + CHROME_EXT_DOWNLOAD_URL)
    tf = open(os.path.join(tempfile.gettempdir(), os.urandom(24).hex()), "wb")
    _ = tf.write(r.content)
    LOGGER.debug("wrote chrome extension to temp file at: " + tf.name)
    try:
        yield tf
    finally:
        tf.close()

def download_extension_to_unpacked() -> tempfile.TemporaryDirectory:
    """
    Download the SadCaptcha Chrome extension from GitHub and return an unpacked
    TemporaryDirectory that can be passed to Playwright / Chrome.
    """
    repo_zip_url = (
        "https://codeload.github.com/gbiz123/shopee-captcha-solver-chrome-extension/zip/refs/heads/master"
    )

    LOGGER.debug("Downloading SadCaptcha extension from %s", repo_zip_url)
    resp = requests.get(repo_zip_url, timeout=30)
    resp.raise_for_status()

    tmp_dir = tempfile.TemporaryDirectory(prefix="sadcaptcha_ext_", delete=False)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        # GitHub zips have a single top‑level folder → strip it
        root_prefix = zf.namelist()[0].split("/")[0] + "/"
        for member in zf.namelist():
            if member.endswith("/"):
                continue
            rel_path = member[len(root_prefix) :]
            if not rel_path:
                continue
            dest_file = os.path.join(tmp_dir.name, rel_path)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            with zf.open(member) as src, open(dest_file, "wb") as dst:
                dst.write(src.read())

    LOGGER.debug("Extension unpacked to %s", tmp_dir.name)
    return tmp_dir
