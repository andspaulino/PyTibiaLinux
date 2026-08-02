from time import time

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


PATH_RETRY_INTERVAL = 0.25


class WalkToTargetCreatureTask(VectorTask):
    def __init__(self):
        super().__init__()
        self.name = 'walkToTargetCreature'
        self.manuallyTerminable = True
        self.targetCreatureCoordinateSinceLastRestart = None
        self.nextPathRetryAt = 0

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

    # Código Linux anterior:
    # def shouldRestart(self, context: Context) -> bool:
    #     if len(self.tasks) == 0:
    #         return True
    #     if context['cavebot']['targetCreature'] is None:
    #         return True
    #     if self.targetCreatureCoordinateSinceLastRestart is None:
    #         return True
    #     targetCoord = context['cavebot']['targetCreature']['coordinate']
    #     if targetCoord[2] != self.targetCreatureCoordinateSinceLastRestart[2]:
    #         return True
    #     distShift = distance.cdist(
    #         [targetCoord],
    #         [self.targetCreatureCoordinateSinceLastRestart],
    #     ).flatten()[0]
    #     return bool(distShift > 2)

    # Adaptação Linux: preserva os passos durante perda visual transitória do
    # marcador de ataque, evita restart quando o alvo já está adjacente e
    # limita tentativas sem caminho para não liberar teclas a cada frame.
    def shouldRestart(self, context: Context) -> bool:
        targetCreature = context['cavebot'].get('targetCreature')
        if targetCreature is None:
            return False
        targetCoord = targetCreature.get('coordinate')
        if targetCoord is None:
            return False
        if self.targetCreatureCoordinateSinceLastRestart is None:
            return True
        if targetCoord[2] != self.targetCreatureCoordinateSinceLastRestart[2]:
            return True
        distShift = distance.cdist(
            [targetCoord],
            [self.targetCreatureCoordinateSinceLastRestart],
        ).flatten()[0]
        if distShift > 2:
            return True
        if len(self.tasks) > 0:
            return False
        playerCoordinate = context.get('radar', {}).get('coordinate')
        if playerCoordinate is None or playerCoordinate[2] != targetCoord[2]:
            return False
        isAdjacent = (
            abs(playerCoordinate[0] - targetCoord[0]) <= 1
            and abs(playerCoordinate[1] - targetCoord[1]) <= 1
        )
        if isAdjacent:
            return False
        return time() >= self.nextPathRetryAt

    def shouldManuallyComplete(self, context: Context) -> bool:
        if context['cavebot']['isAttackingSomeCreature'] == False:
            return True
        return False

    def calculatePathToTargetCreature(self, context: Context):
        targetCreature = context['cavebot'].get('targetCreature')
        if targetCreature is None:
            return
        self.tasks = []
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
        self.targetCreatureCoordinateSinceLastRestart = context['cavebot'][
            'targetCreature'
        ]['coordinate'].copy()
        self.nextPathRetryAt = (
            time() + PATH_RETRY_INTERVAL
            if len(self.tasks) == 0
            else 0
        )
