import src.repositories.gameWindow.core as gameWindowCore
import src.repositories.gameWindow.slot as gameWindowSlot
from src.shared.typings import Waypoint
import src.utils.keyboard as keyboard
from ...typings import Context
from .common.base import BaseTask


# TODO: implement did method checking coordinate change to up floor
class UseRopeTask(BaseTask):
    def __init__(self, waypoint: Waypoint):
        super().__init__()
        self.name = 'useRope'
        self.delayBeforeStart = 1
        self.delayAfterComplete = 1
        self.waypoint = waypoint
        self.inputSent = False

    def isOnExpectedFloor(self, context: Context) -> bool:
        coordinate = context['radar']['coordinate']
        if coordinate is None:
            return False
        return coordinate[2] == self.waypoint['coordinate'][2] - 1

    def shouldIgnore(self, context: Context) -> bool:
        return self.isOnExpectedFloor(context)

    def did(self, context: Context) -> bool:
        return self.isOnExpectedFloor(context)

    def canUseRope(self, context: Context) -> bool:
        coordinate = context['radar']['coordinate']
        targetCoordinate = self.waypoint['coordinate']
        if coordinate is None:
            return False
        if coordinate[2] != targetCoordinate[2]:
            return False
        if (
            abs(coordinate[0] - targetCoordinate[0]) > 1
            or abs(coordinate[1] - targetCoordinate[1]) > 1
        ):
            return False
        return gameWindowCore.getSlotFromCoordinate(
            coordinate,
            targetCoordinate,
        ) is not None

    def shouldRestart(self, context: Context) -> bool:
        return not self.inputSent and self.canUseRope(context)

    def do(self, context: Context) -> Context:
        # Código original:
        # slot = gameWindowCore.getSlotFromCoordinate(
        #     context['radar']['coordinate'], self.waypoint['coordinate'])
        # keyboard.press('o')
        # gameWindowSlot.clickSlot(slot, context['gameWindow']['coordinate'])
        # return context
        if not self.canUseRope(context):
            return context
        slot = gameWindowCore.getSlotFromCoordinate(
            context['radar']['coordinate'],
            self.waypoint['coordinate'],
        )
        keyboard.press(context['cavebot'].get('ropeHotkey', 'o'))
        gameWindowSlot.clickSlot(slot, context['gameWindow']['coordinate'])
        self.inputSent = True
        return context
