import numpy as np

from src.repositories.skills.config import images
from src.repositories.skills.locators import getSkillsIconPosition


def test_getSkillsIconPosition_finds_the_skills_template():
    template = images["icons"]["skills"]
    height, width = template.shape
    screenshot = np.zeros((height + 40, width + 50), dtype=np.uint8)
    screenshot[13:13 + height, 17:17 + width] = template

    assert getSkillsIconPosition(screenshot) == (
        17,
        13,
        width,
        height,
    )
