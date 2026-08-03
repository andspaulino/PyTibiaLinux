from src.gameplay import navigation
from src.gameplay.core.tasks.walkToCoordinate import WalkToCoordinateTask


def makeContext():
    return {
        'cavebot': {
            'holesOrStairs': [],
            'navigation': {},
        },
        'gameWindow': {'monsters': []},
        'radar': {
            'coordinate': [100, 100, 7],
            'lastCoordinateVisited': [100, 100, 7],
        },
        'lastPressedKey': None,
    }


def test_transient_block_is_deduplicated_refreshed_and_expired():
    context = makeContext()

    assert navigation.addTransientBlockedCoordinate(
        context,
        [101, 100, 7],
        now=10.0,
    ) is True
    assert navigation.addTransientBlockedCoordinate(
        context,
        [101, 100, 7],
        now=11.0,
    ) is False

    entries = context['cavebot']['navigation']['transientBlockedCoordinates']
    assert entries == [{
        'coordinate': [101, 100, 7],
        'expiresAt': 14.0,
    }]
    assert navigation.getActiveTransientBlockedCoordinates(
        context,
        now=13.99,
    ) == [(101, 100, 7)]
    assert navigation.getActiveTransientBlockedCoordinates(
        context,
        now=14.0,
    ) == []
    assert entries != context['cavebot']['navigation'][
        'transientBlockedCoordinates'
    ]


def test_walk_to_coordinate_includes_active_transient_blocks(monkeypatch):
    context = makeContext()
    navigation.addTransientBlockedCoordinate(
        context,
        [101, 100, 7],
        now=10.0,
        duration=10.0,
    )
    monkeypatch.setattr(navigation, 'time', lambda: 11.0)

    task = WalkToCoordinateTask([105, 100, 7])

    assert task.getNonWalkableCoordinates(context) == [(101, 100, 7)]


def test_expired_transient_block_changes_obstacle_signature(monkeypatch):
    context = makeContext()
    navigation.addTransientBlockedCoordinate(
        context,
        [101, 100, 7],
        now=10.0,
        duration=3.0,
    )
    monkeypatch.setattr(navigation, 'time', lambda: 11.0)
    task = WalkToCoordinateTask([105, 100, 7])
    task.nonWalkableCoordinatesSignature = (
        (101, 100, 7),
    )

    monkeypatch.setattr(navigation, 'time', lambda: 13.0)

    assert task.shouldRestart(context) is True
    assert context['cavebot']['navigation']['status'] == 'recalculating'
    assert context['cavebot']['navigation']['failureReason'] == (
        'obstacles-changed'
    )
