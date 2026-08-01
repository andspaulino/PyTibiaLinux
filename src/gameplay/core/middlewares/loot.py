import numpy as np
from time import time

from src.repositories.chat.core import hasNewLoot, resetLootBaseline

from ...loot import addCorpseToQueue
from ...lootDiagnostics import printLootDiagnostic
from ...typings import Context
from ..tasks.selectChatTab import SelectChatTabTask


POST_COMBAT_LOOT_DELAY = 0.85


QUICK_LOOT_NEARBY_SLOTS = {
    (column, row)
    for row in range(4, 7)
    for column in range(6, 9)
}


def isTargetCreatureStillAlive(context: Context) -> bool:
    target = (
        context.get('cavebot', {}).get('targetCreature')
        or context.get('cavebot', {}).get('previousTargetCreature')
    )
    if not target or not isinstance(target, dict):
        return False
    targetCoord = target.get('coordinate')
    targetName = target.get('name')
    if targetName == 'Unknown':
        targetName = None

    monsters = context.get('gameWindow', {}).get('monsters', [])
    for monster in monsters:
        mCoord = monster.get('coordinate')
        mName = monster.get('name')
        if targetCoord is not None and mCoord is not None and len(mCoord) == 3 and len(targetCoord) == 3:
            if mCoord[0] == targetCoord[0] and mCoord[1] == targetCoord[1] and mCoord[2] == targetCoord[2]:
                return True
        if targetName and mName == targetName and mCoord is not None and targetCoord is not None:
            if abs(int(mCoord[0]) - int(targetCoord[0])) <= 2 and abs(int(mCoord[1]) - int(targetCoord[1])) <= 2:
                return True

    creatures = context.get('battleList', {}).get('creatures', [])
    if isinstance(creatures, (list, np.ndarray)):
        for creature in creatures:
            cName = creature['name'] if isinstance(creature, dict) or hasattr(creature, '__getitem__') else None
            if targetName and cName == targetName:
                return True
    return False


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
    lootState.setdefault('corpsesToLoot', [])
    lootState.setdefault('lastCombatEndedCreature', None)
    lootState.setdefault('pending', False)
    lootState.setdefault('detectedAt', None)
    lootState.setdefault('quickLootCooldownUntil', 0)
    lootState.setdefault('movementBlockedUntil', 0)
    lootState.setdefault('wasAttacking', False)
    lootState.setdefault('chatMonitoringEnabled', False)

    isAttacking = bool(
        context.get('cavebot', {}).get('isAttackingSomeCreature', False)
    )
    if not lootState.get('enabled', False):
        if lootState['chatMonitoringEnabled']:
            resetLootBaseline()
        lootState['chatMonitoringEnabled'] = False
        lootState['corpsesToLoot'].clear()
        lootState['lastCombatEndedCreature'] = None
        lootState['movementBlockedUntil'] = 0
        lootState['wasAttacking'] = False
        return context

    now = time()

    # Código original Windows / Linux anterior:
    # if lootState['wasAttacking'] and not isAttacking:
    #     lootState['movementBlockedUntil'] = max(
    #         lootState['movementBlockedUntil'],
    #         now + POST_COMBAT_LOOT_DELAY,
    #     )
    #     lootState['lastCombatEndedCreature'] = (
    #         context.get('cavebot', {}).get('targetCreature')
    #         or context.get('cavebot', {}).get('previousTargetCreature')
    #     )
    #     printLootDiagnostic(...)

    # Adaptação Linux: Se a criatura-alvo continua viva/presente no jogo, ignora o flicker
    # de 1 frame do indicador de ataque para não pausar o movimento por 850ms nem resetar o ataque.
    if lootState['wasAttacking'] and not isAttacking:
        if isTargetCreatureStillAlive(context):
            lootState['wasAttacking'] = True
            return context

        lootState['movementBlockedUntil'] = max(
            lootState['movementBlockedUntil'],
            now + POST_COMBAT_LOOT_DELAY,
        )
        lootState['lastCombatEndedCreature'] = (
            context.get('cavebot', {}).get('targetCreature')
            or context.get('cavebot', {}).get('previousTargetCreature')
        )
        printLootDiagnostic(
            'combat_end',
            context,
            adjacentMonster=hasAdjacentMonster(context),
            corpseCandidateCoordinate=(
                lootState['lastCombatEndedCreature'].get('coordinate')
                if isinstance(lootState['lastCombatEndedCreature'], dict)
                else None
            ),
        )
    lootState['wasAttacking'] = isAttacking

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
    isQuickLootInCooldown = now < lootState['quickLootCooldownUntil']
    if hasNewLootLine and isQuickLootInCooldown:
        return context
    if hasNewLootLine:
        corpseCandidate = (
            lootState.get('lastCombatEndedCreature')
            or context.get('cavebot', {}).get('previousTargetCreature')
        )
        addedCorpse = addCorpseToQueue(
            lootState['corpsesToLoot'],
            corpseCandidate,
        )
        lootState['lastCombatEndedCreature'] = None
        if addedCorpse:
            context['cavebot']['previousTargetCreature'] = None
        lootState['pending'] = True
        lootState['detectedAt'] = now
        print('[Loot] Nova linha Loot of detectada')
        printLootDiagnostic(
            'loot_detected',
            context,
            adjacentMonster=hasAdjacentMonster(context),
            corpseQueued=addedCorpse,
            corpseQueueSize=len(lootState['corpsesToLoot']),
        )
    return context
