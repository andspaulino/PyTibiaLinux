from src.gameplay.core.tasks.moveDown import MoveDown


def test_should_test_default_params():
    context = {'radar': {'coordinate': (100, 100, 7)}}
    task = MoveDown(context, 'south')
    assert task.name == 'moveDown'
    assert task.isRootTask is True
    assert task.direction == 'south'
    assert task.floorLevel == 8


def test_should_do(mocker):
    context = {'radar': {'coordinate': (100, 100, 7)}}
    task = MoveDown(context, 'south')
    pressSpy = mocker.patch('src.gameplay.core.tasks.moveDown.press')
    
    res = task.do(context)
    assert res == context
    pressSpy.assert_called_once_with('down')


def test_should_did():
    context = {'radar': {'coordinate': (100, 100, 7)}}
    task = MoveDown(context, 'south')
    assert task.did(context) is False

    context['radar']['coordinate'] = (100, 100, 8)
    assert task.did(context) is True
