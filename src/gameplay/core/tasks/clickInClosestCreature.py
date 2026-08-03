import src.utils.keyboard as keyboard
import src.utils.mouse as mouse
from ...typings import Context
from .common.base import BaseTask


class ClickInClosestCreatureTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.name = 'clickInClosestCreature'
        self.delayOfTimeout = 1

    def shouldIgnore(self, context: Context) -> bool:
        # Código original:
        # return context['cavebot']['targetCreature'] is not None
        targetCreature = context['cavebot'].get('targetCreature')
        if targetCreature is None:
            return False
        closestCreature = context['cavebot'].get('closestCreature')
        if not isinstance(targetCreature, dict) or not isinstance(
            closestCreature,
            dict,
        ):
            return True
        targetCoordinate = targetCreature.get('coordinate')
        closestCoordinate = closestCreature.get('coordinate')
        if targetCoordinate is None or closestCoordinate is None:
            return targetCreature is closestCreature
        return tuple(targetCoordinate) == tuple(closestCoordinate)

    def do(self, context: Context) -> Context:
        # Código original:
        # # attack by mouse click when there are players on screen or ignorable creatures
        # if context['gameWindow']['players'] or context['targeting']['hasIgnorableCreatures']:
        #     keyboard.keyDown('alt')
        #     mouse.leftClick(context['cavebot']
        #                     ['closestCreature']['windowCoordinate'])
        #     keyboard.keyUp('alt')
        #     return context
        # keyboard.press('space')
        # O Space delega a escolha ao Auto-Target do cliente e pode selecionar
        # uma criatura diferente daquela que o A* confirmou como alcançável.
        closestCreature = context['cavebot'].get('closestCreature')
        if not isinstance(closestCreature, dict):
            return context
        windowCoordinate = closestCreature.get('windowCoordinate')
        if windowCoordinate is None:
            return context
        keyboard.keyDown('alt')
        try:
            mouse.leftClick(windowCoordinate)
        finally:
            keyboard.keyUp('alt')
        return context

    def did(self, context: Context) -> bool:
        # Código original:
        # return context['cavebot']['isAttackingSomeCreature']
        if not context['cavebot']['isAttackingSomeCreature']:
            return False
        targetCreature = context['cavebot'].get('targetCreature')
        closestCreature = context['cavebot'].get('closestCreature')
        if not isinstance(targetCreature, dict) or not isinstance(
            closestCreature,
            dict,
        ):
            return True
        targetCoordinate = targetCreature.get('coordinate')
        closestCoordinate = closestCreature.get('coordinate')
        if targetCoordinate is None or closestCoordinate is None:
            return targetCreature is closestCreature
        return tuple(targetCoordinate) == tuple(closestCoordinate)
