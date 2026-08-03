from src.gameplay.typings import Context
import src.gameplay.utils as gameplayUtils
from src.repositories.radar.typings import Coordinate
from ...typings import Context
from ..waypoint import generateFloorWalkpoints
from .common.vector import VectorTask
from .walk import WalkTask


class WalkToCoordinateTask(VectorTask):
    def __init__(self, coordinate: Coordinate):
        super().__init__()
        self.name = 'walkToCoordinate'
        self.coordinate = coordinate
        self.navigationState = 'uninitialized'

    def did(self, context: Context) -> bool:
        currentCoordinate = context['radar']['coordinate']
        if currentCoordinate is None:
            return False
        return gameplayUtils.coordinatesAreEqual(
            currentCoordinate,
            self.coordinate,
        )

    def shouldRestart(self, context: Context) -> bool:
        currentCoordinate = context['radar']['coordinate']
        if currentCoordinate is None:
            return self.navigationState != 'radar-unavailable'
        return self.navigationState == 'radar-unavailable'

    def shouldRestartAfterAllChildrensComplete(self, context: Context) -> bool:
        if context['radar']['coordinate'] is None:
            return False
        if len(self.tasks) == 0:
            return True
        return not gameplayUtils.coordinatesAreEqual(context['radar']['coordinate'], self.coordinate)

    def onBeforeStart(self, context: Context) -> Context:
        self.calculateWalkpoint(context)
        return context

    def onBeforeRestart(self, context: Context) -> Context:
        # Código original:
        # return self.onBeforeStart(context)
        context = gameplayUtils.releaseKeys(context)
        return self.onBeforeStart(context)

    def onInterrupt(self, context: Context) -> Context:
        return gameplayUtils.releaseKeys(context)

    def onComplete(self, context: Context):
        return gameplayUtils.releaseKeys(context)

    # TODO: add unit tests
    def calculateWalkpoint(self, context: Context):
        self.tasks = []
        currentCoordinate = context['radar']['coordinate']

        if currentCoordinate is None:
            self.navigationState = 'radar-unavailable'
            return

        if (
            not isinstance(self.coordinate, (list, tuple))
            or len(self.coordinate) != 3
            or any(value is None for value in self.coordinate)
        ):
            self.navigationState = 'invalid-target'
            return

        if currentCoordinate[2] != self.coordinate[2]:
            self.navigationState = 'wrong-floor'
            return

        if gameplayUtils.coordinatesAreEqual(
            currentCoordinate,
            self.coordinate,
        ):
            self.navigationState = 'arrived'
            return

        # Código original:
        # nonWalkableCoordinates = context['cavebot']['holesOrStairs'].copy()
        # for monster in context['gameWindow']['monsters']:
        #     nonWalkableCoordinates.append(monster['coordinate'])
        # for walkpoint in generateFloorWalkpoints(
        #         context['radar']['coordinate'], self.coordinate,
        #         nonWalkableCoordinates=nonWalkableCoordinates):
        #     self.tasks.append(WalkTask(context, walkpoint).setParentTask(
        #         self).setRootTask(self.rootTask))
        nonWalkableCoordinates = context['cavebot']['holesOrStairs'].copy()
        for monster in context['gameWindow']['monsters']:
            nonWalkableCoordinates.append(monster['coordinate'])
        walkpoints = generateFloorWalkpoints(
            currentCoordinate,
            self.coordinate,
            nonWalkableCoordinates=nonWalkableCoordinates,
        )
        if len(walkpoints) == 0:
            self.navigationState = 'path-not-found'
            return

        self.navigationState = 'path-available'
        for walkpoint in walkpoints:
            self.tasks.append(WalkTask(context, walkpoint).setParentTask(
                self).setRootTask(self.rootTask))
