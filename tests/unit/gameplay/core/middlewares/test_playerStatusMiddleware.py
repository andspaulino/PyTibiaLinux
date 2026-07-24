import numpy as np

from src.gameplay.core.middlewares import playerStatus


def test_setMapPlayerStatusMiddleware_maps_absolute_and_percentage_values(monkeypatch):
    screenshot = np.zeros((10, 10), dtype=np.uint8)
    context = {
        "screenshot": screenshot,
        "statusBar": {
            "hp": None,
            "hpPercentage": None,
            "mana": None,
            "manaPercentage": None,
        },
    }
    monkeypatch.setattr(playerStatus, "getHp", lambda image: 260)
    monkeypatch.setattr(playerStatus, "getHpPercentage", lambda image: 100)
    monkeypatch.setattr(playerStatus, "getMana", lambda image: 73)
    monkeypatch.setattr(playerStatus, "getManaPercentage", lambda image: 63)

    result = playerStatus.setMapPlayerStatusMiddleware(context)

    assert result is context
    assert context["statusBar"] == {
        "hp": 260,
        "hpPercentage": 100,
        "mana": 73,
        "manaPercentage": 63,
    }
