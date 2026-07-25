from types import SimpleNamespace

import src.gameplay.healing.observers.eatFood as observer


class FakeOrchestrator:
    def __init__(self, currentTask=None):
        self.currentTask = currentTask
        self.didReset = False
        self.didDo = False
        self.rootTask = None

    def getCurrentTask(self, context):
        return self.currentTask

    def reset(self):
        self.didReset = True
        self.currentTask = None

    def do(self, context):
        self.didDo = True
        return context

    def setRootTask(self, context, task):
        self.rootTask = task


def makeContext():
    return {
        "screenshot": object(),
        "healing": {
            "eatFood": {
                "enabled": True,
                "eatWhenFoodIslessOrEqual": 10,
                "hotkey": "f",
            }
        },
    }


def test_eatFood_triggers_when_food_less_or_equal(monkeypatch):
    context = makeContext()
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "getFood", lambda *_: 10)

    observer.eatFood(context)

    assert orchestrator.rootTask is not None
    assert orchestrator.rootTask.hotkey == "f"
    assert orchestrator.rootTask.delayAfterComplete == 2


def test_eatFood_does_not_trigger_when_food_greater(monkeypatch):
    context = makeContext()
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "getFood", lambda *_: 11)

    observer.eatFood(context)

    assert orchestrator.rootTask is None


def test_eatFood_does_not_trigger_when_disabled(monkeypatch):
    context = makeContext()
    context["healing"]["eatFood"]["enabled"] = False
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(
        observer,
        "getFood",
        lambda *_: (_ for _ in ()).throw(AssertionError("should not get food")),
    )

    observer.eatFood(context)

    assert orchestrator.rootTask is None
