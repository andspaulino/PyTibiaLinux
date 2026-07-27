import numpy as np

from src.repositories.gameWindow import creatures as game_window_creatures


def make_crop(template, tone):
    return np.where(template == 255, tone, 0).astype(np.uint8)


def test_deterministic_name_accepts_repeated_single_species_with_equal_counts():
    name = game_window_creatures.getDeterministicCreatureName(
        [
            {"name": "Corrupted Ghost"},
            {"name": "Corrupted Ghost"},
        ],
        [(100, 100), (200, 200)],
    )

    assert name == "Corrupted Ghost"


def test_deterministic_name_rejects_unknown_different_species_or_count():
    assert game_window_creatures.getDeterministicCreatureName(
        [{"name": "Corrupted Ghost"}, {"name": "Unknown"}],
        [(100, 100), (200, 200)],
    ) is None
    assert game_window_creatures.getDeterministicCreatureName(
        [{"name": "Corrupted Ghost"}, {"name": "Corrupted Skeleton"}],
        [(100, 100), (200, 200)],
    ) is None
    assert game_window_creatures.getDeterministicCreatureName(
        [{"name": "Corrupted Ghost"}, {"name": "Corrupted Ghost"}],
        [(100, 100)],
    ) is None


def test_multitone_match_accepts_original_health_bar_tones():
    template = np.array([
        [0, 255, 0, 255],
        [255, 255, 0, 0],
        [0, 255, 255, 0],
    ], dtype=np.uint8)

    for tone in game_window_creatures.CREATURE_NAME_TONES:
        confidence = game_window_creatures.getCreatureNameMatchConfidence(
            make_crop(template, tone),
            template,
        )
        assert confidence > 0.99


def test_discriminative_mask_separates_similar_templates(monkeypatch):
    footman = np.zeros((11, 20), dtype=np.uint8)
    assassin = np.zeros((11, 20), dtype=np.uint8)
    footman[2:9, 2:8] = 255
    assassin[2:9, 2:6] = 255
    assassin[2:9, 12:18] = 255
    monkeypatch.setattr(
        game_window_creatures,
        "creaturesNamesHashes",
        {
            "Muglex Clan Footman": footman,
            "Muglex Clan Assassin": assassin,
        },
    )

    masks = game_window_creatures.getCreatureNameDiscriminativeMasks(
        ["Muglex Clan Footman", "Muglex Clan Assassin"]
    )
    crop = make_crop(footman, 57)
    footman_score = game_window_creatures.getCreatureNameMatchConfidence(
        crop,
        footman,
        masks["Muglex Clan Footman"],
    )
    assassin_score = game_window_creatures.getCreatureNameMatchConfidence(
        crop,
        assassin,
        masks["Muglex Clan Assassin"],
    )

    assert footman_score > assassin_score
    assert footman_score - assassin_score >= game_window_creatures.CREATURE_NAME_MIN_MARGIN


def test_classifier_uses_battle_list_candidates_and_local_alignment(monkeypatch):
    footman = np.zeros((11, 20), dtype=np.uint8)
    assassin = np.zeros((11, 20), dtype=np.uint8)
    footman[2:9, 2:8] = 255
    assassin[2:9, 2:6] = 255
    assassin[2:9, 12:18] = 255
    monkeypatch.setattr(
        game_window_creatures,
        "creaturesNamesHashes",
        {
            "Muglex Clan Footman": footman,
            "Muglex Clan Assassin": assassin,
        },
    )

    game_window = np.zeros((80, 160), dtype=np.uint8)
    bar = (70, 40)
    x0, x1, y0, y1 = game_window_creatures.getCreatureNamePosition(
        bar,
        footman,
        game_window.shape[1],
    )
    game_window[y0:y1, x0:x1] = make_crop(footman, 57)

    name, confidence, second_confidence, position = (
        game_window_creatures.classifyCreatureName(
            game_window,
            bar,
            ["Muglex Clan Footman", "Muglex Clan Assassin", "Unknown"],
        )
    )

    assert name == "Muglex Clan Footman"
    assert confidence >= game_window_creatures.CREATURE_NAME_MIN_CONFIDENCE
    assert confidence - second_confidence >= game_window_creatures.CREATURE_NAME_MIN_MARGIN
    assert position == (x0, y0)


