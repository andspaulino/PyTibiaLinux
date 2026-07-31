import tcod
from src.repositories.radar.config import walkableFloorsSqms
from src.shared.typings import Coordinate, CoordinateList
from src.utils.coordinate import getAvailableAroundCoordinates, getClosestCoordinate, getPixelFromCoordinate
from .typings import Checkpoint


# Código original:
# def generateFloorWalkpoints(coordinate: Coordinate, goalCoordinate: Coordinate, nonWalkableCoordinates: CoordinateList = []) -> CoordinateList:
#     pixelCoordinate = getPixelFromCoordinate(coordinate)
#     xFromTheStartOfRadar = pixelCoordinate[0] - 53
#     xFromTheEndOfRadar = pixelCoordinate[0] + 53
#     yFromTheStartOfRadar = pixelCoordinate[1] - 54
#     yFromTheEndOfRadar = pixelCoordinate[1] + 55
#     copiedWalkableFloorSqms = walkableFloorsSqms[coordinate[2]][
#         yFromTheStartOfRadar:yFromTheEndOfRadar, xFromTheStartOfRadar:xFromTheEndOfRadar].copy()
#     for nonWalkableCoordinate in nonWalkableCoordinates:
#         if nonWalkableCoordinate[2] == coordinate[2]:
#             nonWalkableCoordinateInPixelX, nonWalkableCoordinateInPixelY = getPixelFromCoordinate(nonWalkableCoordinate)
#             leX = nonWalkableCoordinateInPixelX - xFromTheStartOfRadar
#             leY = nonWalkableCoordinateInPixelY - yFromTheStartOfRadar
#             if leX >= 0 and leX <= 106 and leY >= 0 and leY <= 109:
#                 copiedWalkableFloorSqms[leY, leX] = 0
#     x = goalCoordinate[0] - coordinate[0] + 53
#     y = goalCoordinate[1] - coordinate[1] + 54
#     return [[coordinate[0] + x - 53,
#                    coordinate[1] + y - 54, coordinate[2]] for y, x in tcod.path.AStar(copiedWalkableFloorSqms, 0).get_path(54, 53, y, x)]


def calculateFloorWalkpoints(
    coordinate: Coordinate,
    goalCoordinate: Coordinate,
    nonWalkableCoordinates: CoordinateList | None = None,
):
    if coordinate is None or goalCoordinate is None:
        return [], 'coordinate-unavailable'
    if len(coordinate) != 3 or len(goalCoordinate) != 3:
        return [], 'coordinate-invalid'

    floor = coordinate[2]
    if floor != goalCoordinate[2]:
        return [], 'different-floor'
    if floor < 0 or floor >= walkableFloorsSqms.shape[0]:
        return [], 'floor-out-of-bounds'

    pixelX, pixelY = getPixelFromCoordinate(coordinate)
    goalPixelX, goalPixelY = getPixelFromCoordinate(goalCoordinate)
    floorHeight, floorWidth = walkableFloorsSqms[floor].shape
    if not (0 <= pixelX < floorWidth and 0 <= pixelY < floorHeight):
        return [], 'origin-out-of-atlas'
    if not (0 <= goalPixelX < floorWidth and 0 <= goalPixelY < floorHeight):
        return [], 'goal-out-of-atlas'

    xStart = pixelX - 53
    xEnd = pixelX + 53
    yStart = pixelY - 54
    yEnd = pixelY + 55
    if xStart < 0 or yStart < 0 or xEnd > floorWidth or yEnd > floorHeight:
        return [], 'path-window-out-of-atlas'

    localGoalX = goalPixelX - xStart
    localGoalY = goalPixelY - yStart
    if not (0 <= localGoalX < 106 and 0 <= localGoalY < 109):
        return [], 'goal-out-of-local-window'

    copiedWalkableFloorSqms = walkableFloorsSqms[floor][
        yStart:yEnd,
        xStart:xEnd,
    ].copy()
    if copiedWalkableFloorSqms.shape != (109, 106):
        return [], 'path-window-invalid'

    for nonWalkableCoordinate in nonWalkableCoordinates or []:
        if nonWalkableCoordinate is None or len(nonWalkableCoordinate) != 3:
            continue
        if nonWalkableCoordinate[2] != floor:
            continue
        obstaclePixelX, obstaclePixelY = getPixelFromCoordinate(
            nonWalkableCoordinate
        )
        localX = obstaclePixelX - xStart
        localY = obstaclePixelY - yStart
        if 0 <= localX < copiedWalkableFloorSqms.shape[1] and 0 <= localY < copiedWalkableFloorSqms.shape[0]:
            copiedWalkableFloorSqms[localY, localX] = 0

    copiedWalkableFloorSqms[54, 53] = 1
    # Código original mantido comentado:
    # if coordinate == goalCoordinate:
    #     return [], None
    if tuple(coordinate) == tuple(goalCoordinate):
        return [], None
    if copiedWalkableFloorSqms[localGoalY, localGoalX] == 0:
        return [], 'goal-not-walkable'

    path = tcod.path.AStar(copiedWalkableFloorSqms, 0).get_path(
        54,
        53,
        localGoalY,
        localGoalX,
    )
    if len(path) == 0:
        return [], 'path-not-found'

    walkpoints = [
        [coordinate[0] + pathX - 53, coordinate[1] + pathY - 54, floor]
        for pathY, pathX in path
    ]
    return walkpoints, None


