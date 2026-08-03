from src.gameplay.core.tasks import quickLootNearbyCorpses as quick_loot_task
from src.gameplay.core.tasks.quickLootNearbyCorpses import QuickLootNearbyCorpsesTask


def test_quick_loot_sends_one_hotkey_and_clears_pending(monkeypatch):
    calls = []
    monkeypatch.setattr(
        quick_loot_task.utilsKeyboard,
        'hotkey',
        lambda *keys: calls.append(keys),
    )
    context = {
        'loot': {
            'quickLootHotkey': 'alt+q',
            'pending': True,
            'detectedAt': 10,
            'quickLootCooldownUntil': 0,
        },
    }

    result = QuickLootNearbyCorpsesTask().do(context)

    assert result is context
    assert calls == [('alt', 'q')]
    assert context['loot']['pending'] is False
    assert context['loot']['detectedAt'] is None
    assert context['loot']['lastQuickLootAt'] is not None
    assert context['loot']['quickLootCooldownUntil'] > context['loot']['lastQuickLootAt']


def test_quick_loot_with_selected_corpse_executes_one_pulse(monkeypatch):
    calls = []
    monkeypatch.setattr(
        quick_loot_task.utilsKeyboard,
        'hotkey',
        lambda *keys: calls.append(keys),
    )
    corpse = {'coordinate': [100, 100, 7]}
    context = {
        'radar': {'coordinate': [100, 101, 7]},
        'loot': {
            'quickLootHotkey': 'alt+q',
            'pending': True,
            'detectedAt': 10,
            'corpsesToLoot': [corpse],
            'quickLootCooldownUntil': 0,
        },
    }

    task = QuickLootNearbyCorpsesTask(selectedCorpseCoordinate=[100, 100, 7])

    task.do(context)

    assert len(calls) == 1
    assert len(context['loot']['corpsesToLoot']) == 0
    assert context['loot']['pending'] is False


def test_discard_after_failed_approach_does_not_send_hotkey(monkeypatch):
    calls = []
    monkeypatch.setattr(
        quick_loot_task.utilsKeyboard,
        'hotkey',
        lambda *keys: calls.append(keys),
    )
    context = {
        'radar': {'coordinate': [100, 100, 7]},
        'loot': {
            'quickLootHotkey': 'alt+q',
            'pending': True,
            'detectedAt': 10,
            'corpsesToLoot': [{'coordinate': [104, 100, 7]}],
            'quickLootCooldownUntil': 0,
        },
    }

    QuickLootNearbyCorpsesTask(
        selectedCorpseCoordinate=[104, 100, 7],
        discardSelectedCorpse=True,
    ).do(context)

    assert calls == []
    assert context['loot']['corpsesToLoot'] == []
    assert context['loot']['pending'] is False

