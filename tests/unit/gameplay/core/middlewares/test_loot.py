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
            "pendingHighlightSlots": [{"slot": (8, 5), "remainingBatches": 6}],
            "highlightedSlots": [],
            "ambientSlots": [],
            "highlightFailureReason": None,
            "lastHighlightSignature": None,
        },
        "radar": {"coordinate": [100, 100, 7]},
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
        lambda frames, *args, **kwargs: calls.append(frames) or accepted_classification(),
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
        lambda frames, *args, **kwargs: accepted_classification(),
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
        lambda frames, *args, **kwargs: {
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


def test_only_disappeared_target_blocks_walk_to_target():
    target = {"slot": (8, 5), "isBeingAttacked": True}
    otherMonster = {"slot": (6, 5), "isBeingAttacked": False}
    context = make_context()
    context["loot"]["pendingHighlightSlots"] = []
    context["cavebot"] = {"previousTargetCreature": target}
    context["gameWindow"].update({
        "previousMonsters": [target, otherMonster],
        "monsters": [otherMonster],
    })

    loot_middleware._updatePendingSlots(context, context["loot"])

    assert context["loot"]["quickLootDetectionPending"] is True
    assert context["loot"]["quickLootBlockingSlot"] == (8, 5)


def test_disappeared_non_target_does_not_block_walk_to_target():
    target = {"slot": (8, 5), "isBeingAttacked": True}
    otherMonster = {"slot": (6, 5), "isBeingAttacked": False}
    context = make_context()
    context["loot"]["pendingHighlightSlots"] = []
    context["cavebot"] = {"previousTargetCreature": target}
    context["gameWindow"].update({
        "previousMonsters": [target, otherMonster],
        "monsters": [target],
    })

    loot_middleware._updatePendingSlots(context, context["loot"])

    assert context["loot"].get("quickLootDetectionPending", False) is False
    assert context["loot"].get("quickLootBlockingSlot") is None


def test_pending_slots_only_accepts_nearby_slots():
    distantMonster = {"slot": (14, 9), "isBeingAttacked": False}
    nearbyMonster = {"slot": (8, 5), "isBeingAttacked": False}
    context = make_context()
    context["loot"]["pendingHighlightSlots"] = []
    context["gameWindow"].update({
        "previousMonsters": [distantMonster, nearbyMonster],
        "monsters": [],
    })

    loot_middleware._updatePendingSlots(context, context["loot"])

    pending_slots = [item["slot"] for item in context["loot"]["pendingHighlightSlots"]]
    assert (8, 5) in pending_slots
    assert (14, 9) not in pending_slots


def test_quick_loot_pending_cleared_when_blocking_slot_is_none_and_not_ready(monkeypatch):
    context = make_context()
    context["loot"].update({
        "quickLootDetectionPending": True,
        "quickLootBlockingSlot": None,
        "quickLootReady": False,
        "quickLootAwaitingConfirmation": False,
        "pendingHighlightSlots": [{"slot": (8, 5), "remainingBatches": 6}],
    })

    monkeypatch.setattr(
        loot_middleware,
        "classifyLootHighlightSlots",
        lambda frames, *args, **kwargs: {
            "accepted": True,
            "failureReason": None,
            "candidates": [],
            "ambient": [],
        },
    )

    for _ in range(12):
        loot_middleware.setLootHighlightingMiddleware(context)

    assert context["loot"]["quickLootDetectionPending"] is False
    assert context["loot"]["quickLootBlockingSlot"] is None


def test_quick_loot_resets_retry_count_on_exhaustion(monkeypatch):
    context = make_context()
    context["loot"].update({
        "enabled": True,
        "quickLootAwaitingConfirmation": True,
        "quickLootConfirmationBatches": 1,
        "quickLootRetryCount": 2,
        "quickLootMaxRetries": 2,
        "quickLootAttemptSlots": [(8, 5)],
        "pendingHighlightSlots": [{"slot": (8, 5), "remainingBatches": 6}],
    })

    monkeypatch.setattr(
        loot_middleware,
        "classifyLootHighlightSlots",
        lambda frames, *args, **kwargs: {
            "accepted": True,
            "failureReason": None,
            "candidates": [{"slot": (8, 5), "motionPixels": 1000, "method": "geometry"}],
            "ambient": [],
        },
    )

    for _ in range(12):
        loot_middleware.setLootHighlightingMiddleware(context)

    assert context["loot"]["quickLootAwaitingConfirmation"] is False
    assert context["loot"]["quickLootRetryCount"] == 0
    assert context["loot"]["quickLootReady"] is False
    assert context["loot"]["quickLootDetectionPending"] is False
    assert context["loot"]["quickLootAttemptSlots"] == []


def test_quick_loot_confirmation_checks_attempt_slots(monkeypatch):
    context = make_context()
    context["loot"].update({
        "enabled": True,
        "quickLootAwaitingConfirmation": True,
        "quickLootConfirmationBatches": 0,
        "quickLootRetryCount": 1,
        "quickLootMaxRetries": 2,
        "quickLootAttemptSlots": [(8, 5)],
        "pendingHighlightSlots": [{"slot": (8, 5), "remainingBatches": 6}],
    })

    monkeypatch.setattr(
        loot_middleware,
        "classifyLootHighlightSlots",
        lambda frames, *args, **kwargs: {
            "accepted": True,
            "failureReason": None,
            "candidates": [],
            "ambient": [],
        },
    )

    for _ in range(12):
        loot_middleware.setLootHighlightingMiddleware(context)

    assert context["loot"]["quickLootAwaitingConfirmation"] is False
    assert context["loot"]["quickLootRetryCount"] == 0
    assert context["loot"]["quickLootDetectionPending"] is False
    assert context["loot"]["pendingHighlightSlots"] == []


def test_slot_cooldown_prevents_retrigger(monkeypatch):
    import time
    context = make_context()
    now = time.time()
    context["loot"].update({
        "enabled": True,
        "slotCooldowns": {(8, 5): now + 10.0},
        "pendingHighlightSlots": [{"slot": (8, 5), "remainingBatches": 6}],
    })

    monkeypatch.setattr(
        loot_middleware,
        "classifyLootHighlightSlots",
        lambda frames, *args, **kwargs: {
            "accepted": True,
            "failureReason": None,
            "candidates": [{"slot": (8, 5), "motionPixels": 1000, "method": "geometry"}],
            "ambient": [],
        },
    )

    for _ in range(12):
        loot_middleware.setLootHighlightingMiddleware(context)

    assert context["loot"]["quickLootReady"] is False
    assert context["loot"]["highlightedSlots"] == []



