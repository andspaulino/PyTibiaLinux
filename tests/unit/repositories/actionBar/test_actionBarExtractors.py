import numpy as np

from src.repositories.actionBar import extractors


def test_getCooldownsImage_returns_none_without_left_arrows(monkeypatch):
    monkeypatch.setattr(extractors.actionBarLocators, "getLeftArrowsPosition", lambda _: None)

    assert extractors.getCooldownsImage(np.zeros((10, 10), dtype=np.uint8)) is None


def test_getCooldownsImage_returns_none_without_right_arrows(monkeypatch):
    monkeypatch.setattr(
        extractors.actionBarLocators,
        "getLeftArrowsPosition",
        lambda _: (10, 20, 17, 34),
    )
    monkeypatch.setattr(extractors.actionBarLocators, "getRightArrowsPosition", lambda _: None)

    assert extractors.getCooldownsImage(np.zeros((100, 100), dtype=np.uint8)) is None


def test_getCooldownsImage_preserves_the_original_offsets(monkeypatch):
    screenshot = np.arange(100 * 200, dtype=np.uint32).reshape(100, 200)
    monkeypatch.setattr(
        extractors.actionBarLocators,
        "getLeftArrowsPosition",
        lambda _: (10, 20, 17, 34),
    )
    monkeypatch.setattr(
        extractors.actionBarLocators,
        "getRightArrowsPosition",
        lambda _: (180, 20, 17, 34),
    )

    result = extractors.getCooldownsImage(screenshot)

    np.testing.assert_array_equal(result, screenshot[57:79, 10:180])
