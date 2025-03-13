"""This class handles the captcha solving for playwright users"""

import logging
import math
import random
from typing import Any
import warnings
from playwright.sync_api import FloatRect, Locator, Page, expect
from playwright.sync_api import TimeoutError
import time

from shopee_captcha_solver.playwright_util import wait_for_locator_to_be_stable

from .syncsolver import SyncSolver

from .selectors import (
    IMAGE_CRAWL_BUTTON_SELECTOR,
    IMAGE_CRAWL_PIECE_IMAGE_SELECTOR,
    IMAGE_CRAWL_PUZZLE_IMAGE_SELECTOR,
    CAPTCHA_PRESENCE_INDICATORS,
    PUZZLE_BUTTON_SELECTOR,
    PUZZLE_PIECE_IMAGE_SELECTOR,
    PUZZLE_PUZZLE_IMAGE_SELECTOR,
) 

from .geometry import (
    get_box_center,
    get_center,
    piece_is_not_moving,
    rotate_angle_from_style,
    xy_to_proportional_point
) 

from .models import (
    ImageCrawlCaptchaRequest,
    ArcedSlideTrajectoryElement,
    dump_to_json
) 

from .api import ApiClient


LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

class PlaywrightSolver(SyncSolver):

    client: ApiClient
    page: Page

    def __init__(
            self,
            page: Page,
            sadcaptcha_api_key: str,
            headers: dict[str, Any] | None = None, 
            proxy: str | None = None,
            dump_requests: bool = False,
            mouse_step_size: int = 3
        ) -> None:
        warnings.warn("!!!PlaywrightSolver is deprecated and no longer maintained!!! Instead, use 'make_playwright_solver_context()' which is imported from 'shopee_captcha_solver.launcher'. Please update your code for more reliability. For more details, please see the instructions on https://www.sadcaptcha.com/dashboard.")
        self.page = page
        self.client = ApiClient(sadcaptcha_api_key)
        self.headers = headers
        self.proxy = proxy
        self.mouse_step_size = mouse_step_size
        super().__init__(dump_requests)

    
    def captcha_is_present(self, timeout: int = 15) -> bool:
        try:
            captcha_locator = self.page.locator(CAPTCHA_PRESENCE_INDICATORS[0])
            for selector in CAPTCHA_PRESENCE_INDICATORS:
                captcha_locator = captcha_locator.or_(self.page.locator(selector))
            
            expect(captcha_locator.first).to_have_count(1, timeout=timeout * 1000)
            LOGGER.debug("captcha is present")
            return True
        except (TimeoutError, AssertionError):
            LOGGER.debug("captcha is not present")
            return False

    
    def captcha_is_not_present(self, timeout: int = 15) -> bool:
        try:
            captcha_locator = self.page.locator(CAPTCHA_PRESENCE_INDICATORS[0])
            for selector in CAPTCHA_PRESENCE_INDICATORS:
                captcha_locator = captcha_locator.or_(self.page.locator(selector))
            expect(captcha_locator.first).to_have_count(0, timeout=timeout * 1000)
            LOGGER.debug("captcha is not present")
            return True
        except (TimeoutError, AssertionError):
            LOGGER.debug("captcha is present")
            return False

    
    def solve_puzzle(self, retries: int = 3) -> None:
        """Simple slide puzzle. Slide puzzle piece to correct location."""
        button_bbox = self._get_element_bounding_box(PUZZLE_BUTTON_SELECTOR)
        start_x, start_y = get_box_center(button_bbox)
        self.page.mouse.move(start_x, start_y)
        self.page.mouse.down()
        start_distance = 10
        for pixel in range(start_distance):
            self.page.mouse.move(start_x + start_distance, start_y + math.log(1 + pixel))
            time.sleep(0.02)
        LOGGER.debug("dragged 10 pixels")
        puzzle_image = self.get_b64_img_from_src(PUZZLE_PUZZLE_IMAGE_SELECTOR)
        piece_image = self.get_b64_img_from_src(PUZZLE_PIECE_IMAGE_SELECTOR)
        resp = self.client.puzzle(puzzle_image, piece_image)
        slide_bar_width = self._get_puzzle_slide_bar_width()
        pixel_distance = int(resp.slide_x_proportion * slide_bar_width)
        LOGGER.debug(f"will continue to drag {pixel_distance} more pixels")
        for pixel in range(start_distance, pixel_distance):
            self.page.mouse.move(start_x + pixel, start_y + math.log(1 + pixel))
            time.sleep(0.01)
        time.sleep(0.5)
        self.page.mouse.up()
        LOGGER.debug("done")

    
    def solve_image_crawl(self) -> None:
        """Solves the image crawl puzzle. This challenge is similar to the puzzle
        challenge, but the puzzle piece travels in an arc, hence then name arced slide.
        The API expects the b64 encoded puzzle and piece images, along with data about the piece's
        trajectory in a list of ArcedSlideTrajectoryElements.

        This function will get the b64 encoded images, and will 'sweep' the slide
        bar to determine the piece's trajectory. Then it sends the data to the API
        and consumes the response.
        
        Determines slider trajectory by dragging the slider element across the entire box,
        and computing the ArcedSlideTrajectoryElement at each location."""
        slide_button_locator = self.page.locator(IMAGE_CRAWL_BUTTON_SELECTOR)
        self._move_mouse_to_element_center(slide_button_locator)
        self.page.mouse.down()
        slide_button_box = self._get_element_bounding_box(IMAGE_CRAWL_BUTTON_SELECTOR)
        start_x = slide_button_box["x"]
        start_y = slide_button_box["y"]
        request = self._gather_arced_slide_request_data(start_x, start_y)
        solution = self.client.image_crawl(request)
        self._drag_mouse_horizontal_with_overshoot(solution.pixels_from_slider_origin, start_x, start_y)
        self.page.mouse.up()

    
    def any_selector_in_list_present(self, selectors: list[str], iframe_selector: str | None = None) -> bool:
        for selector in selectors:
            e = self._get_locator(selector, iframe_selector=iframe_selector)
            for ele in e.all():
                if ele.is_visible():
                    LOGGER.debug("Detected selector: " + selector + " from list " + ", ".join(selectors))
                    return True
        LOGGER.debug("No selector in list found: " + ", ".join(selectors))
        return False

    
    def _gather_arced_slide_request_data(self, slide_button_center_x: float, slide_button_center_y: float) -> ImageCrawlCaptchaRequest:
        """Get the images and trajectory for image crawl request"""
        puzzle = self.get_b64_img_from_src(IMAGE_CRAWL_PUZZLE_IMAGE_SELECTOR)
        piece = self.get_b64_img_from_src(IMAGE_CRAWL_PIECE_IMAGE_SELECTOR)
        trajectory = self._get_slide_piece_trajectory(slide_button_center_x, slide_button_center_y)
        request = ImageCrawlCaptchaRequest(
            puzzle_image_b64=puzzle,
            piece_image_b64=piece,
            slide_piece_trajectory=trajectory
        )
        if self.dump_requests:
            dump_to_json(request, "shopee_image_crawler_request.json")
        return request


    def _get_slide_piece_trajectory(self, slide_button_center_x: float, slide_button_center_y: float) -> list[ArcedSlideTrajectoryElement]:
        """Sweep the button across the bar to determine the trajectory of the slide piece.
        Clicks and drags box, but does not release. Must pass the coordinates of the slide button."""
        slider_piece_locator = self.page.locator(IMAGE_CRAWL_PIECE_IMAGE_SELECTOR)
        slide_bar_width = self._get_arced_slide_bar_width()
        puzzle_img_bounding_box = self._get_element_bounding_box(IMAGE_CRAWL_PUZZLE_IMAGE_SELECTOR)
        trajectory: list[ArcedSlideTrajectoryElement] = []

        times_piece_did_not_move = 0
        for pixel in range(0, int(slide_bar_width), self.mouse_step_size):
            self.page.mouse.move(slide_button_center_x + pixel, slide_button_center_y - pixel)  # - pixel is to drag it diagonally
            wait_for_locator_to_be_stable(slider_piece_locator)
            trajectory_element = self._get_arced_slide_trajectory_element(
                pixel,
                puzzle_img_bounding_box,
                slider_piece_locator
            )
            trajectory.append(trajectory_element)
            if not len(trajectory) > 100 / self.mouse_step_size:
                continue
            if piece_is_not_moving(trajectory):
                times_piece_did_not_move += 1
            else:
                times_piece_did_not_move = 0
            if times_piece_did_not_move >= 10:
                break
        return trajectory

    def _get_puzzle_slide_bar_width(self) -> float:
        """Gets the width of the puzzle slide bar from the width of the image. 
        The slide bar is always the same as the image. 
        We do not get the width of the bar element itself, because the css selector varies from region to region."""
        bg_image_bounding_box = self._get_element_bounding_box(PUZZLE_PUZZLE_IMAGE_SELECTOR)
        slide_bar_width = bg_image_bounding_box["width"]
        return slide_bar_width

    def _get_arced_slide_bar_width(self) -> float:
        """Gets the width of the arced slide bar from the width of the image. 
        The slide bar is always the same as the image. 
        We do not get the width of the bar element itself, because the css selector varies from region to region."""
        bg_image_bounding_box = self._get_element_bounding_box(IMAGE_CRAWL_PUZZLE_IMAGE_SELECTOR)
        slide_bar_width = bg_image_bounding_box["width"]
        return slide_bar_width

    def _click_proportional(
            self,
            selector: str,
            proportion_x: float,
            proportion_y: float,
            iframe_selector: str | None = None
        ) -> None:
        """Click an element inside its bounding box at a point defined by the proportions of x and y
        to the width and height of the entire element

        Args:
            element: FloatRect to click inside
            proportion_x: float from 0 to 1 defining the proportion x location to click 
            proportion_y: float from 0 to 1 defining the proportion y location to click 
        """
        bounding_box = self._get_element_bounding_box(selector, iframe_selector=iframe_selector)
        x_offset = (proportion_x * bounding_box["width"])
        y_offset = (proportion_y * bounding_box["height"]) 
        self._get_locator(selector, iframe_selector=iframe_selector).click(position={"x": x_offset, "y": y_offset}, force=True)
        LOGGER.debug(f"clicked {selector} at offset {x_offset}, {y_offset}")

    def _drag_mouse_horizontal_with_overshoot(self, x_distance: int, start_x_coord: float, start_y_coord: float) -> None:
        self.page.mouse.move(start_x_coord + x_distance, start_y_coord, steps=100)
        overshoot = random.choice([1, 2, 3])
        self.page.mouse.move(start_x_coord + x_distance + overshoot, start_y_coord + overshoot, steps=100) # overshoot forward
        self.page.mouse.move(start_x_coord + x_distance, start_y_coord, steps=75) # overshoot back
        time.sleep(0.2)

    def _get_arced_slide_trajectory_element(
            self,
            current_slider_pixel: int,
            large_img_bounding_box: FloatRect,
            slider_piece_locator: Locator, 
        ) -> ArcedSlideTrajectoryElement:
        """Compute current slider trajectory element by extracting information on the 
        slide button location, the piece rotation, and the piece location"""
        slider_piece_bounding_box = slider_piece_locator.bounding_box()
        if not slider_piece_bounding_box:
            raise ValueError("Bouding box for slider image was None")
        slider_piece_style = slider_piece_locator.get_attribute("style")
        if not slider_piece_style:
            raise ValueError("Slider piece style was None")
        rotate_angle = rotate_angle_from_style(slider_piece_style)
        piece_top = slider_piece_bounding_box["y"]
        piece_left = slider_piece_bounding_box["x"]
        width = slider_piece_bounding_box["width"]
        height = slider_piece_bounding_box["height"]
        piece_center_x, piece_center_y = get_center(piece_left, piece_top, width, height)
        container_x = large_img_bounding_box["x"]
        container_y = large_img_bounding_box["y"]
        container_width = large_img_bounding_box["width"]
        container_height = large_img_bounding_box["height"]
        x_in_container = piece_center_x - container_x
        y_in_container = piece_center_y - container_y
        piece_center = xy_to_proportional_point(x_in_container, y_in_container, container_width, container_height)
        LOGGER.debug(f"top_corner={piece_left}, {piece_top}, center={piece_center_x}, {piece_center_y}, ctr_in_container={x_in_container}, {y_in_container}  prop_center={piece_center.proportion_x}, {piece_center.proportion_y}, container_size={container_width}, {container_height}")
        return ArcedSlideTrajectoryElement(
            pixels_from_slider_origin=current_slider_pixel,
            piece_rotation_angle=rotate_angle,
            piece_center=piece_center
        )

    def _get_locator(self, selector: str, iframe_selector: str | None = None) -> Locator:
        if iframe_selector:
            return self._get_locator_from_frame(selector, iframe_selector)
        else:
            return self.page.locator(selector)

    def _get_element_bounding_box(self, selector: str, iframe_selector: str | None = None) -> FloatRect:
        e = self._get_locator(selector, iframe_selector=iframe_selector)
        box = e.bounding_box()
        if box is None:
            raise ValueError("Bounding box for slide bar was none")
        return box

    def _move_mouse_to_element_center(self, ele: Locator, x_offset: float = 0, y_offset: int = 0) -> None:
        box = ele.bounding_box()
        if box is None:
            raise ValueError("Bounding box for element was none")
        x, y = get_center(box["x"], box["y"], box["width"], box["height"])
        self.page.mouse.move(x + x_offset, y + y_offset)

    
    def get_b64_img_from_src(self, selector: str, iframe_selector: str | None = None) -> str:
        """Get the source of b64 image element and return the portion after the data:image/png;base64,"""
        e = self._get_locator(selector, iframe_selector=iframe_selector)
        url = e.get_attribute("src")
        if not url:
            raise ValueError("element " + selector + " had no url")
        _, data = url.split(",")
        LOGGER.debug("got b64 image from data url")
        return data

    def _get_element_text(self, selector: str, iframe_selector: str | None = None) -> str:
        """Get the text of an element"""
        e = self._get_locator(selector, iframe_selector=iframe_selector)
        text_content = e.text_content()
        if not text_content:
            raise ValueError("element " + selector + " had no text content")
        LOGGER.debug(f"{selector} has text: {text_content}")
        return text_content

    def _get_locator_from_frame(self, selector: str, iframe_selector: str = "frame") -> Locator:
        return self.page.frame_locator(iframe_selector).locator(selector)

    def _compute_puzzle_slide_distance(self, proportion_x: float) -> int:
        e = self.page.locator("#captcha-verify-image")
        box = e.bounding_box()
        if box:
            return int(proportion_x * box["width"])
        raise AttributeError("#captcha-verify-image was found but had no bouding box")

    def _get_element_width(self, selector: str) -> float:
        e = self.page.locator(selector)
        box = e.bounding_box()
        if box:
            return int(box["width"])
        raise AttributeError(".captcha_verify_slide--slidebar was found but had no bouding box")

