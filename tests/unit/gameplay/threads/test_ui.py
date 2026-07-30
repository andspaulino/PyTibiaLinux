from unittest.mock import MagicMock

import pytest

from src.gameplay.threads import ui as ui_thread_module
from src.gameplay.threads.ui import UIThread


def makeContext():
    context = MagicMock()
    context.context = {'shutdown': False}
    return context


def test_ui_thread_runs_application_and_requests_shutdown(monkeypatch):
    context = makeContext()
    application = MagicMock()
    applicationClass = MagicMock(return_value=application)
    monkeypatch.setattr(ui_thread_module, 'Application', applicationClass)

    UIThread(context).run()

    applicationClass.assert_called_once_with(context)
    application.mainloop.assert_called_once_with()
    context.pause.assert_called_once_with()
    assert context.context['shutdown'] is True


def test_ui_thread_requests_shutdown_when_application_fails(monkeypatch):
    context = makeContext()
    monkeypatch.setattr(
        ui_thread_module,
        'Application',
        MagicMock(side_effect=RuntimeError('ui failed')),
    )

    with pytest.raises(RuntimeError, match='ui failed'):
        UIThread(context).run()

    context.pause.assert_called_once_with()
    assert context.context['shutdown'] is True


def test_ui_thread_requests_shutdown_even_when_pause_fails(monkeypatch):
    context = makeContext()
    context.pause.side_effect = RuntimeError('pause failed')
    application = MagicMock()
    monkeypatch.setattr(
        ui_thread_module,
        'Application',
        MagicMock(return_value=application),
    )

    with pytest.raises(RuntimeError, match='pause failed'):
        UIThread(context).run()

    assert context.context['shutdown'] is True
