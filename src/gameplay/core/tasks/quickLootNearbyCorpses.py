from time import time
import src.utils.keyboard as utilsKeyboard
from ...typings import Context
from .common.base import BaseTask


class QuickLootNearbyCorpsesTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.name = 'quickLootNearbyCorpses'
        self.isRootTask = True

    def do(self, context: Context) -> Context:
        lootState = context['loot']
        method = lootState.get('quickLootMethod', 'hotkey')
        if method != 'hotkey':
            raise ValueError(
                f"Método de Quick Loot ainda não implementado: {method}"
            )
        hotkey = lootState.get('quickLootHotkey', 'alt+q')
        keys = tuple(
            key.strip()
            for key in hotkey.split('+')
            if key.strip()
        )
        if len(keys) == 0:
            raise ValueError('Hotkey de Quick Loot não configurada')
        utilsKeyboard.hotkey(*keys)
        lootState['quickLootReady'] = False
        lootState['quickLootAwaitingConfirmation'] = True
        lootState['quickLootConfirmationBatches'] = 0
        lootState['quickLootRetryCount'] = (
            lootState.get('quickLootRetryCount', 0) + 1
        )
        # Código Linux anterior (Marco 8.7):
        # slots = [
        #     item['slot']
        #     for item in lootState.get('highlightedSlots', [])
        # ]
        slots = [
            item['slot']
            for item in lootState.get('highlightedSlots', [])
        ]
        lootState['quickLootAttemptSlots'] = slots
        now = time()
        lootState['quickLootCooldownUntil'] = now + 0.7
        lootState['quickLootDetectionPending'] = False
        lootState['quickLootBlockingSlot'] = None
        slotCooldowns = lootState.setdefault('slotCooldowns', {})
        for slot in slots:
            slotCooldowns[tuple(slot)] = now + 3.0
        print(
            f"[Loot] Quick Loot enviado por {hotkey} "
            f"slots={slots} retry={lootState['quickLootRetryCount']}"
        )
        return context
