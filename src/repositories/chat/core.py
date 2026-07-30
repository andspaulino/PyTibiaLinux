import pathlib
from typing import Tuple, Union
from src.shared.typings import BBox, GrayImage
from src.repositories.gameWindow.core import getLeftArrowPosition
from src.utils.core import cacheObjectPosition, hashit, locate
from src.utils.image import loadFromRGBToGray
from .config import hashes


currentPath = pathlib.Path(__file__).parent.resolve()
chatMenuImg = loadFromRGBToGray(f'{currentPath}/images/chatMenu.png')
chatOnImg = loadFromRGBToGray(f'{currentPath}/images/chatOn.png')
chatOnImgTemp = loadFromRGBToGray(f'{currentPath}/images/chatOnTemp.png')
chatOffImg = loadFromRGBToGray(f'{currentPath}/images/chatOff.png')
chatOffImg = loadFromRGBToGray(f'{currentPath}/images/chatOff.png')
# Código original:
# lootOfTextImg, nothingTextImg e oldListOfLootCheck alimentavam `hasNewLoot()`.
# O detector integral está preservado em
# `docs/historico-looting/chat-loot-detector.py.txt`.


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


# Código original removido do runtime:
# `hasNewLoot()` calculava rolling hashes das últimas linhas `Loot of`, e
# `getLootLines()` localizava os templates `Loot of`/`nothing`. O snapshot
# executável anterior está arquivado em
# `docs/historico-looting/chat-loot-detector.py.txt`.



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
    return leftSidebarArrows[0] + 5, chatMenu[1] + 18, chatStatus[0][0] + 40, (chatStatus[0][1] - 6) - (chatMenu[1] + 13)
