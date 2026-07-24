import numpy as np

from src.repositories.skills import core
from src.repositories.skills.config import images, numbersHashes


def renderThreeDigits(number):
    numberAsString = f"{number:03d}"
    result = np.zeros((8, 22), dtype=np.uint8)
    result[:, 16:22] = images["digits"][int(numberAsString[2])]
    if number >= 10:
        result[:, 8:14] = images["digits"][int(numberAsString[1])]
    if number >= 100:
        result[:, 0:6] = images["digits"][int(numberAsString[0])]
    return result


def placeValue(screenshot, position, value):
    x, y, _, _ = position
    thousands, remainder = divmod(value, 1000)
    screenshot[y:y + 8, x + 122:x + 144] = renderThreeDigits(remainder)
    if thousands > 0:
        screenshot[y:y + 8, x + 94:x + 116] = renderThreeDigits(thousands)


def test_numbersHashes_contains_all_three_digit_values():
    assert set(numbersHashes.values()) == set(range(1000))


def test_getValuesCount_reads_a_value_below_one_thousand():
    screenshot = np.zeros((20, 160), dtype=np.uint8)
    position = (0, 0, 1, 1)
    placeValue(screenshot, position, 260)

    assert core.getValuesCount(screenshot, position) == 260


def test_getValuesCount_reads_a_value_above_one_thousand():
    screenshot = np.zeros((20, 160), dtype=np.uint8)
    position = (0, 0, 1, 1)
    placeValue(screenshot, position, 1260)

    assert core.getValuesCount(screenshot, position) == 1260


def test_getHp_returns_none_when_skills_icon_is_not_found(monkeypatch):
    monkeypatch.setattr(core, "getSkillsIconPosition", lambda _: None)

    assert core.getHp(np.zeros((10, 10), dtype=np.uint8)) is None


def test_getMana_returns_none_when_skills_icon_is_not_found(monkeypatch):
    monkeypatch.setattr(core, "getSkillsIconPosition", lambda _: None)

    assert core.getMana(np.zeros((10, 10), dtype=np.uint8)) is None


def test_getHp_reads_the_region_at_the_original_offset(monkeypatch):
    screenshot = np.zeros((220, 220), dtype=np.uint8)
    skillsPosition = (10, 20, 11, 11)
    hpPosition = (skillsPosition[0] + 5, skillsPosition[1] + 89, 11, 11)
    placeValue(screenshot, hpPosition, 260)
    monkeypatch.setattr(core, "getSkillsIconPosition", lambda _: skillsPosition)

    assert core.getHp(screenshot) == 260


def test_getMana_reads_the_region_at_the_original_offset(monkeypatch):
    screenshot = np.zeros((220, 220), dtype=np.uint8)
    skillsPosition = (10, 20, 11, 11)
    manaPosition = (skillsPosition[0] + 5, skillsPosition[1] + 103, 11, 11)
    placeValue(screenshot, manaPosition, 115)
    monkeypatch.setattr(core, "getSkillsIconPosition", lambda _: skillsPosition)

    assert core.getMana(screenshot) == 115
