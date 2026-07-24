from src.utils import keyboard


def test_keyboard_functions_delegate_to_pyautogui_without_real_input(monkeypatch):
    calls = []
    monkeypatch.setattr(
        keyboard.pyautogui,
        "hotkey",
        lambda *keys: calls.append(("hotkey", keys)),
    )
    monkeypatch.setattr(
        keyboard.pyautogui,
        "keyDown",
        lambda key: calls.append(("keyDown", key)),
    )
    monkeypatch.setattr(
        keyboard.pyautogui,
        "keyUp",
        lambda key: calls.append(("keyUp", key)),
    )
    monkeypatch.setattr(
        keyboard.pyautogui,
        "press",
        lambda *keys: calls.append(("press", keys)),
    )
    monkeypatch.setattr(
        keyboard.pyautogui,
        "write",
        lambda phrase: calls.append(("write", phrase)),
    )

    keyboard.hotkey("ctrl", "a")
    keyboard.keyDown("shift")
    keyboard.keyUp("shift")
    keyboard.press("f1")
    keyboard.write("test")

    assert calls == [
        ("hotkey", ("ctrl", "a")),
        ("keyDown", "shift"),
        ("keyUp", "shift"),
        ("press", ("f1",)),
        ("write", "test"),
    ]
