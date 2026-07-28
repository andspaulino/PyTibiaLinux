from src.repositories.gameWindow.loot import classifyLootHighlightSlots
from ...typings import Context


LOOT_HIGHLIGHT_FRAME_COUNT = 12


def _resetLootHighlightState(lootState):
    lootState['highlightFrames'] = []
    lootState['highlightedSlots'] = []
    lootState['ambientSlots'] = []
    lootState['highlightFailureReason'] = None
    lootState['lastHighlightSignature'] = None


def _getHighlightSignature(candidates, failureReason):
    if failureReason is not None:
        return ('failure', failureReason)
    return (
        'candidates',
        tuple(sorted(item['slot'] for item in candidates)),
    )


def setLootHighlightingMiddleware(context: Context) -> Context:
    lootState = context.setdefault('loot', {})
    lootState.setdefault('highlightFrames', [])
    lootState.setdefault('highlightedSlots', [])
    lootState.setdefault('ambientSlots', [])
    lootState.setdefault('highlightFailureReason', None)
    lootState.setdefault('lastHighlightSignature', None)

    if not lootState.get('monitorHighlighting', False):
        _resetLootHighlightState(lootState)
        return context

    gameWindowImage = context.get('gameWindow', {}).get('image')
    if gameWindowImage is None:
        _resetLootHighlightState(lootState)
        lootState['highlightFailureReason'] = 'game-window-unavailable'
        return context

    lootState['highlightFrames'].append(gameWindowImage.copy())
    if len(lootState['highlightFrames']) < LOOT_HIGHLIGHT_FRAME_COUNT:
        return context

    frames = lootState['highlightFrames'][:LOOT_HIGHLIGHT_FRAME_COUNT]
    lootState['highlightFrames'] = lootState['highlightFrames'][
        LOOT_HIGHLIGHT_FRAME_COUNT:
    ]
    classification = classifyLootHighlightSlots(frames)
    if classification['accepted']:
        candidates = classification['candidates']
        ambient = classification['ambient']
        failureReason = None
    else:
        candidates = []
        ambient = []
        failureReason = classification['failureReason']

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
                f"ambient={ambientSummary}"
            )
        lootState['lastHighlightSignature'] = signature
    return context
