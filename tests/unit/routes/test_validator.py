from copy import deepcopy

import pytest

from src.routes.validator import RouteValidationError, validateRouteDocument


def makeRoute(**overrides):
    route = {
        'schemaVersion': 1,
        'name': 'Minotaurs — Yalahar',
        'waypoints': [
            {
                'label': 'hunt-start',
                'type': 'walk',
                'coordinate': [32781, 31234, 7],
                'options': {},
            },
        ],
    }
    route.update(overrides)
    return route


def assertInvalid(route, expectedMessage):
    with pytest.raises(RouteValidationError) as error:
        validateRouteDocument(route)
    assert expectedMessage in error.value.errors


def test_valid_route_is_normalized_without_mutating_input():
    route = makeRoute()
    route['name'] = '  Minotaurs — Yalahar  '
    route['waypoints'][0]['label'] = '  hunt-start  '
    route['waypoints'][0]['coordinate'] = (32781, 31234, 7)
    originalRoute = deepcopy(route)

    result = validateRouteDocument(route)

    assert route == originalRoute
    assert result['name'] == 'Minotaurs — Yalahar'
    assert result['waypoints'][0]['label'] == 'hunt-start'
    assert result['waypoints'][0]['coordinate'] == [32781, 31234, 7]


def test_empty_route_is_allowed_as_draft():
    result = validateRouteDocument(makeRoute(waypoints=[]))

    assert result['waypoints'] == []


def test_route_has_a_waypoint_limit(monkeypatch):
    from src.routes import validator

    monkeypatch.setattr(validator, 'MAX_ROUTE_WAYPOINTS', 1)
    route = makeRoute()
    route['waypoints'].append({
        'label': '',
        'type': 'walk',
        'coordinate': [32782, 31234, 7],
        'options': {},
    })

    assertInvalid(route, 'route.waypoints não pode exceder 1 itens')


def test_result_does_not_share_waypoints_with_input():
    route = makeRoute()

    result = validateRouteDocument(route)
    result['waypoints'][0]['coordinate'][0] = 1

    assert route['waypoints'][0]['coordinate'][0] == 32781


def test_document_must_be_an_object():
    assertInvalid([], 'route deve ser um objeto')


def test_unknown_schema_version_is_rejected():
    assertInvalid(
        makeRoute(schemaVersion=2),
        'route.schemaVersion não suportada: 2',
    )




def test_name_cannot_be_empty():
    assertInvalid(makeRoute(name='   '), 'route.name não pode ser vazio')


def test_unknown_document_field_is_rejected():
    route = makeRoute()
    route['id'] = 'duplicated-identity'

    assertInvalid(route, 'route.id não é reconhecido')


def test_non_string_unknown_fields_produce_validation_error():
    route = makeRoute()
    route[1] = True

    assertInvalid(route, 'route.1 não é reconhecido')


def test_unknown_waypoint_type_is_rejected():
    route = makeRoute()
    # Código original mantido comentado:
    # route['waypoints'][0]['type'] = 'moveDown'
    route['waypoints'][0]['type'] = 'invalidType'

    assertInvalid(
        route,
        'waypoints[0].type não é suportado neste incremento: invalidType',
    )


def test_floor_change_waypoint_types_are_accepted():
    route = makeRoute()
    route['waypoints'] = [
        {'label': 'w1', 'type': 'moveUp', 'coordinate': [32781, 31234, 7], 'options': {'direction': 'north'}},
        {'label': 'w2', 'type': 'moveDown', 'coordinate': [32781, 31234, 6], 'options': {'direction': 'south'}},
        {'label': 'w3', 'type': 'useHole', 'coordinate': [32781, 31234, 7], 'options': {}},
        {'label': 'w4', 'type': 'useRope', 'coordinate': [32781, 31234, 8], 'options': {}},
        {'label': 'w5', 'type': 'useShovel', 'coordinate': [32781, 31234, 7], 'options': {}},
        {'label': 'w6', 'type': 'useTeleport', 'coordinate': [32781, 31234, 7], 'options': {}},
    ]
    result = validateRouteDocument(route)
    assert len(result['waypoints']) == 6


def test_coordinate_must_have_three_items():
    route = makeRoute()
    route['waypoints'][0]['coordinate'] = [32781, 31234]

    assertInvalid(
        route,
        'waypoints[0].coordinate deve conter exatamente x, y e z',
    )


@pytest.mark.parametrize('invalidValue', ['7', True])
def test_coordinate_must_contain_integers(invalidValue):
    route = makeRoute()
    route['waypoints'][0]['coordinate'] = [32781, 31234, invalidValue]

    assertInvalid(
        route,
        'waypoints[0].coordinate deve conter somente inteiros',
    )


@pytest.mark.parametrize('floor', [-1, 16])
def test_floor_must_be_supported(floor):
    route = makeRoute()
    route['waypoints'][0]['coordinate'] = [32781, 31234, floor]

    assertInvalid(
        route,
        'waypoints[0].coordinate[2] deve estar entre 0 e 15',
    )


def test_walk_options_must_be_empty():
    route = makeRoute()
    route['waypoints'][0]['options'] = {'direction': 'north'}

    assertInvalid(route, 'waypoints[0].options deve ser vazio para walk')


def test_non_empty_labels_must_be_unique_after_normalization():
    route = makeRoute()
    route['waypoints'].append({
        'label': ' hunt-start ',
        'type': 'walk',
        'coordinate': [32782, 31234, 7],
        'options': {},
    })

    assertInvalid(
        route,
        'waypoints[1].label está duplicada: hunt-start',
    )


def test_empty_labels_can_repeat():
    route = makeRoute()
    route['waypoints'][0]['label'] = ''
    route['waypoints'].append({
        'label': '   ',
        'type': 'walk',
        'coordinate': [32782, 31234, 7],
        'options': {},
    })

    result = validateRouteDocument(route)

    assert [waypoint['label'] for waypoint in result['waypoints']] == ['', '']
