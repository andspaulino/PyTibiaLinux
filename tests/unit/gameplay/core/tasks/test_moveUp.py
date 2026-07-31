from src.gameplay.core.tasks.moveUp import MoveUp


def test_should_test_default_params():
    context = {'radar': {'coordinate': (100, 100, 7)}}
    task = MoveUp(context, 'north')
    assert task.name == 'moveUp'
    assert task.isRootTask is True
    assert task.direction == 'north'
    assert task.floorLevel == 6


def test_should_do(mocker):
    context = {'radar': {'coordinate': (100, 100, 7)}}
    task = MoveUp(context, 'north')
    pressSpy = mocker.patch('src.gameplay.core.tasks.moveUp.press')
    
    res = task.do(context)
    assert res == context
    pressSpy.assert_called_once_with('up')


def test_should_did():
    context = {'radar': {'coordinate': (100, 100, 7)}}
    task = MoveUp(context, 'north')
    assert task.did(context) is False

    context['radar']['coordinate'] = (100, 100, 6)
    assert task.did(context) is True
