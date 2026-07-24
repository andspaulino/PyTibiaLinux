from src.gameplay.core.tasks.common.base import BaseTask


def test_baseTask_preserves_defaults_and_hooks():
    context = {}
    task = BaseTask()

    assert task.name == "baseTask"
    assert task.status == "notStarted"
    assert task.delayBeforeStart == 0
    assert task.delayAfterComplete == 0
    assert task.delayOfTimeout == 0
    assert task.retryCount == 0
    assert task.shouldIgnore(context) is False
    assert task.shouldManuallyComplete(context) is False
    assert task.shouldRestart(context) is False
    assert task.did(context) is True
    assert task.do(context) is context
    assert task.ping(context) is context
    assert task.onBeforeStart(context) is context
    assert task.onBeforeRestart(context) is context
    assert task.onIgnored(context) is context
    assert task.onInterrupt(context) is context
    assert task.onComplete(context) is context
    assert task.onTimeout(context) is context


def test_baseTask_sets_parent_and_root_fluently():
    parent = BaseTask(name="parent")
    root = BaseTask(name="root")
    task = BaseTask(name="child")

    assert task.setParentTask(parent) is task
    assert task.setRootTask(root) is task
    assert task.parentTask is parent
    assert task.rootTask is root
