from src.gameplay.utils import releaseKeys

from ...typings import Context
from .walkToCoordinate import WalkToCoordinateTask


class WalkToCorpseTask(WalkToCoordinateTask):
    def __init__(self, coordinate, corpse):
        super().__init__(coordinate)
        self.name = 'lootCorpse'
        self.isRootTask = True
        self.corpse = corpse

    def did(self, context: Context) -> bool:
        if self.pathfindingFailureReason is not None:
            return True
        return super().did(context)

    def onComplete(self, context: Context) -> Context:
        if self.pathfindingFailureReason is not None:
            self.corpse['approachFailed'] = True
        return super().onComplete(context)

    def onTimeout(self, context: Context) -> Context:
        self.corpse['approachFailed'] = True
        navigation = context.setdefault('cavebot', {}).setdefault(
            'navigation',
            {},
        )
        navigation['status'] = 'blocked'
        navigation['failureReason'] = 'corpse-approach-timeout'
        navigation['plannedDirection'] = None
        return releaseKeys(context)
