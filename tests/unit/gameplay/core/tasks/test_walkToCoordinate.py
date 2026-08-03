from src.gameplay.core.tasks.walkToCoordinate import WalkToCoordinateTask


context = {
    'radar': {'coordinate': (1, 2, 3)},
    'lastPressedKey': None,
}
coordinate = (4, 5, 6)


def make_context(current_coordinate=(1, 2, 3)):
    return {
        'radar': {'coordinate': current_coordinate},
        'cavebot': {'holesOrStairs': []},
        'gameWindow': {'monsters': []},
        'lastPressedKey': None,
    }

def test_should_test_default_params():
    task = WalkToCoordinateTask(coordinate)
    assert task.name == 'walkToCoordinate'
    assert task.coordinate == coordinate
    assert task.navigationState == 'uninitialized'

def test_should_method_onBeforeStart_call_calculateWalkpoint(mocker):
    task = WalkToCoordinateTask(coordinate)
    calculateWalkpointSpy = mocker.patch.object(task, 'calculateWalkpoint')
    assert task.onBeforeStart(context) == context
    calculateWalkpointSpy.assert_called_once_with(context)

def test_should_method_onBeforeRestart_call_onBeforeStart(mocker):
    task = WalkToCoordinateTask(coordinate)
    onBeforeStartSpy = mocker.patch.object(task, 'onBeforeStart', return_value=context)
    assert task.onBeforeRestart(context) == context
    onBeforeStartSpy.assert_called_once_with(context)

def test_should_method_onComplete_call_releaseKeys(mocker):
    task = WalkToCoordinateTask(coordinate)
    releaseKeysSpy = mocker.patch('src.gameplay.utils.releaseKeys', return_value=context)
    assert task.onComplete(context) == context
    releaseKeysSpy.assert_called_once_with(context)

def test_should_call_onComplete(mocker):
    task = WalkToCoordinateTask(coordinate)
    releaseKeysSpy = mocker.patch('src.gameplay.utils.releaseKeys', return_value=context)
    assert task.onComplete(context) == context
    releaseKeysSpy.assert_called_once_with(context)

def test_should_method_onInterrupt_call_releaseKeys(mocker):
    task = WalkToCoordinateTask(coordinate)
    releaseKeysSpy = mocker.patch('src.gameplay.utils.releaseKeys', return_value=context)
    assert task.onInterrupt(context) == context
    releaseKeysSpy.assert_called_once_with(context)

def test_should_method_shouldRestartAfterAllChildrensComplete_return_True_when_there_are_no_tasks(mocker):
    task = WalkToCoordinateTask(coordinate)
    coordinatesAreEqualSpy = mocker.patch('src.gameplay.utils.coordinatesAreEqual')
    assert task.shouldRestartAfterAllChildrensComplete(context) == True
    coordinatesAreEqualSpy.assert_not_called()

def test_should_method_shouldRestartAfterAllChildrensComplete_return_True_when_coordinates_are_different(mocker):
    task = WalkToCoordinateTask(coordinate)
    task.tasks = [1]
    coordinatesAreEqualSpy = mocker.patch('src.gameplay.utils.coordinatesAreEqual', return_value=False)
    assert task.shouldRestartAfterAllChildrensComplete(context) == True
    coordinatesAreEqualSpy.assert_called_once_with(context['radar']['coordinate'], coordinate)

def test_should_method_shouldRestartAfterAllChildrensComplete_return_False_when_coordinates_are_equal(mocker):
    task = WalkToCoordinateTask(coordinate)
    task.tasks = [1]
    coordinatesAreEqualSpy = mocker.patch('src.gameplay.utils.coordinatesAreEqual', return_value=True)
    assert task.shouldRestartAfterAllChildrensComplete(context) == False
    coordinatesAreEqualSpy.assert_called_once_with(context['radar']['coordinate'], coordinate)


def test_did_requires_observed_destination():
    task = WalkToCoordinateTask((4, 5, 6))

    assert task.did(make_context(None)) is False
    assert task.did(make_context((4, 5, 5))) is False
    assert task.did(make_context((4, 5, 6))) is True


def test_calculate_walkpoint_marks_radar_unavailable_without_pathfinding(mocker):
    task = WalkToCoordinateTask((4, 5, 6))
    generateWalkpointsSpy = mocker.patch(
        'src.gameplay.core.tasks.walkToCoordinate.generateFloorWalkpoints'
    )

    task.calculateWalkpoint(make_context(None))

    assert task.navigationState == 'radar-unavailable'
    assert task.tasks == []
    generateWalkpointsSpy.assert_not_called()


