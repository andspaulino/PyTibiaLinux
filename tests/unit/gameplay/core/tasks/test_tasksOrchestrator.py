from src.gameplay.core.tasks.common.base import BaseTask
from src.gameplay.core.tasks.common.vector import VectorTask
from src.gameplay.core.tasks.orchestrator import TasksOrchestrator


class HookTask(BaseTask):
    def __init__(self, events, **kwargs):
        super().__init__(**kwargs)
        self.events = events

    def do(self, context):
        self.events.append("do")
        return context

    def onComplete(self, context):
        self.events.append("complete")
        return context

    def onInterrupt(self, context):
        self.events.append("interrupt")
        return context

    def onTimeout(self, context):
        self.events.append("timeout")
        return context


def test_orchestrator_runs_and_completes_a_single_task():
    events = []
    task = HookTask(events, name="single")
    orchestrator = TasksOrchestrator()
    orchestrator.setRootTask({}, task)

    orchestrator.do({})
    assert task.status == "running"
    assert events == ["do"]

    orchestrator.do({})
    assert task.status == "completed"
    assert task.statusReason == "completed"
    assert events == ["do", "complete"]


def test_orchestrator_respects_delays_without_sleeping(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(
        "src.gameplay.core.tasks.orchestrator.time",
        lambda: now[0],
    )
    task = BaseTask(delayBeforeStart=2, delayAfterComplete=3)
    orchestrator = TasksOrchestrator()
    orchestrator.setRootTask({}, task)

    orchestrator.do({})
    assert task.status == "awaitingDelayBeforeStart"

    now[0] = 102.0
    orchestrator.do({})
    assert task.status == "running"

    orchestrator.do({})
    assert task.status == "awaitingDelayToComplete"

    now[0] = 105.0
    orchestrator.do({})
    assert task.status == "completed"


def test_orchestrator_marks_a_timed_out_task(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(
        "src.gameplay.core.tasks.orchestrator.time",
        lambda: now[0],
    )
    events = []
    task = HookTask(events, delayOfTimeout=2)
    task.did = lambda _: False
    orchestrator = TasksOrchestrator()
    orchestrator.setRootTask({}, task)

    orchestrator.do({})
    now[0] = 102.0
    orchestrator.do({})

    assert task.status == "completed"
    assert task.statusReason == "timeout"
    assert events == ["do", "timeout", "complete"]


def test_orchestrator_interrupts_the_current_task_when_root_changes():
    events = []
    firstTask = HookTask(events, name="first")
    secondTask = BaseTask(name="second")
    orchestrator = TasksOrchestrator()
    orchestrator.setRootTask({}, firstTask)

    orchestrator.setRootTask({}, secondTask)

    assert events == ["interrupt"]
    assert orchestrator.rootTask is secondTask
    assert secondTask.isRootTask is True


def test_orchestrator_runs_vector_children_in_order():
    vector = VectorTask(name="vector")
    firstTask = BaseTask(name="first").setParentTask(vector)
    secondTask = BaseTask(name="second").setParentTask(vector)
    vector.tasks = [firstTask, secondTask]
    orchestrator = TasksOrchestrator()
    orchestrator.setRootTask({}, vector)

    orchestrator.do({})
    assert firstTask.status == "running"

    orchestrator.do({})
    assert firstTask.status == "completed"
    assert vector.currentTaskIndex == 1

    orchestrator.do({})
    assert secondTask.status == "running"

    orchestrator.do({})
    assert secondTask.status == "completed"
    assert vector.status == "completed"
