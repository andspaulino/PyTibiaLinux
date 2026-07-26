from ...typings import Context
from .common.base import BaseTask
from .common.vector import VectorTask
from .clickInClosestCreature import ClickInClosestCreatureTask
from .walkToTargetCreature import WalkToTargetCreatureTask


class AttackClosestCreatureTask(VectorTask):
    def __init__(self):
        super().__init__()
        self.name = 'attackClosestCreature'
        self.isRootTask = True

    def onBeforeStart(self, context: Context) -> Context:
        # Código original:
        # self.tasks = [
        #     # TODO: task should have like 5 retries until all tree is destroyed
        #     ClickInClosestCreatureTask().setParentTask(self).setRootTask(self),
        #     WalkToTargetCreatureTask().setParentTask(self).setRootTask(self),
        # ]
        tasks: list[BaseTask] = [
            ClickInClosestCreatureTask().setParentTask(self).setRootTask(self),
        ]
        self.tasks = tasks
        if context['targeting'].get('walkToTarget', False):
            self.tasks.append(
                WalkToTargetCreatureTask().setParentTask(self).setRootTask(self))
        return context
