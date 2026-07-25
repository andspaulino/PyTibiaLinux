from unittest.mock import MagicMock
import pytest
from src.gameplay.threads.pyTibia import PyTibiaThread

class DummyContext:
    def __init__(self, context_dict):
        self.context = context_dict

class CustomDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_count = 0

    def __getitem__(self, key):
        if key == 'pause':
            self.call_count += 1
            if self.call_count > 2:
                raise KeyboardInterrupt()
        return super().__getitem__(key)

def test_pytibia_thread_loop_respects_pause(monkeypatch):
    sleep_calls = []
    monkeypatch.setattr("src.gameplay.threads.pyTibia.sleep", lambda seconds: sleep_calls.append(seconds))

    context_dict = CustomDict({'pause': True})
    ctx = DummyContext(context_dict)
    thread = PyTibiaThread(ctx)

    thread.mainloop()
    assert len(sleep_calls) >= 1
    assert all(s == 0.1 for s in sleep_calls)

def test_pytibia_thread_loop_execution_flow(monkeypatch):
    orchestrator = MagicMock()
    # Mock do() method to return the context passed to it
    orchestrator.do.side_effect = lambda ctx: ctx
    
    context_dict = {
        'pause': False,
        'tasksOrchestrator': orchestrator,
        'statusBar': {'hpPercentage': 100, 'hp': 200, 'manaPercentage': 100, 'mana': 100},
        'screenshot': None
    }
    ctx = DummyContext(context_dict)
    thread = PyTibiaThread(ctx)

    # Mock the middlewares
    mock_set_screenshot = MagicMock(return_value=context_dict)
    mock_set_player_status = MagicMock(return_value=context_dict)
    mock_set_cleanup = MagicMock(return_value=context_dict)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.setScreenshotMiddleware", mock_set_screenshot)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.setMapPlayerStatusMiddleware", mock_set_player_status)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.setCleanUpTasksMiddleware", mock_set_cleanup)

    # Mock the observers
    potions_called = 0
    spells_called = 0
    def mock_potions(c):
        nonlocal potions_called
        potions_called += 1
    def mock_spells(c):
        nonlocal spells_called
        spells_called += 1
        # Pause after first iteration to stop the loop
        c['pause'] = True
        raise KeyboardInterrupt() # Force exit

    monkeypatch.setattr("src.gameplay.threads.pyTibia.healingByPotions", mock_potions)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.healingBySpells", mock_spells)
    monkeypatch.setattr("src.gameplay.threads.pyTibia.swapAmulet", MagicMock())
    monkeypatch.setattr("src.gameplay.threads.pyTibia.swapRing", MagicMock())
    monkeypatch.setattr("src.gameplay.threads.pyTibia.eatFood", MagicMock())
    monkeypatch.setattr("src.gameplay.threads.pyTibia.sleep", MagicMock())

    thread.mainloop()

    assert mock_set_screenshot.call_count == 1
    assert mock_set_player_status.call_count == 1
    assert mock_set_cleanup.call_count == 1
    assert orchestrator.do.call_count == 1
    assert potions_called == 1
    assert spells_called == 1
    assert ctx.context['pause'] is True
