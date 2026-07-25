from types import SimpleNamespace

import src.gameplay.healing.observers.swapRing as observer


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
        "statusBar": {"hpPercentage": 100},
        "healing": {
            "highPriority": {
                "swapRing": {
                    "enabled": True,
                    "tankRingAlwaysEquipped": False,
                    "tankRing": {
                        "hpPercentageLessThanOrEqual": 50,
                        "hotkey": "f8",
                    },
                    "mainRing": {
                        "hpPercentageGreaterThan": 80,
                        "hotkey": "f9",
                    },
                }
            }
        },
    }


def test_swapRing_equips_tank_ring_when_hp_low(monkeypatch):
    context = makeContext()
    context["statusBar"]["hpPercentage"] = 40
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "slotIsEquipped", lambda _, slot: False)
    monkeypatch.setattr(observer, "slotIsAvailable", lambda _, slot: True)

    observer.swapRing(context)

    assert orchestrator.rootTask is not None
    assert orchestrator.rootTask.hotkey == "f8"


def test_swapRing_equips_main_ring_when_hp_high(monkeypatch):
    context = makeContext()
    context["statusBar"]["hpPercentage"] = 90
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "slotIsEquipped", lambda _, slot: False)
    monkeypatch.setattr(observer, "slotIsAvailable", lambda _, slot: True)

    observer.swapRing(context)

    assert orchestrator.rootTask is not None
    assert orchestrator.rootTask.hotkey == "f9"
