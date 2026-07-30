from threading import Event, RLock, Thread
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest

from src.ui import context as ui_context_module
from src.ui.application import Application
from src.ui.context import Context


def makeUiContext(window):
    uiContext = object.__new__(Context)
    uiContext.context = {
        'pause': True,
        'shutdown': False,
        'window': window,
    }
    uiContext.gameplayLock = RLock()
    return uiContext


def test_play_without_window_stays_paused(monkeypatch):
    showError = MagicMock()
    monkeypatch.setattr(ui_context_module.messagebox, 'showerror', showError)
    uiContext = makeUiContext(None)

    uiContext.play()

    showError.assert_called_once()
    assert uiContext.context['pause'] is True


def test_play_activation_failure_stays_paused(monkeypatch):
    window = MagicMock()
    window.activate.return_value = False
    showError = MagicMock()
    getScreenshot = MagicMock()
    monkeypatch.setattr(ui_context_module.messagebox, 'showerror', showError)
    monkeypatch.setattr(ui_context_module, 'getScreenshot', getScreenshot)
    monkeypatch.setattr(ui_context_module.time, 'sleep', MagicMock())
    uiContext = makeUiContext(window)

    uiContext.play()

    window.activate.assert_called_once_with()
    showError.assert_called_once()
    getScreenshot.assert_not_called()
    assert uiContext.context['pause'] is True


def test_play_activation_success_unpauses(monkeypatch):
    window = MagicMock()
    window.activate.return_value = True
    getScreenshot = MagicMock(return_value=object())
    monkeypatch.setattr(ui_context_module, 'getScreenshot', getScreenshot)
    monkeypatch.setattr(ui_context_module.time, 'sleep', MagicMock())
    uiContext = makeUiContext(window)

    uiContext.play()

    window.activate.assert_called_once_with()
    getScreenshot.assert_called_once_with()
    assert uiContext.context['pause'] is False


def test_pause_waits_for_active_gameplay_iteration():
    uiContext = object.__new__(Context)
    uiContext.gameplayLock = RLock()
    orchestrator = MagicMock()
    uiContext.context = {
        'pause': False,
        'tasksOrchestrator': orchestrator,
        'cavebot': {'waypoints': {'currentIndex': 2}},
    }
    attempted = Event()
    completed = Event()

    def pauseFromUi():
        attempted.set()
        uiContext.pause()
        completed.set()

    with uiContext.gameplayLock:
        thread = Thread(target=pauseFromUi)
        thread.start()
        assert attempted.wait(timeout=1)
        assert completed.is_set() is False

    thread.join(timeout=1)
    assert completed.is_set() is True
    assert uiContext.context['pause'] is True
    assert uiContext.context['cavebot']['waypoints']['currentIndex'] is None
    orchestrator.setRootTask.assert_called_once_with(uiContext.context, None)


def test_application_close_pauses_requests_shutdown_and_destroys():
    context = MagicMock()
    context.context = {'shutdown': False}
    application = SimpleNamespace(
        context=context,
        destroy=MagicMock(),
    )

    Application.close(cast(Application, application))

    context.pause.assert_called_once_with()
    assert context.context['shutdown'] is True
    application.destroy.assert_called_once_with()


def test_application_close_destroys_when_pause_fails():
    context = MagicMock()
    context.context = {'shutdown': False}
    context.pause.side_effect = RuntimeError('pause failed')
    application = SimpleNamespace(
        context=context,
        destroy=MagicMock(),
    )

    with pytest.raises(RuntimeError, match='pause failed'):
        Application.close(cast(Application, application))

    assert context.context['shutdown'] is True
    application.destroy.assert_called_once_with()
