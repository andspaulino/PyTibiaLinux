from unittest.mock import MagicMock

from src.gameplay.threads.pyTibia import PyTibiaThread


class DummyContext:
    def __init__(self, context):
        self.context = context


def test_ui_mode_stays_paused_and_does_not_select_window(monkeypatch):
    getTibiaWindows = MagicMock()
    monkeypatch.setattr(
        'src.utils.window.get_tibia_windows',
        getTibiaWindows,
    )
    context = DummyContext({
        'pause': True,
        'shutdown': True,
        'window': None,
    })

    PyTibiaThread(context, uiEnabled=True).mainloop()

    getTibiaWindows.assert_not_called()
    assert context.context['window'] is None
    assert context.context['pause'] is True


def test_cli_mode_preserves_automatic_window_selection(monkeypatch):
    window = MagicMock(title='Tibia Test')
    getTibiaWindows = MagicMock(return_value=[window])
    monkeypatch.setattr(
        'src.utils.window.get_tibia_windows',
        getTibiaWindows,
    )
    context = DummyContext({
        'pause': True,
        'shutdown': True,
        'window': None,
    })

    PyTibiaThread(context, uiEnabled=False).mainloop()

    getTibiaWindows.assert_called_once_with()
    assert context.context['window'] is window
    assert context.context['pause'] is False


def test_shutdown_stops_loop_before_gameplay(monkeypatch):
    context = DummyContext({
        'pause': False,
        'shutdown': True,
        'window': MagicMock(),
    })
    thread = PyTibiaThread(context, uiEnabled=True)
    handleGameData = MagicMock()
    monkeypatch.setattr(thread, 'handleGameData', handleGameData)

    thread.mainloop()

    handleGameData.assert_not_called()
