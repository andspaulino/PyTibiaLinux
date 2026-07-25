from unittest.mock import MagicMock
from src.gameplay.core.middlewares.tasks import setCleanUpTasksMiddleware

def test_set_cleanup_tasks_middleware_resets_completed_root_task():
    orchestrator = MagicMock()
    mock_task = MagicMock()
    mock_task.isRootTask = True
    mock_task.status = 'completed'
    mock_task.rootTask = None
    
    orchestrator.getCurrentTask.return_value = mock_task
    
    context = {'tasksOrchestrator': orchestrator}
    setCleanUpTasksMiddleware(context)
    
    assert orchestrator.reset.call_count == 1

def test_set_cleanup_tasks_middleware_resets_completed_nested_root_task():
    orchestrator = MagicMock()
    mock_task = MagicMock()
    mock_task.isRootTask = False
    mock_task.status = 'running'
    
    mock_root_task = MagicMock()
    mock_root_task.status = 'completed'
    mock_task.rootTask = mock_root_task
    
    orchestrator.getCurrentTask.return_value = mock_task
    
    context = {'tasksOrchestrator': orchestrator}
    setCleanUpTasksMiddleware(context)
    
    assert orchestrator.reset.call_count == 1

def test_set_cleanup_tasks_middleware_no_op_when_running():
    orchestrator = MagicMock()
    mock_task = MagicMock()
    mock_task.isRootTask = True
    mock_task.status = 'running'
    mock_task.rootTask = None
    
    orchestrator.getCurrentTask.return_value = mock_task
    
    context = {'tasksOrchestrator': orchestrator}
    setCleanUpTasksMiddleware(context)
    
    assert orchestrator.reset.call_count == 0
