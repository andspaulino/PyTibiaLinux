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
