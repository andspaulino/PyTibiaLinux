from unittest.mock import MagicMock

from src.gameplay.core.middlewares import gameWindow as game_window_middleware
from src.gameplay.core.middlewares import loot as loot_middleware


def make_context(*, enabled=True, selected=True, monsters=None):
    orchestrator = MagicMock()
    orchestrator.getCurrentTask.return_value = None
    return {
        'loot': {
            'enabled': enabled,
            'pending': False,
            'quickLootCooldownUntil': 0,
            'chatMonitoringEnabled': False,
        },
        'chat': {
            'tabs': {
                'loot': {
                    'isSelected': selected,
                },
            },
        },
        'cavebot': {
            'isAttackingSomeCreature': False,
            'targetCreature': None,
            'previousTargetCreature': None,
        },
        'gameWindow': {
            'previousMonsters': [],
            'monsters': monsters or [],
        },
        'tasksOrchestrator': orchestrator,
        'screenshot': object(),
    }


def test_disabled_loot_does_not_select_tab_or_read_chat(monkeypatch):
    context = make_context(enabled=False, selected=False)
    hasNewLoot = MagicMock()
    monkeypatch.setattr(loot_middleware, 'hasNewLoot', hasNewLoot)

    loot_middleware.setLootChatMiddleware(context)

    context['tasksOrchestrator'].setRootTask.assert_not_called()
    hasNewLoot.assert_not_called()


def test_enabled_loot_forces_loot_tab_when_unselected(monkeypatch):
    context = make_context(selected=False)
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())

    loot_middleware.setLootChatMiddleware(context)

    rootTask = context['tasksOrchestrator'].setRootTask.call_args.args[1]
    assert rootTask.name == 'selectChatTab'
    assert rootTask.tabName == 'loot'


def test_existing_select_chat_tab_root_is_not_recreated(monkeypatch):
    context = make_context(selected=False)
    currentRootTask = MagicMock()
    currentRootTask.name = 'selectChatTab'
    currentTask = MagicMock(rootTask=currentRootTask)
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())

    loot_middleware.setLootChatMiddleware(context)

    context['tasksOrchestrator'].setRootTask.assert_not_called()


def test_first_enabled_cycle_resets_baseline_once(monkeypatch):
    context = make_context()
    resetLootBaseline = MagicMock()
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', resetLootBaseline)
    monkeypatch.setattr(loot_middleware, 'hasNewLoot', MagicMock(return_value=False))

    loot_middleware.setLootChatMiddleware(context)
    loot_middleware.setLootChatMiddleware(context)

    resetLootBaseline.assert_called_once_with()
    assert context['loot']['chatMonitoringEnabled'] is True


def test_attack_end_starts_post_combat_movement_block(monkeypatch):
    context = make_context()
    context['loot']['wasAttacking'] = True
    context['cavebot']['isAttackingSomeCreature'] = False
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())
    monkeypatch.setattr(loot_middleware, 'hasNewLoot', MagicMock(return_value=False))
    monkeypatch.setattr(loot_middleware, 'time', lambda: 10)

    loot_middleware.setLootChatMiddleware(context)

    assert context['loot']['wasAttacking'] is False
    assert context['loot']['movementBlockedUntil'] == 10.85


def test_active_combat_is_recorded_without_starting_block(monkeypatch):
    context = make_context()
    context['cavebot']['isAttackingSomeCreature'] = True
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())
    monkeypatch.setattr(loot_middleware, 'hasNewLoot', MagicMock(return_value=False))
    monkeypatch.setattr(loot_middleware, 'time', lambda: 10)

    loot_middleware.setLootChatMiddleware(context)

    assert context['loot']['wasAttacking'] is True
    assert context['loot']['movementBlockedUntil'] == 0


def test_disabled_loot_clears_combat_movement_block():
    context = make_context(enabled=False)
    context['loot']['wasAttacking'] = True
    context['loot']['movementBlockedUntil'] = 20

    loot_middleware.setLootChatMiddleware(context)

    assert context['loot']['wasAttacking'] is False
    assert context['loot']['movementBlockedUntil'] == 0


