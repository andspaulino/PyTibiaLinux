from src.gameplay.context import context as initial_context
from src.gameplay.core.load import loadContextFromConfig

def test_load_context_from_config():
    # Make a copy of initial_context to avoid mutating the global state
    ctx = initial_context.copy()
    ctx['cavebot'] = initial_context['cavebot'].copy()
    ctx['cavebot']['waypoints'] = initial_context['cavebot']['waypoints'].copy()
    ctx['comboSpells'] = initial_context['comboSpells'].copy()

    config = {
        'backpacks': {
            'main': 'backpack1',
            'loot': 'backpack2',
        },
        'cavebot': {
            'enabled': True,
            'waypoints': {
                'items': [{'type': 'walk', 'label': 'start', 'coordinate': [1, 2, 3]}]
            }
        },
        'comboSpells': {
            'enabled': False,
            'items': [{'spell': 'exori', 'currentSpellIndex': 1}]
        },
        'healing': {
            'highPriority': {
                'swapRing': {'enabled': True}
            }
        }
    }

    loaded_ctx = loadContextFromConfig(config, ctx)

    assert loaded_ctx['backpacks'] == config['backpacks']
    assert loaded_ctx['cavebot']['enabled'] == config['cavebot']['enabled']
    assert loaded_ctx['cavebot']['waypoints']['items'] == config['cavebot']['waypoints']['items']
    assert loaded_ctx['comboSpells']['enabled'] == config['comboSpells']['enabled']
    # combo spells should have currentSpellIndex initialized to 0
    assert loaded_ctx['comboSpells']['items'][0]['spell'] == 'exori'
    assert loaded_ctx['comboSpells']['items'][0]['currentSpellIndex'] == 0
    assert loaded_ctx['healing']['highPriority']['swapRing']['enabled'] == config['healing']['highPriority']['swapRing']['enabled']


def test_load_context_from_config_minimal():
    ctx = initial_context.copy()
    ctx['cavebot'] = initial_context['cavebot'].copy()
    ctx['comboSpells'] = initial_context['comboSpells'].copy()

    config = {
        'backpacks': {
            'main': 'backpack1',
            'loot': 'backpack2',
        },
        'healing': {
            'highPriority': {
                'swapRing': {'enabled': True}
            }
        }
    }

    loaded_ctx = loadContextFromConfig(config, ctx)

    assert loaded_ctx['backpacks'] == config['backpacks']
    assert loaded_ctx['healing']['highPriority']['swapRing']['enabled'] == config['healing']['highPriority']['swapRing']['enabled']
    # Check that defaults were preserved
    assert loaded_ctx['cavebot']['enabled'] == initial_context['cavebot']['enabled']
    assert loaded_ctx['comboSpells']['enabled'] == initial_context['comboSpells']['enabled']

