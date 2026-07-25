import subprocess
from unittest.mock import MagicMock
from src.utils.window import TibiaWindow, get_tibia_windows

def test_tibia_window_activate(monkeypatch):
    subprocess_calls = []

    def mock_run(cmd, *args, **kwargs):
        subprocess_calls.append(cmd)
        return MagicMock(returncode=0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    window = TibiaWindow("12345", "Tibia - CharacterName")
    assert window.activate() is True
    assert subprocess_calls == [
        ['xdotool', 'windowactivate', '12345'],
        ['xdotool', 'windowfocus', '12345']
    ]

def test_tibia_window_activate_failure(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.SubprocessError("Failed to run command")

    monkeypatch.setattr(subprocess, "run", mock_run)

    window = TibiaWindow("12345", "Tibia - CharacterName")
    assert window.activate() is False

def test_get_tibia_windows_success(monkeypatch):
    def mock_run(cmd, *args, **kwargs):
        # cmd[1] is search or getwindowname
        if "search" in cmd:
            stdout = "111\n222\n"
            return MagicMock(returncode=0, stdout=stdout)
        elif "getwindowname" in cmd:
            wid = cmd[2]
            if wid == "111":
                return MagicMock(returncode=0, stdout="Tibia - Character 1\n")
            elif wid == "222":
                return MagicMock(returncode=0, stdout="Tibia - Character 2\n")
        return MagicMock(returncode=1)

    monkeypatch.setattr(subprocess, "run", mock_run)

    windows = get_tibia_windows()
    assert len(windows) == 2
    assert windows[0].window_id == "111"
    assert windows[0].title == "Tibia - Character 1"
    assert windows[1].window_id == "222"
    assert windows[1].title == "Tibia - Character 2"

def test_get_tibia_windows_no_results(monkeypatch):
    def mock_run(cmd, *args, **kwargs):
        return MagicMock(returncode=1, stdout="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    windows = get_tibia_windows()
    assert windows == []

def test_get_tibia_windows_xdotool_missing(monkeypatch):
    def mock_run(*args, **kwargs):
        raise FileNotFoundError("xdotool not found")

    monkeypatch.setattr(subprocess, "run", mock_run)

    windows = get_tibia_windows()
    assert windows == []
