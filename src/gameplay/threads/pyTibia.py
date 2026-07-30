import pyautogui
from time import sleep, time
import traceback
# Código original:
# from src.gameplay.cavebot import resolveCavebotTasks, shouldAskForCavebotTasks
from src.gameplay.combo import comboSpells
from src.gameplay.core.middlewares.battleList import setBattleListMiddleware
from src.gameplay.core.middlewares.chat import setChatTabsMiddleware
from src.gameplay.core.middlewares.gameWindow import VISUAL_TARGETING_FALLBACK_COORDINATE, canUseVisualTargetingWithoutRadar, setDirectionMiddleware, setHandleLootMiddleware, setGameWindowCreaturesMiddleware, setGameWindowMiddleware
from src.gameplay.core.middlewares.loot import setLootHighlightingMiddleware
from src.gameplay.core.middlewares.playerStatus import setMapPlayerStatusMiddleware
from src.gameplay.core.middlewares.radar import setRadarMiddleware, setWaypointIndexMiddleware
from src.gameplay.core.middlewares.screenshot import setScreenshotMiddleware
from src.gameplay.core.middlewares.tasks import setCleanUpTasksMiddleware
from src.gameplay.core.tasks.lootCorpse import LootCorpseTask
from src.gameplay.core.tasks.quickLootNearbyCorpses import QuickLootNearbyCorpsesTask
from src.gameplay.resolvers import resolveTasksByWaypoint
from src.gameplay.healing.observers.eatFood import eatFood
from src.gameplay.healing.observers.healingBySpells import healingBySpells
from src.gameplay.healing.observers.healingByPotions import healingByPotions
from src.gameplay.healing.observers.swapAmulet import swapAmulet
from src.gameplay.healing.observers.swapRing import swapRing
from src.gameplay.targeting import hasCreaturesToAttack, resolveTargetingTasks, shouldAskForTargetingTasks
from src.repositories.gameWindow.creatures import getClosestCreature


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


