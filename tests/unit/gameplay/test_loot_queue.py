from src.gameplay import loot as loot_core


def makeCorpse(label, coordinate):
    return {
        'name': label,
        'coordinate': list(coordinate),
    }


def test_quick_loot_range_uses_three_by_three_area():
    player = (100, 100, 7)

    assert loot_core.isCoordinateInQuickLootRange(player, (101, 101, 7)) is True
    assert loot_core.isCoordinateInQuickLootRange(player, (102, 100, 7)) is False
    assert loot_core.isCoordinateInQuickLootRange(player, (100, 100, 8)) is False


def test_closest_quick_loot_coordinate_moves_only_until_range(monkeypatch):
    monkeypatch.setattr(loot_core, 'isCoordinateWalkable', lambda _: True)

    destination = loot_core.getClosestQuickLootCoordinate(
        (100, 100, 7),
        (102, 100, 7),
    )

    assert destination == (101, 100, 7)


def test_corpse_approach_rejects_distant_or_different_floor(monkeypatch):
    monkeypatch.setattr(loot_core, 'isCoordinateWalkable', lambda _: True)

    assert loot_core.getClosestQuickLootCoordinate(
        (100, 100, 7),
        (106, 100, 7),
    ) is None
    assert loot_core.getClosestQuickLootCoordinate(
        (100, 100, 7),
        (101, 100, 8),
    ) is None


def test_corpse_queue_deduplicates_coordinates():
    corpses = []

    assert loot_core.addCorpseToQueue(
        corpses,
        makeCorpse('first', (101, 100, 7)),
    ) is True
    assert loot_core.addCorpseToQueue(
        corpses,
        makeCorpse('duplicate', (101, 100, 7)),
    ) is False

    assert len(corpses) == 1
    assert corpses[0]['name'] == 'first'


def test_remove_corpses_in_range_keeps_only_uncovered_coordinates():
    corpses = [
        makeCorpse('center', (100, 100, 7)),
        makeCorpse('diagonal', (101, 101, 7)),
        makeCorpse('far', (103, 100, 7)),
        makeCorpse('other-floor', (100, 100, 8)),
    ]

    loot_core.removeCorpsesInQuickLootRange(
        corpses,
        (100, 100, 7),
    )

    assert [corpse['name'] for corpse in corpses] == ['far', 'other-floor']
