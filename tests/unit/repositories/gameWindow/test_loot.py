from pathlib import Path

import numpy as np
import pytest

from src.repositories.gameWindow.loot import (
    classifyLootHighlightSlots,
    getLootHighlightMotionMask,
)


FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "lootHighlighting"
GAME_WINDOW_HEIGHT = 704
GAME_WINDOW_WIDTH = 960
SLOT_SIZE = 64


def load_fixture(name):
    with np.load(FIXTURES / f"{name}.npz") as fixture:
        return {
            "before": fixture["before"],
            "after": fixture["after"],
            "slots": fixture["slots"],
        }


def compose_frames(slot_sequences, slots):
    frame_count = slot_sequences.shape[1]
    frames = np.zeros(
        (frame_count, GAME_WINDOW_HEIGHT, GAME_WINDOW_WIDTH),
        dtype=np.uint8,
    )
    for sequence, (column, row) in zip(slot_sequences, slots):
        x0 = int(column) * SLOT_SIZE
        y0 = int(row) * SLOT_SIZE
        frames[:, y0:y0 + SLOT_SIZE, x0:x0 + SLOT_SIZE] = sequence
    return frames


def candidate_slots(result):
    return {item["slot"] for item in result["candidates"]}


def ambient_slots(result):
    return {item["slot"] for item in result["ambient"]}


def test_multiple_species_are_detected_before_and_cleared_after_loot():
    fixture = load_fixture("multiple_looted")
    before = classifyLootHighlightSlots(
        compose_frames(fixture["before"], fixture["slots"])
    )
    after = classifyLootHighlightSlots(
        compose_frames(fixture["after"], fixture["slots"])
    )

    assert before["accepted"] is True
    assert candidate_slots(before) == {(7, 4), (6, 5), (9, 6)}
    assert all(
        item["temporalSignatureAvailable"] is True
        and item["temporalSignatureAccepted"] is True
        and item["meanMotionRange"] >= 75
        and item["adjacentMotionMedian"] <= 96
        for item in before["candidates"]
    )
    assert (14, 6) in ambient_slots(before)
    assert candidate_slots(after) == set()


def test_control_without_loot_keeps_all_four_corpse_slots_active():
    fixture = load_fixture("control_without_loot")
    before = classifyLootHighlightSlots(
        compose_frames(fixture["before"], fixture["slots"])
    )
    after = classifyLootHighlightSlots(
        compose_frames(fixture["after"], fixture["slots"])
    )
    expected = {(7, 6), (6, 6), (6, 5), (5, 7)}

    assert candidate_slots(before) == expected
    assert candidate_slots(after) == expected
    assert (0, 6) in ambient_slots(before)
    assert (0, 6) in ambient_slots(after)


def test_dp_carlin_environmental_animations_do_not_become_loot_candidates():
    fixture = load_fixture("dp_carlin_ambient")
    expectedSlots = {tuple(slot) for slot in fixture["slots"]}

    for phase in ("before", "after"):
        result = classifyLootHighlightSlots(
            compose_frames(fixture[phase], fixture["slots"])
        )

        assert candidate_slots(result) == set()
        assert expectedSlots <= ambient_slots(result)
        highMotionAmbient = [
            item
            for item in result["ambient"]
            if item["slot"] in expectedSlots
            and item["motionPixels"] >= 800
        ]
        assert len(highMotionAmbient) > 0
        assert all(
            item["temporalSignatureAccepted"] is False
            and item["rejectionReason"] == "temporal-signature"
            for item in highMotionAmbient
        )


def test_environmental_torches_do_not_become_loot_candidates():
    fixture = load_fixture("control_without_corpses")
    before = classifyLootHighlightSlots(
        compose_frames(fixture["before"], fixture["slots"])
    )
    after = classifyLootHighlightSlots(
        compose_frames(fixture["after"], fixture["slots"])
    )

    assert candidate_slots(before) == set()
    assert candidate_slots(after) == set()
    assert ambient_slots(before) == {(7, 3), (13, 7)}


def test_stacked_corpses_produce_one_candidate_per_sqm():
    fixture = load_fixture("stacked_looted")
    before = classifyLootHighlightSlots(
        compose_frames(fixture["before"], fixture["slots"])
    )
    after = classifyLootHighlightSlots(
        compose_frames(fixture["after"], fixture["slots"])
    )

    assert candidate_slots(before) == {(7, 6), (8, 6)}
    assert (11, 3) in ambient_slots(before)
    assert candidate_slots(after) == set()


def test_geometry_recovers_large_connected_highlight_below_absolute_threshold():
    frames = np.zeros((2, GAME_WINDOW_HEIGHT, GAME_WINDOW_WIDTH), dtype=np.uint8)
    x0 = 8 * SLOT_SIZE + 7
    y0 = 5 * SLOT_SIZE + 7
    frames[1, y0:y0 + 50, x0:x0 + 50] = 255
    frames[1, y0 + 4:y0 + 46, x0 + 4:x0 + 46] = 0

    result = classifyLootHighlightSlots(frames)

    assert candidate_slots(result) == {(8, 5)}
    candidate = result["candidates"][0]
    assert candidate["motionPixels"] == 736
    assert candidate["method"] == "geometry"
    assert candidate["motionWidth"] == 50
    assert candidate["motionHeight"] == 50
    assert candidate["largestComponent"] == 736


def test_global_motion_rejects_sequence():
    frames = np.zeros((2, GAME_WINDOW_HEIGHT, GAME_WINDOW_WIDTH), dtype=np.uint8)
    frames[1, :300, :] = 255

    result = classifyLootHighlightSlots(frames)

    assert result["accepted"] is False
    assert result["failureReason"] == "global-motion"
    assert result["candidates"] == []


@pytest.mark.parametrize(
    "frames",
    (
        np.zeros((704, 960), dtype=np.uint8),
        np.zeros((1, 704, 960), dtype=np.uint8),
        np.zeros((2, 0, 960), dtype=np.uint8),
    ),
)
def test_motion_mask_rejects_invalid_sequences(frames):
    with pytest.raises(ValueError):
        getLootHighlightMotionMask(frames)
