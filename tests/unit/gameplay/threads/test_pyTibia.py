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
        "setLootChatMiddleware",
        "setTargetCreatureHistoryMiddleware",
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
            'previousTargetCreature': None,
            'waypoints': {'currentIndex': None, 'items': []},
        },
        'targeting': {
            'enabled': targeting_enabled,
            'creatures': {},
            'canIgnoreCreatures': True,
            'hasIgnorableCreatures': False,
        },
        'gameWindow': {
            'monsters': monsters or [],
            'previousMonsters': [],
        },
        'radar': {'coordinate': [100, 100, 7]},
        'loot': {
            'enabled': False,
            'pending': False,
            'quickLootCooldownUntil': 0,
            'movementBlockedUntil': 0,
        },
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
    resolveTargetingTasks.assert_called_once_with(
        context,
        allowChase=False,
    )


def test_handle_gameplay_tasks_does_not_recreate_attack_root_task(monkeypatch):
    monster = {'name': 'Rat', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(
        targeting_enabled=True, monsters=[monster])
    currentRootTask = MagicMock(name='rootTask')
    currentRootTask.name = 'attackClosestCreature'
    currentRootTask.allowChase = False
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


def test_handle_gameplay_tasks_enables_chase_only_with_targeting_cavebot_and_radar(monkeypatch):
    monster = {'name': 'Rat', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(
        cavebot_enabled=True,
        targeting_enabled=True,
        monsters=[monster],
    )
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    resolveTargetingTasks.assert_called_once_with(
        context,
        allowChase=True,
    )


def test_handle_gameplay_tasks_keeps_selection_only_without_radar(monkeypatch):
    monster = {'name': 'Rat', 'coordinate': [32001, 32000, 7]}
    context = make_gameplay_context(
        cavebot_enabled=True,
        targeting_enabled=True,
        monsters=[monster],
    )
    context['radar']['coordinate'] = None
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    resolveTargetingTasks.assert_called_once_with(
        context,
        allowChase=False,
    )


def test_handle_gameplay_tasks_replaces_attack_root_when_chase_mode_changes(monkeypatch):
    monster = {'name': 'Rat', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(
        cavebot_enabled=True,
        targeting_enabled=True,
        monsters=[monster],
    )
    currentRootTask = MagicMock(name='rootTask')
    currentRootTask.name = 'attackClosestCreature'
    currentRootTask.allowChase = False
    currentTask = MagicMock(rootTask=currentRootTask)
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    resolveTargetingTasks.assert_called_once_with(
        context,
        allowChase=True,
    )


def test_handle_gameplay_tasks_keeps_matching_chase_root(monkeypatch):
    monster = {'name': 'Rat', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(
        cavebot_enabled=True,
        targeting_enabled=True,
        monsters=[monster],
    )
    currentRootTask = MagicMock(name='rootTask')
    currentRootTask.name = 'attackClosestCreature'
    currentRootTask.allowChase = True
    currentTask = MagicMock(rootTask=currentRootTask)
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks,
    )

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


def test_post_combat_delay_waits_before_quick_loot(monkeypatch):
    context = make_gameplay_context()
    context['loot'].update({
        'enabled': True,
        'pending': True,
        'movementBlockedUntil': 11,
    })
    monkeypatch.setattr('src.gameplay.threads.pyTibia.time', lambda: 10)

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] == 'lootPending'
    context['tasksOrchestrator'].setRootTask.assert_not_called()


def test_post_combat_delay_blocks_waypoint_movement(monkeypatch):
    waypoint = {'type': 'walk', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(cavebot_enabled=True)
    context['cavebot']['waypoints'] = {
        'currentIndex': 0,
        'items': [waypoint],
    }
    context['loot'].update({
        'enabled': True,
        'movementBlockedUntil': 11,
    })
    resolveTasksByWaypoint = MagicMock()
    monkeypatch.setattr('src.gameplay.threads.pyTibia.time', lambda: 10)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTasksByWaypoint',
        resolveTasksByWaypoint,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] == 'lootStabilizing'
    resolveTasksByWaypoint.assert_not_called()


def test_post_combat_delay_keeps_distant_target_selection_only(monkeypatch):
    monster = {
        'name': 'Rat',
        'slot': (12, 8),
        'coordinate': [104, 100, 7],
    }
    context = make_gameplay_context(
        cavebot_enabled=True,
        targeting_enabled=True,
        monsters=[monster],
    )
    context['loot'].update({
        'enabled': True,
        'movementBlockedUntil': 11,
    })
    currentRootTask = MagicMock()
    currentRootTask.name = 'attackClosestCreature'
    currentRootTask.allowChase = True
    currentTask = MagicMock(rootTask=currentRootTask)
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr('src.gameplay.threads.pyTibia.time', lambda: 10)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    resolveTargetingTasks.assert_called_once_with(context, allowChase=False)


def test_quick_loot_cooldown_blocks_waypoint_after_input(monkeypatch):
    waypoint = {'type': 'walk', 'coordinate': [101, 100, 7]}
    context = make_gameplay_context(cavebot_enabled=True)
    context['cavebot']['waypoints'] = {
        'currentIndex': 0,
        'items': [waypoint],
    }
    context['loot'].update({
        'enabled': True,
        'pending': False,
        'quickLootCooldownUntil': 11,
    })
    resolveTasksByWaypoint = MagicMock()
    monkeypatch.setattr('src.gameplay.threads.pyTibia.time', lambda: 10)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTasksByWaypoint',
        resolveTasksByWaypoint,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] == 'lootStabilizing'
    resolveTasksByWaypoint.assert_not_called()


def test_handle_gameplay_tasks_loots_without_cavebot_when_death_is_pending():
    context = make_gameplay_context()
    context['loot'].update({
        'enabled': True,
        'pending': True,
    })

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] == 'lootPending'
    rootTask = context['tasksOrchestrator'].setRootTask.call_args.args[1]
    assert rootTask.name == 'quickLootNearbyCorpses'



