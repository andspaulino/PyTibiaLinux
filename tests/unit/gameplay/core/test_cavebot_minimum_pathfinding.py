from types import SimpleNamespace

import numpy as np
import pytest

from src.gameplay.core import waypoint
from src.gameplay.core.tasks.walk import WalkTask
from src.gameplay.core.tasks.walkToCoordinate import WalkToCoordinateTask


def install_floor(monkeypatch, floor=None):
    if floor is None:
        floor = np.ones((109, 106), dtype=np.uint8)
    floors = np.expand_dims(floor, axis=0)
    monkeypatch.setattr(waypoint, "walkableFloorsSqms", floors)
    monkeypatch.setattr(waypoint, "getPixelFromCoordinate", lambda coordinate: coordinate[:2])
    class FakeWalkTask:
        def __init__(self, _context, coordinate):
            self.walkpoint = coordinate

        def setParentTask(self, parentTask):
            self.parentTask = parentTask
            return self

        def setRootTask(self, rootTask):
            self.rootTask = rootTask
            return self

    monkeypatch.setattr(
        "src.gameplay.core.tasks.walkToCoordinate.WalkTask", FakeWalkTask
    )
    return floors


def make_context(coordinate=(53, 54, 0)):
    return {
        "cavebot": {
            "holesOrStairs": [],
            "navigation": {},
        },
        "gameWindow": {"monsters": []},
        "lastPressedKey": None,
        "radar": {
            "coordinate": coordinate,
            "lastCoordinateVisited": coordinate,
        },
    }


def test_calculate_floor_walkpoints_supports_horizontal_vertical_and_diagonal(monkeypatch):
    install_floor(monkeypatch)
    origin = (53, 54, 0)

    horizontal, horizontal_failure = waypoint.calculateFloorWalkpoints(
        origin, (56, 54, 0)
    )
    vertical, vertical_failure = waypoint.calculateFloorWalkpoints(
        origin, (53, 57, 0)
    )
    diagonal, diagonal_failure = waypoint.calculateFloorWalkpoints(
        origin, (56, 57, 0)
    )

    assert horizontal_failure is None
    assert horizontal[-1] == [56, 54, 0]
    assert vertical_failure is None
    assert vertical[-1] == [53, 57, 0]
    assert diagonal_failure is None
    assert diagonal[-1] == [56, 57, 0]


def test_calculate_floor_walkpoints_rejects_invalid_inputs(monkeypatch):
    install_floor(monkeypatch)

    assert waypoint.calculateFloorWalkpoints(None, (53, 54, 0))[1] == "coordinate-unavailable"
    assert waypoint.calculateFloorWalkpoints((53, 54, 0), None)[1] == "coordinate-unavailable"
    assert waypoint.calculateFloorWalkpoints((53, 54, 0), (53, 54, 1))[1] == "different-floor"
    assert waypoint.calculateFloorWalkpoints((53, 54, 2), (54, 54, 2))[1] == "floor-out-of-bounds"
    assert waypoint.calculateFloorWalkpoints((53, 54, 0), (107, 54, 0))[1] == "goal-out-of-atlas"


def test_calculate_floor_walkpoints_rejects_goal_outside_local_window(monkeypatch):
    floor = np.ones((218, 212), dtype=np.uint8)
    floors = np.expand_dims(floor, axis=0)
    monkeypatch.setattr(waypoint, "walkableFloorsSqms", floors)
    monkeypatch.setattr(waypoint, "getPixelFromCoordinate", lambda coordinate: coordinate[:2])

    walkpoints, failure = waypoint.calculateFloorWalkpoints(
        (106, 109, 0),
        (160, 109, 0),
    )

    assert walkpoints == []
    assert failure == "goal-out-of-local-window"


def test_calculate_floor_walkpoints_does_not_modify_global_matrix(monkeypatch):
    floors = install_floor(monkeypatch)
    original = floors.copy()

    walkpoints, failure = waypoint.calculateFloorWalkpoints(
        (53, 54, 0),
        (55, 54, 0),
        nonWalkableCoordinates=[(54, 54, 0)],
    )

    assert failure is None
    assert walkpoints[-1] == [55, 54, 0]
    np.testing.assert_array_equal(floors, original)


