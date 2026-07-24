from src.gameplay.core.tasks.common.vector import VectorTask


def test_vectorTask_preserves_initial_state():
    task = VectorTask(name="vector")

    assert task.name == "vector"
    assert task.currentTaskIndex == 0
    assert task.tasks == []
    assert task.shouldRestartAfterAllChildrensComplete({}) is False
