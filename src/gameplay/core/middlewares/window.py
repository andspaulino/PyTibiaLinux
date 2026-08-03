# Código original Windows:
# import pygetwindow as gw
# import re
# import win32gui
from ...typings import Context
from src.utils.window import get_tibia_windows


# Código original Windows:
# def setTibiaWindowMiddleware(context: Context) -> Context:
#     if context['window'] is None:
#         windowsList: list = []
#         win32gui.EnumWindows(
#             lambda hwnd, param: param.append(hwnd), windowsList)
#         windowsNames = list(
#             map(lambda hwnd: win32gui.GetWindowText(hwnd), windowsList))
#         regex = re.compile(r'Tibia - .*')
#         windowsFilter = list(
#             filter(lambda windowName: regex.match(windowName), windowsNames))
#         if len(windowsFilter) > 0:
#             context['window'] = gw.getWindowsWithTitle(windowsFilter[0])[0]
#     return context


# TODO: add unit tests
def setTibiaWindowMiddleware(context: Context) -> Context:
    if context['window'] is None:
        tibiaWindows = get_tibia_windows()
        if len(tibiaWindows) > 0:
            context['window'] = tibiaWindows[0]
    return context