def test_calculate_floor_walkpoints_reports_path_not_found(monkeypatch):
    floor = np.ones((109, 106), dtype=np.uint8)
    floor[:, 54] = 0
    install_floor(monkeypatch, floor)

    walkpoints, failure = waypoint.calculateFloorWalkpoints(
        (53, 54, 0),
        (55, 54, 0),
    )

    assert walkpoints == []
    assert failure == "path-not-found"


def test_invalid_and_outside_obstacles_are_ignored_safely(monkeypatch):
    install_floor(monkeypatch)

    walkpoints, failure = waypoint.calculateFloorWalkpoints(
        (53, 54, 0),
        (55, 54, 0),
        nonWalkableCoordinates=[None, (500, 500, 0), (54, 54, 1)],
    )

    assert failure is None
    assert walkpoints[-1] == [55, 54, 0]


def test_current_coordinate_is_complete_even_if_atlas_marks_it_blocked(monkeypatch):
    floor = np.ones((109, 106), dtype=np.uint8)
    floor[54, 53] = 0
    install_floor(monkeypatch, floor)

    walkpoints, failure = waypoint.calculateFloorWalkpoints(
        (53, 54, 0),
        (53, 54, 0),
    )

    assert walkpoints == []
    assert failure is None


def test_calculate_floor_walkpoints_rejects_blocked_goal(monkeypatch):
    floor = np.ones((109, 106), dtype=np.uint8)
    floor[54, 55] = 0
    install_floor(monkeypatch, floor)

    walkpoints, failure = waypoint.calculateFloorWalkpoints(
        (53, 54, 0),
        (55, 54, 0),
    )

    assert walkpoints == []
    assert failure == "goal-not-walkable"


def test_walk_to_coordinate_stays_blocked_without_advancing(monkeypatch):
    install_floor(monkeypatch)
    context = make_context()
    task = WalkToCoordinateTask((53, 54, 1))

    task.calculateWalkpoint(context)

    assert task.tasks == []
    assert task.pathfindingFailureReason == "different-floor"
    assert task.did(context) is False
    assert task.shouldRestartAfterAllChildrensComplete(context) is False
    assert context["cavebot"]["navigation"]["status"] == "blocked"
    assert context["cavebot"]["navigation"]["failureReason"] == "different-floor"


def test_walk_to_coordinate_normalizes_and_deduplicates_obstacles():
    context = make_context()
    context["cavebot"]["holesOrStairs"] = [
        (54, 54, 0),
        [54, 54, 0],
        None,
        (54, 54, 1),
        (54, 54),
    ]
    context["gameWindow"]["monsters"] = [
        {"coordinate": (55, 54, 0)},
        {"coordinate": [54, 54, 0]},
        {"coordinate": (55, 54, 1)},
        {"name": "without-coordinate"},
        None,
    ]
    task = WalkToCoordinateTask((56, 54, 0))

    obstacles = task.getNonWalkableCoordinates(context)

    assert obstacles == [(54, 54, 0), (55, 54, 0)]


def test_walk_to_coordinate_initial_route_avoids_static_obstacle(monkeypatch):
    install_floor(monkeypatch)
    context = make_context()
    context["cavebot"]["holesOrStairs"] = [(54, 54, 0)]
    task = WalkToCoordinateTask((55, 54, 0))

    task.calculateWalkpoint(context)

    walkpoints = [tuple(child.walkpoint) for child in task.tasks]
    assert task.pathfindingFailureReason is None
    assert (54, 54, 0) not in walkpoints
    assert walkpoints[-1] == (55, 54, 0)
    assert context["cavebot"]["navigation"]["blockedCoordinates"] == [
        (54, 54, 0)
    ]


def test_walk_to_coordinate_restarts_only_when_obstacles_change(monkeypatch):
    install_floor(monkeypatch)
    context = make_context()
    task = WalkToCoordinateTask((55, 54, 0))
    task.calculateWalkpoint(context)

    assert task.shouldRestart(context) is False

    context["gameWindow"]["monsters"] = [{"coordinate": (54, 54, 0)}]

    assert task.shouldRestart(context) is True
    assert context["cavebot"]["navigation"]["status"] == "recalculating"
    assert context["cavebot"]["navigation"]["failureReason"] == "obstacles-changed"


