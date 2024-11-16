import base64
import json
import os

from ..downloader import download_image_b64
from ..api import ApiClient
from shopee_captcha_solver.models import ImageCrawlCaptchaRequest, ImageCrawlCaptchaResponse, ProportionalPoint, PuzzleCaptchaResponse, SemanticShapesRequest

api_client = ApiClient(os.environ["API_KEY"])

def test_puzzle():
    piece = download_image_b64("https://raw.githubusercontent.com/gbiz123/sadcaptcha-code-examples/master/images/piece.png")
    puzzle = download_image_b64("https://raw.githubusercontent.com/gbiz123/sadcaptcha-code-examples/master/images/puzzle.jpg")
    res = api_client.puzzle(puzzle, piece)
    assert isinstance(res, PuzzleCaptchaResponse)

def test_arced_slide():
    with open("src/shopee_captcha_solver/tests/temu_slide_captcha_request.json") as file:
        data = json.load(file)
        res = api_client.image_crawl(ImageCrawlCaptchaRequest(**data))
        assert isinstance(res, ImageCrawlCaptchaResponse)

def test_semantic_shapes():
    with open("src/shopee_captcha_solver/tests/shapes.png", "rb") as file:
        shapes = base64.b64encode(file.read()).decode()

    challenge = "Please click on the lowercase letter corresponding to the green letter."
    res = api_client.semantic_shapes(SemanticShapesRequest(image_b64=shapes, challenge=challenge))
    assert isinstance(res, ProportionalPoint)

