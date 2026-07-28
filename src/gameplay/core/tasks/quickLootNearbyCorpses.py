from time import time
import src.utils.keyboard as utilsKeyboard
from ...typings import Context
# Código Linux anterior: usado para aplicar cooldown visual aos nove slots.
# from ..middlewares.loot import QUICK_LOOT_NEARBY_SLOTS
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
        # Código Linux anterior (Marco 8.7):
        # utilsKeyboard.hotkey(*keys)
        # lootState['quickLootReady'] = False
        # lootState['quickLootAwaitingConfirmation'] = True
        # lootState['quickLootConfirmationBatches'] = 0
        # lootState['quickLootRetryCount'] = (
        #     lootState.get('quickLootRetryCount', 0) + 1
        # )
        # slots = [
        #     item['slot']
        #     for item in lootState.get('highlightedSlots', [])
        # ]
        # lootState['quickLootAttemptSlots'] = slots
        # now = time()
        # lootState['quickLootCooldownUntil'] = now + 0.7
        # lootState['quickLootDetectionPending'] = False
        # lootState['quickLootBlockingSlot'] = None

        # slots = [
        #     item['slot']
        #     for item in lootState.get('highlightedSlots', [])
        # ]
        slots = tuple(
            tuple(item['slot'])
            for item in lootState.get('highlightedSlots', [])
        )
        utilsKeyboard.hotkey(*keys)
        now = time()
        lootState['quickLootReady'] = False
        lootState['quickLootAwaitingConfirmation'] = True
        lootState['quickLootConfirmationBatches'] = 0
        lootState['quickLootAbsenceBatches'] = 0
        lootState['quickLootRetryCount'] = (
            lootState.get('quickLootRetryCount', 0) + 1
        )
        lootState['quickLootAttemptSlots'] = list(slots)
        lootState['quickLootCooldownUntil'] = now + 0.7
        # Código Linux anterior: liberava a caminhada imediatamente após o
        # input e aplicava cooldown visual aos nove slots, impedindo observar
        # corretamente a confirmação e mortes novas.
        # lootState['quickLootDetectionPending'] = False
        # lootState['quickLootBlockingSlot'] = None
        # slotCooldowns = lootState.setdefault('slotCooldowns', {})
        # for slot in QUICK_LOOT_NEARBY_SLOTS:
        #     slotCooldowns[tuple(slot)] = now + 3.0
        lootState['quickLootDetectionPending'] = True
        print(
            f"[Loot] Quick Loot enviado por {hotkey} "
            f"slots={slots} retry={lootState['quickLootRetryCount']}"
        )
        return context
