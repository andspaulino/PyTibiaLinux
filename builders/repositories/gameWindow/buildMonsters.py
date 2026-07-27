from pathlib import Path

import numpy as np
from src.utils.image import loadFromRGBToGray, save
from src.wiki.creatures import creatures


PYTIBIA_LINUX_ROOT = Path(__file__).resolve().parents[3]
LETTERS_DIR = PYTIBIA_LINUX_ROOT / 'src' / 'repositories' / 'gameWindow' / 'images' / 'letters'
MONSTERS_DIR = PYTIBIA_LINUX_ROOT / 'src' / 'repositories' / 'gameWindow' / 'images' / 'monsters'


# Código original: o builder gerava todos os monstros diretamente dentro de
# main(). A composição foi extraída sem alterar sua ordem ou regras para que a
# ferramenta de cadastro possa gerar somente o novo nome.
# def main():
#     for monster in creatures:
#         monsterLetters = np.zeros((11, 0), dtype=np.uint8)
#         ... composição original preservada abaixo em buildMonsterImage() ...
#         save(monsterLetters, 'src/repositories/gameWindow/images/monsters/{}.png'.format(monster))


def getLetterAssetName(letter: str) -> str:
    if letter == ' ':
        return 'space'
    if letter == '.':
        return 'dot'
    return letter


def buildMonsterImage(monster: str, outputDirectory: Path = MONSTERS_DIR) -> Path:
    monsterLetters = np.zeros((11, 0), dtype=np.uint8)
    for index, originalLetter in enumerate(monster):
        letter = getLetterAssetName(originalLetter)
        letterDirectory = 'uppercase' if originalLetter.isupper() else 'lowercase'
        letterFullPath = LETTERS_DIR / letterDirectory / f'{letter}.png'
        if not letterFullPath.exists():
            raise FileNotFoundError(
                f"Letra sem asset para gerar o template da Game Window: {originalLetter!r} ({letterFullPath})"
            )
        letterAsArray = loadFromRGBToGray(str(letterFullPath)).copy()
        letterAsArray[np.nonzero(letterAsArray == 0)] = 1
        letterAsArray[np.nonzero(letterAsArray == 255)] = 0
        if index > 0:
            previousLetter = monster[index - 1]
            previousLetterIsMessLetter = previousLetter in ('t', 'T', 'r', 'R', 'f', 'L')
            letterIsMessLetter = originalLetter in ('t', 'T', 'f', 'J')
            if previousLetterIsMessLetter or letterIsMessLetter:
                size = 2 if previousLetterIsMessLetter and letterIsMessLetter else 1
                lastColumns = monsterLetters[:, monsterLetters.shape[1] - size:monsterLetters.shape[1]]
                firstColumns = letterAsArray[:, 0:size]
                mergedColumns = np.add(lastColumns, firstColumns)
                monsterLetters = monsterLetters[:, 0:monsterLetters.shape[1] - size]
                monsterLetters = np.hstack((monsterLetters, mergedColumns))
                remainingLetter = letterAsArray[:, size:letterAsArray.shape[1]]
                monsterLetters = np.hstack((monsterLetters, remainingLetter))
            else:
                monsterLetters = np.hstack((monsterLetters, letterAsArray))
        else:
            monsterLetters = np.hstack((monsterLetters, letterAsArray))
    monsterLetters[np.nonzero(monsterLetters == 0)] = 255
    monsterLetters[np.nonzero(monsterLetters == 1)] = 0
    monsterLetters[np.nonzero(monsterLetters == 2)] = 0
    outputDirectory.mkdir(parents=True, exist_ok=True)
    outputPath = outputDirectory / f'{monster}.png'
    save(monsterLetters, str(outputPath))
    return outputPath


def main():
    for monster in creatures:
        buildMonsterImage(monster)


# Trecho restante da implementação original desativada após a extração:
#                     monsterLetters.shape[1] - size:monsterLetters.shape[1]]
#                                                         monsterLetters.shape[1] - size:monsterLetters.shape[1]]
#                     primeiraFileiraDaProximaLetra = letterAsArray[:, 0:size]
#                     somaDasDuas = np.add(ultimaFileiraDaImagem,
#                                         primeiraFileiraDaProximaLetra)
#                     monsterLetters = monsterLetters[:.
#                                                     0:monsterLetters.shape[1] - size]
#                     monsterLetters = np.hstack((monsterLetters, somaDasDuas))
#                     restoDaProximaLetra = letterAsArray[:.
#                                                         size:letterAsArray.shape[1]]
#                     monsterLetters = np.hstack(
#                         (monsterLetters, restoDaProximaLetra))
#                 else:
#                     monsterLetters = np.hstack((monsterLetters, letterAsArray))
#             else:
#                 monsterLetters = np.hstack((monsterLetters, letterAsArray))
#         monsterLetters[np.nonzero(monsterLetters == 0)] = 255
#         monsterLetters[np.nonzero(monsterLetters == 1)] = 0
#         monsterLetters[np.nonzero(monsterLetters == 2)] = 0
#         save(
#             monsterLetters, 'src/repositories/gameWindow/images/monsters/{}.png'.format(monster))


if __name__ == '__main__':
    main()