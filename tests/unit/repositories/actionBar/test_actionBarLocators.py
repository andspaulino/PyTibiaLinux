import numpy as np

from src.repositories.actionBar.config import images
from src.repositories.actionBar.locators import (
    getLeftArrowsPosition,
    getRightArrowsPosition,
)


def screenshotWithTemplate(template, x, y):
    height, width = template.shape
    screenshot = np.zeros((height + y + 10, width + x + 10), dtype=np.uint8)
    screenshot[y:y + height, x:x + width] = template
    return screenshot


def test_getLeftArrowsPosition_finds_the_left_template():
    template = images["arrows"]["left"]

    assert getLeftArrowsPosition(screenshotWithTemplate(template, 7, 13)) == (
        7,
        13,
        template.shape[1],
        template.shape[0],
    )


def test_getRightArrowsPosition_finds_the_right_template():
    template = images["arrows"]["right"]

    assert getRightArrowsPosition(screenshotWithTemplate(template, 19, 11)) == (
        19,
        11,
        template.shape[1],
        template.shape[0],
    )
