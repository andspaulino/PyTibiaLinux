from src.gameplay.core.tasks.singleWalk import SingleWalkTask
from src.gameplay.core.tasks.moveDown import MoveDown
from src.gameplay.core.tasks.moveUp import MoveUp
from src.gameplay.core.tasks.setNextWaypoint import SetNextWaypointTask


def test_should_test_default_params():
    task = SingleWalkTask('moveDown', 'south')
    assert task.name == 'singleWalk'
    assert task.isRootTask is True
    assert task.delayAfterComplete == 2
    assert task.direction == 'south'
    assert task.waypointType == 'moveDown'


def test_should_onBeforeStart_moveDown():
    context = {'radar': {'coordinate': (100, 100, 7)}}
    task = SingleWalkTask('moveDown', 'south')
    
    res = task.onBeforeStart(context)
    assert res == context
    assert len(task.tasks) == 2
    assert isinstance(task.tasks[0], MoveDown)
    assert isinstance(task.tasks[1], SetNextWaypointTask)


def test_should_onBeforeStart_moveUp():
    context = {'radar': {'coordinate': (100, 100, 7)}}
    task = SingleWalkTask('moveUp', 'north')
    
    res = task.onBeforeStart(context)
    assert res == context
    assert len(task.tasks) == 2
    assert isinstance(task.tasks[0], MoveUp)
    assert isinstance(task.tasks[1], SetNextWaypointTask)
