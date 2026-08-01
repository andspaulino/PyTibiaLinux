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
    # When tasks list is empty -> should restart
    assert task.shouldRestart({'cavebot': {'targetCreature': {'coordinate': [10, 10, 7]}}}) is True

    # Simulate active tasks in progress
    task.tasks = ['mock_walk_task']
    task.targetCreatureCoordinateSinceLastRestart = [10, 10, 7]

    # Target shift of 1 SQM -> should NOT restart (tolerates micro-movements)
    ctx_1sqm = {'cavebot': {'targetCreature': {'coordinate': [10, 11, 7]}}}
    assert task.shouldRestart(ctx_1sqm) is False

    # Target shift of > 2 SQM -> SHOULD restart
    ctx_3sqm = {'cavebot': {'targetCreature': {'coordinate': [10, 14, 7]}}}
    assert task.shouldRestart(ctx_3sqm) is True

