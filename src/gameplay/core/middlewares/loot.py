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


def isCreatureStillPresent(context: Context, creature) -> bool:
    if not creature or not isinstance(creature, dict):
        return False
    targetCoord = creature.get('coordinate')
    if targetCoord is None or len(targetCoord) != 3:
        return False
    monsters = context.get('gameWindow', {}).get('monsters', [])
    for monster in monsters:
        if not isinstance(monster, dict):
            continue
        monsterCoord = monster.get('coordinate')
        if (
            monsterCoord is not None
            and len(monsterCoord) == 3
            and tuple(monsterCoord) == tuple(targetCoord)
        ):
            return True
    return False


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
        if not isinstance(monster, dict):
            continue
        mCoord = monster.get('coordinate')
        if (
            targetCoord is not None
            and mCoord is not None
            and len(mCoord) == 3
            and len(targetCoord) == 3
            and mCoord[0] == targetCoord[0]
            and mCoord[1] == targetCoord[1]
            and mCoord[2] == targetCoord[2]
        ):
            return True

    # Código Linux anterior:
    # qualquer criatura homônima na Battle List, ou a até dois SQMs da última
    # coordenada, era aceita como o mesmo alvo e podia ocultar uma morte real.
    # Sem um identificador estável por criatura, somente a coordenada mundial
    # exata é evidência segura de que o alvo específico continua presente.
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
            # Código Linux anterior:
            # lootState['wasAttacking'] = True
            # return context
            # Continua até a leitura do chat: uma linha Loot of é autoridade
            # suficiente para confirmar uma morte mesmo durante um flicker.
            isAttacking = True
        else:
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
        # Código Linux anterior:
        # if isCreatureStillPresent(context, corpseCandidate):
        # Uma percepção visual atrasada, ou outro monstro homônimo ocupando o
        # mesmo SQM, não pode invalidar uma morte já confirmada quando o estado
        # de ataque terminou. A rejeição vale somente durante combate ativo.
        if isAttacking and isCreatureStillPresent(context, corpseCandidate):
            # Uma linha visual antiga/retriggerada não pode transformar o alvo
            # que ainda está sendo atacado na mesma coordenada em cadáver.
            lootState['lastCombatEndedCreature'] = None
            printLootDiagnostic(
                'loot_ignored',
                context,
                reason='corpse-candidate-still-alive',
                corpseQueued=False,
                corpseQueueSize=len(lootState['corpsesToLoot']),
            )
            return context
        addedCorpse = addCorpseToQueue(
            lootState['corpsesToLoot'],
            corpseCandidate,
        )
        lootState['lastCombatEndedCreature'] = None
        if addedCorpse:
            context['cavebot']['previousTargetCreature'] = None
        hasTrackedCorpse = len(lootState['corpsesToLoot']) > 0
        # Código Linux anterior:
        # lootState['pending'] = True
        # Mesmo sem candidato ou cadáver na fila, um retrigger visual marcava
        # pending e enviava Alt+Q durante o waypoint.
        if not hasTrackedCorpse:
            printLootDiagnostic(
                'loot_ignored',
                context,
                reason='no-corpse-candidate',
                corpseQueued=False,
                corpseQueueSize=0,
            )
            return context
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
