from ...lootDiagnostics import printLootDiagnostic
from ...typings import Context
from .common.base import BaseTask
from .common.vector import VectorTask
from .clickInClosestCreature import ClickInClosestCreatureTask
from .walkToTargetCreature import WalkToTargetCreatureTask


class AttackClosestCreatureTask(VectorTask):
    def __init__(self, allowChase: bool = False):
        super().__init__()
        self.name = 'attackClosestCreature'
        self.isRootTask = True
        self.allowChase = allowChase
        self.hasStartedAttacking = False

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
        if self.allowChase:
            self.tasks.append(
                WalkToTargetCreatureTask().setParentTask(self).setRootTask(self))
        # No original, WalkToTargetCreatureTask mantém a árvore ativa durante
        # o combate. No modo Linux selection-only, a própria root aguarda o
        # término do ataque para não ser recriada a cada ciclo.
        self.manuallyTerminable = not self.allowChase
        return context

    def shouldManuallyComplete(self, _: Context) -> bool:
        context = _
        if context['cavebot']['isAttackingSomeCreature']:
            self.hasStartedAttacking = True
            return False
        return self.hasStartedAttacking

    def onInterrupt(self, context: Context) -> Context:
        printLootDiagnostic(
            'attack_root_interrupt',
            context,
            rootAllowChase=self.allowChase,
            hasStartedAttacking=self.hasStartedAttacking,
        )
        return context

    def onComplete(self, context: Context) -> Context:
        printLootDiagnostic(
            'attack_root_complete',
            context,
            rootAllowChase=self.allowChase,
            hasStartedAttacking=self.hasStartedAttacking,
        )
        return context
