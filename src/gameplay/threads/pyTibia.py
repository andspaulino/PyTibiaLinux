import pyautogui
from time import sleep, time
import traceback
from src.gameplay.cavebot import resolveCavebotTasks, shouldAskForCavebotTasks
from src.gameplay.combo import comboSpells
from src.gameplay.core.middlewares.battleList import setBattleListMiddleware
from src.gameplay.core.middlewares.chat import setChatTabsMiddleware
from src.gameplay.core.middlewares.gameWindow import setDirectionMiddleware, setHandleLootMiddleware, setGameWindowCreaturesMiddleware, setGameWindowMiddleware
from src.gameplay.core.middlewares.playerStatus import setMapPlayerStatusMiddleware
from src.gameplay.core.middlewares.radar import setRadarMiddleware, setWaypointIndexMiddleware
from src.gameplay.core.middlewares.screenshot import setScreenshotMiddleware
from src.gameplay.core.middlewares.tasks import setCleanUpTasksMiddleware
from src.gameplay.core.tasks.lootCorpse import LootCorpseTask
from src.gameplay.resolvers import resolveTasksByWaypoint
from src.gameplay.healing.observers.eatFood import eatFood
from src.gameplay.healing.observers.healingBySpells import healingBySpells
from src.gameplay.healing.observers.healingByPotions import healingByPotions
from src.gameplay.healing.observers.swapAmulet import swapAmulet
from src.gameplay.healing.observers.swapRing import swapRing
from src.gameplay.targeting import hasCreaturesToAttack
from src.repositories.gameWindow.creatures import getClosestCreature


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