def test_boolean_ratio_fallback_accepts_clear_winner(monkeypatch):
    ghost = np.zeros((11, 20), dtype=np.uint8)
    skeleton = np.zeros((11, 24), dtype=np.uint8)
    ghost[:, 2:8] = 255
    skeleton[:, 12:20] = 255
    monkeypatch.setattr(
        game_window_creatures,
        "creaturesNamesHashes",
        {"Corrupted Ghost": ghost, "Corrupted Skeleton": skeleton},
    )
    monkeypatch.setattr(
        game_window_creatures,
        "getCreatureNameMatchConfidence",
        lambda crop, template, discriminativeMask=None: 0.30,
    )
    monkeypatch.setattr(
        game_window_creatures,
        "getCreatureNameBooleanViolationRatio",
        lambda crop, template, tolerance: 0.002 if template.shape[1] == 20 else 0.02,
    )

    name, confidence, second_confidence, _ = (
        game_window_creatures.classifyCreatureName(
            np.zeros((80, 160), dtype=np.uint8),
            (70, 40),
            ["Corrupted Ghost", "Corrupted Skeleton"],
        )
    )

    assert name == "Corrupted Ghost"
    assert confidence < game_window_creatures.CREATURE_NAME_MIN_CONFIDENCE
    assert second_confidence == confidence


def test_boolean_ratio_fallback_rejects_ambiguous_candidates(monkeypatch):
    first = np.zeros((11, 20), dtype=np.uint8)
    second = np.zeros((11, 24), dtype=np.uint8)
    monkeypatch.setattr(
        game_window_creatures,
        "creaturesNamesHashes",
        {"First": first, "Second": second},
    )
    monkeypatch.setattr(
        game_window_creatures,
        "getCreatureNameMatchConfidence",
        lambda crop, template, discriminativeMask=None: 0.30,
    )
    monkeypatch.setattr(
        game_window_creatures,
        "getCreatureNameBooleanViolationRatio",
        lambda crop, template, tolerance: 0.0,
    )

    name, _, _, _ = game_window_creatures.classifyCreatureName(
        np.zeros((80, 160), dtype=np.uint8),
        (70, 40),
        ["First", "Second"],
    )

    assert name is None


def test_boolean_ratio_fallback_rejects_approximate_single_candidate(monkeypatch):
    template = np.zeros((11, 20), dtype=np.uint8)
    monkeypatch.setattr(
        game_window_creatures,
        "creaturesNamesHashes",
        {"Only": template},
    )
    monkeypatch.setattr(
        game_window_creatures,
        "getCreatureNameMatchConfidence",
        lambda crop, template, discriminativeMask=None: 0.30,
    )
    monkeypatch.setattr(
        game_window_creatures,
        "getCreatureNameBooleanViolationRatio",
        lambda crop, template, tolerance: 0.001,
    )

    name, _, _, _ = game_window_creatures.classifyCreatureName(
        np.zeros((80, 160), dtype=np.uint8),
        (70, 40),
        ["Only"],
    )

    assert name is None


def test_boolean_exact_match_accepts_single_candidate(monkeypatch):
    template = np.zeros((11, 20), dtype=np.uint8)
    monkeypatch.setattr(
        game_window_creatures,
        "creaturesNamesHashes",
        {"Only": template},
    )
    monkeypatch.setattr(
        game_window_creatures,
        "getCreatureNameMatchConfidence",
        lambda crop, template, discriminativeMask=None: 0.30,
    )

    def exact_only_without_tolerance(crop, template, tolerance):
        return 0.0 if tolerance == 0 else 0.001

    monkeypatch.setattr(
        game_window_creatures,
        "getCreatureNameBooleanViolationRatio",
        exact_only_without_tolerance,
    )

    name, confidence, second_confidence, _ = (
        game_window_creatures.classifyCreatureName(
            np.zeros((80, 160), dtype=np.uint8),
            (70, 40),
            ["Only"],
        )
    )

    assert name == "Only"
    assert confidence < game_window_creatures.CREATURE_NAME_MIN_CONFIDENCE
    assert second_confidence == -1.0
