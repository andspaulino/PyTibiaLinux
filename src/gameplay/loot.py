from copy import deepcopy

from src.repositories.radar.core import isCoordinateWalkable


MAX_CORPSE_APPROACH_DISTANCE = 5


def normalizeCoordinate(coordinate):
    if (
        coordinate is None
        or not hasattr(coordinate, '__len__')
        or len(coordinate) != 3
    ):
        return None
    return tuple(int(value) for value in coordinate)


def isCoordinateInQuickLootRange(playerCoordinate, corpseCoordinate):
    player = normalizeCoordinate(playerCoordinate)
    corpse = normalizeCoordinate(corpseCoordinate)
    if player is None or corpse is None or player[2] != corpse[2]:
        return False
    return (
        abs(player[0] - corpse[0]) <= 1
        and abs(player[1] - corpse[1]) <= 1
    )


def getClosestQuickLootCoordinate(playerCoordinate, corpseCoordinate):
    player = normalizeCoordinate(playerCoordinate)
    corpse = normalizeCoordinate(corpseCoordinate)
    if player is None or corpse is None or player[2] != corpse[2]:
        return None
    corpseDistance = max(
        abs(player[0] - corpse[0]),
        abs(player[1] - corpse[1]),
    )
    if corpseDistance > MAX_CORPSE_APPROACH_DISTANCE:
        return None

    candidates = []
    for yOffset in range(-1, 2):
        for xOffset in range(-1, 2):
            candidate = (
                corpse[0] + xOffset,
                corpse[1] + yOffset,
                corpse[2],
            )
            try:
                if not isCoordinateWalkable(candidate):
                    continue
            except (IndexError, TypeError, ValueError):
                continue
            distanceToPlayer = max(
                abs(player[0] - candidate[0]),
                abs(player[1] - candidate[1]),
            )
            candidates.append((distanceToPlayer, candidate))
    if len(candidates) == 0:
        return None
    candidates.sort(key=lambda item: (item[0], item[1][1], item[1][0]))
    return candidates[0][1]


def addCorpseToQueue(corpsesToLoot, creature):
    if not isinstance(creature, dict):
        return False
    coordinate = normalizeCoordinate(creature.get('coordinate'))
    if coordinate is None:
        return False
    if any(
        normalizeCoordinate(corpse.get('coordinate')) == coordinate
        for corpse in corpsesToLoot
        if isinstance(corpse, dict)
    ):
        return False
    corpse = deepcopy(creature)
    corpse['coordinate'] = list(coordinate)
    corpse['approachFailed'] = False
    corpsesToLoot.append(corpse)
    return True


def removeCorpsesInQuickLootRange(corpsesToLoot, playerCoordinate):
    remainingCorpses = [
        corpse
        for corpse in corpsesToLoot
        if not isCoordinateInQuickLootRange(
            playerCoordinate,
            corpse.get('coordinate') if isinstance(corpse, dict) else None,
        )
    ]
    corpsesToLoot[:] = remainingCorpses


def removeCorpseByCoordinate(corpsesToLoot, corpseCoordinate):
    selectedCoordinate = normalizeCoordinate(corpseCoordinate)
    if selectedCoordinate is None:
        return
    corpsesToLoot[:] = [
        corpse
        for corpse in corpsesToLoot
        if normalizeCoordinate(
            corpse.get('coordinate') if isinstance(corpse, dict) else None
        ) != selectedCoordinate
    ]