def generateFloorWalkpoints(
    coordinate: Coordinate,
    goalCoordinate: Coordinate,
    nonWalkableCoordinates: CoordinateList | None = None,
) -> CoordinateList:
    walkpoints, _ = calculateFloorWalkpoints(
        coordinate,
        goalCoordinate,
        nonWalkableCoordinates,
    )
    return walkpoints


# TODO: add unit tests
def resolveFloorCoordinate(_, nextCoordinate: Coordinate) -> Checkpoint:
    return {
        'goalCoordinate': nextCoordinate,
        'checkInCoordinate': nextCoordinate,
    }


# TODO: add types
# TODO: add unit tests
def resolveMoveDownCoordinate(_, waypoint) -> Checkpoint:
    checkInCoordinate = None
    if waypoint['options']['direction'] == 'north':
        checkInCoordinate = [waypoint['coordinate'][0], waypoint['coordinate'][1] - 2, waypoint['coordinate'][2] + 1]
    elif waypoint['options']['direction'] == 'south':
        checkInCoordinate = [waypoint['coordinate'][0], waypoint['coordinate'][1] + 2, waypoint['coordinate'][2] + 1]
    elif waypoint['options']['direction'] == 'east':
        checkInCoordinate = [waypoint['coordinate'][0] + 2, waypoint['coordinate'][1], waypoint['coordinate'][2] + 1]
    else:
        checkInCoordinate = [waypoint['coordinate'][0] - 2, waypoint['coordinate'][1], waypoint['coordinate'][2] + 1]
    return {
        'goalCoordinate': waypoint['coordinate'],
        'checkInCoordinate': checkInCoordinate,
    }


# TODO: add types
# TODO: add unit tests
def resolveMoveUpCoordinate(_, waypoint) -> Checkpoint:
    checkInCoordinate = None
    if waypoint['options']['direction'] == 'north':
        checkInCoordinate = [waypoint['coordinate'][0], waypoint['coordinate'][1] - 2, waypoint['coordinate'][2] - 1]
    elif waypoint['options']['direction'] == 'south':
        checkInCoordinate = [waypoint['coordinate'][0], waypoint['coordinate'][1] + 2, waypoint['coordinate'][2] - 1]
    elif waypoint['options']['direction'] == 'east':
        checkInCoordinate = [waypoint['coordinate'][0] + 2, waypoint['coordinate'][1], waypoint['coordinate'][2] - 1]
    else:
        checkInCoordinate = [waypoint['coordinate'][0] - 2, waypoint['coordinate'][1], waypoint['coordinate'][2] - 1]
    return {
        'goalCoordinate': waypoint['coordinate'],
        'checkInCoordinate': checkInCoordinate,
    }


# TODO: add unit tests
def resolveUseShovelWaypointCoordinate(coordinate, nextCoordinate: Coordinate) -> Checkpoint:
    availableAroundCoordinates = getAvailableAroundCoordinates(
        nextCoordinate, walkableFloorsSqms[nextCoordinate[2]])
    closestCoordinate = getClosestCoordinate(
        coordinate, availableAroundCoordinates)
    checkInCoordinate = [nextCoordinate[0], nextCoordinate[1], nextCoordinate[2] + 1]
    return {
        'goalCoordinate': closestCoordinate,
        'checkInCoordinate': checkInCoordinate,
    }


# TODO: add unit tests
def resolveUseRopeWaypointCoordinate(_, nextCoordinate: Coordinate) -> Checkpoint:
    return {
        'goalCoordinate': [nextCoordinate[0], nextCoordinate[1], nextCoordinate[2]],
        'checkInCoordinate': [nextCoordinate[0], nextCoordinate[1] + 1, nextCoordinate[2] - 1],
    }


# TODO: add unit tests
def resolveUseHoleCoordinate(_, nextCoordinate: Coordinate) -> Checkpoint:
    return {
        'goalCoordinate': nextCoordinate,
        'checkInCoordinate': [nextCoordinate[0], nextCoordinate[1], nextCoordinate[2] + 1],
    }

def resolveUseTeleportWaypointCoordinate(_, waypoint: Coordinate) -> Checkpoint:
    return {
        'goalCoordinate': waypoint['coordinate'],
        'checkInCoordinate': waypoint['coordinate'],
    }


# TODO: add unit tests
def resolveGoalCoordinate(coordinate: Coordinate, waypoint):
    if waypoint['type'] == 'useRope':
        return resolveUseRopeWaypointCoordinate(coordinate, waypoint['coordinate'])
    if waypoint['type'] == 'useShovel':
        return resolveUseShovelWaypointCoordinate(coordinate, waypoint['coordinate'])
    if waypoint['type'] == 'moveDown':
        return resolveMoveDownCoordinate(coordinate, waypoint)
    if waypoint['type'] == 'moveUp':
        return resolveMoveUpCoordinate(coordinate, waypoint)
    if waypoint['type'] == 'useHole':
        return resolveUseHoleCoordinate(coordinate, waypoint['coordinate'])
    if waypoint['type'] == 'useTeleport':
        return resolveUseTeleportWaypointCoordinate(coordinate, waypoint)
    return resolveFloorCoordinate(coordinate, waypoint['coordinate'])
