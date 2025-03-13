from collections.abc import Generator
import os
import shutil
import zipfile
from contextlib import contextmanager
from io import FileIO
import tempfile
import requests
import logging

LOGGER = logging.getLogger(__name__)

# https://stackoverflow.com/questions/7184793/how-to-download-a-crx-file-from-the-chrome-web-store-for-a-given-id
EXTENSION_ID = "beojaiildognffpjmpiamfofnplkdfih"
CHROME_EXT_DOWNLOAD_URL = f"https://clients2.google.com/service/update2/crx?response=redirect&prodversion=95.0.4638.54&acceptformat=crx2,crx3&x=id%3D{EXTENSION_ID}%26uc"

def download_extension_to_unpacked() -> tempfile.TemporaryDirectory:
    with download_extension_to_tempfile() as f:
        temp_dir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(f.name, "r") as zip_file:
            zip_file.extractall(temp_dir.name)
            LOGGER.debug("extracted crx to directory: " + temp_dir.name)
            return temp_dir


def unpacked_to_crx(dir_name: str) -> str:
    temp_dir = tempfile.TemporaryDirectory()
    zip_name = os.path.join(temp_dir.name, "shopee-captcha-solver")
    shutil.make_archive(
        zip_name,
        "zip",
        dir_name, 
    )
    LOGGER.debug("zipped shopee-captcha-solver to directory: " + temp_dir.name)
    input()
    return zip_name + ".zip"


@contextmanager
def download_extension_to_tempfile() -> Generator[FileIO, None, None]:
    r = requests.get(CHROME_EXT_DOWNLOAD_URL)
    LOGGER.debug("downloaded chrome extension from " + CHROME_EXT_DOWNLOAD_URL)
    tf = tempfile.NamedTemporaryFile("wb")
    _ = tf.write(r.content)
    LOGGER.debug("wrote chrome extension to temp file at: " + tf.name)
    file = FileIO(tf.name)
    try:
        yield file
    finally:
        file.close()
        tf.close()
