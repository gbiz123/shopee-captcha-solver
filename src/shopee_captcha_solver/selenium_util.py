
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait_for_element_to_be_stable(driver, element: WebElement) -> None:
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element))
