from shopee_captcha_solver.download_crx import download_extension_to_tempfile, download_extension_to_unpacked, unpacked_to_crx
import logging
import os

def test_re_zip_crx():
    with download_extension_to_unpacked() as ext:
        zipped = unpacked_to_crx(ext)
        assert os.path.exists(zipped)

def test_download_extension_to_unpac(caplog):
    caplog.set_level(logging.DEBUG)
    with download_extension_to_unpacked() as ext:
        assert os.path.isdir(ext)

def test_download_extension_to_tempfile(caplog):
    caplog.set_level(logging.DEBUG)
    with download_extension_to_tempfile() as ext:
        assert os.path.isfile(ext.name)
