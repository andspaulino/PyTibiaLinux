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
