from src.utils.core import getScreenshot
from ...typings import Context

def setScreenshotMiddleware(context: Context) -> Context:
    context['screenshot'] = getScreenshot()
    return context
