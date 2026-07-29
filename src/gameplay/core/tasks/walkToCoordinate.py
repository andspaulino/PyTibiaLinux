from src.gameplay.typings import Context
import src.gameplay.utils as gameplayUtils
from src.repositories.radar.typings import Coordinate
from ...typings import Context
from ..waypoint import calculateFloorWalkpoints
from .common.vector import VectorTask
from .walk import WalkTask


class WalkToCoordinateTask(VectorTask):
    def __init__(self, coordinate: Coordinate):
        super().__init__()
        self.name = 'walkToCoordinate'
        self.coordinate = coordinate
        self.pathfindingFailureReason = None
        self.nonWalkableCoordinatesSignature = None

    def shouldRestartAfterAllChildrensComplete(self, context: Context) -> bool:
        # Código original:
        # if len(self.tasks) == 0:
        #     return True
        # return not gameplayUtils.coordinatesAreEqual(context['radar']['coordinate'], self.coordinate)
        if self.pathfindingFailureReason is not None:
            return False
        if len(self.tasks) == 0:
            return True
        return not gameplayUtils.coordinatesAreEqual(
            context['radar']['coordinate'], self.coordinate
        )

    def onBeforeStart(self, context: Context) -> Context:
        self.calculateWalkpoint(context)
        return context

    def onBeforeRestart(self, context: Context) -> Context:
        context = gameplayUtils.releaseKeys(context)
        return self.onBeforeStart(context)

    def shouldRestart(self, context: Context) -> bool:
        if context['radar']['coordinate'] is None:
            return False
        currentSignature = self.getNonWalkableCoordinatesSignature(context)
        if self.nonWalkableCoordinatesSignature is None:
            return False
        obstaclesChanged = currentSignature != self.nonWalkableCoordinatesSignature
        if obstaclesChanged:
            navigation = context.setdefault('cavebot', {}).setdefault('navigation', {})
            navigation['status'] = 'recalculating'
            navigation['failureReason'] = 'obstacles-changed'
            navigation['plannedDirection'] = None
        return obstaclesChanged

    def onInterrupt(self, context: Context) -> Context:
        navigation = context.setdefault('cavebot', {}).setdefault('navigation', {})
        navigation['plannedDirection'] = None
        return gameplayUtils.releaseKeys(context)

    def onComplete(self, context: Context):
        navigation = context.setdefault('cavebot', {}).setdefault('navigation', {})
        navigation['plannedDirection'] = None
        if self.pathfindingFailureReason is None:
            navigation['status'] = 'completed'
        return gameplayUtils.releaseKeys(context)

    def did(self, context: Context) -> bool:
        if self.pathfindingFailureReason is not None:
            return False
        return gameplayUtils.coordinatesAreEqual(
            context['radar']['coordinate'], self.coordinate
        )

    def getNonWalkableCoordinates(self, context: Context):
        # Código original:
        # nonWalkableCoordinates = context['cavebot']['holesOrStairs'].copy()
        # for monster in context['gameWindow']['monsters']:
        #     nonWalkableCoordinates.append(monster['coordinate'])
        coordinate = context['radar']['coordinate']
        floor = coordinate[2] if coordinate is not None and len(coordinate) == 3 else None
        candidates = list(context['cavebot']['holesOrStairs'])
        candidates.extend(
            monster.get('coordinate')
            for monster in context['gameWindow']['monsters']
            if isinstance(monster, dict)
        )
        nonWalkableCoordinates = []
        seen = set()
        for candidate in candidates:
            if candidate is None or not hasattr(candidate, '__len__') or len(candidate) != 3:
                continue
            normalizedCoordinate = tuple(candidate)
            if floor is None or normalizedCoordinate[2] != floor:
                continue
            if normalizedCoordinate in seen:
                continue
            seen.add(normalizedCoordinate)
            nonWalkableCoordinates.append(normalizedCoordinate)
        return sorted(nonWalkableCoordinates)

    def getNonWalkableCoordinatesSignature(self, context: Context):
        return tuple(self.getNonWalkableCoordinates(context))

    # TODO: add unit tests
    def calculateWalkpoint(self, context: Context):
        nonWalkableCoordinates = self.getNonWalkableCoordinates(context)
        self.nonWalkableCoordinatesSignature = tuple(nonWalkableCoordinates)

        # Código original:
        # self.tasks = []
        # for walkpoint in generateFloorWalkpoints(
        #         context['radar']['coordinate'], self.coordinate, nonWalkableCoordinates=nonWalkableCoordinates):
        #     self.tasks.append(WalkTask(context, walkpoint).setParentTask(
        #         self).setRootTask(self.rootTask))
        walkpoints, failureReason = calculateFloorWalkpoints(
            context['radar']['coordinate'],
            self.coordinate,
            nonWalkableCoordinates=nonWalkableCoordinates,
        )
        self.pathfindingFailureReason = failureReason
        self.tasks = [
            WalkTask(context, walkpoint).setParentTask(self).setRootTask(self.rootTask)
            for walkpoint in walkpoints
        ]

        navigation = context['cavebot'].setdefault('navigation', {})
        navigation['goalCoordinate'] = self.coordinate
        navigation['walkpoints'] = walkpoints
        navigation['nextWalkpoint'] = walkpoints[0] if walkpoints else None
        navigation['blockedCoordinates'] = nonWalkableCoordinates
        navigation['failureReason'] = failureReason
        navigation['plannedDirection'] = None
        navigation['status'] = 'blocked' if failureReason else (
            'completed' if len(walkpoints) == 0 else 'walking'
        )
