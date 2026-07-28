from src.repositories.gameWindow.loot import classifyLootHighlightSlots
from ...typings import Context


LOOT_HIGHLIGHT_FRAME_COUNT = 12
LOOT_HIGHLIGHT_PENDING_BATCHES = 6
QUICK_LOOT_CONFIRMATION_BATCHES = 2
QUICK_LOOT_NEARBY_SLOTS = {
    (column, row)
    for row in range(4, 7)
    for column in range(6, 9)
}


def _resetFrameBuffer(lootState):
    lootState['highlightFrames'] = []
    lootState['highlightFrameCoordinate'] = None


def _resetLootHighlightState(lootState):
    _resetFrameBuffer(lootState)
    lootState['pendingHighlightSlots'] = []
    lootState['highlightedSlots'] = []
    lootState['ambientSlots'] = []
    lootState['highlightFailureReason'] = None
    lootState['lastHighlightSignature'] = None
    lootState['quickLootReady'] = False
    lootState['quickLootDetectionPending'] = False
    lootState['quickLootBlockingSlot'] = None
    lootState['quickLootAwaitingConfirmation'] = False
    lootState['quickLootConfirmationBatches'] = 0
    lootState['quickLootRetryCount'] = 0


def _getHighlightSignature(candidates, failureReason):
    if failureReason is not None:
        return ('failure', failureReason)
    return (
        'candidates',
        tuple(sorted(item['slot'] for item in candidates)),
    )


def _getCreatureSlots(creatures):
    return {
        tuple(creature['slot'])
        for creature in creatures
        if creature.get('slot') is not None
    }


def _updatePendingSlots(context, lootState):
    gameWindowState = context.get('gameWindow', {})
    previousSlots = _getCreatureSlots(gameWindowState.get('previousMonsters', []))
    currentMonsters = gameWindowState.get('monsters', [])
    currentSlots = _getCreatureSlots(currentMonsters)
    disappearedSlots = previousSlots - currentSlots

    pendingBySlot = {
        tuple(item['slot']): item
        for item in lootState['pendingHighlightSlots']
        if tuple(item['slot']) not in currentSlots
    }
    for slot in disappearedSlots:
        pendingBySlot[slot] = {
            'slot': slot,
            'remainingBatches': LOOT_HIGHLIGHT_PENDING_BATCHES,
        }
    lootState['pendingHighlightSlots'] = list(pendingBySlot.values())

    previousTarget = context.get('cavebot', {}).get('previousTargetCreature')
    currentTargetExists = any(
        creature.get('isBeingAttacked', False)
        for creature in currentMonsters
    )
    if previousTarget is None or currentTargetExists:
        return
    previousTargetSlot = previousTarget.get('slot')
    if previousTargetSlot is None:
        return
    previousTargetSlot = tuple(previousTargetSlot)
    if (
        previousTargetSlot in disappearedSlots
        and previousTargetSlot in QUICK_LOOT_NEARBY_SLOTS
    ):
        lootState['quickLootDetectionPending'] = True
        lootState['quickLootBlockingSlot'] = previousTargetSlot


