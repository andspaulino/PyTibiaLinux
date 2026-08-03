from src.repositories.radar.core import getClosestWaypointIndexFromCoordinate, getCoordinate
from ...typings import Context


# TODO: add unit tests
def setRadarMiddleware(context: Context) -> Context:
    context['radar']['coordinate'] = getCoordinate(
        context['screenshot'], previousCoordinate=context['radar']['previousCoordinate'])
    return context


# TODO: add unit tests
def setWaypointIndexMiddleware(context: Context) -> Context:
    # Guarda defensiva Linux: ausência transitória do Radar não pode gerar
    # índice de waypoint a partir de uma coordenada inexistente.
    if (
        context['radar']['coordinate'] is None
        or len(context['cavebot']['waypoints']['items']) == 0
    ):
        return context
    if context['cavebot']['waypoints']['currentIndex'] is None:
        context['cavebot']['waypoints']['currentIndex'] = getClosestWaypointIndexFromCoordinate(
            context['radar']['coordinate'], context['cavebot']['waypoints']['items'])
    return context
