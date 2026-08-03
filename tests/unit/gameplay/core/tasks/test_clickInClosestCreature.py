from src.gameplay.core.tasks.clickInClosestCreature import ClickInClosestCreatureTask


def test_should_test_default_params():
    task = ClickInClosestCreatureTask()
    assert task.name == 'clickInClosestCreature'
    assert task.delayOfTimeout == 1

def test_should_method_shouldIgnore_return_False_when_has_no_target_creature():
    context = {'cavebot': {'targetCreature': None}}
    task = ClickInClosestCreatureTask()
    assert task.shouldIgnore(context) == False

def test_should_method_shouldIgnore_return_True_when_has_target_creature():
    context = {'cavebot': {'targetCreature': ('Dragon', 'monster', True, (0, 0), (0, 0, 0), (0, 0), (0, 0), False)}}
    task = ClickInClosestCreatureTask()
    assert task.shouldIgnore(context) == True


def test_should_not_ignore_when_current_target_differs_from_reachable_candidate():
    context = {
        'cavebot': {
            'targetCreature': {'coordinate': [100, 100, 7]},
            'closestCreature': {'coordinate': [101, 100, 7]},
        },
    }
    task = ClickInClosestCreatureTask()

    assert task.shouldIgnore(context) is False


def test_should_ignore_when_current_target_matches_reachable_candidate():
    context = {
        'cavebot': {
            'targetCreature': {'coordinate': [100, 100, 7]},
            'closestCreature': {'coordinate': [100, 100, 7]},
        },
    }
    task = ClickInClosestCreatureTask()

    assert task.shouldIgnore(context) is True

def test_should_method_did_return_False_when_is_not_attacking_some_creature():
    context = {'cavebot': {'isAttackingSomeCreature': False}}
    task = ClickInClosestCreatureTask()
    assert task.did(context) == False

def test_should_method_did_return_True_when_is_attacking_some_creature():
    context = {'cavebot': {'isAttackingSomeCreature': True}}
    task = ClickInClosestCreatureTask()
    assert task.did(context) == True


def test_did_waits_until_reachable_candidate_becomes_current_target():
    context = {
        'cavebot': {
            'isAttackingSomeCreature': True,
            'targetCreature': {'coordinate': [100, 100, 7]},
            'closestCreature': {'coordinate': [101, 100, 7]},
        },
    }
    task = ClickInClosestCreatureTask()

    assert task.did(context) is False

    context['cavebot']['targetCreature'] = {
        'coordinate': [101, 100, 7],
    }

    assert task.did(context) is True

def test_should_do_and_ignore_hotkey_attack_when_there_are_players(mocker):
    context = {
        'cavebot': {'closestCreature': {'windowCoordinate': (0, 0)}},
        'gameWindow': {'players': [('Bubble', 'player', True, (0, 0), (0, 0, 0), (0, 0), (0, 0), False)]}
    }
    keyDownSpy = mocker.patch('src.utils.keyboard.keyDown')
    keyUpSpy = mocker.patch('src.utils.keyboard.keyUp')
    pressSpy = mocker.patch('src.utils.keyboard.press')
    leftClickSpy = mocker.patch('src.utils.mouse.leftClick')
    task = ClickInClosestCreatureTask()
    assert task.do(context) == context
    keyDownSpy.assert_called_once_with('alt')
    leftClickSpy.assert_called_once_with(context['cavebot']['closestCreature']['windowCoordinate'])
    keyUpSpy.assert_called_once_with('alt')
    pressSpy.assert_not_called()

def test_should_do_and_ignore_hotkey_attack_when_there_ignorable_creatures(mocker):
    context = {
        'cavebot': {'closestCreature': {'windowCoordinate': (0, 0)}},
        'gameWindow': {'players': []},
        'targeting': {'hasIgnorableCreatures': True}
    }
    keyDownSpy = mocker.patch('src.utils.keyboard.keyDown')
    keyUpSpy = mocker.patch('src.utils.keyboard.keyUp')
    pressSpy = mocker.patch('src.utils.keyboard.press')
    leftClickSpy = mocker.patch('src.utils.mouse.leftClick')
    task = ClickInClosestCreatureTask()
    assert task.do(context) == context
    keyDownSpy.assert_called_once_with('alt')
    leftClickSpy.assert_called_once_with(context['cavebot']['closestCreature']['windowCoordinate'])
    keyUpSpy.assert_called_once_with('alt')
    pressSpy.assert_not_called()

def test_should_click_reachable_candidate_when_there_are_no_players_or_ignorable_creatures(mocker):
    context = {
        'cavebot': {'closestCreature': {'windowCoordinate': (0, 0)}},
        'gameWindow': {'players': []},
        'targeting': {'hasIgnorableCreatures': False}
    }
    keyDownSpy = mocker.patch('src.utils.keyboard.keyDown')
    keyUpSpy = mocker.patch('src.utils.keyboard.keyUp')
    pressSpy = mocker.patch('src.utils.keyboard.press')
    leftClickSpy = mocker.patch('src.utils.mouse.leftClick')
    task = ClickInClosestCreatureTask()

    assert task.do(context) == context

    keyDownSpy.assert_called_once_with('alt')
    leftClickSpy.assert_called_once_with((0, 0))
    keyUpSpy.assert_called_once_with('alt')
    pressSpy.assert_not_called()