def test_walk_to_coordinate_recalculates_without_advancing_goal(monkeypatch):
    install_floor(monkeypatch)
    context = make_context()
    task = WalkToCoordinateTask((55, 54, 0))
    task.calculateWalkpoint(context)
    originalWalkpoints = [tuple(child.walkpoint) for child in task.tasks]
    context["gameWindow"]["monsters"] = [{"coordinate": (54, 54, 0)}]
    released = []
    monkeypatch.setattr(
        "src.gameplay.core.tasks.walkToCoordinate.gameplayUtils.releaseKeys",
        lambda current_context: released.append(True) or current_context,
    )

    task.onBeforeRestart(context)

    recalculatedWalkpoints = [tuple(child.walkpoint) for child in task.tasks]
    assert released == [True]
    assert task.coordinate == (55, 54, 0)
    assert task.pathfindingFailureReason is None
    assert originalWalkpoints != recalculatedWalkpoints
    assert (54, 54, 0) not in recalculatedWalkpoints


def test_walk_to_coordinate_recovers_when_blocking_obstacle_is_removed(monkeypatch):
    install_floor(monkeypatch)
    context = make_context()
    context["gameWindow"]["monsters"] = [{"coordinate": (55, 54, 0)}]
    task = WalkToCoordinateTask((55, 54, 0))
    task.calculateWalkpoint(context)

    assert task.tasks == []
    assert task.pathfindingFailureReason == "goal-not-walkable"

    context["gameWindow"]["monsters"] = []
    assert task.shouldRestart(context) is True
    monkeypatch.setattr(
        "src.gameplay.core.tasks.walkToCoordinate.gameplayUtils.releaseKeys",
        lambda current_context: current_context,
    )
    task.onBeforeRestart(context)

    assert task.pathfindingFailureReason is None
    assert [tuple(child.walkpoint) for child in task.tasks][-1] == (55, 54, 0)
    assert context["cavebot"]["navigation"]["status"] == "walking"


@pytest.mark.parametrize(
    ("origin", "goal", "expectedDirection"),
    [
        ((53, 54, 0), (53, 53, 0), "up"),
        ((53, 54, 0), (53, 55, 0), "down"),
        ((53, 54, 0), (52, 54, 0), "left"),
        ((53, 54, 0), (54, 54, 0), "right"),
    ],
)
def test_walk_task_calculates_direction_and_presses_once(
    monkeypatch, origin, goal, expectedDirection
):
    context = make_context(coordinate=origin)
    task = object.__new__(WalkTask)
    task.walkpoint = goal
    task.parentTask = None
    pressed = []
    monkeypatch.setattr("src.gameplay.core.tasks.walk.press", pressed.append)

    task.do(context)

    assert pressed == [expectedDirection]
    assert context["cavebot"]["navigation"]["plannedDirection"] == expectedDirection


def test_walk_task_holds_key_for_multiple_steps_in_same_direction(monkeypatch):
    context = make_context()
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)
    nextTask = SimpleNamespace(walkpoint=(55, 54, 0))
    finalTask = SimpleNamespace(walkpoint=(56, 54, 0))
    task.parentTask = SimpleNamespace(
        tasks=[task, nextTask, finalTask], currentTaskIndex=0
    )
    held = []
    pressed = []
    monkeypatch.setattr("src.gameplay.core.tasks.walk.keyDown", held.append)
    monkeypatch.setattr("src.gameplay.core.tasks.walk.press", pressed.append)

    task.do(context)

    assert held == ["right"]
    assert pressed == []
    assert context["lastPressedKey"] == "right"


def test_walk_task_releases_held_key_before_direction_change(monkeypatch):
    context = make_context()
    context["lastPressedKey"] = "right"
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)
    nextTask = SimpleNamespace(walkpoint=(54, 55, 0))
    task.parentTask = SimpleNamespace(tasks=[task, nextTask], currentTaskIndex=0)
    released = []
    pressed = []
    monkeypatch.setattr(
        "src.gameplay.core.tasks.walk.releaseKeys",
        lambda current_context: (
            released.append(current_context["lastPressedKey"]),
            current_context.__setitem__("lastPressedKey", None),
            current_context,
        )[-1],
    )
    monkeypatch.setattr("src.gameplay.core.tasks.walk.press", pressed.append)

    task.do(context)

    assert released == ["right"]
    assert pressed == []
    assert context["lastPressedKey"] is None