def test_new_loot_line_marks_pending(monkeypatch):
    context = make_context()
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())
    monkeypatch.setattr(loot_middleware, 'hasNewLoot', MagicMock(return_value=True))

    result = loot_middleware.setLootChatMiddleware(context)

    assert result['loot']['pending'] is True
    assert result['loot']['detectedAt'] is not None


def test_new_loot_line_during_cooldown_only_updates_baseline(monkeypatch):
    context = make_context()
    context['loot']['quickLootCooldownUntil'] = 11
    hasNewLoot = MagicMock(return_value=True)
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())
    monkeypatch.setattr(loot_middleware, 'hasNewLoot', hasNewLoot)
    monkeypatch.setattr(loot_middleware, 'time', lambda: 10)

    result = loot_middleware.setLootChatMiddleware(context)

    hasNewLoot.assert_called_once_with(context['screenshot'])
    assert result['loot']['pending'] is False
    assert result['loot']['detectedAt'] is None


def test_no_new_loot_line_keeps_pending_false(monkeypatch):
    context = make_context()
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())
    monkeypatch.setattr(loot_middleware, 'hasNewLoot', MagicMock(return_value=False))

    loot_middleware.setLootChatMiddleware(context)

    assert context['loot']['pending'] is False


def test_has_adjacent_monster_uses_quick_loot_area():
    context = make_context(monsters=[
        {'slot': (7, 5)},
        {'slot': (12, 8)},
    ])

    assert loot_middleware.hasAdjacentMonster(context) is True


def test_target_history_is_preserved_without_loot_detection(monkeypatch):
    monster = {'name': 'Bug', 'slot': (7, 5)}
    context = make_context(monsters=[monster])
    monkeypatch.setattr(
        game_window_middleware,
        'getTargetCreature',
        lambda monsters: monsters[0],
    )

    result = game_window_middleware.setTargetCreatureHistoryMiddleware(context)

    assert result['cavebot']['targetCreature'] == monster
    assert result['cavebot']['previousTargetCreature'] == monster


def test_combat_end_skipped_when_target_still_alive(monkeypatch):
    monster = {'name': 'Lizard Magician', 'coordinate': (31917, 31875, 8)}
    context = make_context(monsters=[monster])
    context['loot']['wasAttacking'] = True
    context['cavebot']['isAttackingSomeCreature'] = False
    context['cavebot']['previousTargetCreature'] = monster
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())
    monkeypatch.setattr(
        loot_middleware,
        'hasNewLoot',
        MagicMock(return_value=False),
    )

    result = loot_middleware.setLootChatMiddleware(context)

    # Because monster is still alive in gameWindow, combat_end is skipped and movementBlockedUntil stays 0
    assert result['loot']['movementBlockedUntil'] == 0
    assert result['loot']['wasAttacking'] is True
    loot_middleware.hasNewLoot.assert_called_once_with(context['screenshot'])


def test_homonymous_monster_does_not_hide_combat_end(monkeypatch):
    deadTarget = {
        'name': 'Muglex Clan Footman',
        'coordinate': (100, 100, 7),
    }
    otherMonsters = [
        {'name': 'Muglex Clan Footman', 'coordinate': (101, 100, 7)},
    ]
    context = make_context(monsters=otherMonsters)
    context['battleList'] = {
        'creatures': [
            {'name': 'Muglex Clan Footman'},
        ],
    }
    context['loot']['wasAttacking'] = True
    context['cavebot']['isAttackingSomeCreature'] = False
    context['cavebot']['previousTargetCreature'] = deadTarget
    monkeypatch.setattr(loot_middleware, 'resetLootBaseline', MagicMock())
    monkeypatch.setattr(
        loot_middleware,
        'hasNewLoot',
        MagicMock(return_value=True),
    )

    result = loot_middleware.setLootChatMiddleware(context)

    assert result['loot']['movementBlockedUntil'] > 0
    assert result['loot']['wasAttacking'] is False
    assert result['loot']['pending'] is True
    assert result['loot']['corpsesToLoot'][0]['coordinate'] == [100, 100, 7]