def test_handle_gameplay_tasks_keeps_adjacent_combat_without_chase(monkeypatch):
    monster = {
        'name': 'Rat',
        'slot': (8, 5),
        'coordinate': [101, 100, 7],
    }
    context = make_gameplay_context(
        cavebot_enabled=True,
        targeting_enabled=True,
        monsters=[monster],
    )
    context['loot'].update({
        'enabled': True,
        'pending': True,
    })
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.shouldAskForTargetingTasks',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] == 'targeting'
    resolveTargetingTasks.assert_called_once_with(context, allowChase=False)



def test_pending_loot_removes_chase_even_during_protected_single_walk(monkeypatch):
    monster = {
        'name': 'Rat',
        'slot': (8, 5),
        'coordinate': [101, 100, 7],
    }
    context = make_gameplay_context(
        cavebot_enabled=True,
        targeting_enabled=True,
        monsters=[monster],
    )
    context['loot'].update({
        'enabled': True,
        'pending': True,
    })
    currentRootTask = MagicMock()
    currentRootTask.name = 'attackClosestCreature'
    currentRootTask.allowChase = True
    currentTask = MagicMock()
    currentTask.name = 'singleWalk'
    currentTask.rootTask = currentRootTask
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask
    resolveTargetingTasks = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestCreature',
        MagicMock(return_value=monster),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.hasCreaturesToAttack',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTargetingTasks',
        resolveTargetingTasks,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    resolveTargetingTasks.assert_called_once_with(context, allowChase=False)



def test_handle_gameplay_tasks_does_not_walk_while_adjacent_monster_blocks_loot(monkeypatch):
    waypoint = {'type': 'walk', 'coordinate': [101, 100, 7]}
    monster = {'name': 'Rat', 'slot': (8, 5)}
    context = make_gameplay_context(
        cavebot_enabled=True,
        targeting_enabled=False,
        monsters=[monster],
    )
    context['cavebot']['waypoints'] = {
        'currentIndex': 0,
        'items': [waypoint],
    }
    context['loot'].update({
        'enabled': True,
        'pending': True,
    })
    resolveTasksByWaypoint = MagicMock()
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.resolveTasksByWaypoint',
        resolveTasksByWaypoint,
    )

    PyTibiaThread(None).handleGameplayTasks(context)

    assert context['way'] == 'lootPending'
    resolveTasksByWaypoint.assert_not_called()
    context['tasksOrchestrator'].setRootTask.assert_not_called()


