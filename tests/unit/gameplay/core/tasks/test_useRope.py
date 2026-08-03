from src.gameplay.core.tasks.useRope import UseRopeTask


def test_should_test_default_params():
    waypoint = ('', 'walk', (0, 0, 0), {})
    task = UseRopeTask(waypoint)
    assert task.name == 'useRope'
    assert task.delayBeforeStart == 1
    assert task.delayAfterComplete == 1
    assert task.waypoint == waypoint
    assert task.inputSent is False


def make_context(coordinate=(7, 7, 9)):
    return {
        'gameWindow': {'coordinate': (1, 2, 3)},
        'radar': {'coordinate': coordinate},
        'cavebot': {'ropeHotkey': '-'},
    }


def test_should_do(mocker):
    context = make_context()
    waypoint = {'coordinate': (7, 8, 9)}
    task = UseRopeTask(waypoint)
    slot = (0, 0)
    getSlotFromCoordinateSpy = mocker.patch(
        'src.repositories.gameWindow.core.getSlotFromCoordinate', return_value=slot)
    clickSlotSpy = mocker.patch('src.repositories.gameWindow.slot.clickSlot')
    pressSpy = mocker.patch('src.utils.keyboard.press')

    assert task.do(context) == context

    assert task.inputSent is True
    getSlotFromCoordinateSpy.assert_called_with(
        context['radar']['coordinate'], waypoint['coordinate'])
    clickSlotSpy.assert_called_once_with(
        slot, context['gameWindow']['coordinate'])
    pressSpy.assert_called_once_with('-')


def test_did_and_should_ignore_require_expected_floor():
    task = UseRopeTask({'coordinate': (7, 8, 9)})

    assert task.did(make_context(None)) is False
    assert task.did(make_context((7, 7, 9))) is False
    assert task.shouldIgnore(make_context((7, 7, 9))) is False
    assert task.did(make_context((20, 20, 8))) is True
    assert task.shouldIgnore(make_context((20, 20, 8))) is True


def test_does_not_send_input_without_radar(mocker):
    task = UseRopeTask({'coordinate': (7, 8, 9)})
    pressSpy = mocker.patch('src.utils.keyboard.press')
    clickSlotSpy = mocker.patch('src.repositories.gameWindow.slot.clickSlot')

    assert task.do(make_context(None)) == make_context(None)

    assert task.inputSent is False
    pressSpy.assert_not_called()
    clickSlotSpy.assert_not_called()


def test_does_not_send_input_on_wrong_floor(mocker):
    task = UseRopeTask({'coordinate': (7, 8, 9)})
    pressSpy = mocker.patch('src.utils.keyboard.press')
    clickSlotSpy = mocker.patch('src.repositories.gameWindow.slot.clickSlot')

    task.do(make_context((7, 7, 10)))

    assert task.inputSent is False
    pressSpy.assert_not_called()
    clickSlotSpy.assert_not_called()


def test_does_not_send_input_far_from_rope(mocker):
    task = UseRopeTask({'coordinate': (7, 8, 9)})
    getSlotFromCoordinateSpy = mocker.patch(
        'src.repositories.gameWindow.core.getSlotFromCoordinate')
    pressSpy = mocker.patch('src.utils.keyboard.press')

    task.do(make_context((10, 10, 9)))

    assert task.inputSent is False
    getSlotFromCoordinateSpy.assert_not_called()
    pressSpy.assert_not_called()


def test_does_not_send_input_when_slot_is_invalid(mocker):
    task = UseRopeTask({'coordinate': (7, 8, 9)})
    mocker.patch(
        'src.repositories.gameWindow.core.getSlotFromCoordinate',
        return_value=None,
    )
    pressSpy = mocker.patch('src.utils.keyboard.press')
    clickSlotSpy = mocker.patch('src.repositories.gameWindow.slot.clickSlot')

    task.do(make_context())

    assert task.inputSent is False
    pressSpy.assert_not_called()
    clickSlotSpy.assert_not_called()


def test_should_restart_only_before_input_when_position_becomes_valid(mocker):
    task = UseRopeTask({'coordinate': (7, 8, 9)})
    mocker.patch(
        'src.repositories.gameWindow.core.getSlotFromCoordinate',
        return_value=(7, 6),
    )

    assert task.shouldRestart(make_context(None)) is False
    assert task.shouldRestart(make_context((10, 10, 9))) is False
    assert task.shouldRestart(make_context()) is True

    task.inputSent = True
    assert task.shouldRestart(make_context()) is False
