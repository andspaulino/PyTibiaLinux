#!/usr/bin/env python3
"""
Captura e registra monstros desconhecidos da Battle List e gera o template
binário correspondente da Game Window usando as letras originais.

Execução a partir da raiz:
  poetry -C PyTibia-Linux run python tools/capture_unknown_monsters.py
"""

import re
import sys
import time
from pathlib import Path

PYTIBIA_LINUX_ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = PYTIBIA_LINUX_ROOT.parent
sys.path.insert(0, str(PYTIBIA_LINUX_ROOT))

import cv2
import numpy as np

from builders.repositories.gameWindow.buildMonsters import buildMonsterImage
from src.wiki.creatures import creatures as wikiCreatures
from src.repositories.battleList.core import getCreatures, getFilledSlotsCount
from src.repositories.battleList.extractors import getContent as getBattleListContent
from src.repositories.battleList.locators import getBattleListIconPosition
from src.utils.core import getScreenshot, hashit


MONSTERS_DIR = PYTIBIA_LINUX_ROOT / "src" / "repositories" / "battleList" / "images" / "monsters"
CREATURES_FILE = PYTIBIA_LINUX_ROOT / "src" / "wiki" / "creatures.py"


def formatWikiValue(value):
    return "None" if value is None else str(value)


def upsertCreatureWiki(monsterName, exp=None, hp=None):
    if not CREATURES_FILE.exists():
        print(f"Erro: Arquivo {CREATURES_FILE} não encontrado.")
        return False

    content = CREATURES_FILE.read_text(encoding="utf-8")
    existing = wikiCreatures.get(monsterName)
    existingMisalignment = (
        existing.get('gameWindowMisalignment', {'x': 0, 'y': 0})
        if existing is not None
        else {'x': 0, 'y': 0}
    )
    finalExp = exp if exp is not None else (
        existing.get('exp') if existing is not None else None
    )
    finalHp = hp if hp is not None else (
        existing.get('hp') if existing is not None else None
    )
    newEntry = (
        f"    {monsterName!r}: {{'exp': {formatWikiValue(finalExp)}, "
        f"'hp': {formatWikiValue(finalHp)}, "
        "'gameWindowMisalignment': "
        f"{{'x': {existingMisalignment['x']}, 'y': {existingMisalignment['y']}}}}},"
    )

    if existing is not None:
        entryPattern = re.compile(
            rf"^\s*{re.escape(repr(monsterName))}:.*$",
            re.MULTILINE,
        )
        updatedContent, replacements = entryPattern.subn(newEntry, content, count=1)
        if replacements != 1:
            print(f"Erro ao localizar a entrada existente de '{monsterName}'.")
            return False
        CREATURES_FILE.write_text(updatedContent, encoding="utf-8")
        print(
            f"✓ Wiki atualizado: '{monsterName}' "
            f"(exp={finalExp}, hp={finalHp})"
        )
        return True

    insertPos = content.rfind("}")
    if insertPos == -1:
        print("Erro ao localizar fim do dicionário em creatures.py")
        return False
    beforeInsert = content[:insertPos].rstrip()
    if not beforeInsert.endswith(","):
        beforeInsert += ","
    updatedContent = beforeInsert + "\n" + newEntry + "\n" + content[insertPos:]
    CREATURES_FILE.write_text(updatedContent, encoding="utf-8")
    print(
        f"✓ Registrado no Wiki ({CREATURES_FILE}): '{monsterName}' "
        f"(exp={finalExp}, hp={finalHp})"
    )
    return True


# Nome anterior preservado para chamadas externas existentes.
def appendToCreaturesWiki(monsterName, exp=None, hp=None):
    return upsertCreatureWiki(monsterName, exp=exp, hp=hp)


def readOptionalNonNegativeInteger(label):
    while True:
        value = input(f"{label} (Enter para manter como None): ").strip()
        if not value:
            return None
        try:
            parsedValue = int(value)
        except ValueError:
            print("Digite um número inteiro ou pressione Enter.")
            continue
        if parsedValue < 0:
            print("O valor não pode ser negativo.")
            continue
        return parsedValue


def confirmCreatureRegistration(monsterName, exp, hp):
    existing = wikiCreatures.get(monsterName)
    if existing is not None:
        print(
            "Entrada existente: "
            f"exp={existing.get('exp')}, hp={existing.get('hp')}, "
            f"gameWindowMisalignment={existing.get('gameWindowMisalignment')}"
        )
    print(f"Novo cadastro: nome={monsterName!r}, exp={exp}, hp={hp}")
    confirmation = input("Confirmar gravação? [s/N]: ").strip().lower()
    return confirmation in ('s', 'sim', 'y', 'yes')


def saveMonsterImage(monsterName, nameRegion):
    # Processa o recorte para que apenas as letras (valores 192 ou 247) fiquem com 192 e o fundo fique 0 (preto puro)
    processedImage = np.zeros_like(nameRegion, dtype=np.uint8)
    processedImage[(nameRegion == 192) | (nameRegion == 247)] = 192

    imagePath = MONSTERS_DIR / f"{monsterName}.png"
    success = cv2.imwrite(str(imagePath), processedImage)
    if success:
        print(f"✓ Imagem binarizada (fundo preto 0) salva em: {imagePath}")
    else:
        print(f"Erro ao salvar imagem em: {imagePath}")
    return success


