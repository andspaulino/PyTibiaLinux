import numpy as np
import pytest

from src.repositories.gameWindow import creatures


def make_template(pattern):
    return np.where(np.array(pattern, dtype=np.uint8) == 1, 255, 0).astype(np.uint8)


def place_name(image, bar, template, *, tone=76, x_offset=0, y_offset=0):
    x0, x1, y0, y1 = creatures.getCreatureNamePosition(
        bar, template, image.shape[1])
    mask = template == 255
    crop = image[
        y0 + y_offset:y1 + y_offset,
        x0 + x_offset:x1 + x_offset,
    ]
    crop[mask] = tone


def test_match_confidence_normalizes_linux_font_intensity():
    template = make_template([
        [0, 1, 0],
        [1, 0, 1],
        [1, 1, 1],
    ])
    crop = np.where(template == 255, 76, 20).astype(np.uint8)

    assert creatures.getCreatureNameMatchConfidence(crop, template) == 1.0


def test_classifier_accepts_expected_name_with_small_position_offset(monkeypatch):
    template = make_template([
        [0, 1, 0, 0, 1],
        [1, 0, 1, 1, 0],
        [1, 1, 1, 0, 1],
        [1, 0, 1, 1, 0],
        [1, 0, 1, 0, 1],
        [0, 0, 0, 1, 0],
        [1, 1, 0, 0, 1],
        [0, 1, 1, 1, 0],
        [1, 0, 0, 1, 1],
        [0, 1, 0, 0, 1],
        [1, 0, 1, 1, 0],
    ])
    monkeypatch.setattr(creatures, 'creaturesNamesHashes', {'Cave Rat': template})
    image = np.full((80, 100), 20, dtype=np.uint8)
    bar = (40, 40)
    place_name(image, bar, template, x_offset=1)

    name, confidence, second, position = creatures.classifyCreatureName(
        image, bar, ['Cave Rat'])

    assert name == 'Cave Rat'
    assert confidence == 1.0
    assert second == -1.0
    expected = creatures.getCreatureNamePosition(bar, template, image.shape[1])
    assert position == (expected[0] + 1, expected[2])


def test_classifier_uses_margin_between_distinct_candidates(monkeypatch):
    template = make_template([
        [0, 1, 0],
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1],
    ])
    monkeypatch.setattr(
        creatures,
        'creaturesNamesHashes',
        {'Rat': template, 'Bat': template.copy()},
    )
    image = np.full((80, 100), 20, dtype=np.uint8)
    bar = (40, 40)
    place_name(image, bar, template)

    name, best, second, _ = creatures.classifyCreatureName(
        image, bar, ['Rat', 'Bat'])

    assert name is None
    assert best == pytest.approx(1.0)
    assert second == pytest.approx(1.0)


def test_classifier_rejects_region_without_name(monkeypatch):
    template = make_template([
        [0, 1, 0],
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1],
    ])
    monkeypatch.setattr(creatures, 'creaturesNamesHashes', {'Rat': template})
    image = np.full((80, 100), 20, dtype=np.uint8)

    name, confidence, _, position = creatures.classifyCreatureName(
        image, (40, 40), ['Rat'])

    assert name is None
    assert confidence == -1.0
    assert position is None
