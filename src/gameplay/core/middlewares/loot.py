from time import time

from ...typings import Context


QUICK_LOOT_NEARBY_SLOTS = {
    (column, row)
    for row in range(4, 7)
    for column in range(6, 9)
}


# Código Linux anterior:
# - importava `hasNewLoot` da aba Loot;
# - acumulava 12 frames da Game Window;
# - classificava Loot Highlighting por magnitude, geometria e assinatura temporal;
# - mantinha confirmação visual, retries e estados de ausência.
# A implementação integral foi preservada para consulta em:
# `docs/historico-looting/loot-highlighting-middleware.py.txt`.


def _getCreatureSlot(creature):
    slot = creature.get('slot')
    return tuple(slot) if slot is not None else None


def hasAdjacentMonster(context: Context) -> bool:
    return any(
        _getCreatureSlot(monster) in QUICK_LOOT_NEARBY_SLOTS
        for monster in context.get('gameWindow', {}).get('monsters', [])
    )


def setLootDeathMiddleware(context: Context) -> Context:
    lootState = context.setdefault('loot', {})
    lootState.setdefault('pending', False)
    lootState.setdefault('pendingSlot', None)
    lootState.setdefault('detectedAt', None)
    lootState.setdefault('quickLootCooldownUntil', 0)

    if not lootState.get('enabled', False) or lootState['pending']:
        return context

    cavebotState = context.get('cavebot', {})
    previousTarget = cavebotState.get('previousTargetCreature')
    if previousTarget is None:
        return context

    previousTargetSlot = _getCreatureSlot(previousTarget)
    if previousTargetSlot not in QUICK_LOOT_NEARBY_SLOTS:
        return context

    gameWindowState = context.get('gameWindow', {})
    previousSlots = {
        slot
        for slot in (
            _getCreatureSlot(monster)
            for monster in gameWindowState.get('previousMonsters', [])
        )
        if slot is not None
    }
    if previousTargetSlot not in previousSlots:
        return context

    currentMonsters = gameWindowState.get('monsters', [])
    currentSlots = {
        slot
        for slot in (_getCreatureSlot(monster) for monster in currentMonsters)
        if slot is not None
    }
    currentTargetExists = any(
        monster.get('isBeingAttacked', False)
        for monster in currentMonsters
    )
    if currentTargetExists or previousTargetSlot in currentSlots:
        return context

    lootState['pending'] = True
    lootState['pendingSlot'] = previousTargetSlot
    lootState['detectedAt'] = time()
    cavebotState['previousTargetCreature'] = None
    print(f'[Loot] Morte detectada no 3x3 slot={previousTargetSlot}')
    return context
