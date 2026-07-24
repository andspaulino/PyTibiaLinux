import numpy as np

from src.repositories.statusBar.config import barSize
from src.repositories.statusBar.extractors import getHpBar, getManaBar


def test_getHpBar_extracts_original_offset_and_size():
    screenshot = np.arange(30 * 150, dtype=np.uint16).reshape(30, 150)
    iconPosition = (10, 7, 11, 11)

    result = getHpBar(screenshot, iconPosition)

    np.testing.assert_array_equal(
        result,
        screenshot[12, 23:23 + barSize],
    )
    assert result.shape == (94,)


def test_getManaBar_extracts_original_offset_and_size():
    screenshot = np.arange(30 * 150, dtype=np.uint16).reshape(30, 150)
    iconPosition = (10, 7, 11, 11)

    result = getManaBar(screenshot, iconPosition)

    np.testing.assert_array_equal(
        result,
        screenshot[12, 24:24 + barSize],
    )
    assert result.shape == (94,)
