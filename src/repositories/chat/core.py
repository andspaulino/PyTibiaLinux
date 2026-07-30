import pathlib
from typing import Tuple, Union

import numpy as np
from src.shared.typings import BBox, GrayImage
from src.repositories.gameWindow.core import getLeftArrowPosition
from src.utils.core import cacheObjectPosition, hashit, locate, locateMultiple
# Código original:
# from src.utils.image import convertGraysToBlack, loadFromRGBToGray
from src.utils.image import loadFromRGBToGray
from .config import hashes


currentPath = pathlib.Path(__file__).parent.resolve()
chatMenuImg = loadFromRGBToGray(f'{currentPath}/images/chatMenu.png')
chatOnImg = loadFromRGBToGray(f'{currentPath}/images/chatOn.png')
chatOnImgTemp = loadFromRGBToGray(f'{currentPath}/images/chatOnTemp.png')
chatOffImg = loadFromRGBToGray(f'{currentPath}/images/chatOff.png')
chatOffImg = loadFromRGBToGray(f'{currentPath}/images/chatOff.png')
lootOfTextImg = loadFromRGBToGray(f'{currentPath}/images/lootOfText.png')
nothingTextImg = loadFromRGBToGray(f'{currentPath}/images/nothingText.png')
# Código original:
# oldListOfLootCheck = []
# A adaptação usa `None` para criar o baseline inicial sem falso evento.
oldListOfLootCheck: list | None = None


# TODO: add unit tests
# TODO: add perf
# TODO: add tests
def getTabs(screenshot: GrayImage):
    shouldFindTabs = True
    tabIndex = 0
    tabs = {}
    leftSidebarArrowsPosition = getLeftArrowPosition(screenshot)
    chatMenuPosition = getChatMenuPosition(screenshot)
    if leftSidebarArrowsPosition is None or chatMenuPosition is None:
        return {}
    # Código original:
    # x, y, width, height = leftSidebarArrowsPosition[0] + 18, chatMenuPosition[1], chatMenuPosition[0] - (
    #     leftSidebarArrowsPosition[0] + 18), 20
    x, y, width, height = leftSidebarArrowsPosition[0] + 18, chatMenuPosition[1], chatMenuPosition[0] - (
        leftSidebarArrowsPosition[0] + 18), 20
    chatsTabsContainerImage = screenshot[y:y + height, x:x + width]
    while shouldFindTabs:
        xOfTab = tabIndex * 96
        firstPixel = chatsTabsContainerImage[0, xOfTab]
        if firstPixel != 114 and firstPixel != 125:
            shouldFindTabs = False
            continue
        tabImage = chatsTabsContainerImage[2:16, xOfTab + 2:xOfTab + 2 + 92]
        tabName = hashes['tabs'].get(hashit(tabImage), 'Unknown')
        if tabName != 'Unknown':
            tabs.setdefault(
                tabName, {'isSelected': firstPixel == 114, 'position': (x + xOfTab, y, 92, 14)})
        tabIndex += 1
    return tabs


def resetLootBaseline() -> None:
    global oldListOfLootCheck
    oldListOfLootCheck = None


def normalizeLootLine(lineImage: GrayImage) -> GrayImage:
    # Código original:
    # return convertGraysToBlack(lineImage)
    return np.where(lineImage > 100, 255, 0).astype(np.uint8)


def hasNewLoot(screenshot: GrayImage) -> bool:
    global oldListOfLootCheck
    lootLines = getLootLines(screenshot)
    listOfLootCheck = [
        hashit(normalizeLootLine(lineImage))
        for lineImage, _ in lootLines[-5:]
    ]
    # Código original:
    # if len(listOfLootCheck) != 0 and len(oldListOfLootCheck) == 0:
    #     oldListOfLootCheck = listOfLootCheck
    #     return True
    if oldListOfLootCheck is None:
        oldListOfLootCheck = listOfLootCheck
        return False
    previousLootHashes = oldListOfLootCheck
    hasNewLine = any(
        lootLineHash not in previousLootHashes
        for lootLineHash in listOfLootCheck
    )
    oldListOfLootCheck = listOfLootCheck
    return hasNewLine


def getLootLines(screenshot: GrayImage) -> list:
    chatContainerPos = getChatMessagesContainerPosition(screenshot)
    if chatContainerPos is None:
        return []
    (x, y, w, h) = chatContainerPos
    messages = screenshot[y:y + h, x:x + w]
    lootLines = locateMultiple(lootOfTextImg, messages) or []
    linesWithLoot = []
    for line in lootLines:
        line = x, line[1] + y, w, line[3]
        lineImg = screenshot[line[1]:line[1] +
                             line[3], line[0]:line[0] + line[2]]
        nothingFound = locate(nothingTextImg, lineImg)
        if nothingFound is None:
            linesWithLoot.append((lineImg, line))
    return linesWithLoot




# TODO: add unit tests
# TODO: add perf
@cacheObjectPosition
def getChatMenuPosition(screenshot: GrayImage) -> Union[BBox, None]:
    return locate(screenshot, chatMenuImg)


# TODO: add unit tests
# TODO: add perf
@cacheObjectPosition
def getChatOffPosition(screenshot: GrayImage) -> Union[BBox, None]:
    return locate(screenshot, chatOffImg, confidence=0.985)


# TODO: add unit tests
# TODO: add perf
def getChatStatus(screenshot: GrayImage) -> Tuple[BBox, bool]:
    # TODO: chat off/on pos is always the same. Get it by hash
    chatOffPos = getChatOffPosition(screenshot)
    if chatOffPos:
        return chatOffPos, False
    chatOnPos = locate(screenshot, chatOnImgTemp, confidence=0.9)
    return chatOnPos, True


# TODO: add unit tests
# TODO: add perf
@cacheObjectPosition
def getChatMessagesContainerPosition(screenshot: GrayImage) -> BBox:
    leftSidebarArrows = getLeftArrowPosition(screenshot)
    chatMenu = getChatMenuPosition(screenshot)
    chatStatus = getChatStatus(screenshot)
    if leftSidebarArrows is None or chatMenu is None or chatStatus[0] is None:
        return None
    # Código original:
    # return leftSidebarArrows[0] + 5, chatMenu[1] + 18, chatStatus[0][0] + 40, (chatStatus[0][1] - 6) - (chatMenu[1] + 13)
    left = leftSidebarArrows[0] + 5
    right = chatStatus[0][0] + 40
    return (
        left,
        chatMenu[1] + 18,
        right - left,
        (chatStatus[0][1] - 6) - (chatMenu[1] + 13),
    )
