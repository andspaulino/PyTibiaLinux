import pyautogui
from contextlib import nullcontext
from time import sleep, time
import traceback
# Código original:
# from src.gameplay.cavebot import resolveCavebotTasks, shouldAskForCavebotTasks
from src.gameplay.combo import comboSpells
from src.gameplay.core.middlewares.battleList import setBattleListMiddleware
from src.gameplay.core.middlewares.chat import setChatTabsMiddleware
from src.gameplay.core.middlewares.gameWindow import VISUAL_TARGETING_FALLBACK_COORDINATE, canUseVisualTargetingWithoutRadar, setDirectionMiddleware, setTargetCreatureHistoryMiddleware, setGameWindowCreaturesMiddleware, setGameWindowMiddleware
from src.gameplay.core.middlewares.loot import hasAdjacentMonster, setLootChatMiddleware
from src.gameplay.core.middlewares.playerStatus import setMapPlayerStatusMiddleware
from src.gameplay.core.middlewares.radar import setRadarMiddleware, setWaypointIndexMiddleware
from src.gameplay.core.middlewares.screenshot import setScreenshotMiddleware
from src.gameplay.core.middlewares.tasks import setCleanUpTasksMiddleware
# Código original:
# from src.gameplay.core.tasks.lootCorpse import LootCorpseTask
from src.gameplay.core.tasks.common.base import BaseTask
from src.gameplay.core.tasks.quickLootNearbyCorpses import QuickLootNearbyCorpsesTask
from src.gameplay.core.tasks.walkToCorpse import WalkToCorpseTask
from src.gameplay.resolvers import resolveTasksByWaypoint
from src.gameplay.healing.observers.eatFood import eatFood
from src.gameplay.healing.observers.healingBySpells import healingBySpells
from src.gameplay.healing.observers.healingByPotions import healingByPotions
from src.gameplay.healing.observers.swapAmulet import swapAmulet
from src.gameplay.healing.observers.swapRing import swapRing
from src.gameplay.loot import (
    getClosestQuickLootCoordinate,
    isCoordinateInQuickLootRange,
    markCorpseAsProcessing,
    removeExpiredCorpses,
)
from src.gameplay.lootDiagnostics import printLootDiagnostic
from src.gameplay.navigation import getActiveTransientBlockedCoordinates
from src.gameplay.targeting import hasCreaturesToAttack, resolveTargetingTasks, shouldAskForTargetingTasks
from src.repositories.gameWindow.creatures import getClosestCreature, getClosestReachableCreature


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

QUICK_LOOT_STABILIZATION_DELAY = 0.15


def _getCurrentRootTask(context, currentTask):
    orchestratorRoot = getattr(
        context.get('tasksOrchestrator'),
        'rootTask',
        None,
    )
    if isinstance(orchestratorRoot, BaseTask):
        return orchestratorRoot
    if currentTask is None:
        return None
    return currentTask.rootTask or currentTask


