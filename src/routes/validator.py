from copy import deepcopy
from typing import Literal, cast

from .schema import (
    ROUTE_SCHEMA_VERSION,
    SUPPORTED_WAYPOINT_TYPES,
    RouteDocument,
    Waypoint,
)


ROUTE_DOCUMENT_FIELDS = {'schemaVersion', 'name', 'waypoints'}
WAYPOINT_FIELDS = {'label', 'type', 'coordinate', 'options'}
MAX_ROUTE_WAYPOINTS = 10_000


class RouteValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors.copy()
        super().__init__('; '.join(self.errors))


def _validateExactFields(
    value: dict,
    expectedFields: set[str],
    path: str,
    errors: list[str],
) -> None:
    missingFields = expectedFields - value.keys()
    unknownFields = value.keys() - expectedFields
    for field in sorted(missingFields):
        errors.append(f'{path}.{field} é obrigatório')
    for field in sorted(unknownFields, key=str):
        errors.append(f'{path}.{field!s} não é reconhecido')


def _isInteger(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validateWaypoint(
    value: object,
    index: int,
    errors: list[str],
) -> Waypoint | None:
    path = f'waypoints[{index}]'
    if not isinstance(value, dict):
        errors.append(f'{path} deve ser um objeto')
        return None

    errorsBeforeWaypoint = len(errors)
    _validateExactFields(value, WAYPOINT_FIELDS, path, errors)

    label = value.get('label')
    if not isinstance(label, str):
        errors.append(f'{path}.label deve ser uma string')
    else:
        label = label.strip()

    waypointType = value.get('type')
    if not isinstance(waypointType, str):
        errors.append(f'{path}.type deve ser uma string')
    elif waypointType not in SUPPORTED_WAYPOINT_TYPES:
        errors.append(
            f'{path}.type não é suportado neste incremento: {waypointType}'
        )

    coordinate = value.get('coordinate')
    normalizedCoordinate: list[int] | None = None
    if not isinstance(coordinate, (list, tuple)):
        errors.append(f'{path}.coordinate deve ser uma lista [x, y, z]')
    elif len(coordinate) != 3:
        errors.append(f'{path}.coordinate deve conter exatamente x, y e z')
    elif not all(_isInteger(item) for item in coordinate):
        errors.append(f'{path}.coordinate deve conter somente inteiros')
    else:
        normalizedCoordinate = list(coordinate)
        if not 0 <= normalizedCoordinate[2] <= 15:
            errors.append(f'{path}.coordinate[2] deve estar entre 0 e 15')

    options = value.get('options')
    if not isinstance(options, dict):
        errors.append(f'{path}.options deve ser um objeto')
    # Código original mantido comentado:
    # elif waypointType == 'walk' and options != {}:
    #     errors.append(f'{path}.options deve ser vazio para walk')
    elif waypointType in ('walk', 'useHole', 'useRope', 'useShovel', 'useTeleport') and options != {}:
        errors.append(f'{path}.options deve ser vazio para {waypointType}')
    elif waypointType in ('moveUp', 'moveDown'):
        direction = options.get('direction') if isinstance(options, dict) else None
        if direction not in ('north', 'south', 'east', 'west'):
            errors.append(f'{path}.options.direction deve ser norte, sul, leste ou oeste')

    if len(errors) != errorsBeforeWaypoint:
        return None

    return Waypoint(
        label=cast(str, label),
        type=cast(str, waypointType),
        coordinate=cast(list[int], normalizedCoordinate),
        options=deepcopy(cast(dict[str, object], options)),
    )


def validateRouteDocument(document: object) -> RouteDocument:
    errors: list[str] = []
    if not isinstance(document, dict):
        raise RouteValidationError(['route deve ser um objeto'])

    _validateExactFields(document, ROUTE_DOCUMENT_FIELDS, 'route', errors)

    schemaVersion = document.get('schemaVersion')
    if not _isInteger(schemaVersion):
        errors.append('route.schemaVersion deve ser um inteiro')
    elif schemaVersion != ROUTE_SCHEMA_VERSION:
        errors.append(
            f'route.schemaVersion não suportada: {schemaVersion}'
        )



    name = document.get('name')
    if not isinstance(name, str):
        errors.append('route.name deve ser uma string')
    else:
        name = name.strip()
        if name == '':
            errors.append('route.name não pode ser vazio')

    waypointsValue = document.get('waypoints')
    normalizedWaypoints: list[Waypoint] = []
    if not isinstance(waypointsValue, list):
        errors.append('route.waypoints deve ser uma lista')
    else:
        if len(waypointsValue) > MAX_ROUTE_WAYPOINTS:
            errors.append(
                f'route.waypoints não pode exceder {MAX_ROUTE_WAYPOINTS} itens'
            )
        labels: set[str] = set()
        for index, waypointValue in enumerate(
            waypointsValue[:MAX_ROUTE_WAYPOINTS]
        ):
            waypoint = _validateWaypoint(waypointValue, index, errors)
            if waypoint is None:
                continue
            if waypoint['label'] != '':
                if waypoint['label'] in labels:
                    errors.append(
                        f'waypoints[{index}].label está duplicada: '
                        f'{waypoint["label"]}'
                    )
                labels.add(waypoint['label'])
            normalizedWaypoints.append(waypoint)

    if errors:
        raise RouteValidationError(errors)

    return RouteDocument(
        schemaVersion=cast(Literal[1], schemaVersion),
        name=cast(str, name),
        waypoints=normalizedWaypoints,
    )
