from src.shared.typings import Waypoint
from ...typings import Context
from .common.vector import VectorTask
from .useHole import UseHoleTask
from .setNextWaypoint import SetNextWaypointTask


class UseHoleWaypointTask(VectorTask):
    def __init__(self, waypoint: Waypoint):
        super().__init__()
        self.name = 'useHoleWaypoint'
        self.isRootTask = True
        self.waypoint = waypoint

    def onBeforeStart(self, context: Context) -> Context:
        self.tasks = [
            UseHoleTask(self.waypoint).setParentTask(self).setRootTask(self),
            SetNextWaypointTask().setParentTask(self).setRootTask(self),
        ]
        return context
