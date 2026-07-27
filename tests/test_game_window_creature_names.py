import numpy as np

from src.repositories.gameWindow import creatures as game_window_creatures


def make_crop(template, tone):
    return np.where(template == 255, tone, 0).astype(np.uint8)


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
