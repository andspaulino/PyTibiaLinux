from time import time

import src.utils.keyboard as utilsKeyboard
from ...lootDiagnostics import printLootDiagnostic
from ...typings import Context
from .common.base import BaseTask


class QuickLootNearbyCorpsesTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.name = 'quickLootNearbyCorpses'
        self.isRootTask = True

    def do(self, context: Context) -> Context:
        lootState = context['loot']
        hotkey = lootState.get('quickLootHotkey', 'alt+q')
        keys = tuple(
            key.strip()
            for key in hotkey.split('+')
            if key.strip()
        )
        if len(keys) == 0:
            raise ValueError('Hotkey de Quick Loot não configurada')

        # Código Linux anterior:
        # o input iniciava confirmação por Loot Highlighting, registrava slots,
        # contava ausência e podia agendar até dois retries. A implementação
        # integral está em `docs/historico-looting/loot-highlighting-middleware.py.txt`.
        printLootDiagnostic(
            'quick_loot_send',
            context,
            hotkey=hotkey,
        )
        utilsKeyboard.hotkey(*keys)
        now = time()
        lootState['pending'] = False
        lootState['detectedAt'] = None
        lootState['lastQuickLootAt'] = now
        lootState['quickLootCooldownUntil'] = now + 0.7
        print(f'[Loot] Quick Loot enviado por {hotkey}')
        return context
