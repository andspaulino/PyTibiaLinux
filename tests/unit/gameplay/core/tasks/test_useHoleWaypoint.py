from src.gameplay.core.tasks.useHole import UseHoleTask
from src.gameplay.core.tasks.useHoleWaypoint import UseHoleWaypointTask
from src.gameplay.core.tasks.setNextWaypoint import SetNextWaypointTask


def test_should_test_default_params():
    waypoint = {'coordinate': (100, 100, 7), 'type': 'useHole'}
    task = UseHoleWaypointTask(waypoint)
    assert task.name == 'useHoleWaypoint'
    assert task.isRootTask is True
    assert task.waypoint == waypoint


def test_should_onBeforeStart():
    context = {'radar': {'coordinate': (100, 100, 7)}}
    waypoint = {'coordinate': (100, 100, 7), 'type': 'useHole'}
    task = UseHoleWaypointTask(waypoint)

    res = task.onBeforeStart(context)
    assert res == context
    assert len(task.tasks) == 2
    assert isinstance(task.tasks[0], UseHoleTask)
    assert isinstance(task.tasks[1], SetNextWaypointTask)