def test_radar_transition_restarts_only_when_availability_changes():
    task = WalkToCoordinateTask((4, 5, 6))
    task.navigationState = 'path-available'

    assert task.shouldRestart(make_context(None)) is True

    task.navigationState = 'radar-unavailable'
    assert task.shouldRestart(make_context(None)) is False
    assert task.shouldRestart(make_context((1, 2, 3))) is True


def test_restored_radar_recalculates_path(mocker):
    task = WalkToCoordinateTask((4, 2, 3))
    task.navigationState = 'radar-unavailable'
    walkTask = mocker.patch(
        'src.gameplay.core.tasks.walkToCoordinate.WalkTask'
    )
    child = object()
    walkTask.return_value.setParentTask.return_value.setRootTask.return_value = child
    generateWalkpointsSpy = mocker.patch(
        'src.gameplay.core.tasks.walkToCoordinate.generateFloorWalkpoints',
        return_value=[(2, 2, 3), (3, 2, 3), (4, 2, 3)],
    )
    currentContext = make_context((1, 2, 3))

    assert task.shouldRestart(currentContext) is True
    task.onBeforeRestart(currentContext)

    assert task.navigationState == 'path-available'
    assert task.tasks == [child, child, child]
    generateWalkpointsSpy.assert_called_once_with(
        (1, 2, 3),
        (4, 2, 3),
        nonWalkableCoordinates=[],
    )


def test_empty_path_stays_blocked_without_restart_per_frame(mocker):
    task = WalkToCoordinateTask((4, 2, 3))
    generateWalkpointsSpy = mocker.patch(
        'src.gameplay.core.tasks.walkToCoordinate.generateFloorWalkpoints',
        return_value=[],
    )
    currentContext = make_context((1, 2, 3))

    task.calculateWalkpoint(currentContext)

    assert task.navigationState == 'path-not-found'
    assert task.tasks == []
    assert task.did(currentContext) is False
    assert task.shouldRestart(currentContext) is False
    generateWalkpointsSpy.assert_called_once()


def test_current_destination_is_arrived_without_pathfinding(mocker):
    task = WalkToCoordinateTask((4, 5, 6))
    generateWalkpointsSpy = mocker.patch(
        'src.gameplay.core.tasks.walkToCoordinate.generateFloorWalkpoints'
    )
    currentContext = make_context((4, 5, 6))

    task.calculateWalkpoint(currentContext)

    assert task.navigationState == 'arrived'
    assert task.tasks == []
    assert task.did(currentContext) is True
    generateWalkpointsSpy.assert_not_called()


def test_wrong_floor_does_not_run_pathfinding_or_complete(mocker):
    task = WalkToCoordinateTask((4, 5, 6))
    generateWalkpointsSpy = mocker.patch(
        'src.gameplay.core.tasks.walkToCoordinate.generateFloorWalkpoints'
    )
    currentContext = make_context((4, 5, 7))

    task.calculateWalkpoint(currentContext)

    assert task.navigationState == 'wrong-floor'
    assert task.tasks == []
    assert task.did(currentContext) is False
    generateWalkpointsSpy.assert_not_called()


def test_invalid_target_does_not_run_pathfinding(mocker):
    task = WalkToCoordinateTask(None)
    generateWalkpointsSpy = mocker.patch(
        'src.gameplay.core.tasks.walkToCoordinate.generateFloorWalkpoints'
    )
    currentContext = make_context((1, 2, 3))

    task.calculateWalkpoint(currentContext)

    assert task.navigationState == 'invalid-target'
    assert task.tasks == []
    generateWalkpointsSpy.assert_not_called()


def test_on_before_restart_releases_keys_before_recalculating(mocker):
    events = []
    task = WalkToCoordinateTask((4, 5, 6))
    releaseKeysSpy = mocker.patch(
        'src.gameplay.utils.releaseKeys',
        side_effect=lambda currentContext: events.append('release') or currentContext,
    )
    onBeforeStartSpy = mocker.patch.object(
        task,
        'onBeforeStart',
        side_effect=lambda currentContext: events.append('recalculate') or currentContext,
    )
    currentContext = make_context((1, 2, 3))

    assert task.onBeforeRestart(currentContext) == currentContext
    assert events == ['release', 'recalculate']
    releaseKeysSpy.assert_called_once_with(currentContext)
    onBeforeStartSpy.assert_called_once_with(currentContext)
