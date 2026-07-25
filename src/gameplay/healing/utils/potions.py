# TODO: add typings
# TODO: add unit tests
def matchHpHealing(healing, statusBar):
    if statusBar['hpPercentage'] is None or statusBar['manaPercentage'] is None:
        return False
    if healing['hpPercentageLessThanOrEqual'] is not None:
        if statusBar['hpPercentage'] > healing['hpPercentageLessThanOrEqual']:
            return False
    if healing['manaPercentageGreaterThanOrEqual'] is not None:
        if statusBar['manaPercentage'] < healing['manaPercentageGreaterThanOrEqual']:
            return False
    return True


# TODO: add typings
# TODO: add unit tests
def matchManaHealing(healing, statusBar):
    if statusBar['manaPercentage'] is None:
        return False
    if healing['manaPercentageLessThanOrEqual'] is None:
        return False
    if statusBar['manaPercentage'] > healing['manaPercentageLessThanOrEqual']:
        return False
    return True