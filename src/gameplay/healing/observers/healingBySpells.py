from src.gameplay.core.tasks.orchestrator import TasksOrchestrator
from src.gameplay.core.tasks.useHotkey import UseHotkeyTask
from src.repositories.actionBar.core import hasCooldownByName
from src.wiki.spells import spells
from ...typings import Context


tasksOrchestrator = TasksOrchestrator()


# TODO: add unit tests
def healingBySpells(context: Context):
    currentTask = tasksOrchestrator.getCurrentTask(context)
    if currentTask is not None:
        if currentTask.status == 'completed':
            tasksOrchestrator.reset()
        else:
            tasksOrchestrator.do(context)
            return
    if context['statusBar']['hpPercentage'] is None or context['statusBar']['mana'] is None:
        return
    if context['healing']['spells']['criticalHealing']['enabled']:
        crit_spell = context['healing']['spells']['criticalHealing']['spell']
        crit_hotkey = context['healing']['spells']['criticalHealing'].get('hotkey', '5')
        if context['statusBar']['hpPercentage'] <= context['healing']['spells']['criticalHealing']['hpPercentageLessThanOrEqual'] and context['statusBar']['mana'] >= spells[crit_spell]['manaNeeded'] and not hasCooldownByName(context['screenshot'], crit_spell):
            tasksOrchestrator.setRootTask(
                context, UseHotkeyTask(crit_hotkey))
            return
    if context['healing']['spells']['lightHealing']['enabled']:
        light_spell = context['healing']['spells']['lightHealing']['spell']
        light_hotkey = context['healing']['spells']['lightHealing'].get('hotkey', '6')
        if context['statusBar']['hpPercentage'] <= context['healing']['spells']['lightHealing']['hpPercentageLessThanOrEqual'] and context['statusBar']['mana'] >= spells[light_spell]['manaNeeded'] and not hasCooldownByName(context['screenshot'], light_spell):
            tasksOrchestrator.setRootTask(
                context, UseHotkeyTask(light_hotkey))
            return
    if context['healing']['spells']['utura']['enabled']:
        utura_hotkey = context['healing']['spells']['utura'].get('hotkey', '7')
        if context['statusBar']['mana'] >= spells['utura']['manaNeeded'] and not hasCooldownByName(context['screenshot'], 'utura'):
            tasksOrchestrator.setRootTask(
                context, UseHotkeyTask(utura_hotkey))
            return
    if context['healing']['spells']['uturaGran']['enabled']:
        utura_gran_hotkey = context['healing']['spells']['uturaGran'].get('hotkey', '8')
        if context['statusBar']['mana'] >= spells['utura gran']['manaNeeded'] and not hasCooldownByName(context['screenshot'], 'utura gran'):
            tasksOrchestrator.setRootTask(
                context, UseHotkeyTask(utura_gran_hotkey))
