import numpy as np

from src.repositories.gameWindow import creatures


def install_floor(monkeypatch, floor=None):
    if floor is None:
        floor = np.ones((109, 106), dtype=np.uint8)
    monkeypatch.setattr(
        creatures,
        'walkableFloorsSqms',
        np.expand_dims(floor, axis=0),
    )
    monkeypatch.setattr(
        creatures,
        'getPixelFromCoordinate',
        lambda coordinate: coordinate[:2],
    )


def make_creature(name, slot):
    return {
        'name': name,
        'slot': slot,
        'coordinate': [53 - 7 + slot[0], 54 - 5 + slot[1], 0],
        'windowCoordinate': slot,
    }


def test_single_creature_behind_wall_is_not_reachable(monkeypatch):
    floor = np.ones((109, 106), dtype=np.uint8)
    floor[49:60, 55] = 0
    install_floor(monkeypatch, floor)
    unreachable = make_creature('Behind wall', (11, 5))

    result = creatures.getClosestReachableCreature(
        [unreachable],
        (53, 54, 0),
    )

    assert result is None


def test_reachable_creature_is_selected_when_first_candidate_is_blocked(
    monkeypatch,
):
    floor = np.ones((109, 106), dtype=np.uint8)
    floor[49:60, 55] = 0
    install_floor(monkeypatch, floor)
    unreachable = make_creature('Behind wall', (11, 5))
    reachable = make_creature('Nearby', (8, 5))

    reachability = creatures.getCreatureReachability(
        [unreachable, reachable],
        (53, 54, 0),
    )

    assert [item['creature']['name'] for item in reachability] == ['Nearby']
    assert reachability[0]['distance'] == 0
    assert creatures.getClosestReachableCreature(
        [unreachable, reachable],
        (53, 54, 0),
    ) is reachable


def test_all_unreachable_creatures_return_no_candidate(monkeypatch):
    floor = np.ones((109, 106), dtype=np.uint8)
    floor[49:60, 55] = 0
    install_floor(monkeypatch, floor)
    monsters = [
        make_creature('First', (11, 4)),
        make_creature('Second', (12, 6)),
    ]

    assert creatures.getCreatureReachability(
        monsters,
        (53, 54, 0),
    ) == []
    assert creatures.getClosestReachableCreature(
        monsters,
        (53, 54, 0),
    ) is None


def test_reachability_does_not_modify_global_walkability(monkeypatch):
    floor = np.ones((109, 106), dtype=np.uint8)
    install_floor(monkeypatch, floor)
    original = creatures.walkableFloorsSqms.copy()

    creatures.getCreatureReachability(
        [make_creature('Nearby', (8, 5))],
        (53, 54, 0),
        nonWalkableCoordinates=[(54, 55, 0)],
    )

    np.testing.assert_array_equal(creatures.walkableFloorsSqms, original)
