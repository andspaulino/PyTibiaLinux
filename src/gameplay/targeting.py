from .cavebot import resolveCavebotTasks
from .typings import Context


PROTECTED_TARGETING_TASKS = (
    'dropFlasks',
    'lootCorpse',
    'moveDown',
    'moveUp',
    'refillChecker',
    'singleWalk',
    'useRopeWaypoint',
    'useTeleportWaypoint',
    'useShovelWaypoint',
)


# TODO: add unit tests
def hasCreaturesToAttack(context: Context) -> bool:
    context['targeting']['hasIgnorableCreatures'] = False
    if len(context['gameWindow']['monsters']) == 0:
        context['targeting']['canIgnoreCreatures'] = True
        return False
    if context['targeting']['canIgnoreCreatures'] == False:
        return True
    ignorableGameWindowCreatures = []
    for gameWindowCreature in context['gameWindow']['monsters']:
        shouldIgnoreCreature = context['targeting']['creatures'].get(gameWindowCreature['name'], { 'ignore': False })['ignore']
        if shouldIgnoreCreature:
            context['targeting']['hasIgnorableCreatures'] = True
            ignorableGameWindowCreatures.append(gameWindowCreature)
    return len(ignorableGameWindowCreatures) < len(context['gameWindow']['monsters'])


def shouldAskForTargetingTasks(context: Context) -> bool:
    currentTask = context['tasksOrchestrator'].getCurrentTask(context)
    if currentTask is None:
        return True
    return currentTask.name not in PROTECTED_TARGETING_TASKS


def resolveTargetingTasks(context: Context) -> Context:
    # O estado de combate permanece em context['cavebot'] para preservar os
    # contratos originais enquanto a habilitação do targeting é independente.
    return resolveCavebotTasks(context)
