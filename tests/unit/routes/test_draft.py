from copy import deepcopy

import pytest

from src.routes.draft import RouteDraft
from src.routes.store import RouteStore
from src.routes.validator import RouteValidationError


def makeWaypoint(label='route-1', x=32562):
    return {
        'label': label,
        'type': 'walk',
        'coordinate': [x, 32480, 7],
        'options': {},
    }


def makeRoute():
    return {
        'schemaVersion': 1,
        'name': 'Muglex Newhaven',
        'waypoints': [makeWaypoint()],
    }


def test_create_starts_with_clean_empty_route():
    draft = RouteDraft.create('Muglex Newhaven')

    assert draft.routeId is None
    assert draft.document['name'] == 'Muglex Newhaven'
    assert draft.document['waypoints'] == []
    assert draft.isDirty is False


def test_open_loads_independent_clean_document(tmp_path):
    store = RouteStore(tmp_path)
    route = makeRoute()
    store.save('muglex-newhaven.json', route)

    draft = RouteDraft.open(store, 'muglex-newhaven')
    exposedDocument = draft.document
    exposedDocument['waypoints'][0]['coordinate'][0] = 1

    assert draft.routeId == 'muglex-newhaven'
    assert draft.document['waypoints'][0]['coordinate'][0] == 32562
    assert draft.isDirty is False
    assert route['waypoints'][0]['coordinate'][0] == 32562
    assert store.load('muglex-newhaven.json')['waypoints'][0][
        'coordinate'
    ][0] == 32562


def test_set_name_marks_draft_dirty():
    draft = RouteDraft.create('Original')

    draft.setName('Updated')

    assert draft.document['name'] == 'Updated'
    assert draft.isDirty is True


def test_add_update_remove_and_move_waypoints():
    draft = RouteDraft.create('Route')
    firstWaypoint = makeWaypoint('first', 1)
    secondWaypoint = makeWaypoint('second', 2)

    draft.addWaypoint(firstWaypoint)
    draft.addWaypoint(secondWaypoint)
    updatedWaypoint = makeWaypoint('updated', 3)
    draft.updateWaypoint(0, updatedWaypoint)
    draft.moveWaypoint(1, 0)

    assert [
        waypoint['label']
        for waypoint in draft.document['waypoints']
    ] == ['second', 'updated']
    draft.removeWaypoint(1)
    assert [
        waypoint['label']
        for waypoint in draft.document['waypoints']
    ] == ['second']
    assert draft.isDirty is True


def test_added_waypoint_does_not_alias_caller():
    draft = RouteDraft.create('Route')
    waypoint = makeWaypoint()

    draft.addWaypoint(waypoint)
    waypoint['coordinate'][0] = 1

    assert draft.document['waypoints'][0]['coordinate'][0] == 32562


def test_invalid_waypoint_does_not_change_draft():
    draft = RouteDraft.create('Route')
    previousDocument = deepcopy(draft.document)
    invalidWaypoint = makeWaypoint()
    invalidWaypoint['type'] = 'moveDown'

    with pytest.raises(RouteValidationError):
        draft.addWaypoint(invalidWaypoint)

    assert draft.document == previousDocument
    assert draft.isDirty is False


def test_invalid_index_does_not_change_draft():
    draft = RouteDraft.create('Route')
    previousDocument = deepcopy(draft.document)

    with pytest.raises(IndexError):
        draft.removeWaypoint(0)

    assert draft.document == previousDocument


def test_save_persists_and_marks_draft_clean(tmp_path):
    store = RouteStore(tmp_path)
    draft = RouteDraft.create('Muglex Newhaven')
    draft.addWaypoint(makeWaypoint())

    draft.save(store, 'muglex-newhaven')

    assert draft.routeId == 'muglex-newhaven'
    assert draft.isDirty is False
    assert store.load('muglex-newhaven.json') == draft.document


def test_save_uses_existing_route_id(tmp_path):
    store = RouteStore(tmp_path)
    store.save('muglex-newhaven.json', makeRoute())
    draft = RouteDraft.open(store, 'muglex-newhaven')
    draft.setName('Updated')

    draft.save(store)

    assert store.load('muglex-newhaven.json')['name'] == 'Updated'


def test_save_as_changes_name_and_route_id_atomically(tmp_path):
    store = RouteStore(tmp_path)
    draft = RouteDraft.create('Original')
    draft.addWaypoint(makeWaypoint())

    draft.saveAs(store, 'new-route', 'New name')

    assert draft.routeId == 'new-route'
    assert draft.document['name'] == 'New name'
    assert draft.isDirty is False
    assert store.load('new-route.json')['name'] == 'New name'


def test_failed_save_as_preserves_complete_draft(tmp_path, monkeypatch):
    store = RouteStore(tmp_path)
    draft = RouteDraft.create('Original')
    draft.addWaypoint(makeWaypoint())
    previousDocument = draft.document

    def failSave(routeFile, document):
        raise OSError('save failed')

    monkeypatch.setattr(store, 'save', failSave)

    with pytest.raises(OSError, match='save failed'):
        draft.saveAs(store, 'new-route', 'New name')

    assert draft.routeId is None
    assert draft.document == previousDocument
    assert draft.isDirty is True


def test_save_requires_route_id(tmp_path):
    draft = RouteDraft.create('Route')

    with pytest.raises(
        ValueError,
        match='routeId é obrigatório para salvar a rota',
    ):
        draft.save(RouteStore(tmp_path))


def test_failed_save_preserves_dirty_draft(tmp_path, monkeypatch):
    store = RouteStore(tmp_path)
    draft = RouteDraft.create('Route')
    draft.addWaypoint(makeWaypoint())
    previousDocument = deepcopy(draft.document)

    def failSave(routeFile, document):
        raise OSError('save failed')

    monkeypatch.setattr(store, 'save', failSave)

    with pytest.raises(OSError, match='save failed'):
        draft.save(store, 'route')

    assert draft.document == previousDocument
    assert draft.routeId is None
    assert draft.isDirty is True


def test_discard_restores_last_saved_document(tmp_path):
    store = RouteStore(tmp_path)
    draft = RouteDraft.create('Route')
    draft.addWaypoint(makeWaypoint())
    draft.save(store, 'route')
    draft.setName('Unsaved')
    draft.removeWaypoint(0)

    draft.discard()

    assert draft.document['name'] == 'Route'
    assert len(draft.document['waypoints']) == 1
    assert draft.isDirty is False


def test_move_with_invalid_destination_does_not_lose_waypoint():
    draft = RouteDraft.create('Route')
    draft.addWaypoint(makeWaypoint())
    previousDocument = deepcopy(draft.document)

    with pytest.raises(IndexError):
        draft.moveWaypoint(0, 2)

    assert draft.document == previousDocument
