from time import time


TRANSIENT_BLOCK_DURATION = 3.0


def _normalizeCoordinate(coordinate):
    if (
        coordinate is None
        or not hasattr(coordinate, '__len__')
        or len(coordinate) != 3
    ):
        return None
    try:
        return tuple(int(value) for value in coordinate)
    except (TypeError, ValueError, OverflowError):
        return None


def getActiveTransientBlockedCoordinates(context, now=None):
    currentTime = time() if now is None else now
    navigation = context.setdefault('cavebot', {}).setdefault(
        'navigation',
        {},
    )
    entries = navigation.setdefault('transientBlockedCoordinates', [])
    activeEntries = []
    activeCoordinates = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        coordinate = _normalizeCoordinate(entry.get('coordinate'))
        expiresAt = entry.get('expiresAt')
        if coordinate is None or not isinstance(expiresAt, (int, float)):
            continue
        if expiresAt <= currentTime or coordinate in seen:
            continue
        seen.add(coordinate)
        activeEntries.append({
            'coordinate': list(coordinate),
            'expiresAt': expiresAt,
        })
        activeCoordinates.append(coordinate)
    navigation['transientBlockedCoordinates'] = activeEntries
    return activeCoordinates


def addTransientBlockedCoordinate(
    context,
    coordinate,
    now=None,
    duration=TRANSIENT_BLOCK_DURATION,
):
    normalizedCoordinate = _normalizeCoordinate(coordinate)
    if normalizedCoordinate is None:
        return False
    currentTime = time() if now is None else now
    activeCoordinates = getActiveTransientBlockedCoordinates(
        context,
        now=currentTime,
    )
    navigation = context['cavebot']['navigation']
    entries = navigation['transientBlockedCoordinates']
    expiresAt = currentTime + duration
    for entry in entries:
        if _normalizeCoordinate(entry.get('coordinate')) == normalizedCoordinate:
            entry['expiresAt'] = expiresAt
            return False
    entries.append({
        'coordinate': list(normalizedCoordinate),
        'expiresAt': expiresAt,
    })
    return normalizedCoordinate not in activeCoordinates