def test_decisive_corpse_approach_and_quick_loot_flow(monkeypatch):
    """
    Decisive test:
    1. Player at (100, 100, 7). Monster dies 2 SQMs away at (102, 100, 7).
    2. handleGameplayTasks schedules WalkToCorpseTask to (101, 100, 7).
    3. Player moves to (101, 100, 7) (now within 3x3 range).
    4. handleGameplayTasks schedules QuickLootNearbyCorpsesTask.
    5. QuickLootNearbyCorpsesTask removes corpse, clears pending.
    6. Next cycle resumes targeting/cavebot.
    """
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.getClosestQuickLootCoordinate',
        lambda p, c: (101, 100, 7),
    )
    monkeypatch.setattr(
        'src.gameplay.threads.pyTibia.isCoordinateInQuickLootRange',
        lambda p, c: abs(p[0] - c[0]) <= 1 and abs(p[1] - c[1]) <= 1 and p[2] == c[2],
    )

    context = make_gameplay_context(cavebot_enabled=True, targeting_enabled=True)
    context['radar']['coordinate'] = [100, 100, 7]
    context['loot'].update({
        'enabled': True,
        'pending': True,
        'corpsesToLoot': [{'name': 'Dragon', 'coordinate': [102, 100, 7]}],
    })

    # Cycle 1: Out of range (2 SQM away) -> schedules WalkToCorpseTask
    PyTibiaThread(None).handleGameplayTasks(context)
    assert context['way'] == 'lootCorpses'
    task1 = context['tasksOrchestrator'].setRootTask.call_args.args[1]
    assert task1.name == 'lootCorpse'
    assert task1.coordinate == (101, 100, 7)

    # Simulate walking to (101, 100, 7)
    context['radar']['coordinate'] = [101, 100, 7]
    context['tasksOrchestrator'].getCurrentTask.return_value = None

    # Cycle 2: In 3x3 range -> schedules QuickLootNearbyCorpsesTask
    PyTibiaThread(None).handleGameplayTasks(context)
    assert context['way'] == 'lootCorpses'
    task2 = context['tasksOrchestrator'].setRootTask.call_args.args[1]
    assert task2.name == 'quickLootNearbyCorpses'
    assert task2.discardSelectedCorpse is False

    # Execute QuickLootNearbyCorpsesTask.do at time t=10.0
    monkeypatch.setattr('src.gameplay.core.tasks.quickLootNearbyCorpses.time', lambda: 10.0)
    monkeypatch.setattr('src.utils.keyboard.hotkey', MagicMock())
    task2.do(context)

    # Corpse should be removed from corpsesToLoot and pending cleared
    assert len(context['loot']['corpsesToLoot']) == 0
    assert context['loot']['pending'] is False

    # Cycle 3: After quick loot cooldown (0.7s), queue empty -> resumes Cavebot / Waypoint
    monkeypatch.setattr('src.gameplay.threads.pyTibia.time', lambda: 10.8)
    context['cavebot']['waypoints'] = {'currentIndex': 0, 'items': [{'type': 'walk'}]}
    monkeypatch.setattr('src.gameplay.threads.pyTibia.resolveTasksByWaypoint', MagicMock())
    PyTibiaThread(None).handleGameplayTasks(context)
    assert context['way'] == 'waypoint'


def test_failed_corpse_approach_fallback_discards_corpse(monkeypatch):
    context = make_gameplay_context(cavebot_enabled=True)
    context['radar']['coordinate'] = [100, 100, 7]
    context['loot'].update({
        'enabled': True,
        'pending': True,
        'corpsesToLoot': [{
            'name': 'Demon',
            'coordinate': [104, 100, 7],
            'approachFailed': True,
        }],
    })

    # Cycle 1: approachFailed is True -> schedules QuickLootNearbyCorpsesTask with discardSelectedCorpse=True
    PyTibiaThread(None).handleGameplayTasks(context)
    task = context['tasksOrchestrator'].setRootTask.call_args.args[1]
    assert task.name == 'quickLootNearbyCorpses'
    assert task.discardSelectedCorpse is True

    # Execute task.do
    monkeypatch.setattr('src.utils.keyboard.hotkey', MagicMock())
    task.do(context)

    # Corpse must be discarded
    assert len(context['loot']['corpsesToLoot']) == 0
    assert context['loot']['pending'] is False


def test_radar_missing_fallback_retries_before_discarding(monkeypatch):
    context = make_gameplay_context(cavebot_enabled=True)
    context['radar']['coordinate'] = None
    corpse = {'name': 'Wolf', 'coordinate': [100, 100, 7]}
    context['loot'].update({
        'enabled': True,
        'pending': True,
        'corpsesToLoot': [corpse],
    })

    # Ticks 1 & 2: missing radar count increases, discard is False
    PyTibiaThread(None).handleGameplayTasks(context)
    task1 = context['tasksOrchestrator'].setRootTask.call_args.args[1]
    assert task1.discardSelectedCorpse is False
    assert corpse['radarMissingCount'] == 1

    PyTibiaThread(None).handleGameplayTasks(context)
    task2 = context['tasksOrchestrator'].setRootTask.call_args.args[1]
    assert task2.discardSelectedCorpse is False
    assert corpse['radarMissingCount'] == 2

    # Tick 3: radar missing >= 3 -> discard is True
    PyTibiaThread(None).handleGameplayTasks(context)
    task3 = context['tasksOrchestrator'].setRootTask.call_args.args[1]
    assert task3.discardSelectedCorpse is True
    assert corpse['radarMissingCount'] == 3


def test_corpse_queue_expiration_removes_stale_corpses(monkeypatch):
    context = make_gameplay_context(cavebot_enabled=True)
    context['radar']['coordinate'] = [100, 100, 7]
    context['loot'].update({
        'enabled': True,
        'pending': True,
        'corpsesToLoot': [{
            'name': 'Rat',
            'coordinate': [105, 100, 7],
            'queuedAt': 100.0,
        }],
    })
    monkeypatch.setattr('src.gameplay.threads.pyTibia.time', lambda: 110.0)

    # handleGameplayTasks should expire the corpse, clear pending
    PyTibiaThread(None).handleGameplayTasks(context)

    assert len(context['loot']['corpsesToLoot']) == 0
    assert context['loot']['pending'] is False