class PyTibiaThread:
    # TODO: add typings
    def __init__(self, context):
        self.context = context

    def mainloop(self):
        # Seleção automática de janela no Linux (Modo CLI sem UI)
        if self.context.context.get('window') is None:
            from src.utils.window import get_tibia_windows
            windows = get_tibia_windows()
            if windows:
                self.context.context['window'] = windows[0]
                self.context.context['pause'] = False
                print(f"[PyTibia Engine] Janela do Tibia conectada: {windows[0].title}")
            else:
                print("[PyTibia Engine] Aviso: Nenhuma janela do Tibia foi encontrada. Abra o jogo.")

        print("[PyTibia Engine] Loop de gameplay ativo.")

        while True:
            try:
                if self.context.context['pause']:
                    # Código original: continue
                    sleep(0.1)
                    continue
                startTime = time()
                self.context.context = self.handleGameData(
                    self.context.context)
                self.context.context = self.handleGameplayTasks(
                    self.context.context)
                self.context.context = self.context.context['tasksOrchestrator'].do(
                    self.context.context)
                self.context.context['radar']['lastCoordinateVisited'] = self.context.context['radar']['coordinate']
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
        context = setLootHighlightingMiddleware(context)
        context = setHandleLootMiddleware(context)
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
            and canResolveClosestCreature
            and len(context['gameWindow']['monsters']) > 0
        ):
            closestCreatureCoordinate = (
                context['radar']['coordinate']
                if context['radar']['coordinate'] is not None
                else VISUAL_TARGETING_FALLBACK_COORDINATE
            )
            context['cavebot']['closestCreature'] = getClosestCreature(
                context['gameWindow']['monsters'], closestCreatureCoordinate)

        currentTask = context['tasksOrchestrator'].getCurrentTask(context)
        if currentTask is not None and currentTask.name == 'selectChatTab':
            return context

        lootState = context.get('loot', {})
        quickLootEnabled = (
            lootState.get('enabled', False)
            and lootState.get('mode', 'quickLoot') == 'quickLoot'
        )
        now = time()
        isQuickLootInCooldown = now < lootState.get('quickLootCooldownUntil', 0)
        # Código Linux anterior (Marco 8.7):
        # if quickLootEnabled and lootState.get('quickLootReady', False):
        if quickLootEnabled and lootState.get('quickLootReady', False) and not isQuickLootInCooldown:
            context['way'] = 'lootCorpses'
            currentRootTask = (
                currentTask.rootTask
                if currentTask is not None and currentTask.rootTask is not None
                else currentTask
            )
            if (
                currentRootTask is not None
                and currentRootTask.name != 'quickLootNearbyCorpses'
            ):
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

        # Código original: o Looting legado permanece disponível para o modo
        # de abertura individual de corpses associado ao Cavebot.
        if cavebotEnabled and len(context['loot']['corpsesToLoot']) > 0:
            context['way'] = 'lootCorpses'
            if currentTask is not None and currentTask.rootTask is not None and currentTask.rootTask.name != 'lootCorpse':
                context['tasksOrchestrator'].setRootTask(context, None)
            if context['tasksOrchestrator'].getCurrentTask(context) is None:
                # TODO: get closest dead corpse
                firstDeadCorpse = context['loot']['corpsesToLoot'][0]
                context['tasksOrchestrator'].setRootTask(
                    context, LootCorpseTask(firstDeadCorpse))
            context['gameWindow']['previousMonsters'] = context['gameWindow']['monsters']
            return context

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

        now = time()
        isQuickLootInCooldown = now < lootState.get('quickLootCooldownUntil', 0)
        isQuickLootReady = (
            quickLootEnabled
            and lootState.get('quickLootReady', False)
            and not isQuickLootInCooldown
        )
        hasHighlightedCandidates = (
            len(lootState.get('highlightedSlots', [])) > 0
        )
        # Código Linux anterior: só bloqueava depois dos 12 frames, quando já
        # havia highlight, e liberava durante o cooldown/confirmação. Com
        # `walkToTarget`, o corpse podia sair do `3×3` antes do Quick Loot.
        # isQuickLootPending = (
        #     quickLootEnabled
        #     and lootState.get('quickLootDetectionPending', False)
        #     and not isQuickLootInCooldown
        #     and hasHighlightedCandidates
        # )
        isQuickLootPending = (
            quickLootEnabled
            and lootState.get('quickLootDetectionPending', False)
            and (
                lootState.get('quickLootBlockingSlot') is not None
                or lootState.get('quickLootAwaitingConfirmation', False)
                or hasHighlightedCandidates
            )
        )

        lootBlocksMovement = isQuickLootPending or isQuickLootReady
        allowChase = (
            targetingEnabled
            and cavebotEnabled
            and context['radar']['coordinate'] is not None
            and not context.get('pause', False)
            and not lootBlocksMovement
        )
        hasCreaturesToAttackAfterCheck = (
            targetingEnabled
            and hasCreaturesToAttack(context)
        )

        if isQuickLootPending and not isQuickLootReady:
            context['way'] = 'lootPending'
            currentRootTask = (
                currentTask.rootTask
                if currentTask is not None and currentTask.rootTask is not None
                else currentTask
            )
            if (
                currentRootTask is not None
                and currentRootTask.name == 'attackClosestCreature'
            ):
                context['tasksOrchestrator'].setRootTask(context, None)
        elif hasCreaturesToAttackAfterCheck:
            context['way'] = 'targeting'
            if shouldAskForTargetingTasks(context):
                currentRootTask = (
                    currentTask.rootTask
                    if currentTask is not None and currentTask.rootTask is not None
                    else currentTask
                )
                hasMatchingAttackRoot = (
                    currentRootTask is not None
                    and currentRootTask.name == 'attackClosestCreature'
                    and getattr(currentRootTask, 'allowChase', False) == allowChase
                )
                if not hasMatchingAttackRoot:
                    context = resolveTargetingTasks(
                        context,
                        allowChase=allowChase,
                    )
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
