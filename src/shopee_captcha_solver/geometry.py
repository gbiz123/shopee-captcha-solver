import re

from playwright.async_api import FloatRect

from shopee_captcha_solver.models import ArcedSlideTrajectoryElement, ProportionalPoint

def rotate_angle_from_style(style: str) -> float:
    """Extract the rotate value from the css style attribute"""
    if not "rotate" in style:
        return 0
    rotate_string = re.sub(r".*rotate\(|deg.*", "", style)
    return float(rotate_string)


def xy_to_proportional_point(
        x_in_container: float,
        y_in_container: float,
        container_width: float,
        container_height: float,
    ) -> ProportionalPoint:
    """Convert an x, y pair into a propotional point where the 
    resulting x and y proportions are the fraction of the width
    and height respectively.
    """
    return ProportionalPoint(
        proportion_x = x_in_container / container_width,
        proportion_y = y_in_container / container_height,
    )

def get_box_center(box: FloatRect) -> tuple[float, float]:
    """Get the center of a box from a FloatRect"""
    center_x = box["x"] + (box["width"] / 2)
    center_y = box["y"] + (box["height"] / 2)
    return center_x, center_y


def get_center(left_x: float, top_y: float, width: float, height: float) -> tuple[float, float]:
    """Get the center of a box from the left, top, width, and height measurements"""
    center_x = left_x + (width / 2)
    center_y = top_y + (height / 2)
    return center_x, center_y


def piece_is_not_moving(trajectory: list[ArcedSlideTrajectoryElement]) -> bool:
    """Return True if the last two trajectory elements have the same proportion_x, 
    indicating that the piece is not moving"""
    if trajectory[-2].piece_center.proportion_x == trajectory[-1].piece_center.proportion_x:
        return True
    else:
        return False


def interpolate_trajectory(trajectory: list[ArcedSlideTrajectoryElement], element_spacing: int) -> list[ArcedSlideTrajectoryElement]:
    """Perform linear interpolation between each element so that there
    is an element at each pixel distance from origin"""
    new_trajectory = []



