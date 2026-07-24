import numpy as np

from src.repositories.statusBar import core


def test_getFilledBarPercentage_returns_one_hundred_for_a_full_bar():
    bar = np.full(94, 79, dtype=np.uint8)

    assert core.getFilledBarPercentage(
        bar, allowedPixelsColors=np.array([79])) == 100


def test_getFilledBarPercentage_returns_fifty_for_a_half_bar():
    bar = np.concatenate(
        (
            np.full(47, 79, dtype=np.uint8),
            np.zeros(47, dtype=np.uint8),
        )
    )

    assert core.getFilledBarPercentage(
        bar, allowedPixelsColors=np.array([79])) == 50


def test_getFilledBarPercentage_returns_zero_for_an_empty_bar():
    bar = np.zeros(94, dtype=np.uint8)

    assert core.getFilledBarPercentage(
        bar, allowedPixelsColors=np.array([79])) == 0


def test_getHpPercentage_returns_none_when_hp_icon_is_not_found(monkeypatch):
    monkeypatch.setattr(core, "getHpIconPosition", lambda _: None)

    assert core.getHpPercentage(np.zeros((10, 10), dtype=np.uint8)) is None


def test_getManaPercentage_returns_none_when_mana_icon_is_not_found(monkeypatch):
    monkeypatch.setattr(core, "getManaIconPosition", lambda _: None)

    assert core.getManaPercentage(np.zeros((10, 10), dtype=np.uint8)) is None


def test_getHpPercentage_uses_the_original_allowed_colors(monkeypatch):
    bar = np.full(94, core.hpBarAllowedPixelsColors[0], dtype=np.uint8)
    monkeypatch.setattr(core, "getHpIconPosition", lambda _: (1, 2, 3, 4))
    monkeypatch.setattr(core, "getHpBar", lambda *_: bar)

    assert core.getHpPercentage(np.zeros((10, 10), dtype=np.uint8)) == 100


def test_getManaPercentage_uses_the_original_allowed_colors(monkeypatch):
    bar = np.full(94, core.manaBarAllowedPixelsColors[0], dtype=np.uint8)
    monkeypatch.setattr(core, "getManaIconPosition", lambda _: (1, 2, 3, 4))
    monkeypatch.setattr(core, "getManaBar", lambda *_: bar)

    assert core.getManaPercentage(np.zeros((10, 10), dtype=np.uint8)) == 100
