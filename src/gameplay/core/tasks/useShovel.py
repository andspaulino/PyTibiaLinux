import src.gameplay.utils as gameplayUtils
import src.repositories.gameWindow.core as gameWindowCore
import src.repositories.gameWindow.slot as gameWindowSlot
from src.shared.typings import Waypoint
import src.utils.keyboard as keyboard
from ...typings import Context
from .common.base import BaseTask


class UseShovelTask(BaseTask):
    def __init__(self, waypoint: Waypoint):
        super().__init__()
        self.name = 'useShovel'
        self.delayBeforeStart = 1
        self.delayAfterComplete = 0.5
        self.waypoint = waypoint

    def shouldIgnore(self, context: Context) -> bool:
        coordinate = context['radar']['coordinate']
        waypointState = context['cavebot']['waypoints']['state']
        checkInCoordinate = (
            waypointState.get('checkInCoordinate')
            if waypointState is not None
            else None
        )
        if (
            coordinate is not None
            and checkInCoordinate is not None
            and gameplayUtils.coordinatesAreEqual(
                coordinate, checkInCoordinate
            )
        ):
            return True

        # Código original:
        # return gameWindowCore.isHoleOpen(
        #     context['gameWindow']['image'], gameWindowCore.images[context['resolution']]['holeOpen'], context['radar']['coordinate'], self.waypoint['coordinate'])
        return gameWindowCore.isHoleOpen(
            context['gameWindow']['image'], gameWindowCore.images[context['resolution']]['holeOpen'], context['radar']['coordinate'], self.waypoint['coordinate'])

    def do(self, context: Context) -> Context:
        slot = gameWindowCore.getSlotFromCoordinate(
            context['radar']['coordinate'], self.waypoint['coordinate'])
        # Código original:
        # keyboard.press('p')
        keyboard.press(context['cavebot'].get('shovelHotkey', 'p'))
        gameWindowSlot.clickSlot(slot, context['gameWindow']['coordinate'])
        return context

    def did(self, context: Context) -> bool:
        return self.shouldIgnore(context)
