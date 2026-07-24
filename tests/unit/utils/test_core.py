import cv2
import numpy as np

from src.utils import core


class FakeCamera:
    def __init__(self, screenshots):
        self.monitors = [
            {"left": 0, "top": 0, "width": 2, "height": 2},
            {"left": 0, "top": 0, "width": 2, "height": 2},
        ]
        self.screenshots = iter(screenshots)
        self.grabbedMonitors = []

    def grab(self, monitor):
        self.grabbedMonitors.append(monitor)
        return next(self.screenshots)


def setup_function():
    core.camera = None
    core.latestScreenshot = None


def test_getScreenshot_converts_primary_monitor_bgra_frame_to_grayscale():
    screenshot = np.array(
        [
            [[0, 0, 255, 255], [0, 255, 0, 255]],
            [[255, 0, 0, 255], [255, 255, 255, 255]],
        ],
        dtype=np.uint8,
    )
    camera = FakeCamera([screenshot])
    core.camera = camera

    result = core.getScreenshot()

    expected = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2GRAY)
    np.testing.assert_array_equal(result, expected)
    assert result.shape == (2, 2)
    assert result.dtype == np.uint8
    assert camera.grabbedMonitors == [camera.monitors[1]]


def test_getScreenshot_returns_latest_valid_frame_when_grab_returns_none():
    screenshot = np.array([[[10, 20, 30, 255]]], dtype=np.uint8)
    camera = FakeCamera([screenshot, None])
    core.camera = camera

    firstResult = core.getScreenshot()
    secondResult = core.getScreenshot()

    assert secondResult is firstResult


def test_getScreenshot_returns_none_without_a_previous_valid_frame():
    core.camera = FakeCamera([None])

    assert core.getScreenshot() is None


def test_getCamera_reuses_the_same_capture_instance(monkeypatch):
    createdCameras = []
    fakeCamera = FakeCamera([])

    def createCamera():
        createdCameras.append(fakeCamera)
        return fakeCamera

    monkeypatch.setattr(core, "MSS", createCamera)

    assert core.getCamera() is fakeCamera
    assert core.getCamera() is fakeCamera
    assert createdCameras == [fakeCamera]
