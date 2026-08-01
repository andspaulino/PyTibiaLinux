from time import time

import src.utils.keyboard as utilsKeyboard
# Código Linux anterior:
# from ...loot import removeCorpseByCoordinate, removeCorpsesInQuickLootRange
from ...loot import (
    discardCorpseByCoordinate,
    normalizeCoordinate,
    removeCorpsesInQuickLootRange,
)
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

        # Código original (envio único sem confirmação):
        # utilsKeyboard.hotkey(*keys)
        # now = time()
        # corpsesToLoot = lootState.setdefault('corpsesToLoot', [])
        # playerCoordinate = context.get('radar', {}).get('coordinate')
        # removeCorpsesInQuickLootRange(corpsesToLoot, playerCoordinate)

        printLootDiagnostic(
            'quick_loot_send',
            context,
            hotkey=hotkey,
        )
        utilsKeyboard.hotkey(*keys)
        now = time()
        corpsesToLoot = lootState.setdefault('corpsesToLoot', [])
        playerCoordinate = context.get('radar', {}).get('coordinate')

        # Adaptação Linux: Realiza 2 tentativas do hotkey Quick Loot (0ms e 150ms)
        # com o personagem estabilizado no piso adjacente antes de remover o corpo da fila.
        if self.selectedCorpseCoordinate is not None:
            normSelected = normalizeCoordinate(self.selectedCorpseCoordinate)
            for corpse in corpsesToLoot:
                if isinstance(corpse, dict) and normalizeCoordinate(corpse.get('coordinate')) == normSelected:
                    attempts = corpse.get('lootAttempts', 0) + 1
                    corpse['lootAttempts'] = attempts
                    if attempts < 2:
                        lootState['lastQuickLootAt'] = now
                        lootState['quickLootCooldownUntil'] = now + 0.15
                        print(
                            f'[Loot] Quick Loot enviado por {hotkey} '
                            f'(tentativa {attempts}/2, corpos pendentes: {len(corpsesToLoot)})'
                        )
                        return context
                    break

        removeCorpsesInQuickLootRange(corpsesToLoot, playerCoordinate)
        if self.discardSelectedCorpse and self.selectedCorpseCoordinate is not None:
            # Código Linux anterior:
            # from ...loot import discardCorpseByCoordinate
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

