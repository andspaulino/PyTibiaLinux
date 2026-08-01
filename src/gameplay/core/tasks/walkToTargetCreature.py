import numpy as np
from scipy.spatial import distance
from src.gameplay.typings import Context
import src.gameplay.utils as gameplayUtils
from ...lootDiagnostics import printLootDiagnostic
from ...typings import Context
from ...utils import releaseKeys
from ..waypoint import generateFloorWalkpoints
from .common.vector import VectorTask
from .walk import WalkTask


class WalkToTargetCreatureTask(VectorTask):
    def __init__(self):
        super().__init__()
        self.name = 'walkToTargetCreature'
        self.manuallyTerminable = True
        self.targetCreatureCoordinateSinceLastRestart = None

    def onBeforeStart(self, context: Context) -> Context:
        self.calculatePathToTargetCreature(context)
        return context

    def onBeforeRestart(self, context: Context) -> Context:
        targetCreature = context['cavebot'].get('targetCreature') or {}
        printLootDiagnostic(
            'chase_restart',
            context,
            previousTargetCoordinate=self.targetCreatureCoordinateSinceLastRestart,
            nextTargetCoordinate=targetCreature.get('coordinate'),
        )
        context = releaseKeys(context)
        return self.onBeforeStart(context)

    def onInterrupt(self, context: Context) -> Context:
        printLootDiagnostic('chase_interrupt', context)
        return releaseKeys(context)

    def onComplete(self, context: Context) -> Context:
        printLootDiagnostic('chase_complete', context)
        return releaseKeys(context)

    # Código original Windows:
    # def shouldRestart(self, context: Context) -> bool:
    #     if len(self.tasks) == 0:
    #         return True
    #     if context['cavebot']['targetCreature'] is None:
    #         return True
    #     return not gameplayUtils.coordinatesAreEqual(context['cavebot']['targetCreature']['coordinate'], self.targetCreatureCoordinateSinceLastRestart)

    # Adaptação Linux: Evita cancelar a rota em andamento (len(self.tasks) > 0)
    # quando a criatura à distância apenas dá um pequeno passo de 1 SQM,
    # permitindo caminhada contínua até concluir os passos ou se o alvo se afastar > 2 SQM.
    def shouldRestart(self, context: Context) -> bool:
        if len(self.tasks) == 0:
            return True
        if context['cavebot']['targetCreature'] is None:
            return True
        if self.targetCreatureCoordinateSinceLastRestart is None:
            return True
        targetCoord = context['cavebot']['targetCreature']['coordinate']
        if targetCoord[2] != self.targetCreatureCoordinateSinceLastRestart[2]:
            return True
        distShift = distance.cdist([targetCoord], [self.targetCreatureCoordinateSinceLastRestart]).flatten()[0]
        return bool(distShift > 2)

    def shouldManuallyComplete(self, context: Context) -> bool:
        if context['cavebot']['isAttackingSomeCreature'] == False:
            return True
        return False

    def calculatePathToTargetCreature(self, context: Context):
        self.tasks = []
        if context['cavebot']['targetCreature'] is None:
            return
        nonWalkableCoordinates = context['cavebot']['holesOrStairs'].copy()
        # TODO: also, detect players
        for monster in context['gameWindow']['monsters']:
            if np.array_equal(monster['coordinate'], context['cavebot']['targetCreature']['coordinate']) == False:
                nonWalkableCoordinates.append(monster['coordinate'])
        walkpoints = []
        dist = distance.cdist([context['radar']['coordinate']], [
                              context['cavebot']['targetCreature']['coordinate']]).flatten()[0]
        if dist < 2:
            gameWindowHeight, gameWindowWidth = context['gameWindow']['image'].shape
            gameWindowCenter = (gameWindowWidth // 2, gameWindowHeight // 2)
            monsterGameWindowCoordinate = context['cavebot']['targetCreature']['gameWindowCoordinate']
            moduleX = abs(gameWindowCenter[0] - monsterGameWindowCoordinate[0])
            moduleY = abs(gameWindowCenter[1] - monsterGameWindowCoordinate[1])
            if moduleX > 64 or moduleY > 64:
                walkpoints.append(context['cavebot']
                                  ['targetCreature']['coordinate'])
        else:
            walkpoints = generateFloorWalkpoints(
                context['radar']['coordinate'], context['cavebot']['targetCreature']['coordinate'], nonWalkableCoordinates=nonWalkableCoordinates)
            if walkpoints:
                walkpoints.pop()
        for walkpoint in walkpoints:
            self.tasks.append(WalkTask(context, walkpoint).setParentTask(
                self).setRootTask(self.rootTask))
        self.targetCreatureCoordinateSinceLastRestart = context['cavebot']['targetCreature']['coordinate'].copy(
        )
