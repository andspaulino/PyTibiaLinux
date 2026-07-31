from time import time

import src.utils.keyboard as utilsKeyboard
from ...loot import removeCorpseByCoordinate, removeCorpsesInQuickLootRange
from ...lootDiagnostics import printLootDiagnostic
from ...typings import Context
from .common.base import BaseTask


class QuickLootNearbyCorpsesTask(BaseTask):
    def __init__(
        self,
        selectedCorpseCoordinate=None,
        discardSelectedCorpse=False,
    ):
        super().__init__()
        self.name = 'quickLootNearbyCorpses'
        self.isRootTask = True
        self.selectedCorpseCoordinate = selectedCorpseCoordinate
        self.discardSelectedCorpse = discardSelectedCorpse

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
        corpsesToLoot = lootState.setdefault('corpsesToLoot', [])
        playerCoordinate = context.get('radar', {}).get('coordinate')
        removeCorpsesInQuickLootRange(corpsesToLoot, playerCoordinate)
        if self.discardSelectedCorpse and self.selectedCorpseCoordinate is not None:
            from ...loot import discardCorpseByCoordinate
            discardCorpseByCoordinate(
                corpsesToLoot,
                self.selectedCorpseCoordinate,
                context=context,
                reason='approach-failed',
            )
        lootState['pending'] = len(corpsesToLoot) > 0
        lootState['detectedAt'] = (
            lootState.get('detectedAt')
            if lootState['pending']
            else None
        )
        lootState['lastQuickLootAt'] = now
        lootState['quickLootCooldownUntil'] = now + 0.7
        print(
            f'[Loot] Quick Loot enviado por {hotkey} '
            f'(corpos pendentes: {len(corpsesToLoot)})'
        )
        return context

