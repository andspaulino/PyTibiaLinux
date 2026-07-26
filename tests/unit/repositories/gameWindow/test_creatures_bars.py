import numpy as np

from src.repositories.gameWindow.creatures import (
    CREATURE_BAR_HEIGHT,
    CREATURE_BAR_WIDTH,
    getCreaturesBars,
)


def draw_bar(image, x, y, *, filled_width=None, color=113):
    image[y:y + CREATURE_BAR_HEIGHT, x:x + CREATURE_BAR_WIDTH] = 0
    inner_width = CREATURE_BAR_WIDTH - 2
    if filled_width is None:
        filled_width = inner_width
    image[y + 1:y + 3, x + 1:x + 1 + filled_width] = color
    return image


def test_get_creatures_bars_finds_full_31_by_4_bar():
    image = np.full((100, 120), 255, dtype=np.uint8)
    draw_bar(image, 20, 30)

    assert getCreaturesBars(image) == [(20, 30)]


def test_get_creatures_bars_finds_partially_filled_bar():
    image = np.full((100, 120), 255, dtype=np.uint8)
    draw_bar(image, 20, 30, filled_width=12)

    assert getCreaturesBars(image) == [(20, 30)]


def test_get_creatures_bars_finds_multiple_bars():
    image = np.full((160, 220), 255, dtype=np.uint8)
    draw_bar(image, 20, 30)
    draw_bar(image, 90, 80, filled_width=8)

    assert getCreaturesBars(image) == [(20, 30), (90, 80)]


def test_get_creatures_bars_returns_empty_without_bars():
    image = np.full((100, 120), 255, dtype=np.uint8)

    assert getCreaturesBars(image) == []


def test_get_creatures_bars_rejects_invalid_right_border():
    image = np.full((100, 120), 255, dtype=np.uint8)
    draw_bar(image, 20, 30)
    image[31:33, 50] = 113

    assert getCreaturesBars(image) == []


def test_get_creatures_bars_does_not_match_old_27_pixel_geometry():
    image = np.full((100, 120), 255, dtype=np.uint8)
    image[30:34, 20:47] = 0
    image[31:33, 21:46] = 113

    assert getCreaturesBars(image) == []