def setLootHighlightingMiddleware(context: Context) -> Context:
    lootState = context.setdefault('loot', {})
    lootState.setdefault('highlightFrames', [])
    lootState.setdefault('highlightFrameCoordinate', None)
    lootState.setdefault('pendingHighlightSlots', [])
    lootState.setdefault('highlightedSlots', [])
    lootState.setdefault('ambientSlots', [])
    lootState.setdefault('highlightFailureReason', None)
    lootState.setdefault('lastHighlightSignature', None)
    lootState.setdefault('quickLootReady', False)
    lootState.setdefault('quickLootDetectionPending', False)
    lootState.setdefault('quickLootBlockingSlot', None)
    lootState.setdefault('quickLootAwaitingConfirmation', False)
    lootState.setdefault('quickLootConfirmationBatches', 0)
    lootState.setdefault('quickLootRetryCount', 0)
    lootState.setdefault('quickLootMaxRetries', 2)

    if not lootState.get('monitorHighlighting', False):
        _resetLootHighlightState(lootState)
        return context

    _updatePendingSlots(context, lootState)
    pendingSlots = [
        tuple(item['slot'])
        for item in lootState['pendingHighlightSlots']
    ]
    if len(pendingSlots) == 0:
        _resetFrameBuffer(lootState)
        if (
            not lootState.get('quickLootAwaitingConfirmation', False)
            and not lootState.get('quickLootReady', False)
        ):
            lootState['quickLootDetectionPending'] = False
            lootState['quickLootBlockingSlot'] = None
        if lootState['highlightedSlots']:
            lootState['highlightedSlots'] = []
            signature = _getHighlightSignature([], None)
            if signature != lootState['lastHighlightSignature']:
                print('[Loot Highlighting] candidates=[] ambient=[]')
                lootState['lastHighlightSignature'] = signature
        return context

    gameWindowImage = context.get('gameWindow', {}).get('image')
    radarCoordinate = context.get('radar', {}).get('coordinate')
    if gameWindowImage is None:
        _resetFrameBuffer(lootState)
        lootState['highlightFailureReason'] = 'game-window-unavailable'
        lootState['quickLootDetectionPending'] = False
        return context
    if radarCoordinate is None:
        _resetFrameBuffer(lootState)
        lootState['highlightFailureReason'] = 'radar-unavailable'
        lootState['quickLootDetectionPending'] = False
        return context

    frameCoordinate = lootState['highlightFrameCoordinate']
    if frameCoordinate is None:
        lootState['highlightFrameCoordinate'] = radarCoordinate
    elif tuple(frameCoordinate) != tuple(radarCoordinate):
        _resetFrameBuffer(lootState)
        lootState['highlightFrameCoordinate'] = radarCoordinate

    lootState['highlightFrames'].append(gameWindowImage.copy())
    if len(lootState['highlightFrames']) < LOOT_HIGHLIGHT_FRAME_COUNT:
        return context

    frames = lootState['highlightFrames'][:LOOT_HIGHLIGHT_FRAME_COUNT]
    _resetFrameBuffer(lootState)
    classification = classifyLootHighlightSlots(
        frames,
        eligibleSlots=pendingSlots,
    )
    if classification['accepted']:
        candidates = classification['candidates']
        ambient = classification['ambient']
        failureReason = None
    else:
        candidates = []
        ambient = []
        failureReason = classification['failureReason']

    confirmedSlots = {item['slot'] for item in candidates}
    nearbyConfirmedSlots = confirmedSlots & QUICK_LOOT_NEARBY_SLOTS
    if lootState.get('enabled', False):
        if lootState['quickLootAwaitingConfirmation']:
            if len(nearbyConfirmedSlots) == 0:
                lootState['quickLootAwaitingConfirmation'] = False
                lootState['quickLootConfirmationBatches'] = 0
                lootState['quickLootRetryCount'] = 0
                lootState['quickLootReady'] = False
                lootState['quickLootDetectionPending'] = False
                lootState['quickLootBlockingSlot'] = None
                lootState['pendingHighlightSlots'] = [
                    item
                    for item in lootState['pendingHighlightSlots']
                    if tuple(item['slot']) not in QUICK_LOOT_NEARBY_SLOTS
                ]
                print('[Loot] Quick Loot confirmado pelo desaparecimento do highlight')
            else:
                lootState['quickLootConfirmationBatches'] += 1
                if (
                    lootState['quickLootConfirmationBatches']
                    >= QUICK_LOOT_CONFIRMATION_BATCHES
                ):
                    lootState['quickLootAwaitingConfirmation'] = False
                    lootState['quickLootConfirmationBatches'] = 0
                    if (
                        lootState['quickLootRetryCount']
                        < lootState['quickLootMaxRetries']
                    ):
                        lootState['quickLootReady'] = True
                        lootState['quickLootDetectionPending'] = True
                    else:
                        lootState['quickLootReady'] = False
                        lootState['quickLootDetectionPending'] = False
                        lootState['quickLootBlockingSlot'] = None
                        lootState['highlightFailureReason'] = (
                            'quick-loot-not-confirmed'
                        )
                        print('[Loot] Quick Loot não confirmado; retries esgotados')
        elif len(nearbyConfirmedSlots) > 0:
            lootState['quickLootReady'] = True
            lootState['quickLootDetectionPending'] = True

    remainingPending = []
    for item in lootState['pendingHighlightSlots']:
        slot = tuple(item['slot'])
        if slot in confirmedSlots:
            item['remainingBatches'] = LOOT_HIGHLIGHT_PENDING_BATCHES
            remainingPending.append(item)
            continue
        item['remainingBatches'] -= 1
        if item['remainingBatches'] > 0:
            remainingPending.append(item)
    lootState['pendingHighlightSlots'] = remainingPending
    remainingPendingSlots = {
        tuple(item['slot'])
        for item in remainingPending
    }
    blockingSlot = lootState.get('quickLootBlockingSlot')
    if (
        blockingSlot is not None
        and tuple(blockingSlot) not in remainingPendingSlots
        and not lootState['quickLootReady']
        and not lootState['quickLootAwaitingConfirmation']
    ):
        lootState['quickLootDetectionPending'] = False
        lootState['quickLootBlockingSlot'] = None

    lootState['highlightedSlots'] = candidates
    lootState['ambientSlots'] = ambient
    lootState['highlightFailureReason'] = failureReason
    signature = _getHighlightSignature(candidates, failureReason)
    if signature != lootState['lastHighlightSignature']:
        if failureReason is not None:
            print(f"[Loot Highlighting] rejected={failureReason}")
        else:
            candidateSummary = [
                (
                    item['slot'],
                    item['motionPixels'],
                    item['method'],
                )
                for item in candidates
            ]
            ambientSummary = [
                (item['slot'], item['motionPixels'])
                for item in ambient
            ]
            print(
                f"[Loot Highlighting] candidates={candidateSummary} "
                f"ambient={ambientSummary} pending={pendingSlots}"
            )
        lootState['lastHighlightSignature'] = signature
    return context
