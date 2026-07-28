from unittest.mock import MagicMock

from src.gameplay.threads.pyTibia import PyTibiaThread

class DummyContext:
    def __init__(self, context_dict):
        self.context = context_dict

class LoopStopException(BaseException):
    pass

class CustomDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_count = 0

    def __getitem__(self, key):
        if key == 'pause':
            self.call_count += 1
            if self.call_count > 2:
                raise LoopStopException()
        return super().__getitem__(key)

def test_pytibia_thread_loop_respects_pause(monkeypatch):
    sleep_calls = []
    monkeypatch.setattr("src.gameplay.threads.pyTibia.sleep", lambda seconds: sleep_calls.append(seconds))

    context_dict = CustomDict({'pause': True, 'window': 'Tibia'})
    ctx = DummyContext(context_dict)
    thread = PyTibiaThread(ctx)

    try:
        thread.mainloop()
    except LoopStopException:
        pass

    assert len(sleep_calls) >= 1
    assert all(s == 0.1 for s in sleep_calls)

def test_pytibia_thread_loop_execution_flow(monkeypatch):
    orchestrator = MagicMock()
    # Mock do() method to return the context passed to it
    orchestrator.do.side_effect = lambda ctx: ctx
    
    context_dict = {
        'pause': False,
        'window': 'Tibia',
        'tasksOrchestrator': orchestrator,
        'statusBar': {'hpPercentage': 100, 'hp': 200, 'manaPercentage': 100, 'mana': 100},
        'screenshot': None,
        'radar': {'coordinate': [100, 100, 7]},
        'cavebot': {'enabled': False, 'closestCreature': None, 'waypoints': {'currentIndex': None, 'items': []}},
        'targeting': {'enabled': False},
        'loot': {'corpsesToLoot': [], 'enabled': False},
        'gameWindow': {'monsters': [], 'previousMonsters': []},
    }
    ctx = DummyContext(context_dict)
    thread = PyTibiaThread(ctx)

    # Mock all middlewares in handleGameData
    middlewares = [
        "setScreenshotMiddleware",
        "setRadarMiddleware",
        "setChatTabsMiddleware",
        "setBattleListMiddleware",
        "setGameWindowMiddleware",
        "setDirectionMiddleware",
        "setGameWindowCreaturesMiddleware",
        "setLootHighlightingMiddleware",
        "setHandleLootMiddleware",
        "setWaypointIndexMiddleware",
        "setMapPlayerStatusMiddleware",
        "setCleanUpTasksMiddleware",
    ]
    mock_set_screenshot = MagicMock(return_value=context_dict)
    mock_set_player_status = MagicMock(return_value=context_dict)
    mock_set_cleanup = MagicMock(return_value=context_dict)
    for middleware in middlewares:
        monkeypatch.setattr(f"src.gameplay.threads.pyTibia.{middleware}", MagicMock(return_value=context_dict))
    monkeypatch.setattr("src.gameplay.threads.pyTibia.setScreenshotMiddleware", mock_set_screenshot)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.setMapPlayerStatusMiddleware", mock_set_player_status)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.setCleanUpTasksMiddleware", mock_set_cleanup)

    # Mock the observers
    potions_called = 0
    spells_called = 0
    def mock_potions(c):
        nonlocal potions_called
        potions_called += 1
    def mock_spells(c):
        nonlocal spells_called
        spells_called += 1
        # Pause after first iteration to stop the loop
        c['pause'] = True
        raise LoopStopException() # Force exit

    monkeypatch.setattr("src.gameplay.threads.pyTibia.healingByPotions", mock_potions)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.healingBySpells", mock_spells)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.comboSpells", MagicMock())
    monkeypatch.setattr("src.gameplay.threads.pyTibia.swapAmulet", MagicMock())
    monkeypatch.setattr("src.gameplay.threads.pyTibia.swapRing", MagicMock())
    monkeypatch.setattr("src.gameplay.threads.pyTibia.eatFood", MagicMock())
    monkeypatch.setattr("src.gameplay.threads.pyTibia.sleep", MagicMock())

    try:
        thread.mainloop()
    except LoopStopException:
        pass

    assert mock_set_screenshot.call_count == 1
    assert mock_set_player_status.call_count == 1
    assert mock_set_cleanup.call_count == 1
    assert orchestrator.do.call_count == 1
    assert potions_called == 1
    assert spells_called == 1
    assert ctx.context['pause'] is True


def make_gameplay_context(*, cavebot_enabled=False, targeting_enabled=False, monsters=None):
    orchestrator = MagicMock()
    orchestrator.getCurrentTask.return_value = None
    return {
        'cavebot': {
            'enabled': cavebot_enabled,
            'closestCreature': None,
            'isAttackingSomeCreature': False,
            'targetCreature': None,
            'waypoints': {'currentIndex': None, 'items': []},
        },
        'targeting': {
            'enabled': targeting_enabled,
            'walkToTarget': False,
            'creatures': {},
            'canIgnoreCreatures': True,
            'hasIgnorableCreatures': False,
        },
        'gameWindow': {
            'monsters': monsters or [],
            'previousMonsters': [],
        },
        'radar': {'coordinate': [100, 100, 7]},
        'loot': {'corpsesToLoot': []},
        'tasksOrchestrator': orchestrator,
        'way': None,
    }


