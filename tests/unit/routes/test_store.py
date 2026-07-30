import json

import pytest

from src.routes import store as route_store
from src.routes.store import RouteStore
from src.routes.validator import RouteValidationError


def makeRoute():
    return {
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


def test_save_creates_directory_and_load_round_trips_unicode(tmp_path):
    routesDirectory = tmp_path / 'routes'
    store = RouteStore(routesDirectory)

    saved = store.save('minotaurs-yalahar.json', makeRoute())
    loaded = store.load('minotaurs-yalahar.json')

    assert saved == loaded
    assert loaded['name'] == 'Minotaurs — Yalahar'
    assert routesDirectory.is_dir()
    assert '\\u2014' not in (
        routesDirectory / 'minotaurs-yalahar.json'
    ).read_text(encoding='utf-8')


def test_save_and_load_return_independent_copies(tmp_path):
    store = RouteStore(tmp_path)
    route = makeRoute()

    saved = store.save('minotaurs-yalahar.json', route)
    saved['waypoints'][0]['coordinate'][0] = 1
    loaded = store.load('minotaurs-yalahar.json')
    loaded['waypoints'][0]['coordinate'][0] = 2

    assert route['waypoints'][0]['coordinate'][0] == 32781
    assert store.load('minotaurs-yalahar.json')['waypoints'][0][
        'coordinate'
    ][0] == 32781


def test_list_routes_returns_only_regular_json_files_sorted(tmp_path):
    store = RouteStore(tmp_path)
    store.save('swamp-trolls.json', makeRoute())
    store.save('minotaurs-yalahar.json', makeRoute())
    (tmp_path / 'notes.txt').write_text('ignore', encoding='utf-8')
    (tmp_path / 'nested.json').mkdir()

    assert store.listRoutes() == [
        'minotaurs-yalahar.json',
        'swamp-trolls.json',
    ]


def test_list_routes_returns_empty_when_directory_does_not_exist(tmp_path):
    assert RouteStore(tmp_path / 'missing').listRoutes() == []


@pytest.mark.parametrize(
    'routeFile',
    [
        '../file.json',
        'nested/route.json',
        'nested\\route.json',
        '/tmp/route.json',
        'route.txt',
        'Minotaurs Yalahar.json',
        'route_name.json',
        '',
    ],
)
def test_unsafe_or_invalid_file_names_are_rejected(tmp_path, routeFile):
    with pytest.raises(ValueError):
        RouteStore(tmp_path).save(routeFile, makeRoute())


def test_route_identity_comes_only_from_file_name(tmp_path):
    store = RouteStore(tmp_path)

    store.save('other-route.json', makeRoute())
    loaded = store.load('other-route.json')

    assert 'id' not in loaded



def test_load_rejects_file_above_size_limit(tmp_path, monkeypatch):
    routePath = tmp_path / 'oversized.json'
    routePath.write_text('{}', encoding='utf-8')
    monkeypatch.setattr(route_store, 'MAX_ROUTE_FILE_SIZE_BYTES', 1)

    with pytest.raises(ValueError, match='excede o limite de 1 bytes'):
        RouteStore(tmp_path).load(routePath.name)


def test_load_rejects_malformed_json(tmp_path):
    routePath = tmp_path / 'broken.json'
    routePath.write_text('{', encoding='utf-8')

    with pytest.raises(json.JSONDecodeError):
        RouteStore(tmp_path).load('broken.json')


def test_load_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        RouteStore(tmp_path).load('missing.json')


def test_validation_failure_preserves_existing_file(tmp_path):
    store = RouteStore(tmp_path)
    routePath = tmp_path / 'minotaurs-yalahar.json'
    store.save(routePath.name, makeRoute())
    previousContent = routePath.read_text(encoding='utf-8')
    invalidRoute = makeRoute()
    invalidRoute['waypoints'][0]['coordinate'] = [1, 2]

    with pytest.raises(RouteValidationError):
        store.save(routePath.name, invalidRoute)

    assert routePath.read_text(encoding='utf-8') == previousContent


def test_replace_failure_preserves_existing_file_and_removes_temporary(
    tmp_path,
    monkeypatch,
):
    store = RouteStore(tmp_path)
    routePath = tmp_path / 'minotaurs-yalahar.json'
    store.save(routePath.name, makeRoute())
    previousContent = routePath.read_text(encoding='utf-8')
    updatedRoute = makeRoute()
    updatedRoute['name'] = 'Updated route'

    def failReplace(source, destination):
        raise OSError('replace failed')

    monkeypatch.setattr(route_store.os, 'replace', failReplace)

    with pytest.raises(OSError, match='replace failed'):
        store.save(routePath.name, updatedRoute)

    assert routePath.read_text(encoding='utf-8') == previousContent
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        'minotaurs-yalahar.json',
    ]


def test_store_rejects_route_file_symlink(tmp_path):
    target = tmp_path / 'target.json'
    target.write_text('{}', encoding='utf-8')
    routePath = tmp_path / 'minotaurs-yalahar.json'
    routePath.symlink_to(target)

    store = RouteStore(tmp_path)
    with pytest.raises(
        ValueError,
        match='o arquivo de rota não pode ser um link simbólico',
    ):
        store.load(routePath.name)
    with pytest.raises(
        ValueError,
        match='o arquivo de rota não pode ser um link simbólico',
    ):
        store.save(routePath.name, makeRoute())


def test_store_rejects_routes_directory_symlink(tmp_path):
    targetDirectory = tmp_path / 'target'
    targetDirectory.mkdir()
    routesDirectory = tmp_path / 'routes'
    routesDirectory.symlink_to(targetDirectory, target_is_directory=True)

    with pytest.raises(
        ValueError,
        match='o diretório de rotas não pode atravessar links simbólicos',
    ):
        RouteStore(routesDirectory).listRoutes()


def test_store_rejects_symlink_in_routes_directory_ancestor(tmp_path):
    targetDirectory = tmp_path / 'target'
    routesDirectory = targetDirectory / 'routes'
    routesDirectory.mkdir(parents=True)
    linkedParent = tmp_path / 'linked-parent'
    linkedParent.symlink_to(targetDirectory, target_is_directory=True)

    with pytest.raises(
        ValueError,
        match='o diretório de rotas não pode atravessar links simbólicos',
    ):
        RouteStore(linkedParent / 'routes').save(
            'minotaurs-yalahar.json',
            makeRoute(),
        )


def test_list_routes_ignores_symlinked_json_files(tmp_path):
    target = tmp_path / 'target.txt'
    target.write_text('{}', encoding='utf-8')
    (tmp_path / 'linked.json').symlink_to(target)

    assert RouteStore(tmp_path).listRoutes() == []
