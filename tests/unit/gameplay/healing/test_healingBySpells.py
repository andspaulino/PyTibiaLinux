from types import SimpleNamespace

import src.gameplay.healing.observers.healingBySpells as observer
from src.wiki.spells import spells


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
            "hpPercentage": 100,
            "mana": 1000,
        },
        "healing": {
            "spells": {
                "criticalHealing": {
                    "enabled": False,
                    "spell": "exura gran ico",
                    "hpPercentageLessThanOrEqual": 30,
                    "hotkey": "1",
                },
                "lightHealing": {
                    "enabled": False,
                    "spell": "exura ico",
                    "hpPercentageLessThanOrEqual": 80,
                    "hotkey": "2",
                },
                "utura": {
                    "enabled": False,
                    "hotkey": "3",
                },
                "uturaGran": {
                    "enabled": False,
                    "hotkey": "4",
                },
            }
        },
    }


def test_healingBySpells_advances_active_task(monkeypatch):
    orchestrator = FakeOrchestrator(SimpleNamespace(status="running"))
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(
        observer,
        "hasCooldownByName",
        lambda *_: (_ for _ in ()).throw(AssertionError("should not check cooldown")),
    )

    observer.healingBySpells(makeContext())

    assert orchestrator.didDo is True
    assert orchestrator.rootTask is None


def test_healingBySpells_resets_completed_task(monkeypatch):
    orchestrator = FakeOrchestrator(SimpleNamespace(status="completed"))
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)

    observer.healingBySpells(makeContext())

    assert orchestrator.didReset is True


def test_healingBySpells_triggers_critical_healing(monkeypatch):
    context = makeContext()
    context["statusBar"]["hpPercentage"] = 25
    context["healing"]["spells"]["criticalHealing"]["enabled"] = True
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "hasCooldownByName", lambda *_: False)

    observer.healingBySpells(context)

    assert orchestrator.rootTask is not None
    assert orchestrator.rootTask.hotkey == "1"


def test_healingBySpells_triggers_light_healing_when_critical_disabled(monkeypatch):
    context = makeContext()
    context["statusBar"]["hpPercentage"] = 50
    context["healing"]["spells"]["lightHealing"]["enabled"] = True
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "hasCooldownByName", lambda *_: False)

    observer.healingBySpells(context)

    assert orchestrator.rootTask is not None
    assert orchestrator.rootTask.hotkey == "2"


def test_healingBySpells_triggers_utura(monkeypatch):
    context = makeContext()
    context["healing"]["spells"]["utura"]["enabled"] = True
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "hasCooldownByName", lambda *_: False)

    observer.healingBySpells(context)

    assert orchestrator.rootTask is not None
    assert orchestrator.rootTask.hotkey == "3"


def test_healingBySpells_triggers_utura_gran(monkeypatch):
    context = makeContext()
    context["healing"]["spells"]["uturaGran"]["enabled"] = True
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "hasCooldownByName", lambda *_: False)

    observer.healingBySpells(context)

    assert orchestrator.rootTask is not None
    assert orchestrator.rootTask.hotkey == "4"


def test_healingBySpells_respects_cooldown_and_mana(monkeypatch):
    context = makeContext()
    context["statusBar"]["hpPercentage"] = 25
    context["statusBar"]["mana"] = spells["exura gran ico"]["manaNeeded"] - 1
    context["healing"]["spells"]["criticalHealing"]["enabled"] = True
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(observer, "tasksOrchestrator", orchestrator)
    monkeypatch.setattr(observer, "hasCooldownByName", lambda *_: False)

    observer.healingBySpells(context)

    assert orchestrator.rootTask is None