def test_handle_gameplay_tasks_does_nothing_when_targeting_and_cavebot_are_disabled(monkeypatch):
    context = make_gameplay_context(monsters=[{'name': 'Rat'}])
    getClosestCreature = MagicMock()
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature', getClosestCreature)

    result = PyTibiaThread(None).handleGameplayTasks(context)

    assert result is context
    assert context['way'] is None
    assert context['cavebot']['closestCreature'] is None
    assert context['gameWindow']['previousMonsters'] == context['gameWindow']['monsters']
    getClosestCreature.assert_not_called()
    context['tasksOrchestrator'].setRootTask.assert_not_called()


def test_handle_gameplay_tasks_targets_without_cavebot(monkeypatch):
    monster = {'name': 'Rat', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(
        targeting_enabled=True, monsters=[monster])
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks)

    result = PyTibiaThread(None).handleGameplayTasks(context)

    assert result is context
    assert context['way'] == 'targeting'
    assert context['cavebot']['closestCreature'] is monster
    resolveTargetingTasks.assert_called_once_with(context)


def test_handle_gameplay_tasks_does_not_recreate_attack_root_task(monkeypatch):
    monster = {'name': 'Rat', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(
        targeting_enabled=True, monsters=[monster])
    currentRootTask = MagicMock(name='rootTask')
    currentRootTask.name = 'attackClosestCreature'
    currentTask = MagicMock(rootTask=currentRootTask)
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks)

    PyTibiaThread(None).handleGameplayTasks(context)

    resolveTargetingTasks.assert_not_called()


def test_handle_gameplay_tasks_resolves_waypoint_only_when_cavebot_is_enabled(monkeypatch):
    waypoint = {'type': 'walk', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(cavebot_enabled=True)
    context['cavebot']['waypoints'] = {
        'currentIndex': 0,
        'items': [waypoint],
    }
    waypointTask = MagicMock(name='waypointTask')
    resolveTasksByWaypoint = MagicMock(return_value=waypointTask)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTasksByWaypoint',
        resolveTasksByWaypoint)

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] == 'waypoint'
    resolveTasksByWaypoint.assert_called_once_with(waypoint)
    context['tasksOrchestrator'].setRootTask.assert_called_once_with(
        context, waypointTask)


def test_handle_gameplay_tasks_accepts_empty_waypoints(monkeypatch):
    context = make_gameplay_context(cavebot_enabled=True)
    resolveTasksByWaypoint = MagicMock()
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTasksByWaypoint',
        resolveTasksByWaypoint)

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] == 'waypoint'
    resolveTasksByWaypoint.assert_not_called()
    context['tasksOrchestrator'].setRootTask.assert_not_called()


def test_handle_gameplay_tasks_does_not_loot_when_cavebot_is_disabled(monkeypatch):
    context = make_gameplay_context()
    context['loot']['corpsesToLoot'] = [{'coordinate': [101, 100, 7]}]

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] is None
    context['tasksOrchestrator'].setRootTask.assert_not_called()


def test_handle_gameplay_tasks_prioritizes_targeting_over_pending_loot_when_creatures_exist(monkeypatch):
    monster = {'name': 'Rat', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(
        targeting_enabled=True, monsters=[monster])
    context['loot'] = {
        'enabled': True,
        'mode': 'quickLoot',
        'quickLootDetectionPending': True,
        'quickLootReady': False,
        'corpsesToLoot': [],
    }
    context['tasksOrchestrator'].getCurrentTask.return_value = None
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks)

    result = PyTibiaThread(None).handleGameplayTasks(context)

    assert result is context
    assert context['way'] == 'targeting'
    context['tasksOrchestrator'].setRootTask.assert_not_called()
    resolveTargetingTasks.assert_called_once_with(context)


def test_handle_gameplay_tasks_prioritizes_targeting_during_quick_loot_cooldown(monkeypatch):
    from time import time
    monster = {'name': 'Rat', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(
        targeting_enabled=True, monsters=[monster])
    context['loot'] = {
        'enabled': True,
        'mode': 'quickLoot',
        'quickLootDetectionPending': True,
        'quickLootReady': True,
        'quickLootCooldownUntil': time() + 10.0,
        'corpsesToLoot': [],
    }
    context['tasksOrchestrator'].getCurrentTask.return_value = None
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True))
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks)

    result = PyTibiaThread(None).handleGameplayTasks(context)

    assert result is context
    assert context['way'] == 'targeting'
    resolveTargetingTasks.assert_called_once_with(context)


def test_handle_gameplay_tasks_pauses_when_quick_loot_is_pending_and_no_creatures_to_attack(monkeypatch):
    context = make_gameplay_context()
    context['loot'] = {
        'enabled': True,
        'mode': 'quickLoot',
        'quickLootDetectionPending': True,
        'quickLootReady': False,
        'corpsesToLoot': [],
    }
    currentRootTask = MagicMock(name='rootTask')
    currentRootTask.name = 'attackClosestCreature'
    currentTask = MagicMock(rootTask=currentRootTask)
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask
    resolveTargetingTasks = MagicMock()
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks)

    result = PyTibiaThread(None).handleGameplayTasks(context)

    assert result is context
    assert context['way'] == 'lootPending'
    context['tasksOrchestrator'].setRootTask.assert_called_once_with(
        context, None)
    resolveTargetingTasks.assert_not_called()

