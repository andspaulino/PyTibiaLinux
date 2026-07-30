import json
from copy import deepcopy

import pytest

from src.gameplay.core.load import loadContextFromConfig
from src.routes.store import RouteStore
from src.routes.validator import RouteValidationError


def makeContext():
    return {
        'backpacks': {
            'main': '',
            'loot': '',
        },
        'cavebot': {
            'enabled': False,
            'waypoints': {
                'items': [],
                'currentIndex': 3,
                'state': {'goal': [1, 2, 3]},
            },
        },
    }


def makeWaypoint(label, x):
    return {
        'label': label,
        'type': 'walk',
        'coordinate': [x, 31234, 7],
        'options': {},
    }


def makeRoute():
    return {
        'schemaVersion': 1,
        'name': 'Muglex Newhaven',
        'waypoints': [
            makeWaypoint('route-1', 32562),
            makeWaypoint('route-2', 32557),
        ],
    }


def test_empty_config_returns_existing_context():
    context = makeContext()

    assert loadContextFromConfig({}, context) is context


def test_legacy_waypoints_continue_to_load_without_aliasing_config():
    context = makeContext()
    config = {
        'cavebot': {
            'enabled': True,
            'waypoints': {
                'items': [makeWaypoint('legacy', 1)],
            },
        },
    }
    originalConfig = deepcopy(config)

    result = loadContextFromConfig(config, context)
    result['cavebot']['waypoints']['items'][0]['coordinate'][0] = 99

    assert config == originalConfig
    assert config['cavebot']['waypoints']['items'][0]['coordinate'][0] == 1
    assert result['cavebot']['enabled'] is True
    assert result['cavebot']['waypoints']['currentIndex'] == 3


def test_external_route_has_priority_and_resets_runtime_state(tmp_path):
    RouteStore(tmp_path).save('muglex-newhaven.json', makeRoute())
    context = makeContext()
    config = {
        'cavebot': {
            'enabled': True,
            'routeId': 'muglex-newhaven',
            'waypoints': {
                'items': [makeWaypoint('legacy', 1)],
            },
        },
    }
    originalConfig = deepcopy(config)

    result = loadContextFromConfig(config, context, tmp_path)

    assert config == originalConfig
    assert 'routeId' not in result['cavebot']
    assert [item['label'] for item in result['cavebot']['waypoints']['items']] == [
        'route-1',
        'route-2',
    ]
    assert result['cavebot']['waypoints']['currentIndex'] is None
    assert result['cavebot']['waypoints']['state'] is None


def test_external_route_items_do_not_alias_loaded_document(tmp_path):
    route = makeRoute()
    RouteStore(tmp_path).save('muglex-newhaven.json', route)
    context = makeContext()
    config = {'cavebot': {'routeId': 'muglex-newhaven'}}

    result = loadContextFromConfig(config, context, tmp_path)
    result['cavebot']['waypoints']['items'][0]['coordinate'][0] = 1

    assert route['waypoints'][0]['coordinate'][0] == 32562
    assert RouteStore(tmp_path).load('muglex-newhaven.json')[
        'waypoints'
    ][0]['coordinate'][0] == 32562


@pytest.mark.parametrize('routeId', [None, '', 123, True])
def test_route_id_must_be_a_non_empty_string_without_mutating_context(
    tmp_path,
    routeId,
):
    context = makeContext()
    originalContext = deepcopy(context)
    config = {
        'backpacks': {'main': 'changed', 'loot': 'changed'},
        'cavebot': {'enabled': True, 'routeId': routeId},
    }

    with pytest.raises(
        ValueError,
        match='cavebot.routeId deve ser uma string não vazia',
    ):
        loadContextFromConfig(config, context, tmp_path)

    assert context == originalContext


def test_route_id_must_be_a_safe_slug(tmp_path):
    config = {'cavebot': {'routeId': '../other'}}

    with pytest.raises(
        ValueError,
        match='routeFile deve conter somente o nome do arquivo',
    ):
        loadContextFromConfig(config, makeContext(), tmp_path)


def test_missing_external_route_fails_without_legacy_fallback(tmp_path):
    context = makeContext()
    originalContext = deepcopy(context)
    config = {
        'backpacks': {'main': 'changed', 'loot': 'changed'},
        'cavebot': {
            'routeId': 'missing-route',
            'waypoints': {
                'items': [makeWaypoint('legacy', 1)],
            },
        },
    }

    with pytest.raises(FileNotFoundError):
        loadContextFromConfig(config, context, tmp_path)

    assert context == originalContext


def test_malformed_external_route_is_rejected_without_mutating_context(
    tmp_path,
):
    (tmp_path / 'broken-route.json').write_text('{', encoding='utf-8')
    context = makeContext()
    originalContext = deepcopy(context)
    config = {
        'backpacks': {'main': 'changed', 'loot': 'changed'},
        'cavebot': {'enabled': True, 'routeId': 'broken-route'},
    }

    with pytest.raises(json.JSONDecodeError):
        loadContextFromConfig(config, context, tmp_path)

    assert context == originalContext


def test_invalid_external_route_is_rejected_without_mutating_context(tmp_path):
    invalidRoute = makeRoute()
    invalidRoute['waypoints'][0]['type'] = 'moveDown'
    (tmp_path / 'invalid-route.json').write_text(
        json.dumps(invalidRoute),
        encoding='utf-8',
    )
    context = makeContext()
    originalContext = deepcopy(context)
    config = {
        'backpacks': {'main': 'changed', 'loot': 'changed'},
        'cavebot': {'enabled': True, 'routeId': 'invalid-route'},
    }

    with pytest.raises(RouteValidationError):
        loadContextFromConfig(config, context, tmp_path)

    assert context == originalContext


def test_external_route_rejects_invalid_waypoints_container_before_merge(
    tmp_path,
):
    RouteStore(tmp_path).save('muglex-newhaven.json', makeRoute())
    context = makeContext()
    originalContext = deepcopy(context)
    config = {
        'backpacks': {'main': 'changed', 'loot': 'changed'},
        'cavebot': {
            'enabled': True,
            'routeId': 'muglex-newhaven',
            'waypoints': None,
        },
    }

    with pytest.raises(
        ValueError,
        match='cavebot.waypoints deve ser um objeto',
    ):
        loadContextFromConfig(config, context, tmp_path)

    assert context == originalContext
