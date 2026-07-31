from copy import deepcopy
from pathlib import Path

from src.routes.store import DEFAULT_ROUTES_DIRECTORY, RouteStore


ROUTE_ID_MISSING = object()


def merge_dict(target: dict, source: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            merge_dict(target[key], value)
        else:
            target[key] = value
    return target


# TODO: add types
# TODO: add unit tests
def loadContextFromConfig(
    config,
    context,
    routesDirectory: Path | None = None,
):
    if not config:
        return context

    configToMerge = deepcopy(config)
    cavebotConfig = configToMerge.get('cavebot', {})
    routeId = (
        cavebotConfig.pop('routeId', ROUTE_ID_MISSING)
        if isinstance(cavebotConfig, dict)
        else ROUTE_ID_MISSING
    )

    # Código Linux anterior:
    # return merge_dict(context, config)
    if routeId is ROUTE_ID_MISSING:
        return merge_dict(context, configToMerge)
    if not isinstance(routeId, str) or routeId == '':
        raise ValueError('cavebot.routeId deve ser uma string não vazia')

    if (
        'waypoints' in cavebotConfig
        and not isinstance(cavebotConfig['waypoints'], dict)
    ):
        raise ValueError('cavebot.waypoints deve ser um objeto')

    routeStore = RouteStore(
        routesDirectory
        if routesDirectory is not None
        else DEFAULT_ROUTES_DIRECTORY
    )
    route = routeStore.load(f'{routeId}.json')

    loadedContext = merge_dict(context, configToMerge)
    # Código original mantido comentado:
    # loadedContext['cavebot']['waypoints']['items'] = deepcopy(
    #     route['waypoints']
    # )
    # loadedContext['cavebot']['waypoints']['currentIndex'] = None
    # loadedContext['cavebot']['waypoints']['state'] = None
    routeWaypoints = deepcopy(route['waypoints'])
    loadedContext['cavebot']['waypoints']['items'] = routeWaypoints
    loadedContext['cavebot']['waypoints']['currentIndex'] = None
    loadedContext['cavebot']['waypoints']['state'] = None
    loadedContext['cavebot']['holesOrStairs'] = [
        item['coordinate']
        for item in routeWaypoints
        if isinstance(item, dict)
        and item.get('type') in ('moveUp', 'moveDown', 'useHole', 'useRope', 'useShovel', 'useTeleport')
        and item.get('coordinate') is not None
    ]
    return loadedContext
