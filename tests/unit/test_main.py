import sys
from unittest.mock import MagicMock, patch
import pytest
import main as main_entry

def test_main_cli_execution_with_single_window(monkeypatch):
    # Mock TinyDB
    mock_db = MagicMock()
    mock_profile = {
        'name': 'Test Profile',
        'enabled': True,
        'config': {
            'backpacks': {'main': '', 'loot': ''},
            'cavebot': {'enabled': False, 'waypoints': {'items': []}},
            'comboSpells': {'enabled': False, 'items': []},
            'healing': {}
        }
    }
    mock_db.search.return_value = [mock_profile]
    monkeypatch.setattr(main_entry, "TinyDB", lambda path: mock_db)
    
    # Mock window listing
    mock_window = MagicMock()
    mock_window.title = "Tibia - Character"
    mock_window.activate.return_value = True
    monkeypatch.setattr(main_entry, "get_tibia_windows", lambda: [mock_window])
    
    # Mock sleep
    sleep_calls = []
    monkeypatch.setattr(main_entry.time, "sleep", lambda secs: sleep_calls.append(secs))
    
    # Mock PyTibiaThread
    mainloop_called = False
    def mock_mainloop(self):
        nonlocal mainloop_called
        mainloop_called = True
        
    monkeypatch.setattr(main_entry.PyTibiaThread, "mainloop", mock_mainloop)
    
    main_entry.main()
    
    assert mainloop_called is True
    assert sleep_calls == [1]
    assert mock_window.activate.call_count == 1

def test_main_cli_execution_with_multiple_windows(monkeypatch):
    # Mock TinyDB
    mock_db = MagicMock()
    mock_profile = {
        'name': 'Test Profile',
        'enabled': True,
        'config': {
            'backpacks': {'main': '', 'loot': ''},
            'cavebot': {'enabled': False, 'waypoints': {'items': []}},
            'comboSpells': {'enabled': False, 'items': []},
            'healing': {}
        }
    }
    mock_db.search.return_value = [mock_profile]
    monkeypatch.setattr(main_entry, "TinyDB", lambda path: mock_db)
    
    # Mock window listing
    mock_window1 = MagicMock()
    mock_window1.title = "Tibia - Character 1"
    mock_window2 = MagicMock()
    mock_window2.title = "Tibia - Character 2"
    mock_window2.activate.return_value = True
    monkeypatch.setattr(main_entry, "get_tibia_windows", lambda: [mock_window1, mock_window2])
    
    # Mock input for choice selection (we pick 2, which corresponds to mock_window2)
    input_choices = ["2"]
    monkeypatch.setattr("builtins.input", lambda prompt: input_choices.pop(0))
    
    # Mock sleep
    monkeypatch.setattr(main_entry.time, "sleep", MagicMock())
    
    # Mock PyTibiaThread
    mainloop_called = False
    def mock_mainloop(self):
        nonlocal mainloop_called
        mainloop_called = True
        
    monkeypatch.setattr(main_entry.PyTibiaThread, "mainloop", mock_mainloop)
    
    main_entry.main()
    
    assert mainloop_called is True
    assert mock_window2.activate.call_count == 1
    assert mock_window1.activate.call_count == 0

def test_main_cli_execution_no_profile_exits(monkeypatch):
    # Mock TinyDB with no profiles
    mock_db = MagicMock()
    mock_db.search.return_value = []
    monkeypatch.setattr(main_entry, "TinyDB", lambda path: mock_db)
    
    exit_called = False
    def mock_exit(code):
        nonlocal exit_called
        exit_called = True
        raise SystemExit(code)
        
    monkeypatch.setattr(sys, "exit", mock_exit)
    
    with pytest.raises(SystemExit):
        main_entry.main()
        
    assert exit_called is True

def test_main_cli_execution_no_windows_exits(monkeypatch):
    # Mock TinyDB
    mock_db = MagicMock()
    mock_profile = {
        'name': 'Test Profile',
        'enabled': True,
        'config': {
            'backpacks': {'main': '', 'loot': ''},
            'cavebot': {'enabled': False, 'waypoints': {'items': []}},
            'comboSpells': {'enabled': False, 'items': []},
            'healing': {}
        }
    }
    mock_db.search.return_value = [mock_profile]
    monkeypatch.setattr(main_entry, "TinyDB", lambda path: mock_db)
    
    # Mock window listing (empty)
    monkeypatch.setattr(main_entry, "get_tibia_windows", lambda: [])
    
    exit_called = False
    def mock_exit(code):
        nonlocal exit_called
        exit_called = True
        raise SystemExit(code)
        
    monkeypatch.setattr(sys, "exit", mock_exit)
    
    with pytest.raises(SystemExit):
        main_entry.main()
        
    assert exit_called is True