class PyTibiaThread:
    # TODO: add typings
    def __init__(self, context, uiEnabled=False):
        self.context = context
        self.uiEnabled = uiEnabled

    def mainloop(self):
        # Seleção automática de janela no Linux (Modo CLI sem UI)
        # Código Linux anterior:
        # if self.context.context.get('window') is None:
        if (
            not self.uiEnabled
            and self.context.context.get('window') is None
        ):
            from src.utils.window import get_tibia_windows
            windows = get_tibia_windows()
            if windows:
                self.context.context['window'] = windows[0]
                self.context.context['pause'] = False
                print(f"[PyTibia Engine] Janela do Tibia conectada: {windows[0].title}")
            else:
                print("[PyTibia Engine] Aviso: Nenhuma janela do Tibia foi encontrada. Abra o jogo.")

        print("[PyTibia Engine] Loop de gameplay ativo.")

        # Código original/Linux anterior:
        # while True:
        while not self.context.context.get('shutdown', False):
            try:
                if self.context.context['pause']:
                    # Código original: continue
                    sleep(0.1)
                    continue
                startTime = time()
                gameplayLock = getattr(
                    self.context,
                    'gameplayLock',
                    nullcontext(),
                )
                with gameplayLock:
                    if (
                        self.context.context.get('shutdown', False)
                        or self.context.context['pause']
                    ):
                        continue
                    self.context.context = self.handleGameData(
                        self.context.context)
                    self.context.context = self.handleGameplayTasks(
                        self.context.context)
                    self.context.context = self.context.context[
                        'tasksOrchestrator'
                    ].do(self.context.context)
                    self.context.context['radar'][
                        'lastCoordinateVisited'
                    ] = self.context.context['radar']['coordinate']
                    healingByPotions(self.context.context)
                    healingBySpells(self.context.context)
                    comboSpells(self.context.context)
                    swapAmulet(self.context.context)
                    swapRing(self.context.context)
                    eatFood(self.context.context)
                endTime = time()
                diff = endTime - startTime
                sleep(max(0.045 - diff, 0))
            # Código Linux anterior (Marco 2.6):
            # except:
            #     print('An exception occurred:', traceback.format_exc())
            except Exception:
                print('An exception occurred:', traceback.format_exc())

    def handleGameData(self, context):
        if context['pause']:
            return context
        context = setScreenshotMiddleware(context)
        context = setRadarMiddleware(context)
        context = setChatTabsMiddleware(context)
        context = setBattleListMiddleware(context)
        context = setGameWindowMiddleware(context)
        context = setDirectionMiddleware(context)
        context = setGameWindowCreaturesMiddleware(context)
        # Código Linux anterior:
        # context = setLootHighlightingMiddleware(context)
        # context = setHandleLootMiddleware(context)
        context = setLootChatMiddleware(context)
        context = setTargetCreatureHistoryMiddleware(context)
        context = setWaypointIndexMiddleware(context)
        context = setMapPlayerStatusMiddleware(context)
        context = setCleanUpTasksMiddleware(context)
        return context

    # Código original da adaptação Linux antes do Marco 8.5:
    # def handleGameplayTasks(self, context):
    #     if not context['cavebot']['enabled']:
    #         return context
    #     context['cavebot']['closestCreature'] = getClosestCreature(
    #         context['gameWindow']['monsters'], context['radar']['coordinate'])
    #     currentTask = context['tasksOrchestrator'].getCurrentTask(context)
    #     if currentTask is not None and currentTask.name == 'selectChatTab':
    #         return context
    #     if len(context['loot']['corpsesToLoot']) > 0:
    #         context['way'] = 'lootCorpses'
    #         if currentTask is not None and currentTask.rootTask is not None and currentTask.rootTask.name != 'lootCorpse':
    #             context['tasksOrchestrator'].setRootTask(context, None)
    #         if context['tasksOrchestrator'].getCurrentTask(context) is None:
    #             firstDeadCorpse = context['loot']['corpsesToLoot'][0]
    #             context['tasksOrchestrator'].setRootTask(
    #                 context, LootCorpseTask(firstDeadCorpse))
    #         context['gameWindow']['previousMonsters'] = context['gameWindow']['monsters']
    #         return context
    #     hasCreaturesToAttackAfterCheck = hasCreaturesToAttack(context)
    #     if hasCreaturesToAttackAfterCheck:
    #         if context['cavebot']['closestCreature'] is not None:
    #             context['way'] = 'cavebot'
    #         else:
    #             context['way'] = 'waypoint'
    #     else:
    #         context['way'] = 'waypoint'
    #     if hasCreaturesToAttackAfterCheck and shouldAskForCavebotTasks(context):
    #         currentRootTask = currentTask.rootTask if currentTask is not None else None
    #         isTryingToAttackClosestCreature = currentRootTask is not None and (
    #             currentRootTask.name == 'attackClosestCreature')
    #         if not isTryingToAttackClosestCreature:
    #             context = resolveCavebotTasks(context)
    #     elif context['way'] == 'waypoint':
    #         if context['tasksOrchestrator'].getCurrentTask(context) is None:
    #             currentWaypointIndex = context['cavebot']['waypoints']['currentIndex']
    #             currentWaypoint = context['cavebot']['waypoints']['items'][currentWaypointIndex]
    #             context['tasksOrchestrator'].setRootTask(
    #                 context, resolveTasksByWaypoint(currentWaypoint))
    #     context['gameWindow']['previousMonsters'] = context['gameWindow']['monsters']
    #     return context

    def handleGameplayTasks(self, context):
        targetingEnabled = context['targeting'].get('enabled', False)
        cavebotEnabled = context['cavebot'].get('enabled', False)

        context['cavebot']['closestCreature'] = None
        hasAttackableCreatures = (
            targetingEnabled
            and hasCreaturesToAttack(context)
        )
        attackableMonsters = []
        if hasAttackableCreatures:
            canIgnoreCreatures = context['targeting'].get(
                'canIgnoreCreatures',
                True,
            )
            for monster in context['gameWindow']['monsters']:
                creatureConfig = context['targeting']['creatures'].get(
                    monster.get('name'),
                    {'ignore': False},
                )
                if canIgnoreCreatures and creatureConfig.get('ignore', False):
                    continue
                attackableMonsters.append(monster)

        # Código Linux anterior: o Targeting era bloqueado sempre que o Radar
        # não reconhecia a coordenada mundial, mesmo sem Cavebot/caminhada.
        # if (
        #     targetingEnabled
        #     and context['radar']['coordinate'] is not None
        #     and len(context['gameWindow']['monsters']) > 0
        # ):
        #     context['cavebot']['closestCreature'] = getClosestCreature(
        #         context['gameWindow']['monsters'], context['radar']['coordinate'])
        canResolveClosestCreature = (
            context['radar']['coordinate'] is not None
            or canUseVisualTargetingWithoutRadar(context)
        )
        if (
            targetingEnabled
            and hasAttackableCreatures
            and canResolveClosestCreature
            and len(attackableMonsters) > 0
        ):
            radarCoordinate = context['radar']['coordinate']
            if cavebotEnabled and radarCoordinate is not None:
                # Código Linux anterior:
                # context['cavebot']['closestCreature'] = getClosestCreature(
                #     context['gameWindow']['monsters'], radarCoordinate)
                nonWalkableCoordinates = list(
                    context['cavebot'].get('holesOrStairs', [])
                )
                nonWalkableCoordinates.extend(
                    getActiveTransientBlockedCoordinates(context)
                )
                context['cavebot']['closestCreature'] = (
                    getClosestReachableCreature(
                        attackableMonsters,
                        radarCoordinate,
                        nonWalkableCoordinates=nonWalkableCoordinates,
                    )
                )
            else:
                closestCreatureCoordinate = (
                    radarCoordinate
                    if radarCoordinate is not None
                    else VISUAL_TARGETING_FALLBACK_COORDINATE
                )
                context['cavebot']['closestCreature'] = getClosestCreature(
                    attackableMonsters,
                    closestCreatureCoordinate,
                )

        currentTask = context['tasksOrchestrator'].getCurrentTask(context)
        if currentTask is not None and currentTask.name == 'selectChatTab':
            return context

        lootState = context.get('loot', {})
        quickLootEnabled = lootState.get('enabled', False)
        # Código Linux anterior (recalculado após expiração para evitar estado obsoleto):
        # quickLootPending = (
        #     quickLootEnabled
        #     and lootState.get('pending', False)
        # )
        adjacentMonsterExists = hasAdjacentMonster(context)
        now = time()
        isPostCombatLootDelay = (
            now < lootState.get('movementBlockedUntil', 0)
        )
        isQuickLootInCooldown = (
            now < lootState.get('quickLootCooldownUntil', 0)
        )

        corpsesToLoot = lootState.setdefault('corpsesToLoot', [])
        currentRootTask = _getCurrentRootTask(context, currentTask)
        protectedCorpseCoordinate = None
        if currentRootTask is not None:
            if currentRootTask.name == 'lootCorpse':
                rootCorpse = getattr(currentRootTask, 'corpse', None)
                protectedCorpseCoordinate = (
                    rootCorpse.get('coordinate')
                    if isinstance(rootCorpse, dict)
                    else None
                )
            elif currentRootTask.name == 'quickLootNearbyCorpses':
                protectedCorpseCoordinate = getattr(
                    currentRootTask,
                    'selectedCorpseCoordinate',
                    None,
                )
        hadCorpses = len(corpsesToLoot) > 0
        removeExpiredCorpses(
            corpsesToLoot,
            context,
            protectedCoordinate=protectedCorpseCoordinate,
        )
        if hadCorpses and len(corpsesToLoot) == 0:
            lootState['pending'] = False

        quickLootPending = (
            quickLootEnabled
            and lootState.get('pending', False)
        )

        if quickLootPending and len(corpsesToLoot) > 0:
            context['way'] = 'lootCorpses'
            currentRootTask = _getCurrentRootTask(context, currentTask)
            if (
                currentRootTask is not None
                and currentRootTask.name == 'lootCorpse'
            ):
                context['gameWindow']['previousMonsters'] = (
                    context['gameWindow']['monsters']
                )
                return context
            if isPostCombatLootDelay or isQuickLootInCooldown:
                if currentRootTask is not None:
                    printLootDiagnostic(
                        'movement_root_cleared',
                        context,
                        adjacentMonster=adjacentMonsterExists,
                        reason='tracked_corpse_wait',
                    )
                    context['tasksOrchestrator'].setRootTask(context, None)
                context['gameWindow']['previousMonsters'] = (
                    context['gameWindow']['monsters']
                )
                return context

            selectedCorpse = corpsesToLoot[0]
            markCorpseAsProcessing(selectedCorpse)
            selectedCorpseCoordinate = selectedCorpse.get('coordinate')
            playerCoordinate = context.get('radar', {}).get('coordinate')

            if playerCoordinate is None:
                radarMissingCount = selectedCorpse.get('radarMissingCount', 0) + 1
                selectedCorpse['radarMissingCount'] = radarMissingCount
                # Código Linux anterior:
                # nextLootTask = QuickLootNearbyCorpsesTask(
                #     selectedCorpseCoordinate,
                #     discardSelectedCorpse=(radarMissingCount >= 3),
                # )
                # Sem Radar, o hotkey podia ser enviado mais de uma vez na
                # posição errada. As duas primeiras leituras agora apenas
                # aguardam; a terceira descarta com segurança e sem input.
                if radarMissingCount < 3:
                    context['gameWindow']['previousMonsters'] = (
                        context['gameWindow']['monsters']
                    )
                    return context
                nextLootTask = QuickLootNearbyCorpsesTask(
                    selectedCorpseCoordinate,
                    discardSelectedCorpse=True,
                )
            elif isCoordinateInQuickLootRange(
                playerCoordinate,
                selectedCorpseCoordinate,
            ):
                quickLootReadyAt = selectedCorpse.get('quickLootReadyAt')
                if quickLootReadyAt is None:
                    selectedCorpse['quickLootReadyAt'] = (
                        now + QUICK_LOOT_STABILIZATION_DELAY
                    )
                    printLootDiagnostic(
                        'corpse_stabilizing',
                        context,
                        corpseCoordinate=selectedCorpseCoordinate,
                        readyAt=selectedCorpse['quickLootReadyAt'],
                    )
                    if currentRootTask is not None:
                        context['tasksOrchestrator'].setRootTask(
                            context,
                            None,
                        )
                    context['gameWindow']['previousMonsters'] = (
                        context['gameWindow']['monsters']
                    )
                    return context
                if now < quickLootReadyAt:
                    context['gameWindow']['previousMonsters'] = (
                        context['gameWindow']['monsters']
                    )
                    return context
                nextLootTask = QuickLootNearbyCorpsesTask(
                    selectedCorpseCoordinate,
                    discardSelectedCorpse=False,
                )
            elif selectedCorpse.get('approachFailed', False):
                nextLootTask = QuickLootNearbyCorpsesTask(
                    selectedCorpseCoordinate,
                    discardSelectedCorpse=True,
                )
            else:
                selectedCorpse.pop('quickLootReadyAt', None)
                approachCoordinate = getClosestQuickLootCoordinate(
                    playerCoordinate,
                    selectedCorpseCoordinate,
                )
                if approachCoordinate is None:
                    selectedCorpse['approachFailed'] = True
                    nextLootTask = QuickLootNearbyCorpsesTask(
                        selectedCorpseCoordinate,
                        discardSelectedCorpse=True,
                    )
                else:
                    nextLootTask = WalkToCorpseTask(
                        approachCoordinate,
                        selectedCorpse,
                    )
            if currentRootTask is not None:
                context['tasksOrchestrator'].setRootTask(context, None)
            context['tasksOrchestrator'].setRootTask(
                context,
                nextLootTask,
            )
            printLootDiagnostic(
                'corpse_task_scheduled',
                context,
                corpseCoordinate=selectedCorpseCoordinate,
                nextTask=nextLootTask.name,
            )
            context['gameWindow']['previousMonsters'] = (
                context['gameWindow']['monsters']
            )
            return context

        # Código Linux anterior:
        # `quickLootReady`, Highlighting, confirmação visual e retries decidiam
        # quando criar esta root. O fluxo simples usa somente uma nova linha
        # `Loot of` e a ausência de monstro adjacente.
        if quickLootPending and not adjacentMonsterExists:
            context['way'] = 'lootPending'
            currentRootTask = (
                currentTask.rootTask
                if currentTask is not None and currentTask.rootTask is not None
                else currentTask
            )
            if isPostCombatLootDelay or isQuickLootInCooldown:
                if currentRootTask is not None:
                    printLootDiagnostic(
                        'movement_root_cleared',
                        context,
                        adjacentMonster=False,
                        reason='loot_wait',
                    )
                    context['tasksOrchestrator'].setRootTask(context, None)
                context['gameWindow']['previousMonsters'] = (
                    context['gameWindow']['monsters']
                )
                return context
            if (
                currentRootTask is not None
                and currentRootTask.name != 'quickLootNearbyCorpses'
            ):
                printLootDiagnostic(
                    'movement_root_cleared',
                    context,
                    adjacentMonster=False,
                    reason='quick_loot_priority',
                )
                context['tasksOrchestrator'].setRootTask(context, None)
            if context['tasksOrchestrator'].getCurrentTask(context) is None:
                context['tasksOrchestrator'].setRootTask(
                    context,
                    QuickLootNearbyCorpsesTask(),
                )
            context['gameWindow']['previousMonsters'] = (
                context['gameWindow']['monsters']
            )
            return context

        # Código original:
        # a fila `corpsesToLoot` criava `LootCorpseTask`, que executava nove
        # Shift+RightClick. O cliente atual usa uma única operação de área.

        # Código Linux anterior (Marco 8.5):
        # hasCreaturesToAttackAfterCheck = (
        #     targetingEnabled
        #     and context['cavebot']['closestCreature'] is not None
        #     and hasCreaturesToAttack(context)
        # )
        # if hasCreaturesToAttackAfterCheck:
        #     context['way'] = 'targeting'
        #     if shouldAskForTargetingTasks(context):
        #         currentRootTask = currentTask.rootTask if currentTask is not None else None
        #         isTryingToAttackClosestCreature = currentRootTask is not None and (
        #             currentRootTask.name == 'attackClosestCreature')
        #         if not isTryingToAttackClosestCreature:
        #             context = resolveTargetingTasks(context)

        # Código Linux anterior (Marco 8.7):
        # isQuickLootPending = (
        #     quickLootEnabled
        #     and lootState.get('quickLootDetectionPending', False)
        # )
        # hasCreaturesToAttackAfterCheck = (
        #     targetingEnabled
        #     and context['cavebot']['closestCreature'] is not None
        #     and hasCreaturesToAttack(context)
        # )
        # if isQuickLootPending and not lootState.get('quickLootReady', False):
        #     context['way'] = 'lootPending'
        #     currentRootTask = (
        #         currentTask.rootTask
        #         if currentTask is not None and currentTask.rootTask is not None
        #         else currentTask
        #     )
        #     if (
        #         currentRootTask is not None
        #         and currentRootTask.name == 'attackClosestCreature'
        #     ):
        #         context['tasksOrchestrator'].setRootTask(context, None)
        # elif hasCreaturesToAttackAfterCheck:
        #     context['way'] = 'targeting'
        #     if shouldAskForTargetingTasks(context):
        #         currentRootTask = currentTask.rootTask if currentTask is not None else None
        #         isTryingToAttackClosestCreature = currentRootTask is not None and (
        #             currentRootTask.name == 'attackClosestCreature')
        #         if not isTryingToAttackClosestCreature:
        #             context = resolveTargetingTasks(context)

        # Código Linux anterior:
        # lootBlocksMovement = quickLootPending
        lootBlocksMovement = (
            quickLootPending
            or isPostCombatLootDelay
            or isQuickLootInCooldown
        )
        allowChase = (
            targetingEnabled
            and cavebotEnabled
            and context['radar']['coordinate'] is not None
            and not context.get('pause', False)
            and not lootBlocksMovement
        )
        # Código Linux anterior:
        # hasCreaturesToAttackAfterCheck = (
        #     targetingEnabled
        #     and hasCreaturesToAttack(context)
        # )
        hasCreaturesToAttackAfterCheck = (
            targetingEnabled
            and hasAttackableCreatures
            and context['cavebot']['closestCreature'] is not None
        )

        if hasCreaturesToAttackAfterCheck:
            context['way'] = 'targeting'
            currentRootTask = (
                currentTask.rootTask
                if currentTask is not None and currentTask.rootTask is not None
                else currentTask
            )
            hasAttackRootWithDifferentChaseMode = (
                currentRootTask is not None
                and currentRootTask.name == 'attackClosestCreature'
                and getattr(currentRootTask, 'allowChase', False) != allowChase
            )
            if (
                hasAttackRootWithDifferentChaseMode
                or shouldAskForTargetingTasks(context)
            ):
                hasMatchingAttackRoot = (
                    currentRootTask is not None
                    and currentRootTask.name == 'attackClosestCreature'
                    and getattr(currentRootTask, 'allowChase', False) == allowChase
                )
                if not hasMatchingAttackRoot:
                    if (
                        hasAttackRootWithDifferentChaseMode
                        and lootBlocksMovement
                    ):
                        printLootDiagnostic(
                            'chase_disabled',
                            context,
                            adjacentMonster=adjacentMonsterExists,
                        )
                    context = resolveTargetingTasks(
                        context,
                        allowChase=allowChase,
                    )
        else:
            targetIsCurrentlyUnreachable = (
                targetingEnabled
                and cavebotEnabled
                and context['radar']['coordinate'] is not None
                and hasAttackableCreatures
                and context['cavebot']['closestCreature'] is None
            )
            if (
                targetIsCurrentlyUnreachable
                and currentRootTask is not None
                and currentRootTask.name == 'attackClosestCreature'
            ):
                printLootDiagnostic(
                    'target_unreachable',
                    context,
                    reason='no-adjacent-path',
                )
                context['tasksOrchestrator'].setRootTask(context, None)
            if lootBlocksMovement:
                context['way'] = (
                    'lootPending'
                    if quickLootPending
                    else 'lootStabilizing'
                )
                currentRootTask = (
                    currentTask.rootTask
                    if currentTask is not None and currentTask.rootTask is not None
                    else currentTask
                )
                if currentRootTask is not None:
                    printLootDiagnostic(
                        'movement_root_cleared',
                        context,
                        adjacentMonster=adjacentMonsterExists,
                    )
                    context['tasksOrchestrator'].setRootTask(context, None)
            else:
                context['way'] = 'waypoint' if cavebotEnabled else None
                currentTask = context['tasksOrchestrator'].getCurrentTask(context)
                currentWaypointIndex = context['cavebot']['waypoints']['currentIndex']
                waypoints = context['cavebot']['waypoints']['items']
                if (
                    cavebotEnabled
                    and currentTask is None
                    and currentWaypointIndex is not None
                    and 0 <= currentWaypointIndex < len(waypoints)
                ):
                    context['tasksOrchestrator'].setRootTask(
                        context, resolveTasksByWaypoint(waypoints[currentWaypointIndex]))

        context['gameWindow']['previousMonsters'] = context['gameWindow']['monsters']
        return context
