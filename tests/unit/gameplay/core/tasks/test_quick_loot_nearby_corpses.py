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
            'pendingSlot': (8, 5),
            'detectedAt': 10,
            'quickLootCooldownUntil': 0,
        },
    }

    result = QuickLootNearbyCorpsesTask().do(context)

    assert result is context
    assert calls == [('alt', 'q')]
    assert context['loot']['pending'] is False
    assert context['loot']['pendingSlot'] is None
    assert context['loot']['detectedAt'] is None
    assert context['loot']['lastQuickLootAt'] is not None
    assert context['loot']['quickLootCooldownUntil'] > context['loot']['lastQuickLootAt']
