import numpy as np

from src.gameplay.core.middlewares import gameWindow as game_window_middleware


def make_context(*, targeting=True, cavebot=False, walk_to_target=False):
    return {
        "targeting": {
            "enabled": targeting,
            "walkToTarget": walk_to_target,
        },
        "cavebot": {"enabled": cavebot},
        "battleList": {
            "creatures": [{"name": "Bug"}],
            "beingAttackedCreatureCategory": None,
        },
        "gameWindow": {
            "coordinate": (100, 100),
            "image": np.zeros((704, 960), dtype=np.uint8),
            "creatures": [],
            "monsters": [],
            "players": [],
            "walkedPixelsInSqm": 0,
        },
        "radar": {"coordinate": None},
        "comingFromDirection": None,
    }


def test_visual_targeting_fallback_is_restricted_to_stationary_targeting():
    assert game_window_middleware.canUseVisualTargetingWithoutRadar(
        make_context()
    )
    assert not game_window_middleware.canUseVisualTargetingWithoutRadar(
        make_context(cavebot=True)
    )
    assert not game_window_middleware.canUseVisualTargetingWithoutRadar(
        make_context(walk_to_target=True)
    )
    assert not game_window_middleware.canUseVisualTargetingWithoutRadar(
        make_context(targeting=False)
    )


def test_game_window_maps_monsters_without_radar_in_visual_mode(monkeypatch):
    context = make_context()
    captured = {}
    monster = {"name": "Bug", "type": "monster"}

    monkeypatch.setattr(
        game_window_middleware,
        "getBeingAttackedCreatureCategory",
        lambda creatures: None,
    )

    def fake_get_creatures(
        battle_list_creatures,
        direction,
        game_window_coordinate,
        game_window_image,
        coordinate,
        **kwargs,
    ):
        captured["coordinate"] = coordinate
        return [monster]

    monkeypatch.setattr(
        game_window_middleware,
        "getCreatures",
        fake_get_creatures,
    )

    result = game_window_middleware.setGameWindowCreaturesMiddleware(context)

    assert captured["coordinate"] == (
        game_window_middleware.VISUAL_TARGETING_FALLBACK_COORDINATE
    )
    assert result["gameWindow"]["monsters"] == [monster]


def test_game_window_still_requires_radar_when_walking(monkeypatch):
    context = make_context(walk_to_target=True)
    called = False

    def fake_get_creatures(*args, **kwargs):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(
        game_window_middleware,
        "getCreatures",
        fake_get_creatures,
    )

    result = game_window_middleware.setGameWindowCreaturesMiddleware(context)

    assert not called
    assert result["gameWindow"]["monsters"] == []
