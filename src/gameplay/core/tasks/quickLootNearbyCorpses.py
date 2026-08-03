from time import sleep, time

import src.utils.keyboard as utilsKeyboard
# Código Linux anterior:
# from ...loot import removeCorpseByCoordinate, removeCorpsesInQuickLootRange
from ...loot import (
    discardCorpseByCoordinate,
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

        now = time()
        corpsesToLoot = lootState.setdefault('corpsesToLoot', [])
        playerCoordinate = context.get('radar', {}).get('coordinate')

        # Código Linux anterior:
        # mesmo quando a aproximação havia falhado, a task enviava dois Alt+Q
        # fora do alcance antes de descartar o cadáver selecionado.
        if self.discardSelectedCorpse and self.selectedCorpseCoordinate is not None:
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
            return context

        printLootDiagnostic(
            'quick_loot_send',
            context,
            hotkey=hotkey,
        )
        # Código Linux anterior:
        # utilsKeyboard.hotkey(*keys)
        # Com pyautogui.PAUSE=0, a combinação era pressionada e liberada quase
        # instantaneamente; o log registrava o envio, mas o cliente podia não
        # reconhecer o Quick Loot. Continua sendo um único pressionamento da
        # tecla final, mantendo os modificadores brevemente.
        modifiers = keys[:-1]
        finalKey = keys[-1]
        pressedModifiers = []
        finalKeyIsPressed = False
        try:
            for modifier in modifiers:
                utilsKeyboard.keyDown(modifier)
                pressedModifiers.append(modifier)
            if pressedModifiers:
                sleep(0.05)
            # Código Linux anterior:
            # utilsKeyboard.press(finalKey)
            # Com PAUSE=0, até uma tecla única tinha key-down/key-up imediato.
            utilsKeyboard.keyDown(finalKey)
            finalKeyIsPressed = True
            sleep(0.05)
        finally:
            if finalKeyIsPressed:
                utilsKeyboard.keyUp(finalKey)
            for modifier in reversed(pressedModifiers):
                utilsKeyboard.keyUp(modifier)

        # Código Linux anterior:
        # eram enviados dois pulsos, separados por 0,15 s, usando lootAttempts
        # persistido no cadáver. O cliente atual confirmou que um único Alt+Q
        # é suficiente para toda a área 3×3.
        # if self.selectedCorpseCoordinate is not None:
        #     normSelected = normalizeCoordinate(self.selectedCorpseCoordinate)
        #     for corpse in corpsesToLoot:
        #         if (
        #             isinstance(corpse, dict)
        #             and normalizeCoordinate(corpse.get('coordinate'))
        #             == normSelected
        #         ):
        #             attempts = corpse.get('lootAttempts', 0) + 1
        #             corpse['lootAttempts'] = attempts
        #             if attempts < 2:
        #                 lootState['quickLootCooldownUntil'] = now + 0.15
        #                 return context
        #             break

        removeCorpsesInQuickLootRange(corpsesToLoot, playerCoordinate)
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

