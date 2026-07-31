from typing import Literal, TypedDict


ROUTE_SCHEMA_VERSION = 1
ROUTE_FILE_SUFFIX = '.json'
# Código original mantido comentado:
# SUPPORTED_WAYPOINT_TYPES = frozenset({'walk'})
SUPPORTED_WAYPOINT_TYPES = frozenset({
    'walk',
    'moveUp',
    'moveDown',
    'useHole',
    'useRope',
    'useShovel',
    'useTeleport',
})


class Waypoint(TypedDict):
    label: str
    type: str
    coordinate: list[int]
    options: dict[str, object]


class RouteDocument(TypedDict):
    schemaVersion: Literal[1]
    name: str
    waypoints: list[Waypoint]
