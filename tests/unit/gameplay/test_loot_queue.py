from src.gameplay import loot as loot_core


def makeCorpse(label, coordinate):
    return {
        'name': label,
        'coordinate': list(coordinate),
    }


def test_normalize_coordinate_handles_various_inputs():
    assert loot_core.normalizeCoordinate([100, 200, 7]) == (100, 200, 7)
    assert loot_core.normalizeCoordinate((100, 200, 7)) == (100, 200, 7)
    assert loot_core.normalizeCoordinate(None) is None
    assert loot_core.normalizeCoordinate([100, 200]) is None
    assert loot_core.normalizeCoordinate([100, 200, 7, 8]) is None
    assert loot_core.normalizeCoordinate(['abc', 'def', 'ghi']) is None
    assert loot_core.normalizeCoordinate('invalid') is None


def test_quick_loot_range_uses_three_by_three_area():
    player = (100, 100, 7)

    assert loot_core.isCoordinateInQuickLootRange(player, (100, 100, 7)) is True
    assert loot_core.isCoordinateInQuickLootRange(player, (101, 101, 7)) is True
    assert loot_core.isCoordinateInQuickLootRange(player, (102, 100, 7)) is False
    assert loot_core.isCoordinateInQuickLootRange(player, (100, 100, 8)) is False
    assert loot_core.isCoordinateInQuickLootRange(None, (100, 100, 7)) is False
    assert loot_core.isCoordinateInQuickLootRange(player, None) is False


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


def test_closest_quick_loot_coordinate_filters_unwalkable_tiles(monkeypatch):
    # Only tile (101, 101, 7) is walkable around corpse (102, 100, 7)
    def walkable_stub(coord):
        return coord == (101, 101, 7)

    monkeypatch.setattr(loot_core, 'isCoordinateWalkable', walkable_stub)

    destination = loot_core.getClosestQuickLootCoordinate(
        (100, 100, 7),
        (102, 100, 7),
    )

    assert destination == (101, 101, 7)


def test_corpse_queue_deduplicates_coordinates_and_preserves_fifo():
    corpses = []
    c1 = makeCorpse('first', (101, 100, 7))
    c2 = makeCorpse('duplicate', (101, 100, 7))
    c3 = makeCorpse('second', (103, 100, 7))

    assert loot_core.addCorpseToQueue(corpses, c1) is True
    assert loot_core.addCorpseToQueue(corpses, c2) is False
    assert loot_core.addCorpseToQueue(corpses, c3) is True

    assert len(corpses) == 2
    assert corpses[0]['name'] == 'first'
    assert corpses[1]['name'] == 'second'

    # Ensure added object is a copy and has queuedAt timestamp
    assert corpses[0] is not c1
    assert 'queuedAt' in corpses[0]


def test_add_corpse_to_queue_rejects_invalid_creatures():
    corpses = []
    assert loot_core.addCorpseToQueue(corpses, None) is False
    assert loot_core.addCorpseToQueue(corpses, 'invalid') is False
    assert loot_core.addCorpseToQueue(corpses, {'name': 'NoCoord'}) is False
    assert len(corpses) == 0


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


def test_discard_corpse_by_coordinate():
    corpses = [
        makeCorpse('first', (101, 100, 7)),
        makeCorpse('second', (103, 100, 7)),
    ]

    loot_core.discardCorpseByCoordinate(corpses, (101, 100, 7))
    assert len(corpses) == 1
    assert corpses[0]['name'] == 'second'


def test_remove_expired_corpses(monkeypatch):
    corpses = [
        {
            'name': 'old',
            'coordinate': [100, 100, 7],
            'processingStartedAt': 100.0,
        },
        {
            'name': 'fresh',
            'coordinate': [105, 100, 7],
            'processingStartedAt': 106.0,
        },
    ]
    monkeypatch.setattr(loot_core, 'time', lambda: 109.0)

    loot_core.removeExpiredCorpses(corpses)

    assert len(corpses) == 1
    assert corpses[0]['name'] == 'fresh'


def test_waiting_corpse_does_not_expire_before_processing(monkeypatch):
    corpse = {
        'name': 'waiting',
        'coordinate': [100, 100, 7],
        'queuedAt': 100.0,
    }
    corpses = [corpse]
    monkeypatch.setattr(loot_core, 'time', lambda: 120.0)

    loot_core.removeExpiredCorpses(corpses)

    assert corpses == [corpse]
    assert 'processingStartedAt' not in corpse


def test_active_corpse_is_protected_from_processing_timeout(monkeypatch):
    corpse = {
        'name': 'active',
        'coordinate': [100, 100, 7],
        'processingStartedAt': 100.0,
    }
    corpses = [corpse]
    monkeypatch.setattr(loot_core, 'time', lambda: 120.0)

    loot_core.removeExpiredCorpses(
        corpses,
        protectedCoordinate=[100, 100, 7],
    )

    assert corpses == [corpse]

