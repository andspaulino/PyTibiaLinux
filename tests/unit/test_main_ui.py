from unittest.mock import MagicMock

import pytest

import main as main_entry


def test_main_starts_ui_mode_and_joins_after_gameplay(monkeypatch):
    contextInstance = MagicMock()
    contextInstance.context = {'shutdown': False}
    contextClass = MagicMock(return_value=contextInstance)
    uiThread = MagicMock()
    uiThreadClass = MagicMock(return_value=uiThread)
    gameplayThread = MagicMock()
    gameplayThreadClass = MagicMock(return_value=gameplayThread)
    monkeypatch.setattr(main_entry, 'Context', contextClass)
    monkeypatch.setattr(main_entry, 'UIThread', uiThreadClass)
    monkeypatch.setattr(main_entry, 'PyTibiaThread', gameplayThreadClass)

    main_entry.main()

    contextClass.assert_called_once_with(main_entry.context)
    uiThreadClass.assert_called_once_with(contextInstance)
    uiThread.start.assert_called_once_with()
    gameplayThreadClass.assert_called_once_with(
        contextInstance,
        uiEnabled=True,
    )
    gameplayThread.mainloop.assert_called_once_with()
    assert contextInstance.context['shutdown'] is True
    contextInstance.pause.assert_called_once_with()
    uiThread.requestClose.assert_called_once_with()
    uiThread.join.assert_called_once_with()


def test_main_cli_mode_does_not_start_ui(monkeypatch):
    contextInstance = MagicMock()
    contextInstance.context = {'shutdown': False}
    contextClass = MagicMock(return_value=contextInstance)
    uiThreadClass = MagicMock()
    gameplayThread = MagicMock()
    gameplayThreadClass = MagicMock(return_value=gameplayThread)
    monkeypatch.setattr(main_entry, 'Context', contextClass)
    monkeypatch.setattr(main_entry, 'UIThread', uiThreadClass)
    monkeypatch.setattr(main_entry, 'PyTibiaThread', gameplayThreadClass)

    main_entry.main(uiEnabled=False)

    uiThreadClass.assert_not_called()
    gameplayThreadClass.assert_called_once_with(
        contextInstance,
        uiEnabled=False,
    )
    contextInstance.pause.assert_called_once_with()


def test_main_closes_ui_after_keyboard_interrupt(monkeypatch):
    contextInstance = MagicMock()
    contextInstance.context = {'shutdown': False}
    uiThread = MagicMock()
    gameplayThread = MagicMock()
    gameplayThread.mainloop.side_effect = KeyboardInterrupt()
    monkeypatch.setattr(
        main_entry, 'Context', MagicMock(return_value=contextInstance))
    monkeypatch.setattr(
        main_entry, 'UIThread', MagicMock(return_value=uiThread))
    monkeypatch.setattr(
        main_entry,
        'PyTibiaThread',
        MagicMock(return_value=gameplayThread),
    )

    with pytest.raises(KeyboardInterrupt):
        main_entry.main(uiEnabled=True)

    assert contextInstance.context['shutdown'] is True
    contextInstance.pause.assert_called_once_with()
    uiThread.requestClose.assert_called_once_with()
    uiThread.join.assert_called_once_with()
