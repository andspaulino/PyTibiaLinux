from copy import deepcopy
from typing import cast

from .schema import RouteDocument, Waypoint
from .store import RouteStore
from .validator import validateRouteDocument


class RouteDraft:
    def __init__(
        self,
        document: RouteDocument,
        routeId: str | None = None,
    ):
        validatedDocument = validateRouteDocument(document)
        self.routeId = routeId
        self._document = deepcopy(validatedDocument)
        self._persistedDocument = deepcopy(validatedDocument)
        self.isDirty = False

    @property
    def document(self) -> RouteDocument:
        return deepcopy(self._document)

    @classmethod
    def create(cls, name: str) -> 'RouteDraft':
        return cls({
            'schemaVersion': 1,
            'name': name,
            'waypoints': [],
        })

    @classmethod
    def open(cls, store: RouteStore, routeId: str) -> 'RouteDraft':
        document = store.load(f'{routeId}.json')
        return cls(document, routeId=routeId)

    def _replaceDocument(self, document: object) -> None:
        self._document = validateRouteDocument(document)
        self.isDirty = self._document != self._persistedDocument

    def _validateWaypointIndex(self, index: int) -> None:
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or not 0 <= index < len(self._document['waypoints'])
        ):
            raise IndexError('índice de waypoint fora da rota')

    def setName(self, name: str) -> None:
        document = deepcopy(self._document)
        document['name'] = name
        self._replaceDocument(document)

    def addWaypoint(self, waypoint: object) -> None:
        document = deepcopy(self._document)
        document['waypoints'].append(
            cast(Waypoint, deepcopy(waypoint))
        )
        self._replaceDocument(document)

    def updateWaypoint(self, index: int, waypoint: object) -> None:
        self._validateWaypointIndex(index)
        document = deepcopy(self._document)
        document['waypoints'][index] = cast(
            Waypoint,
            deepcopy(waypoint),
        )
        self._replaceDocument(document)

    def removeWaypoint(self, index: int) -> None:
        self._validateWaypointIndex(index)
        document = deepcopy(self._document)
        document['waypoints'].pop(index)
        self._replaceDocument(document)

    def moveWaypoint(self, sourceIndex: int, destinationIndex: int) -> None:
        self._validateWaypointIndex(sourceIndex)
        self._validateWaypointIndex(destinationIndex)
        document = deepcopy(self._document)
        waypoint = document['waypoints'].pop(sourceIndex)
        document['waypoints'].insert(destinationIndex, waypoint)
        self._replaceDocument(document)

    def save(self, store: RouteStore, routeId: str | None = None) -> None:
        selectedRouteId = routeId if routeId is not None else self.routeId
        if selectedRouteId is None or selectedRouteId == '':
            raise ValueError('routeId é obrigatório para salvar a rota')
        savedDocument = store.save(
            f'{selectedRouteId}.json',
            self._document,
        )
        self.routeId = selectedRouteId
        self._document = deepcopy(savedDocument)
        self._persistedDocument = deepcopy(savedDocument)
        self.isDirty = False

    def saveAs(
        self,
        store: RouteStore,
        routeId: str,
        name: str,
    ) -> None:
        document = deepcopy(self._document)
        document['name'] = name
        savedDocument = store.save(f'{routeId}.json', document)
        self.routeId = routeId
        self._document = deepcopy(savedDocument)
        self._persistedDocument = deepcopy(savedDocument)
        self.isDirty = False

    def discard(self) -> None:
        self._document = deepcopy(self._persistedDocument)
        self.isDirty = False
