import numpy as np

from src.repositories.statusBar.config import images
from src.repositories.statusBar.locators import (
    getHpIconPosition,
    getManaIconPosition,
)


def screenshotWithTemplate(template, x, y):
    height, width = template.shape
    screenshot = np.zeros((height + y + 10, width + x + 10), dtype=np.uint8)
    screenshot[y:y + height, x:x + width] = template
    return screenshot


def test_getHpIconPosition_finds_the_hp_template():
    template = images["icons"]["hp"]
    screenshot = screenshotWithTemplate(template, 17, 13)

    assert getHpIconPosition(screenshot) == (
        17,
        13,
        template.shape[1],
        template.shape[0],
    )


def test_getManaIconPosition_finds_the_mana_template():
    template = images["icons"]["mana"]
    screenshot = screenshotWithTemplate(template, 19, 11)

    assert getManaIconPosition(screenshot) == (
        19,
        11,
        template.shape[1],
        template.shape[0],
    )
