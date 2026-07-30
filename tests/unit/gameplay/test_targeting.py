from unittest.mock import MagicMock

from src.gameplay.targeting import (
    hasCreaturesToAttack,
    resolveTargetingTasks,
    shouldAskForTargetingTasks,
)


def make_context(monsters=None):
    orchestrator = MagicMock()
    orchestrator.getCurrentTask.return_value = None
    return {
        'gameWindow': {'monsters': monsters or []},
        'targeting': {
            'canIgnoreCreatures': True,
            'hasIgnorableCreatures': False,
            'creatures': {},
        },
        'tasksOrchestrator': orchestrator,
    }


def test_has_creatures_to_attack_returns_false_without_monsters():
    context = make_context()

    assert hasCreaturesToAttack(context) is False
    assert context['targeting']['canIgnoreCreatures'] is True
    assert context['targeting']['hasIgnorableCreatures'] is False


def test_has_creatures_to_attack_returns_false_when_all_monsters_are_ignored():
    context = make_context([{'name': 'Rat'}, {'name': 'Snake'}])
    context['targeting']['creatures'] = {
        'Rat': {'ignore': True},
        'Snake': {'ignore': True},
    }

    assert hasCreaturesToAttack(context) is False
    assert context['targeting']['hasIgnorableCreatures'] is True


def test_has_creatures_to_attack_returns_true_when_one_monster_is_valid():
    context = make_context([{'name': 'Rat'}, {'name': 'Snake'}])
    context['targeting']['creatures'] = {
        'Rat': {'ignore': True},
        'Snake': {'ignore': False},
    }

    assert hasCreaturesToAttack(context) is True
    assert context['targeting']['hasIgnorableCreatures'] is True


def test_should_ask_for_targeting_when_orchestrator_is_idle():
    context = make_context()

    assert shouldAskForTargetingTasks(context) is True


def test_should_not_interrupt_protected_task():
    context = make_context()
    currentTask = MagicMock()
    currentTask.name = 'lootCorpse'
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask

    assert shouldAskForTargetingTasks(context) is False


def test_should_interrupt_waypoint_task():
    context = make_context()
    currentTask = MagicMock()
    currentTask.name = 'walkToWaypoint'
    context['tasksOrchestrator'].getCurrentTask.return_value = currentTask

    assert shouldAskForTargetingTasks(context) is True


def test_resolve_targeting_preserves_original_resolver(monkeypatch):
    context = make_context()
    originalResolver = MagicMock(return_value=context)
    monkeypatch.setattr(
        'src.gameplay.targeting.resolveCavebotTasks', originalResolver)

    assert resolveTargetingTasks(context, allowChase=True) is context
    originalResolver.assert_called_once_with(context, allowChase=True)
