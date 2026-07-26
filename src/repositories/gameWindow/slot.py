from typing import Union
from src.shared.typings import BBox, Slot
from src.utils.mouse import leftClick, moveTo, rightClick


# TODO: add unit tests
# TODO: add perf
def getSlotPosition(slot: Slot, gameWindowPosition: BBox) -> Union[Slot, None]:
    if slot is None or gameWindowPosition is None:
        return None
    # Código original:
    # (gameWindowPositionX, gameWindowPositionY, gameWindowWidth, gameWindowHeight) = gameWindowPosition
    # (slotX, slotY) = slot
    (gameWindowPositionX, gameWindowPositionY, gameWindowWidth, gameWindowHeight) = gameWindowPosition
    (slotX, slotY) = slot
    slotHeight = gameWindowHeight // 11
    slotWidth = gameWindowWidth // 15
    slotXCoordinate = gameWindowPositionX + (slotX * slotWidth)
    slotYCoordinate = gameWindowPositionY + (slotY * slotHeight)
    return (slotXCoordinate, slotYCoordinate)


# TODO: add unit tests
# TODO: add perf
def moveToSlot(slot: Slot, gameWindowPosition: BBox):
    slotPosition = getSlotPosition(slot, gameWindowPosition)
    if slotPosition is None:
        return
    moveTo(slotPosition)


# TODO: add unit tests
# TODO: add perf
def clickSlot(slot: Slot, gameWindowPosition: BBox):
    slotPosition = getSlotPosition(slot, gameWindowPosition)
    if slotPosition is None:
        return
    # Código original:
    # moveToSlot(slot, gameWindowPosition)
    # leftClick()
    moveTo(slotPosition)
    leftClick()


# TODO: add unit tests
# TODO: add perf
def rightClickSlot(slot: Slot, gameWindowPosition: BBox):
    slotPosition = getSlotPosition(slot, gameWindowPosition)
    if slotPosition is None:
        return
    # Código original:
    # moveToSlot(slot, gameWindowPosition)
    # rightClick()
    moveTo(slotPosition)
    rightClick()
