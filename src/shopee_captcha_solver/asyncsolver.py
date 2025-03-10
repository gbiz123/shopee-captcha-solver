"""Abstract base class for Temu Captcha Async Solvers"""

import logging
import asyncio
from abc import ABC, abstractmethod


from shopee_captcha_solver.captchatype import CaptchaType
from shopee_captcha_solver.selectors import IMAGE_CRAWL_UNIQUE_IDENTIFIERS, PUZZLE_UNIQUE_IDENTIFIERS

LOGGER = logging.getLogger(__name__)

class AsyncSolver(ABC):

    def __init__(self, dump_requests: bool = False):
        self.dump_requests = dump_requests

    async def solve_captcha_if_present(self, captcha_detect_timeout: int = 15, retries: int = 3) -> None:
        """Solves any captcha that is present, if one is detected

        Args:
            captcha_detect_timeout: return if no captcha is detected in this many seconds
            retries: number of times to retry captcha
        """
        for _ in range(retries):
            if not await self.captcha_is_present(captcha_detect_timeout):
                LOGGER.debug("Captcha is not present")
                return
            else:
                match await self.identify_captcha():
                    case CaptchaType.IMAGE_CRAWL: 
                        await self.solve_image_crawl()
                    case CaptchaType.PUZZLE: 
                        await self.solve_puzzle()
                    case CaptchaType.SEMANTIC_SHAPES: 
                        await self.solve_semantic_shapes()
            if await self.captcha_is_not_present(timeout=5):
                return
            else:
                await asyncio.sleep(5)

    async def identify_captcha(self) -> CaptchaType:
        for _ in range(30):
            if await self.any_selector_in_list_present(PUZZLE_UNIQUE_IDENTIFIERS):
                LOGGER.debug("detected puzzle")
                return CaptchaType.PUZZLE
            elif await self.any_selector_in_list_present(IMAGE_CRAWL_UNIQUE_IDENTIFIERS):
                LOGGER.debug("detected arced slide")
                return CaptchaType.IMAGE_CRAWL
            else:
                await asyncio.sleep(1)
        raise ValueError("Neither puzzle, or arced slide was present")

    @abstractmethod
    async def captcha_is_present(self, timeout: int = 15) -> bool:
        pass

    @abstractmethod
    async def captcha_is_not_present(self, timeout: int = 15) -> bool:
        pass

    @abstractmethod
    async def solve_image_crawl(self) -> None:
        pass

    @abstractmethod
    async def solve_puzzle(self) -> None:
        pass

    @abstractmethod
    async def get_b64_img_from_src(self, selector: str) -> str:
        pass

    @abstractmethod
    async def any_selector_in_list_present(self, selectors: list[str]) -> bool:
        pass
