import numpy as np

from src.gameplay.core.middlewares import gameWindow as game_window_middleware
from src.gameplay.core.middlewares import loot as loot_middleware


FRAME = np.zeros((704, 960), dtype=np.uint8)


def make_context(*, monitor=True, image=FRAME):
    return {
        "loot": {
            "enabled": False,
            "monitorHighlighting": monitor,
            "highlightFrames": [],
            "highlightedSlots": [],
            "ambientSlots": [],
            "highlightFailureReason": None,
            "lastHighlightSignature": None,
        },
        "gameWindow": {"image": image},
    }


def accepted_classification():
    return {
        "accepted": True,
        "failureReason": None,
        "candidates": [
            {
                "slot": (8, 5),
                "motionPixels": 736,
                "method": "geometry",
            }
        ],
        "ambient": [{"slot": (13, 5), "motionPixels": 332}],
    }


def test_disabled_monitor_clears_passive_state():
    context = make_context(monitor=False)
    context["loot"]["highlightFrames"] = [FRAME]
    context["loot"]["highlightedSlots"] = [{"slot": (8, 5)}]

    result = loot_middleware.setLootHighlightingMiddleware(context)

    assert result["loot"]["highlightFrames"] == []
    assert result["loot"]["highlightedSlots"] == []
    assert result["loot"]["highlightFailureReason"] is None


def test_middleware_waits_for_twelve_frames_before_classifying(monkeypatch):
    context = make_context()
    calls = []
    monkeypatch.setattr(
        loot_middleware,
        "classifyLootHighlightSlots",
        lambda frames: calls.append(frames) or accepted_classification(),
    )

    for _ in range(11):
        loot_middleware.setLootHighlightingMiddleware(context)

    assert calls == []
    assert len(context["loot"]["highlightFrames"]) == 11

    loot_middleware.setLootHighlightingMiddleware(context)

    assert len(calls) == 1
    assert len(calls[0]) == 12
    assert context["loot"]["highlightFrames"] == []
    assert context["loot"]["highlightedSlots"][0]["slot"] == (8, 5)


def test_middleware_logs_only_when_candidate_slots_change(monkeypatch, capsys):
    context = make_context()
    monkeypatch.setattr(
        loot_middleware,
        "classifyLootHighlightSlots",
        lambda frames: accepted_classification(),
    )

    for _ in range(12):
        loot_middleware.setLootHighlightingMiddleware(context)
    firstOutput = capsys.readouterr().out
    for _ in range(12):
        loot_middleware.setLootHighlightingMiddleware(context)
    secondOutput = capsys.readouterr().out

    assert "(8, 5), 736, 'geometry'" in firstOutput
    assert secondOutput == ""


def test_global_motion_rejection_is_exposed_in_context(monkeypatch):
    context = make_context()
    monkeypatch.setattr(
        loot_middleware,
        "classifyLootHighlightSlots",
        lambda frames: {
            "accepted": False,
            "failureReason": "global-motion",
            "candidates": [],
            "ambient": [],
        },
    )

    for _ in range(12):
        loot_middleware.setLootHighlightingMiddleware(context)

    assert context["loot"]["highlightedSlots"] == []
    assert context["loot"]["highlightFailureReason"] == "global-motion"


def test_missing_game_window_resets_buffer_and_exposes_reason():
    context = make_context(image=None)
    context["loot"]["highlightFrames"] = [FRAME]

    loot_middleware.setLootHighlightingMiddleware(context)

    assert context["loot"]["highlightFrames"] == []
    assert context["loot"]["highlightFailureReason"] == "game-window-unavailable"


def test_disabled_legacy_loot_preserves_shared_target_tracking(monkeypatch):
    monster = {"name": "Muglex Clan Footman"}
    context = {
        "loot": {"enabled": False},
        "cavebot": {
            "targetCreature": None,
            "previousTargetCreature": None,
        },
        "gameWindow": {"monsters": [monster]},
    }
    monkeypatch.setattr(
        game_window_middleware,
        "getTargetCreature",
        lambda monsters: monsters[0],
    )

    result = game_window_middleware.setHandleLootMiddleware(context)

    assert result["cavebot"]["targetCreature"] == monster
    assert result["cavebot"]["previousTargetCreature"] == monster
