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
        return self.onBeforeStart(context)

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

    # TODO: add unit tests
    def calculateWalkpoint(self, context: Context):
        nonWalkableCoordinates = context['cavebot']['holesOrStairs'].copy()
        for monster in context['gameWindow']['monsters']:
            nonWalkableCoordinates.append(monster['coordinate'])

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