class PyTibiaThread:
    # TODO: add typings
    # Código original:
    # def __init__(self, context):
    #     self.context = context
    def __init__(self, context, uiEnabled=False):
        self.context = context
        self.uiEnabled = uiEnabled
        self._lastDiagnosticState = None

    def mainloop(self):
        if (
            not self.uiEnabled
            and self.context.context.get('window') is None
        ):
            from src.utils.window import get_tibia_windows
            windows = get_tibia_windows()
            if windows:
                self.context.context['window'] = windows[0]
                self.context.context['pause'] = False
                print(
                    '[PyTibia Engine] Janela do Tibia conectada: '
                    f'{windows[0].title}'
                )
            else:
                print(
                    '[PyTibia Engine] Aviso: Nenhuma janela do Tibia foi '
                    'encontrada. Abra o jogo.'
                )

        print('[PyTibia Engine] Loop de gameplay ativo.')

        # Código original:
        # while True:
        while not self.context.context.get('shutdown', False):
            try:
                if self.context.context['pause']:
                    # Código original: continue
                    sleep(0.1)
                    continue
                startTime = time()
                with self.context.gameplayLock:
                    if (
                        self.context.context.get('shutdown', False)
                        or self.context.context['pause']
                    ):
                        continue
                    self.context.context = self.handleGameData(
                        self.context.context)
                    self.context.context = self.handleGameplayTasks(
                        self.context.context)
                    self.context.context = self.context.context['tasksOrchestrator'].do(
                        self.context.context)
                    self.logMainState(self.context.context)
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
            # Código original:
            # except:
            #     print('An exception occurred:', traceback.format_exc())
            except Exception:
                print('An exception occurred:', traceback.format_exc())

    def logMainState(self, context):
        orchestrator = context['tasksOrchestrator']
        currentTask = orchestrator.getCurrentTask(context)
        rootTask = orchestrator.rootTask
        rootName = rootTask.name if rootTask is not None else None
        taskName = currentTask.name if currentTask is not None else None

        navigationTask = currentTask
        while (
            navigationTask is not None
            and not hasattr(navigationTask, 'navigationState')
        ):
            navigationTask = navigationTask.parentTask
        navigationState = (
            navigationTask.navigationState
            if navigationTask is not None
            else None
        )

        coordinate = context.get('radar', {}).get('coordinate')
        coordinateSignature = (
            tuple(coordinate) if coordinate is not None else None
        )

        waypoints = context.get('cavebot', {}).get('waypoints', {})
        waypointIndex = waypoints.get('currentIndex')
        waypointItems = waypoints.get('items', [])
        waypoint = (
            waypointItems[waypointIndex]
            if (
                isinstance(waypointIndex, int)
                and 0 <= waypointIndex < len(waypointItems)
            )
            else None
        )
        waypointLabel = waypoint.get('label') if waypoint else None
        waypointType = waypoint.get('type') if waypoint else None
        waypointCoordinate = waypoint.get('coordinate') if waypoint else None
        waypointCoordinateSignature = (
            tuple(waypointCoordinate)
            if waypointCoordinate is not None
            else None
        )

        cavebot = context.get('cavebot', {})
        target = cavebot.get('targetCreature')
        targetName = target.get('name') if isinstance(target, dict) else None
        targetCoordinate = (
            target.get('coordinate') if isinstance(target, dict) else None
        )
        targetCoordinateSignature = (
            tuple(targetCoordinate)
            if targetCoordinate is not None
            else None
        )
        isAttacking = bool(cavebot.get('isAttackingSomeCreature', False))
        corpseCount = len(context.get('loot', {}).get('corpsesToLoot', []))
        lastPressedKey = context.get('lastPressedKey')

        diagnosticState = (
            coordinateSignature,
            rootName,
            taskName,
            navigationState,
            waypointIndex,
            waypointLabel,
            waypointType,
            waypointCoordinateSignature,
            isAttacking,
            targetName,
            targetCoordinateSignature,
            corpseCount,
            lastPressedKey,
        )
        if diagnosticState == self._lastDiagnosticState:
            return
        self._lastDiagnosticState = diagnosticState

        print(
            '[MainDiag] '
            f'coordinate={coordinateSignature} '
            f'root={rootName} task={taskName} '
            f'navigation={navigationState} '
            f'waypointIndex={waypointIndex} '
            f'waypoint={waypointLabel}:{waypointType}:{waypointCoordinateSignature} '
            f'attacking={isAttacking} '
            f'target={targetName}:{targetCoordinateSignature} '
            f'corpses={corpseCount} lastKey={lastPressedKey}'
        )

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
        context = setHandleLootMiddleware(context)
        context = setWaypointIndexMiddleware(context)
        context = setMapPlayerStatusMiddleware(context)
        context = setCleanUpTasksMiddleware(context)
        return context

    def handleGameplayTasks(self, context):
        # Código original:
        # context['cavebot']['closestCreature'] = getClosestCreature(
        #     context['gameWindow']['monsters'], context['radar']['coordinate'])
        # Guarda defensiva Linux: sem Radar não calcula posições mundiais de
        # criaturas nem cria uma coordenada sintética.
        if context['radar']['coordinate'] is None:
            context['cavebot']['closestCreature'] = None
        else:
            context['cavebot']['closestCreature'] = getClosestCreature(
                context['gameWindow']['monsters'],
                context['radar']['coordinate'],
            )
        currentTask = context['tasksOrchestrator'].getCurrentTask(context)
        if currentTask is not None and currentTask.name == 'selectChatTab':
            return context
        if len(context['loot']['corpsesToLoot']) > 0:
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
        hasCreaturesToAttackAfterCheck = hasCreaturesToAttack(context)
        if hasCreaturesToAttackAfterCheck:
            if context['cavebot']['closestCreature'] is not None:
                context['way'] = 'cavebot'
            else:
                context['way'] = 'waypoint'
        else:
            context['way'] = 'waypoint'
        if hasCreaturesToAttackAfterCheck and shouldAskForCavebotTasks(context):
            currentRootTask = currentTask.rootTask if currentTask is not None else None
            isTryingToAttackClosestCreature = currentRootTask is not None and (
                currentRootTask.name == 'attackClosestCreature')
            if not isTryingToAttackClosestCreature:
                context = resolveCavebotTasks(context)
        elif context['way'] == 'waypoint':
            if context['tasksOrchestrator'].getCurrentTask(context) is None:
                currentWaypointIndex = context['cavebot']['waypoints']['currentIndex']
                currentWaypoint = context['cavebot']['waypoints']['items'][currentWaypointIndex]
                context['tasksOrchestrator'].setRootTask(
                    context, resolveTasksByWaypoint(currentWaypoint))
        context['gameWindow']['previousMonsters'] = context['gameWindow']['monsters']
        return context
