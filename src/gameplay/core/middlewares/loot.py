from time import time

from src.repositories.chat.core import hasNewLoot, resetLootBaseline

from ...typings import Context
from ..tasks.selectChatTab import SelectChatTabTask


QUICK_LOOT_NEARBY_SLOTS = {
    (column, row)
    for row in range(4, 7)
    for column in range(6, 9)
}


# Código Linux anterior:
# a morte era inferida quando `previousTargetCreature` desaparecia entre dois
# frames da Game Window. O snapshot está preservado em
# `docs/historico-looting/loot-disappearance-middleware.py.txt`.


def _getCreatureSlot(creature):
    slot = creature.get('slot')
    return tuple(slot) if slot is not None else None


def hasAdjacentMonster(context: Context) -> bool:
    return any(
        _getCreatureSlot(monster) in QUICK_LOOT_NEARBY_SLOTS
        for monster in context.get('gameWindow', {}).get('monsters', [])
    )


def setLootChatMiddleware(context: Context) -> Context:
    lootState = context.setdefault('loot', {})
    lootState.setdefault('pending', False)
    lootState.setdefault('detectedAt', None)
    lootState.setdefault('quickLootCooldownUntil', 0)
    lootState.setdefault('chatMonitoringEnabled', False)

    if not lootState.get('enabled', False):
        if lootState['chatMonitoringEnabled']:
            resetLootBaseline()
        lootState['chatMonitoringEnabled'] = False
        return context

    if not lootState['chatMonitoringEnabled']:
        resetLootBaseline()
        lootState['chatMonitoringEnabled'] = True

    lootTab = context.get('chat', {}).get('tabs', {}).get('loot')
    if lootTab is None:
        return context

    if not lootTab.get('isSelected', False):
        currentTask = context['tasksOrchestrator'].getCurrentTask(context)
        currentRootTask = (
            currentTask.rootTask
            if currentTask is not None and currentTask.rootTask is not None
            else currentTask
        )
        if (
            currentRootTask is None
            or currentRootTask.name != 'selectChatTab'
        ):
            context['tasksOrchestrator'].setRootTask(
                context,
                SelectChatTabTask('loot'),
            )
        return context

    hasNewLootLine = hasNewLoot(context['screenshot'])
    isQuickLootInCooldown = time() < lootState['quickLootCooldownUntil']
    if hasNewLootLine and isQuickLootInCooldown:
        return context
    if hasNewLootLine:
        lootState['pending'] = True
        lootState['detectedAt'] = time()
        print('[Loot] Nova linha Loot of detectada')
    return context
