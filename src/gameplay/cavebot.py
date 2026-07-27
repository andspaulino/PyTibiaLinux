from typing import Union
from src.repositories.gameWindow.creatures import hasTargetToCreature
from .core.tasks.attackClosestCreature import AttackClosestCreatureTask
from .typings import Context


def canKeepVisualTargetWithoutRadar(context: Context) -> bool:
    return (
        context['radar']['coordinate'] is None
        and context['targeting'].get('enabled', False)
        and not context['targeting'].get('walkToTarget', False)
        and not context['cavebot'].get('enabled', False)
    )


# TODO: add unit tests
def resolveCavebotTasks(context: Context) -> Union[AttackClosestCreatureTask, None]:
    currentTask = context['tasksOrchestrator'].getCurrentTask(context)
    if context['cavebot']['isAttackingSomeCreature']:
        if context['cavebot']['targetCreature'] is None:
            return context
        # Código original:
        # if hasTargetToCreature(
        #         context['gameWindow']['monsters'], context['cavebot']['targetCreature'], context['radar']['coordinate']) == False:
        #     if context['cavebot']['closestCreature'] is None:
        #         return context
        #     context['tasksOrchestrator'].setRootTask(
        #         context, AttackClosestCreatureTask())
        #     return context
        radarCoordinate = context['radar']['coordinate']
        if radarCoordinate is None:
            if not canKeepVisualTargetWithoutRadar(context):
                return context
        elif not hasTargetToCreature(
            context['gameWindow']['monsters'],
            context['cavebot']['targetCreature'],
            radarCoordinate,
        ):
            if context['cavebot']['closestCreature'] is None:
                return context
            context['tasksOrchestrator'].setRootTask(
                context, AttackClosestCreatureTask())
            return context
        if currentTask is None or context['tasksOrchestrator'].rootTask.name != 'attackClosestCreature':
            context['tasksOrchestrator'].setRootTask(
                context, AttackClosestCreatureTask())
        return context
    if context['cavebot']['closestCreature'] is None:
        return context
    context['tasksOrchestrator'].setRootTask(
        context, AttackClosestCreatureTask())
    return context


# TODO: add unit tests
def shouldAskForCavebotTasks(context: Context) -> bool:
    if context['way'] != 'cavebot':
        return False
    currentTask = context['tasksOrchestrator'].getCurrentTask(context)
    if currentTask is None:
        return True
    return (currentTask.name not in ['dropFlasks', 'lootCorpse', 'moveDown', 'moveUp', 'refillChecker', 'singleWalk', 'refillChecker', 'useRopeWaypoint', 'useTeleportWaypoint', 'useShovelWaypoint'])
