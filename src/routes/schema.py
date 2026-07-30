from typing import Literal, TypedDict


ROUTE_SCHEMA_VERSION = 1
ROUTE_FILE_SUFFIX = '.json'
SUPPORTED_WAYPOINT_TYPES = frozenset({'walk'})


class Waypoint(TypedDict):
    label: str
    type: Literal['walk']
    coordinate: list[int]
    options: dict[str, object]


class RouteDocument(TypedDict):
    schemaVersion: Literal[1]
    name: str
    waypoints: list[Waypoint]
