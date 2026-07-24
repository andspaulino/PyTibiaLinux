from src.gameplay.core.tasks import useHotkey


def test_useHotkeyTask_preserves_contract_and_uses_keyboard_wrapper(monkeypatch):
    pressedKeys = []
    monkeypatch.setattr(useHotkey, "press", pressedKeys.append)
    context = {}
    task = useHotkey.UseHotkeyTask("f1", delayAfterComplete=2)

    result = task.do(context)

    assert result is context
    assert task.name == "useHotkey"
    assert task.hotkey == "f1"
    assert task.delayAfterComplete == 2
    assert pressedKeys == ["f1"]
