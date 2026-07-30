import numpy as np

from src.repositories.chat import core


def test_loot_line_normalization_ignores_dark_chat_background():
    firstBackground = np.array([
        [36, 140, 89],
        [47, 140, 68],
    ], dtype=np.uint8)
    secondBackground = np.array([
        [80, 140, 40],
        [59, 140, 49],
    ], dtype=np.uint8)

    assert np.array_equal(
        core.normalizeLootLine(firstBackground),
        core.normalizeLootLine(secondBackground),
    )


def test_first_read_creates_baseline_without_event(monkeypatch):
    firstLine = object()
    monkeypatch.setattr(core, 'getLootLines', lambda screenshot: [(firstLine, None)])
    monkeypatch.setattr(core, 'normalizeLootLine', lambda image: image)
    monkeypatch.setattr(core, 'hashit', lambda image: image)
    core.resetLootBaseline()

    assert core.hasNewLoot(object()) is False


def test_new_loot_line_after_baseline_is_detected(monkeypatch):
    firstLine = object()
    secondLine = object()
    lines = [(firstLine, None)]
    monkeypatch.setattr(core, 'getLootLines', lambda screenshot: lines)
    monkeypatch.setattr(core, 'normalizeLootLine', lambda image: image)
    monkeypatch.setattr(core, 'hashit', lambda image: image)
    core.resetLootBaseline()

    assert core.hasNewLoot(object()) is False
    lines.append((secondLine, None))
    assert core.hasNewLoot(object()) is True
    assert core.hasNewLoot(object()) is False


def test_first_line_after_empty_baseline_is_detected(monkeypatch):
    line = object()
    lines = []
    monkeypatch.setattr(core, 'getLootLines', lambda screenshot: lines)
    monkeypatch.setattr(core, 'normalizeLootLine', lambda image: image)
    monkeypatch.setattr(core, 'hashit', lambda image: image)
    core.resetLootBaseline()

    assert core.hasNewLoot(object()) is False
    lines.append((line, None))
    assert core.hasNewLoot(object()) is True


def test_chat_messages_width_ends_at_chat_status(monkeypatch):
    monkeypatch.setattr(core, 'getLeftArrowPosition', lambda screenshot: (176, 0, 0, 0))
    monkeypatch.setattr(core, 'getChatMenuPosition', lambda screenshot: (1539, 800, 0, 0))
    monkeypatch.setattr(core, 'getChatStatus', lambda screenshot: ((1500, 1000, 0, 0), False))

    screenshot = np.zeros((1080, 1920), dtype=np.uint8)

    assert core.getChatMessagesContainerPosition(screenshot) == (
        181,
        818,
        1359,
        181,
    )
