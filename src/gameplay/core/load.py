def merge_dict(target, source):
    """Recursively merges source dict keys into target dict."""
    for k, v in source.items():
        if k in target and isinstance(target[k], dict) and isinstance(v, dict):
            merge_dict(target[k], v)
        else:
            # If target has a dict but source has something else, or if k is new
            if isinstance(v, dict):
                target[k] = v.copy()
            else:
                target[k] = v

def loadContextFromConfig(config, context):
    # backpacks
    if 'backpacks' in config:
        context['backpacks'].update(config['backpacks'])
    # cavebot
    if 'cavebot' in config:
        merge_dict(context['cavebot'], config['cavebot'])
    # comboSpells
    if 'comboSpells' in config:
        context['comboSpells']['enabled'] = config['comboSpells']['enabled']
        if 'items' in config['comboSpells']:
            context['comboSpells']['items'] = []
            for comboSpellsItem in config['comboSpells']['items']:
                comboSpellsItemCopy = comboSpellsItem.copy()
                comboSpellsItemCopy['currentSpellIndex'] = 0
                context['comboSpells']['items'].append(comboSpellsItemCopy)
    # healing
    if 'healing' in config:
        merge_dict(context['healing'], config['healing'])
    return context
