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


def test_hasCooldownByName_classifies_exura_ico_exclusively(monkeypatch):
    cooldowns = np.zeros((22, 100), dtype=np.uint8)
    cooldowns[0:20, 30:50] = images["cooldowns"]["exura ico"]
    cooldowns[20, 30] = 255
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)

    assert core.hasCooldownByName(cooldowns, "exura ico") == True
    assert core.hasCooldownByName(cooldowns, "exura med ico") is False


def test_hasCooldownByName_classifies_exura_med_ico_exclusively(monkeypatch):
    cooldowns = np.zeros((22, 100), dtype=np.uint8)
    cooldowns[0:20, 30:50] = images["cooldowns"]["exura med ico"]
    cooldowns[20, 30] = 255
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)

    assert core.hasCooldownByName(cooldowns, "exura med ico") == True
    assert core.hasCooldownByName(cooldowns, "exura ico") is False


def test_hasCooldownByName_rejects_low_confidence_healing_icon(monkeypatch):
    cooldowns = np.zeros((22, 100), dtype=np.uint8)
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)

    assert core.hasCooldownByName(cooldowns, "exura ico") is False


def test_hasCooldownByName_rejects_ambiguous_healing_icon(monkeypatch):
    cooldowns = np.zeros((22, 100), dtype=np.uint8)
    exuraIco = images["cooldowns"]["exura ico"]
    cooldowns[0:20, 30:50] = exuraIco
    cooldowns[20, 30] = 255
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)
    monkeypatch.setitem(images["cooldowns"], "exura med ico", exuraIco)

    assert core.hasCooldownByName(cooldowns, "exura ico") is False
    assert core.hasCooldownByName(cooldowns, "exura med ico") is False


def test_hasCooldownByName_preserves_generic_spell_detection(monkeypatch):
    cooldowns = np.zeros((22, 100), dtype=np.uint8)
    cooldowns[20, 30] = 255
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)
    monkeypatch.setattr(core.coreUtils, "locate", lambda *_: (30, 0, 20, 20))

    assert core.hasCooldownByName(cooldowns, "exori") == True


def test_global_cooldown_hashes_are_recognized(monkeypatch):
    cooldowns = np.zeros((22, 80), dtype=np.uint8)
    cooldowns[0:20, 4:24] = images["cooldowns"]["attack"]
    cooldowns[0:20, 29:49] = images["cooldowns"]["healing"]
    cooldowns[0:20, 54:74] = images["cooldowns"]["support"]
    cooldowns[20, 29] = 255
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)

    assert core.hasAttackCooldown(cooldowns) is True
    assert core.hasHealingCooldown(cooldowns) == True
    assert core.hasSupportCooldown(cooldowns) is True


def test_hasHealingCooldown_returns_none_without_cooldowns_region(monkeypatch):
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: None)

    assert core.hasHealingCooldown(np.zeros((10, 10), dtype=np.uint8)) is None


def test_hasHealingCooldown_accepts_dark_inactive_icon(monkeypatch):
    cooldowns = np.zeros((22, 80), dtype=np.uint8)
    template = images["cooldowns"]["healing"]
    cooldowns[0:20, 29:49] = np.clip(template * 0.3, 0, 255).astype(np.uint8)
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)

    assert core.hasHealingCooldown(cooldowns) == False


def test_hasHealingCooldown_reads_active_pixel_after_template_matching(monkeypatch):
    cooldowns = np.zeros((22, 80), dtype=np.uint8)
    cooldowns[0:20, 29:49] = images["cooldowns"]["healing"]
    cooldowns[20, 29] = 255
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)

    assert core.hasHealingCooldown(cooldowns) == True


def test_hasHealingCooldown_rejects_incorrect_icon(monkeypatch):
    cooldowns = np.zeros((22, 80), dtype=np.uint8)
    cooldowns[0:20, 29:49] = images["cooldowns"]["support"]
    cooldowns[20, 29] = 255
    monkeypatch.setattr(core.actionBarExtractors, "getCooldownsImage", lambda _: cooldowns)

    assert core.hasHealingCooldown(cooldowns) is False
