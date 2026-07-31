from src.gameplay.core.tasks.useTeleportWaypoint import UseTeleportWaypointTask
from src.gameplay.core.tasks.rightClickInCoordinate import RightClickInCoordinateTask
from src.gameplay.core.tasks.setNextWaypoint import SetNextWaypointTask


def test_should_test_default_params():
    waypoint = {'coordinate': (100, 100, 7), 'type': 'useTeleport'}
    task = UseTeleportWaypointTask(waypoint)
    assert task.name == 'useTeleportWaypoint'
    assert task.isRootTask is True
    assert task.waypoint == waypoint


def test_should_onBeforeStart():
    context = {'radar': {'coordinate': (100, 100, 7)}}
    waypoint = {'coordinate': (100, 100, 7), 'type': 'useTeleport'}
    task = UseTeleportWaypointTask(waypoint)
    
    res = task.onBeforeStart(context)
    assert res == context
    assert len(task.tasks) == 2
    assert isinstance(task.tasks[0], RightClickInCoordinateTask)
    assert isinstance(task.tasks[1], SetNextWaypointTask)
