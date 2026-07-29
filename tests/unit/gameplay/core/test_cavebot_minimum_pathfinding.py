import numpy as np

from src.gameplay.core import waypoint
from src.gameplay.core.tasks.walk import WalkTask
from src.gameplay.core.tasks.walkToCoordinate import WalkToCoordinateTask


def install_floor(monkeypatch, floor=None):
    if floor is None:
        floor = np.ones((109, 106), dtype=np.uint8)
    floors = np.expand_dims(floor, axis=0)
    monkeypatch.setattr(waypoint, "walkableFloorsSqms", floors)
    monkeypatch.setattr(waypoint, "getPixelFromCoordinate", lambda coordinate: coordinate[:2])
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


def test_walk_task_does_not_send_input_without_coordinate(monkeypatch):
    context = make_context(coordinate=None)
    task = object.__new__(WalkTask)
    task.walkpoint = (54, 54, 0)
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
    assert context["cavebot"]["navigation"]["failureReason"] == "coordinate-unavailable"
