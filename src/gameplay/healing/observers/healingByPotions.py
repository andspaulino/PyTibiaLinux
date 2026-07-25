from src.gameplay.core.tasks.orchestrator import TasksOrchestrator
from src.gameplay.core.tasks.useHotkey import UseHotkeyTask
from src.repositories.actionBar.core import slotIsAvailable
from ...typings import Context
from ..utils.potions import matchHpHealing, matchManaHealing


tasksOrchestrator = TasksOrchestrator()


def getSlot(hotkey: str, defaultSlot: int) -> int:
    if hotkey and hotkey.isdigit():
        return int(hotkey)
    return defaultSlot


# TODO: add unit tests
def healingByPotions(context: Context):
    currentTask = tasksOrchestrator.getCurrentTask(context)
    if currentTask is not None:
        if currentTask.status == 'completed':
            tasksOrchestrator.reset()
        else:
            tasksOrchestrator.do(context)
            return
    if context['healing']['potions']['firstHealthPotion']['enabled']:
        hp_hotkey = context['healing']['potions']['firstHealthPotion']['hotkey']
        hp_slot = getSlot(hp_hotkey, 1)
        if matchHpHealing(context['healing']['potions']['firstHealthPotion'], context['statusBar']) and slotIsAvailable(context['screenshot'], hp_slot):
            tasksOrchestrator.setRootTask(context, UseHotkeyTask(
                hp_hotkey, delayAfterComplete=1))
            return
    if context['healing']['potions']['firstManaPotion']['enabled']:
        mana_hotkey = context['healing']['potions']['firstManaPotion']['hotkey']
        mana_slot = getSlot(mana_hotkey, 2)
        if matchManaHealing(context['healing']['potions']['firstManaPotion'], context['statusBar']) and slotIsAvailable(context['screenshot'], mana_slot):
            tasksOrchestrator.setRootTask(context, UseHotkeyTask(
                mana_hotkey, delayAfterComplete=1))
            return
