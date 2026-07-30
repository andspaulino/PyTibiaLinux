from src.repositories.battleList.core import getBeingAttackedCreatureCategory
# Código original:
# from src.repositories.chat.core import hasNewLoot
from src.repositories.gameWindow.config import gameWindowSizes
from src.repositories.gameWindow.core import getCoordinate, getImageByCoordinate
from src.repositories.gameWindow.creatures import getCreatures, getCreaturesByType, getTargetCreature
# Código original:
# from src.repositories.gameWindow.creatures import getDifferentCreaturesBySlots
# from ...comboSpells.core import spellsPath
from ...typings import Context
# Código original:
# from ..tasks.selectChatTab import SelectChatTabTask


# Coordenada interna sem significado mundial, usada somente para montar a grade
# visual quando o Targeting está desacoplado do Radar e não pode caminhar.
VISUAL_TARGETING_FALLBACK_COORDINATE = (32000, 32000, 7)


def canUseVisualTargetingWithoutRadar(context: Context) -> bool:
    return context['targeting'].get('enabled', False)



# TODO: add unit tests
def setDirectionMiddleware(context: Context) -> Context:
    if context['radar']['coordinate'] is None:
        return context
    if context['radar']['previousCoordinate'] is None:
        context['radar']['previousCoordinate'] = context['radar']['coordinate']
    if context['radar']['coordinate'][0] != context['radar']['previousCoordinate'][0] or context['radar']['coordinate'][1] != context['radar']['previousCoordinate'][1] or context['radar']['coordinate'][2] != context['radar']['previousCoordinate'][2]:
        comingFromDirection = None
        if context['radar']['coordinate'][2] != context['radar']['previousCoordinate'][2]:
            comingFromDirection = None
        elif context['radar']['coordinate'][0] != context['radar']['previousCoordinate'][0] and context['radar']['coordinate'][1] != context['radar']['previousCoordinate'][1]:
            comingFromDirection = None
        elif context['radar']['coordinate'][0] != context['radar']['previousCoordinate'][0]:
            comingFromDirection = 'left' if context['radar']['coordinate'][
                0] > context['radar']['previousCoordinate'][0] else 'right'
        elif context['radar']['coordinate'][1] != context['radar']['previousCoordinate'][1]:
            comingFromDirection = 'top' if context['radar']['coordinate'][
                1] > context['radar']['previousCoordinate'][1] else 'bottom'
        context['comingFromDirection'] = comingFromDirection
    # if context['gameWindow']['previousGameWindowImage'] is not None:
    #     context['gameWindow']['walkedPixelsInSqm'] = getWalkedPixels(context)
    context['gameWindow']['previousGameWindowImage'] = context['gameWindow']['image']
    context['radar']['previousCoordinate'] = context['radar']['coordinate']
    return context


# Código original:
# `setHandleLootMiddleware` selecionava a aba Loot, chamava `hasNewLoot()` e
# associava mensagens do chat ao último alvo ou a mortes inferidas por spells.
# A cópia integral está preservada em
# `docs/historico-looting/chat-loot-detector.py.txt` e no histórico Git.


def setTargetCreatureHistoryMiddleware(context: Context) -> Context:
    context['cavebot']['targetCreature'] = getTargetCreature(
        context['gameWindow']['monsters'])
    if context['cavebot']['targetCreature'] is not None:
        context['cavebot']['previousTargetCreature'] = context['cavebot']['targetCreature']
    return context


# TODO: add unit tests
def setGameWindowMiddleware(context: Context) -> Context:
    context['gameWindow']['coordinate'] = getCoordinate(
        context['screenshot'], gameWindowSizes[context['resolution']])
    if context['gameWindow']['coordinate'] is None:
        context['gameWindow']['image'] = None
        return context
    # Código original:
    context['gameWindow']['image'] = getImageByCoordinate(
        context['screenshot'], context['gameWindow']['coordinate'], gameWindowSizes[context['resolution']])
    return context


# TODO: add unit tests
def setGameWindowCreaturesMiddleware(context: Context) -> Context:
    # Código Linux anterior:
    # if context['gameWindow']['coordinate'] is None or context['radar']['coordinate'] is None or context['gameWindow']['image'] is None:
    #     context['gameWindow']['creatures'] = []
    #     context['gameWindow']['monsters'] = []
    #     context['gameWindow']['players'] = []
    #     return context
    if (
        context['gameWindow']['coordinate'] is None
        or context['gameWindow']['image'] is None
        or (
            context['radar']['coordinate'] is None
            and not canUseVisualTargetingWithoutRadar(context)
        )
    ):
        context['gameWindow']['creatures'] = []
        context['gameWindow']['monsters'] = []
        context['gameWindow']['players'] = []
        return context
    creatureBaseCoordinate = (
        context['radar']['coordinate']
        if context['radar']['coordinate'] is not None
        else VISUAL_TARGETING_FALLBACK_COORDINATE
    )
    # Código original:
    context['battleList']['beingAttackedCreatureCategory'] = getBeingAttackedCreatureCategory(
        context['battleList']['creatures'])
    context['gameWindow']['creatures'] = getCreatures(
        context['battleList']['creatures'], context['comingFromDirection'], context['gameWindow']['coordinate'], context['gameWindow']['image'], creatureBaseCoordinate, beingAttackedCreatureCategory=context['battleList']['beingAttackedCreatureCategory'], walkedPixelsInSqm=context['gameWindow']['walkedPixelsInSqm'])
    if len(context['gameWindow']['creatures']) == 0:
        context['gameWindow']['monsters'] = []
        context['gameWindow']['players'] = []
        return context
    context['gameWindow']['monsters'] = getCreaturesByType(
        context['gameWindow']['creatures'], 'monster')
    context['gameWindow']['players'] = getCreaturesByType(
        context['gameWindow']['creatures'], 'player')
    return context
