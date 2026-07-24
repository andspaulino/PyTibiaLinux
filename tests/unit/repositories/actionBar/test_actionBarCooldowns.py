import numpy as np

from src.repositories.actionBar import core
from src.repositories.actionBar.config import images


def test_hasCooldownByImage_returns_none_without_cooldowns_region(monkeypatch):
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: None)

    assert core.hasCooldownByImage(np.zeros((10, 10), dtype=np.uint8), images["cooldowns"]["exori"]) is None


def test_hasCooldownByImage_returns_false_when_template_is_absent(monkeypatch):
    cooldowns = np.zeros((22, 100), dtype=np.uint8)
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)
    monkeypatch.setattr(core.coreUtils, "locate", lambda *_: None)

    assert core.hasCooldownByImage(cooldowns, images["cooldowns"]["exori"]) is False


def test_hasCooldownByImage_reads_the_original_active_pixel(monkeypatch):
    cooldowns = np.zeros((22, 100), dtype=np.uint8)
    cooldowns[20, 30] = 255
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)
    monkeypatch.setattr(core.coreUtils, "locate", lambda *_: (30, 0, 20, 20))

    assert core.hasCooldownByImage(cooldowns, images["cooldowns"]["exori"]) == True


def test_global_cooldown_hashes_are_recognized(monkeypatch):
    cooldowns = np.zeros((22, 80), dtype=np.uint8)
    cooldowns[0:20, 4:24] = images["cooldowns"]["attack"]
    cooldowns[0:20, 29:49] = images["cooldowns"]["healing"]
    cooldowns[0:20, 54:74] = images["cooldowns"]["support"]
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)

    assert core.hasAttackCooldown(cooldowns) is True
    assert core.hasHealingCooldown(cooldowns) is True
    assert core.hasSupportCooldown(cooldowns) is True
