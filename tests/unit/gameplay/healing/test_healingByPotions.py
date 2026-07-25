from types import SimpleNamespace

import src.gameplay.healing.observers.healingByPotions as observer


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
        "statusBar": {
            "hpPercentage": 30,
            "manaPercentage": 30,
        },
        "healing": {
            "potions": {
                "firstHealthPotion": {
                    "enabled": False,
                    "hotkey": "1",
                    "hpPercentageLessThanOrEqual": 50,
                    "manaPercentageGreaterThanOrEqual": 0,
                },
                "firstManaPotion": {
                    "enabled": False,
                    "hotkey": "2",
                    "manaPercentageLessThanOrEqual": 50,
                },
            }
        },
    }


def test_healingByPotions_advances_active_internal_task(monkeypatch):
    orchestrator = FakeOrchestrator(SimpleNamespace(status="running"))
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(
        observer,
        "slotIsAvailable",
        lambda *_: (_ for _ in ()).throw(AssertionError("slot should not be read")),
    )

    observer.healingByPotions(makeContext())

    assert orchestrator.didDo is True
    assert orchestrator.rootTask is None


def test_healingByPotions_resets_completed_internal_task(monkeypatch):
    orchestrator = FakeOrchestrator(SimpleNamespace(status="completed"))
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)

    observer.healingByPotions(makeContext())

    assert orchestrator.didReset is True


def test_healingByPotions_prioritizes_health_potion(monkeypatch):
    context = makeContext()
    context["healing"]["potions"]["firstHealthPotion"]["enabled"] = True
    context["healing"]["potions"]["firstManaPotion"]["enabled"] = True
    orchestrator = FakeOrchestrator()
    checkedSlots = []
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "matchHpHealing", lambda *_: True)
    monkeypatch.setattr(observer, "matchManaHealing", lambda *_: True)
    monkeypatch.setattr(
        observer,
        "slotIsAvailable",
        lambda _, slot: checkedSlots.append(slot) or True,
    )

    observer.healingByPotions(context)

    assert checkedSlots == [1]
    assert orchestrator.rootTask.hotkey == "1"
    assert orchestrator.rootTask.delayAfterComplete == 1


def test_healingByPotions_uses_mana_potion_after_health_does_not_match(monkeypatch):
    context = makeContext()
    context["healing"]["potions"]["firstHealthPotion"]["enabled"] = True
    context["healing"]["potions"]["firstManaPotion"]["enabled"] = True
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "matchHpHealing", lambda *_: False)
    monkeypatch.setattr(observer, "matchManaHealing", lambda *_: True)
    monkeypatch.setattr(observer, "slotIsAvailable", lambda _, slot: slot == 2)

    observer.healingByPotions(context)

    assert orchestrator.rootTask.hotkey == "2"
    assert orchestrator.rootTask.delayAfterComplete == 1


def test_healingByPotions_does_not_schedule_unavailable_slot(monkeypatch):
    context = makeContext()
    context["healing"]["potions"]["firstHealthPotion"]["enabled"] = True
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "matchHpHealing", lambda *_: True)
    monkeypatch.setattr(observer, "slotIsAvailable", lambda *_: False)

    observer.healingByPotions(context)

    assert orchestrator.rootTask is None
