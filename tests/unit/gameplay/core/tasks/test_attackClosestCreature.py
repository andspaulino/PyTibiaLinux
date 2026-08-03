from src.gameplay.core.tasks import walkToTargetCreature as walk_task_module
from src.gameplay.core.tasks.attackClosestCreature import AttackClosestCreatureTask
from src.gameplay.core.tasks.clickInClosestCreature import ClickInClosestCreatureTask
from src.gameplay.core.tasks.walkToTargetCreature import WalkToTargetCreatureTask


context = {'cavebot': {'isAttackingSomeCreature': False}}

def test_should_test_default_params():
    task = AttackClosestCreatureTask()
    assert task.name == 'attackClosestCreature'
    assert task.isRootTask == 1

def test_onBeforeStart_without_walking_to_target():
    task = AttackClosestCreatureTask(allowChase=False)
    assert task.onBeforeStart(context) == context
    assert len(task.tasks) == 1
    assert isinstance(task.tasks[0], ClickInClosestCreatureTask)
    assert task.tasks[0].parentTask == task
    assert task.tasks[0].rootTask == task
    assert task.allowChase is False
    assert task.manuallyTerminable is True


def test_selection_only_root_completes_only_after_combat_ends():
    task = AttackClosestCreatureTask(allowChase=False)
    task.onBeforeStart(context)

    assert task.shouldManuallyComplete(context) is False
    context['cavebot']['isAttackingSomeCreature'] = True
    assert task.shouldManuallyComplete(context) is False
    context['cavebot']['isAttackingSomeCreature'] = False
    assert task.shouldManuallyComplete(context) is True


def test_onBeforeStart_with_walking_to_target():
    task = AttackClosestCreatureTask(allowChase=True)
    assert task.onBeforeStart(context) == context
    assert len(task.tasks) == 2
    assert isinstance(task.tasks[0], ClickInClosestCreatureTask)
    assert isinstance(task.tasks[1], WalkToTargetCreatureTask)
    assert task.tasks[1].parentTask == task
    assert task.tasks[1].rootTask == task
    assert task.allowChase is True
    assert task.manuallyTerminable is False


def test_walkToTargetCreature_shouldRestart_tolerance():
    task = WalkToTargetCreatureTask()
    # A target that appears after an unavailable frame starts path calculation.
    assert task.shouldRestart({
        'cavebot': {'targetCreature': {'coordinate': [10, 10, 7]}},
    }) is True

    # Simulate active tasks in progress.
    task.tasks = ['mock_walk_task']
    task.targetCreatureCoordinateSinceLastRestart = [10, 10, 7]

    # Grid shifts of up to 2 SQMs per axis do not restart.
    ctx_1sqm = {
        'cavebot': {'targetCreature': {'coordinate': [10, 11, 7]}},
    }
    assert task.shouldRestart(ctx_1sqm) is False
    ctx_1x2sqm = {
        'cavebot': {'targetCreature': {'coordinate': [11, 12, 7]}},
    }
    assert task.shouldRestart(ctx_1x2sqm) is False
    ctx_2x2sqm = {
        'cavebot': {'targetCreature': {'coordinate': [12, 12, 7]}},
    }
    assert task.shouldRestart(ctx_2x2sqm) is False

    # Target shift of > 2 SQMs on one axis -> SHOULD restart.
    ctx_3sqm = {
        'cavebot': {'targetCreature': {'coordinate': [10, 13, 7]}},
    }
    assert task.shouldRestart(ctx_3sqm) is True


def test_walk_to_target_keeps_current_path_when_target_is_temporarily_missing():
    task = WalkToTargetCreatureTask()
    task.tasks = ['mock_walk_task']
    task.targetCreatureCoordinateSinceLastRestart = [10, 10, 7]

    shouldRestart = task.shouldRestart({
        'cavebot': {
            'isAttackingSomeCreature': True,
            'targetCreature': None,
        },
    })

    assert shouldRestart is False
    assert task.tasks == ['mock_walk_task']


def test_walk_to_target_does_not_restart_when_target_is_adjacent():
    task = WalkToTargetCreatureTask()
    task.tasks = []
    task.targetCreatureCoordinateSinceLastRestart = [10, 10, 7]

    shouldRestart = task.shouldRestart({
        'cavebot': {'targetCreature': {'coordinate': [10, 10, 7]}},
        'radar': {'coordinate': [11, 11, 7]},
    })

    assert shouldRestart is False


def test_walk_to_target_throttles_empty_distant_path(monkeypatch):
    task = WalkToTargetCreatureTask()
    task.tasks = []
    task.targetCreatureCoordinateSinceLastRestart = [10, 10, 7]
    task.nextPathRetryAt = 10.25
    context = {
        'cavebot': {'targetCreature': {'coordinate': [10, 10, 7]}},
        'radar': {'coordinate': [15, 15, 7]},
    }

    monkeypatch.setattr(walk_task_module, 'time', lambda: 10.24)
    assert task.shouldRestart(context) is False

    monkeypatch.setattr(walk_task_module, 'time', lambda: 10.25)
    assert task.shouldRestart(context) is True


def test_walk_to_target_does_not_clear_path_if_target_disappears_before_start():
    task = WalkToTargetCreatureTask()
    task.tasks = ['existing_walk_task']
    context = {'cavebot': {'targetCreature': None}}

    task.calculatePathToTargetCreature(context)

    assert task.tasks == ['existing_walk_task']

