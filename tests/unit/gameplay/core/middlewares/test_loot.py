from src.gameplay.core.middlewares import gameWindow as game_window_middleware
from src.gameplay.core.middlewares import loot as loot_middleware


def make_context(*, enabled=True, previous_target=None, previous=None, current=None):
    return {
        'loot': {
            'enabled': enabled,
            'pending': False,
            'pendingSlot': None,
        },
        'cavebot': {
            'targetCreature': None,
            'previousTargetCreature': previous_target,
        },
        'gameWindow': {
            'previousMonsters': previous or [],
            'monsters': current or [],
        },
    }


def test_disappeared_attacked_target_in_nearby_area_marks_loot_pending():
    target = {'slot': (8, 5), 'isBeingAttacked': True}
    context = make_context(
        previous_target=target,
        previous=[target],
        current=[],
    )

    result = loot_middleware.setLootDeathMiddleware(context)

    assert result['loot']['pending'] is True
    assert result['loot']['pendingSlot'] == (8, 5)
    assert result['loot']['detectedAt'] is not None
    assert result['cavebot']['previousTargetCreature'] is None


def test_disappeared_target_outside_nearby_area_does_not_mark_loot():
    target = {'slot': (5, 5), 'isBeingAttacked': True}
    context = make_context(previous_target=target, previous=[target], current=[])

    loot_middleware.setLootDeathMiddleware(context)

    assert context['loot']['pending'] is False


def test_stale_previous_target_not_present_in_previous_frame_is_ignored():
    target = {'slot': (8, 5), 'isBeingAttacked': True}
    context = make_context(
        previous_target=target,
        previous=[],
        current=[],
    )

    loot_middleware.setLootDeathMiddleware(context)

    assert context['loot']['pending'] is False



def test_target_still_visible_does_not_mark_loot():
    target = {'slot': (8, 5), 'isBeingAttacked': True}
    context = make_context(
        previous_target=target,
        previous=[target],
        current=[target],
    )

    loot_middleware.setLootDeathMiddleware(context)

    assert context['loot']['pending'] is False


def test_disabled_loot_does_not_mark_pending():
    target = {'slot': (8, 5), 'isBeingAttacked': True}
    context = make_context(
        enabled=False,
        previous_target=target,
        previous=[target],
        current=[],
    )

    loot_middleware.setLootDeathMiddleware(context)

    assert context['loot']['pending'] is False
    assert context['cavebot']['previousTargetCreature'] is target


def test_has_adjacent_monster_uses_quick_loot_area():
    context = make_context(current=[
        {'slot': (7, 5)},
        {'slot': (12, 8)},
    ])

    assert loot_middleware.hasAdjacentMonster(context) is True


def test_target_history_is_preserved_without_chat_or_highlighting(monkeypatch):
    monster = {'name': 'Bug', 'slot': (7, 5)}
    context = make_context(current=[monster])
    monkeypatch.setattr(
        game_window_middleware,
        'getTargetCreature',
        lambda monsters: monsters[0],
    )

    result = game_window_middleware.setTargetCreatureHistoryMiddleware(context)

    assert result['cavebot']['targetCreature'] == monster
    assert result['cavebot']['previousTargetCreature'] == monster