def buildGameWindowMonsterImage(monsterName):
    try:
        imagePath = buildMonsterImage(monsterName)
    except FileNotFoundError as error:
        print(f"Erro ao gerar template da Game Window: {error}")
        return False
    print(
        "✓ Template da Game Window gerado com fundo branco 255 e nome preto 0: "
        f"{imagePath}"
    )
    return True


def main():
    print("=" * 60)
    print("Capturador de Novos Monstros para o Battle List (PyTibia Linux)")
    print("=" * 60)
    print("1. Deixe o Tibia visível na tela com a janela do Battle List aberta.")
    print("2. A leitura será realizada em 3 segundos...")

    for secondsRemaining in range(3, 0, -1):
        print(f"Capturando em {secondsRemaining}...")
        time.sleep(1)

    screenshot = getScreenshot()
    if screenshot is None:
        print("Erro: Não foi possível capturar a tela.")
        return

    iconPos = getBattleListIconPosition(screenshot)
    if iconPos is None:
        print("Erro: Ícone do Battle List não encontrado na tela.")
        print("Verifique se o painel do Battle List está aberto e visível.")
        return

    content = getBattleListContent(screenshot)
    if content is None:
        print("Erro: Conteúdo do Battle List (bottomBar) não localizado.")
        return

    filledSlots = getFilledSlotsCount(content)
    creatures = getCreatures(content)

    print(f"\nDetectados {filledSlots} slots no Battle List:")
    unknownSlots = []
    for idx, creature in enumerate(creatures):
        name = creature['name']
        isAttacked = creature['isBeingAttacked']
        print(f"  Slot {idx + 1}: {name} (BeingAttacked={isAttacked})")
        if name == 'Unknown':
            unknownSlots.append((idx, creature))

    if not unknownSlots:
        print("\nNenhum monstro 'Unknown' detectado! Todos os monstros visíveis já estão cadastrados.")
        return

    print(f"\nEncontrado(s) {len(unknownSlots)} monstro(s) desconhecido(s) ('Unknown'):")

    for slotIdx, _ in unknownSlots:
        # Recorte exato do nome (11px altura x 131px largura):
        # A linha de texto (linha 8 da imagem de 11px) fica na linha 11 do slot em content (y1 + 8 = 3 + 8 = 11).
        y1 = slotIdx * 22 + 3
        y2 = y1 + 11
        x1 = 23
        x2 = 154
        nameRegion = content[y1:y2, x1:x2]

        # Linha de texto para hash (linha 8 da imagem de 11px de altura)
        creatureNameLine = nameRegion[8, 0:115]
        lineHash = hashit(creatureNameLine)

        print("-" * 60)
        print(f"Monstro desconhecido no Slot {slotIdx + 1}:")
        print(f"  Hash da linha de texto: {lineHash}")

        tempPath = TEMP_ROOT / f"temp_unknown_slot_{slotIdx + 1}.png"
        processedTemp = np.zeros_like(nameRegion, dtype=np.uint8)
        processedTemp[(nameRegion == 192) | (nameRegion == 247)] = 192
        cv2.imwrite(str(tempPath), processedTemp)
        print(f"  Recorte temporário salvo em: {tempPath}")

        print("\nDigite o nome EXATO do monstro (ex: 'Cave Rat', 'Dragon', etc.):")
        print("Pressione Enter sem digitar nada para ignorar este slot.")
        try:
            monsterName = input("Nome do monstro: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada pelo usuário.")
            break

        if not monsterName:
            print("Slot ignorado.")
            continue

        try:
            monsterExp = readOptionalNonNegativeInteger("XP do monstro")
            monsterHp = readOptionalNonNegativeInteger("HP total do monstro")
            if not confirmCreatureRegistration(monsterName, monsterExp, monsterHp):
                print("Cadastro cancelado; nenhum arquivo foi alterado para este slot.")
                continue
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada pelo usuário.")
            break

        # Salvar o template da Battle List e registrar o catálogo antes de
        # montar o template da Game Window com as letras originais.
        if saveMonsterImage(monsterName, nameRegion):
            wikiUpdated = appendToCreaturesWiki(
                monsterName,
                exp=monsterExp,
                hp=monsterHp,
            )
            gameWindowBuilt = (
                buildGameWindowMonsterImage(monsterName)
                if wikiUpdated
                else False
            )
            if wikiUpdated and gameWindowBuilt:
                print(f"🎉 Monstro '{monsterName}' cadastrado com sucesso!")
                print("Execute novamente o screen_preview.py para testar o reconhecimento!")
            else:
                print(
                    f"Cadastro de '{monsterName}' ficou incompleto; "
                    "revise os erros acima."
                )

    print("\nProcesso finalizado.")


if __name__ == "__main__":
    main()