def test_walk_task_releases_held_key_on_final_isolated_step(monkeypatch):
    context = make_context()
    context["lastPressedKey"] = "right"
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)
    task.parentTask = SimpleNamespace(tasks=[task], currentTaskIndex=0)
    released = []
    monkeypatch.setattr(
        "src.gameplay.core.tasks.walk.releaseKeys",
        lambda current_context: (
            released.append(current_context["lastPressedKey"]),
            current_context.__setitem__("lastPressedKey", None),
            current_context,
        )[-1],
    )

    task.do(context)

    assert released == ["right"]
    assert context["lastPressedKey"] is None


def test_walk_task_completion_is_confirmed_only_by_observed_coordinate():
    context = make_context(coordinate=(53, 54, 0))
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)

    assert task.did(context) is False
    context["radar"]["coordinate"] = None
    assert task.did(context) is False
    context["radar"]["coordinate"] = (54, 54, 0)
    assert task.did(context) is True


@pytest.mark.parametrize("hook", ["onInterrupt", "onTimeout"])
def test_walk_task_releases_keys_on_interrupt_and_timeout(monkeypatch, hook):
    context = make_context()
    context["lastPressedKey"] = "right"
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)
    released = []
    monkeypatch.setattr(
        "src.gameplay.core.tasks.walk.releaseKeys",
        lambda current_context: (
            released.append(current_context["lastPressedKey"]),
            current_context.__setitem__("lastPressedKey", None),
            current_context,
        )[-1],
    )

    result = getattr(task, hook)(context)

    assert result is context
    assert released == ["right"]
    assert context["lastPressedKey"] is None
    assert context["cavebot"]["navigation"]["plannedDirection"] is None
    if hook == "onTimeout":
        assert context["cavebot"]["navigation"]["status"] == "blocked"
        assert context["cavebot"]["navigation"]["failureReason"] == "movement-timeout"


def test_walk_task_does_not_send_input_without_coordinate(monkeypatch):
    context = make_context(coordinate=None)
    context["radar"]["lastCoordinateVisited"] = (53, 54, 0)
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)
    task.parentTask = None
    pressed = []
    held = []
    released = []
    monkeypatch.setattr("src.gameplay.core.tasks.walk.press", pressed.append)
    monkeypatch.setattr("src.gameplay.core.tasks.walk.keyDown", held.append)
    monkeypatch.setattr(
        "src.gameplay.core.tasks.walk.releaseKeys",
        lambda current_context: released.append(True) or current_context,
    )

    result = task.do(context)

    assert result is context
    assert pressed == []
    assert held == []
    assert released == [True]
    assert task.shouldIgnore(context) is False
    assert task.did(context) is False
    assert context["cavebot"]["navigation"]["failureReason"] == "coordinate-unavailable"


def test_walk_task_ping_releases_held_key_and_resumes_after_radar_returns(monkeypatch):
    context = make_context(coordinate=None)
    context["lastPressedKey"] = "right"
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)
    task.parentTask = None
    released = []
    resumed = []
    monkeypatch.setattr(
        "src.gameplay.core.tasks.walk.releaseKeys",
        lambda current_context: (
            released.append(current_context["lastPressedKey"]),
            current_context.__setitem__("lastPressedKey", None),
            current_context,
        )[-1],
    )

    task.ping(context)

    assert released == ["right"]
    assert context["lastPressedKey"] is None
    assert context["cavebot"]["navigation"]["status"] == "radar-unavailable"
    assert context["cavebot"]["navigation"]["failureReason"] == "coordinate-unavailable"

    context["radar"]["coordinate"] = (53, 54, 0)
    monkeypatch.setattr(task, "do", lambda current_context: resumed.append(True) or current_context)

    task.ping(context)

    assert resumed == [True]
    assert context["cavebot"]["navigation"]["status"] == "walking"
    assert context["cavebot"]["navigation"]["failureReason"] is None


def test_walk_task_resumes_after_coordinate_returns(monkeypatch):
    context = make_context(coordinate=(53, 54, 0))
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)
    task.parentTask = None
    pressed = []
    monkeypatch.setattr(
        "src.gameplay.core.tasks.walk.getDirectionBetweenCoordinates",
        lambda current, goal: "right",
    )
    monkeypatch.setattr("src.gameplay.core.tasks.walk.press", pressed.append)

    result = task.do(context)

    assert result is context
    assert pressed == ["right"]
    assert task.did(context) is False
    assert context["cavebot"]["navigation"]["plannedDirection"] == "right"
