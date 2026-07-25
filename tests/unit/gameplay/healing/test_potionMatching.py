from src.gameplay.healing.utils.potions import matchHpHealing, matchManaHealing


def test_matchHpHealing_accepts_inclusive_hp_and_mana_limits():
    healing = {
        "hpPercentageLessThanOrEqual": 40,
        "manaPercentageGreaterThanOrEqual": 80,
    }
    statusBar = {"hpPercentage": 40, "manaPercentage": 80}

    assert matchHpHealing(healing, statusBar) is True


def test_matchHpHealing_rejects_hp_above_limit():
    healing = {
        "hpPercentageLessThanOrEqual": 40,
        "manaPercentageGreaterThanOrEqual": 50,
    }
    statusBar = {"hpPercentage": 41, "manaPercentage": 80}

    assert matchHpHealing(healing, statusBar) is False


def test_matchHpHealing_rejects_mana_below_limit_even_when_hp_matches():
    healing = {
        "hpPercentageLessThanOrEqual": 70,
        "manaPercentageGreaterThanOrEqual": 50,
    }
    statusBar = {"hpPercentage": 40, "manaPercentage": 49}

    assert matchHpHealing(healing, statusBar) is False


def test_matchHpHealing_uses_mana_instead_of_hp_for_mana_limit():
    healing = {
        "hpPercentageLessThanOrEqual": 70,
        "manaPercentageGreaterThanOrEqual": 50,
    }
    statusBar = {"hpPercentage": 40, "manaPercentage": 80}

    assert matchHpHealing(healing, statusBar) is True


def test_matchHpHealing_ignores_optional_none_limits():
    healing = {
        "hpPercentageLessThanOrEqual": None,
        "manaPercentageGreaterThanOrEqual": None,
    }
    statusBar = {"hpPercentage": 100, "manaPercentage": 0}

    assert matchHpHealing(healing, statusBar) is True


def test_matchManaHealing_requires_a_configured_limit():
    healing = {"manaPercentageLessThanOrEqual": None}
    statusBar = {"manaPercentage": 0}

    assert matchManaHealing(healing, statusBar) is False


def test_matchManaHealing_accepts_inclusive_limit():
    healing = {"manaPercentageLessThanOrEqual": 30}
    statusBar = {"manaPercentage": 30}

    assert matchManaHealing(healing, statusBar) is True


def test_matchManaHealing_rejects_mana_above_limit():
    healing = {"manaPercentageLessThanOrEqual": 30}
    statusBar = {"manaPercentage": 31}

    assert matchManaHealing(healing, statusBar) is False
