from src.gameplay.context import context
from src.gameplay.core.tasks.orchestrator import TasksOrchestrator


def test_context_preserves_player_status_contract():
    assert context["statusBar"] == {
        "hpPercentage": None,
        "hp": None,
        "manaPercentage": None,
        "mana": None,
    }


def test_context_uses_the_migrated_tasks_orchestrator():
    assert isinstance(context["tasksOrchestrator"], TasksOrchestrator)
