import numpy as np

from src.repositories.actionBar import core
from src.utils.image import loadFromRGBToGray


LEFT_ARROWS_POSITION = (0, 0, 17, 34)


def slotX(slot):
    return 17 + (slot * 2) + ((slot - 1) * 34)


def test_slotIsAvailable_returns_none_when_action_bar_is_not_found(monkeypatch):
    monkeypatch.setattr(core.actionBarLocators, "getLeftArrowsPosition", lambda _: None)

    assert core.slotIsAvailable(np.zeros((40, 100), dtype=np.uint8), 1) is None


def test_slotIsAvailable_detects_available_and_unavailable_slots(monkeypatch):
    screenshot = np.zeros((40, 100), dtype=np.uint8)
    monkeypatch.setattr(
        core.actionBarLocators,
        "getLeftArrowsPosition",
        lambda _: LEFT_ARROWS_POSITION,
    )

    assert core.slotIsAvailable(screenshot, 1) is True

    x = slotX(1)
    screenshot[1, x + 2:x + 12:2] = 54
    assert core.slotIsAvailable(screenshot, 1) is False


def test_slotIsAvailable_uses_the_expected_geometry_for_slot_two(monkeypatch):
    screenshot = np.zeros((40, 120), dtype=np.uint8)
    monkeypatch.setattr(
        core.actionBarLocators,
        "getLeftArrowsPosition",
        lambda _: LEFT_ARROWS_POSITION,
    )
    x = slotX(2)
    screenshot[1, x + 2:x + 12:2] = 54

    assert core.slotIsAvailable(screenshot, 1) is True
    assert core.slotIsAvailable(screenshot, 2) is False


def test_slotIsEquipped_preserves_the_original_pixel_check(monkeypatch):
    screenshot = np.zeros((40, 100), dtype=np.uint8)
    monkeypatch.setattr(
        core.actionBarLocators,
        "getLeftArrowsPosition",
        lambda _: LEFT_ARROWS_POSITION,
    )
    x = slotX(1)

    assert core.slotIsEquipped(screenshot, 1) == False
    screenshot[0, x] = 41
    assert core.slotIsEquipped(screenshot, 1) == True


def test_getSlotCount_reads_normalized_digit_cells(monkeypatch):
    screenshot = np.zeros((40, 100), dtype=np.uint8)
    monkeypatch.setattr(
        core.actionBarLocators,
        "getLeftArrowsPosition",
        lambda _: LEFT_ARROWS_POSITION,
    )
    x = slotX(1)
    for power, digit in enumerate((5, 4, 3)):
        right = x + 32 - (power * 6)
        digitImage = loadFromRGBToGray(
            f"src/repositories/actionBar/images/digits/{digit}.png"
        )
        screenshot[25:31, right - 6:right] = digitImage

    assert core.getSlotCount(screenshot, 1) == 345


def test_getSlotCount_normalizes_grayscale_before_hashing(monkeypatch):
    screenshot = np.zeros((40, 100), dtype=np.uint8)
    monkeypatch.setattr(
        core.actionBarLocators,
        "getLeftArrowsPosition",
        lambda _: LEFT_ARROWS_POSITION,
    )
    x = slotX(1)
    digitImage = loadFromRGBToGray(
        "src/repositories/actionBar/images/digits/8.png"
    )
    grayscaleDigit = np.where(digitImage == 255, 200, 100).astype(np.uint8)
    screenshot[25:31, x + 26:x + 32] = grayscaleDigit

    assert core.getSlotCount(screenshot, 1) == 8
