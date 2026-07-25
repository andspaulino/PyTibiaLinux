from unittest.mock import MagicMock
import src.gameplay.core.middlewares.screenshot as screenshot_mw

def test_screenshot_middleware(monkeypatch):
    mock_screenshot = MagicMock()
    monkeypatch.setattr(screenshot_mw, "getScreenshot", lambda: mock_screenshot)
    
    context = {}
    result = screenshot_mw.setScreenshotMiddleware(context)
    assert result['screenshot'] == mock_screenshot
