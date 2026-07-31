from types import SimpleNamespace
from unittest.mock import MagicMock

from src.gameplay.lootDiagnostics import printLootDiagnostic


def test_loot_diagnostic_reads_task_tree_without_running_lifecycle(capsys):
    childTask = SimpleNamespace(name='walk', rootTask=None)
    rootTask = SimpleNamespace(
        name='attackClosestCreature',
        allowChase=True,
        tasks=[childTask],
        currentTaskIndex=0,
    )
    childTask.rootTask = rootTask
    orchestrator = SimpleNamespace(
        rootTask=rootTask,
        getCurrentTask=MagicMock(),
    )
    context = {
        'tasksOrchestrator': orchestrator,
        'cavebot': {
            'isAttackingSomeCreature': True,
            'targetCreature': {
                'name': 'Rat',
                'coordinate': [101, 100, 7],
            },
        },
        'loot': {
            'pending': True,
            'movementBlockedUntil': 12.5,
            'quickLootCooldownUntil': 13.0,
        },
        'radar': {'coordinate': [100, 100, 7]},
        'gameWindow': {'monsters': [{'slot': (8, 5)}]},
        'lastPressedKey': 'right',
    }

    printLootDiagnostic('test_event', context, adjacentMonster=True)

    output = capsys.readouterr().out
    assert '[LootDiag]' in output
    assert 'event=test_event' in output
    assert 'task=walk' in output
    assert 'root=attackClosestCreature' in output
    assert 'allowChase=True' in output
    assert 'lastKey=right' in output
    assert 'adjacentMonster=True' in output
    orchestrator.getCurrentTask.assert_not_called()
