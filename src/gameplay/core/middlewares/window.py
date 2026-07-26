from ...typings import Context
from src.utils.window import get_tibia_windows


# TODO: add unit tests
def setTibiaWindowMiddleware(context: Context) -> Context:
    if context['window'] is None:
        tibia_windows = get_tibia_windows()
        if len(tibia_windows) > 0:
            context['window'] = tibia_windows[0]
    return context
