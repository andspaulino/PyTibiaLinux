from time import time


def _getCurrentTaskWithoutLifecycle(context):
    orchestrator = context.get('tasksOrchestrator')
    task = getattr(orchestrator, 'rootTask', None)
    while task is not None and hasattr(task, 'tasks'):
        tasks = getattr(task, 'tasks', [])
        if len(tasks) == 0:
            break
        currentTaskIndex = getattr(task, 'currentTaskIndex', 0)
        if not 0 <= currentTaskIndex < len(tasks):
            break
        task = tasks[currentTaskIndex]
    return task


def _getRootTask(context, currentTask):
    orchestrator = context.get('tasksOrchestrator')
    orchestratorRoot = getattr(orchestrator, 'rootTask', None)
    if orchestratorRoot is not None:
        return orchestratorRoot
    if currentTask is None:
        return None
    return getattr(currentTask, 'rootTask', None) or currentTask


def printLootDiagnostic(event, context, **details):
    currentTask = _getCurrentTaskWithoutLifecycle(context)
    rootTask = _getRootTask(context, currentTask)
    cavebotState = context.get('cavebot', {})
    lootState = context.get('loot', {})
    targetCreature = cavebotState.get('targetCreature') or {}
    monsters = context.get('gameWindow', {}).get('monsters', [])
    monsterSlots = [
        monster.get('slot')
        for monster in monsters
        if isinstance(monster, dict)
    ]
    fields = {
        'time': round(time(), 3),
        'event': event,
        'coordinate': context.get('radar', {}).get('coordinate'),
        'task': getattr(currentTask, 'name', None),
        'root': getattr(rootTask, 'name', None),
        'allowChase': getattr(rootTask, 'allowChase', None),
        'lastKey': context.get('lastPressedKey'),
        'pending': lootState.get('pending', False),
        'movementBlockedUntil': round(
            lootState.get('movementBlockedUntil', 0),
            3,
        ),
        'cooldownUntil': round(
            lootState.get('quickLootCooldownUntil', 0),
            3,
        ),
        'isAttacking': cavebotState.get('isAttackingSomeCreature', False),
        'target': targetCreature.get('name'),
        'targetCoordinate': targetCreature.get('coordinate'),
        'monsterSlots': monsterSlots,
    }
    fields.update(details)
    serializedFields = ' '.join(
        f'{key}={value}'
        for key, value in fields.items()
    )
    print(f'[LootDiag] {serializedFields}')
