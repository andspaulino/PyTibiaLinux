import pyautogui
from time import sleep, time
import traceback
from src.gameplay.core.middlewares.screenshot import setScreenshotMiddleware
from src.gameplay.core.middlewares.playerStatus import setMapPlayerStatusMiddleware
from src.gameplay.core.middlewares.tasks import setCleanUpTasksMiddleware
from src.gameplay.healing.observers.eatFood import eatFood
from src.gameplay.healing.observers.healingBySpells import healingBySpells
from src.gameplay.healing.observers.healingByPotions import healingByPotions
from src.gameplay.healing.observers.swapAmulet import swapAmulet
from src.gameplay.healing.observers.swapRing import swapRing

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

class PyTibiaThread:
    def __init__(self, context):
        self.context = context

    def mainloop(self):
        while True:
            try:
                # If paused, sleep briefly to avoid 100% CPU usage (busy-wait fix)
                if self.context.context['pause']:
                    sleep(0.1)
                    continue
                
                startTime = time()
                self.context.context = self.handleGameData(
                    self.context.context)
                self.context.context = self.handleGameplayTasks(
                    self.context.context)
                self.context.context = self.context.context['tasksOrchestrator'].do(
                    self.context.context)
                
                # Executing only the observers that are already implemented
                healingByPotions(self.context.context)
                healingBySpells(self.context.context)
                swapAmulet(self.context.context)
                swapRing(self.context.context)
                eatFood(self.context.context)
                
                endTime = time()
                diff = endTime - startTime
                # Sleep to maintain ~45ms loop cycle
                sleep(max(0.045 - diff, 0))
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt detected. Stopping gameplay loop.")
                self.context.context['pause'] = True
                break
            except Exception:
                print('An exception occurred in PyTibiaThread loop:', traceback.format_exc())
                # Safety pause on critical error
                sleep(1)

    def handleGameData(self, context):
        if context['pause']:
            return context
        context = setScreenshotMiddleware(context)
        # setMapPlayerStatusMiddleware reads HP and Mana from screenshot
        context = setMapPlayerStatusMiddleware(context)
        context = setCleanUpTasksMiddleware(context)
        return context

    def handleGameplayTasks(self, context):
        # Cavebot, Targeting, and Looting tasks are not yet implemented.
        # This will be populated as those sub-modules are ported in future milestones.
        return context
