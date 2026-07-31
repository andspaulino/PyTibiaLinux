from copy import deepcopy
from threading import RLock
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest

from src.routes.store import RouteStore
from src.ui import context as ui_context_module
from src.ui.context import Context
from src.ui.pages.cavebot import cavebotPage as cavebot_page_module
from src.ui.pages.cavebot.cavebotPage import CavebotPage


OLD_WAYPOINT = {
    'label': 'old',
    'type': 'walk',
    'coordinate': [100, 100, 7],
    'options': {},
}
NEW_WAYPOINT = {
    'label': 'new',
    'type': 'walk',
    'coordinate': [200, 200, 7],
    'options': {},
}


def makeRouteStore(tmp_path):
    store = RouteStore(tmp_path)
    store.save('new-route.json', {
        'schemaVersion': 1,
        'name': 'New route',
        'waypoints': [NEW_WAYPOINT],
    })
    return store


def makeContext(paused=True):
    uiContext = object.__new__(Context)
    uiContext.gameplayLock = RLock()
    uiContext.routeApplicationPending = False
    uiContext.db = MagicMock()
    uiContext.enabledProfile = {
        'config': {
            'cavebot': {
                'enabled': False,
                'routeId': 'old-route',
            },
        },
    }
    uiContext.context = {
        'pause': paused,
        'window': None,
        'tasksOrchestrator': MagicMock(),
        'cavebot': {
            'enabled': False,
            'waypoints': {
                'items': [deepcopy(OLD_WAYPOINT)],
                'currentIndex': 3,
                'state': 'walking',
            },
        },
    }
    return uiContext


def test_activate_route_updates_profile_and_runtime_with_independent_copy(tmp_path):
    store = makeRouteStore(tmp_path)
    uiContext = makeContext()

    uiContext.activateRoute('new-route', routeStore=store)

    assert uiContext.getActiveRouteId() == 'new-route'
    assert uiContext.context['cavebot']['waypoints']['items'] == [NEW_WAYPOINT]
    assert uiContext.context['cavebot']['waypoints']['currentIndex'] is None
    assert uiContext.context['cavebot']['waypoints']['state'] is None
    assert uiContext.routeApplicationPending is False
    uiContext.context['tasksOrchestrator'].setRootTask.assert_called_once_with(
        uiContext.context,
        None,
    )
    uiContext.db.update.assert_called_once_with(uiContext.enabledProfile)

    loadedRoute = store.load('new-route.json')
    uiContext.context['cavebot']['waypoints']['items'][0]['label'] = 'runtime'
    assert loadedRoute['waypoints'][0]['label'] == 'new'


def test_activate_route_requires_pause_without_mutating_state(tmp_path):
    store = makeRouteStore(tmp_path)
    uiContext = makeContext(paused=False)
    previousProfile = deepcopy(uiContext.enabledProfile)
    previousWaypoints = deepcopy(
        uiContext.context['cavebot']['waypoints']
    )

    with pytest.raises(RuntimeError, match='Pause the bot'):
        uiContext.activateRoute('new-route', routeStore=store)

    assert uiContext.enabledProfile == previousProfile
    assert uiContext.context['cavebot']['waypoints'] == previousWaypoints
    uiContext.db.update.assert_not_called()
    uiContext.context['tasksOrchestrator'].setRootTask.assert_not_called()


def test_activate_route_load_failure_preserves_profile_and_runtime(tmp_path):
    uiContext = makeContext()
    previousProfile = deepcopy(uiContext.enabledProfile)
    previousWaypoints = deepcopy(
        uiContext.context['cavebot']['waypoints']
    )

    with pytest.raises(FileNotFoundError):
        uiContext.activateRoute('missing', routeStore=RouteStore(tmp_path))

    assert uiContext.enabledProfile == previousProfile
    assert uiContext.context['cavebot']['waypoints'] == previousWaypoints
    uiContext.db.update.assert_not_called()


def test_activate_route_database_failure_restores_profile_and_runtime(tmp_path):
    store = makeRouteStore(tmp_path)
    uiContext = makeContext()
    uiContext.db.update.side_effect = OSError('database unavailable')
    previousProfile = deepcopy(uiContext.enabledProfile)
    previousWaypoints = deepcopy(
        uiContext.context['cavebot']['waypoints']
    )

    with pytest.raises(OSError, match='database unavailable'):
        uiContext.activateRoute('new-route', routeStore=store)

    assert uiContext.enabledProfile == previousProfile
    assert uiContext.context['cavebot']['waypoints'] == previousWaypoints
    assert uiContext.routeApplicationPending is False
    uiContext.context['tasksOrchestrator'].setRootTask.assert_not_called()


def test_activate_route_task_reset_failure_marks_application_pending(tmp_path):
    store = makeRouteStore(tmp_path)
    uiContext = makeContext()
    uiContext.context['tasksOrchestrator'].setRootTask.side_effect = RuntimeError(
        'interrupt failed'
    )
    previousWaypoints = deepcopy(
        uiContext.context['cavebot']['waypoints']
    )

    with pytest.raises(RuntimeError, match='interrupt failed'):
        uiContext.activateRoute('new-route', routeStore=store)

    assert uiContext.getActiveRouteId() == 'new-route'
    assert uiContext.context['cavebot']['waypoints'] == previousWaypoints
    assert uiContext.routeApplicationPending is True


def test_play_is_blocked_while_active_route_application_is_pending(monkeypatch):
    uiContext = makeContext()
    uiContext.routeApplicationPending = True
    showError = MagicMock()
    monkeypatch.setattr(ui_context_module.messagebox, 'showerror', showError)

    uiContext.play()

    showError.assert_called_once()
    assert uiContext.context['pause'] is True


def makePage(routeId='route-a', activeRouteId='route-a'):
    context = MagicMock()
    context.context = {
        'pause': True,
        'cavebot': {'enabled': True},
    }
    context.getActiveRouteId.return_value = activeRouteId
    context.routeApplicationPending = False
    routeDraft = MagicMock()
    routeDraft.routeId = routeId
    routeDraft.isDirty = False
    page = SimpleNamespace(
        context=context,
        routeDraft=routeDraft,
        routeStore=MagicMock(),
        routeSelection=MagicMock(),
        activeRouteStatus=MagicMock(),
        refreshRouteChoices=MagicMock(),
        refreshWaypointsTable=MagicMock(),
        refreshActiveRouteStatus=MagicMock(),
        updateRouteSelectionControls=MagicMock(),
        cavebotEnabled=MagicMock(),
        _requirePaused=MagicMock(return_value=True),
    )
    return cast(CavebotPage, page)


def test_activate_route_blocks_dirty_draft(monkeypatch):
    page = makePage()
    page.routeDraft.isDirty = True
    showError = MagicMock()
    monkeypatch.setattr(cavebot_page_module.messagebox, 'showerror', showError)

    CavebotPage.activateRoute(page)

    showError.assert_called_once()
    page.context.activateRoute.assert_not_called()


def test_activate_route_applies_clean_saved_draft():
    page = makePage(routeId='route-b', activeRouteId='route-a')

    CavebotPage.activateRoute(page)

    page.context.activateRoute.assert_called_once_with(
        'route-b',
        routeStore=page.routeStore,
        enableCavebot=None,
    )
    page.refreshActiveRouteStatus.assert_called_once_with()


def test_activate_route_can_enable_cavebot_in_profile_and_runtime(tmp_path):
    store = makeRouteStore(tmp_path)
    uiContext = makeContext()

    uiContext.activateRoute(
        'new-route',
        routeStore=store,
        enableCavebot=True,
    )

    assert uiContext.enabledProfile['config']['cavebot']['enabled'] is True
    assert uiContext.context['cavebot']['enabled'] is True


def test_disable_cavebot_persists_and_resets_runtime_state():
    uiContext = makeContext()
    uiContext.enabledProfile['config']['cavebot']['enabled'] = True
    uiContext.context['cavebot']['enabled'] = True

    uiContext.setCavebotEnabled(False)

    assert uiContext.enabledProfile['config']['cavebot']['enabled'] is False
    assert uiContext.context['cavebot']['enabled'] is False
    assert uiContext.context['cavebot']['waypoints']['currentIndex'] is None
    assert uiContext.context['cavebot']['waypoints']['state'] is None
    uiContext.context['tasksOrchestrator'].setRootTask.assert_called_once_with(
        uiContext.context,
        None,
    )
    uiContext.db.update.assert_called_once_with(uiContext.enabledProfile)


def test_route_dropdown_selection_opens_route_automatically():
    page = makePage()
    page.openSelectedRoute = MagicMock()

    CavebotPage.onRouteSelected(page)

    page.openSelectedRoute.assert_called_once_with()


def test_toggle_cavebot_off_disables_runtime_and_unlocks_route_selection():
    page = makePage()
    page.cavebotEnabled.get.return_value = False

    CavebotPage.toggleCavebotEnabled(page)

    page.context.setCavebotEnabled.assert_called_once_with(False)
    page.refreshActiveRouteStatus.assert_called_once_with()
    page.updateRouteSelectionControls.assert_called_once_with()


def test_toggle_cavebot_on_activates_selected_route():
    page = makePage()
    page.cavebotEnabled.get.return_value = True
    page.activateRoute = MagicMock(return_value=True)

    CavebotPage.toggleCavebotEnabled(page)

    page.activateRoute.assert_called_once_with(enableCavebot=True)
    page.cavebotEnabled.set.assert_not_called()
    page.updateRouteSelectionControls.assert_called_once_with()


def test_next_waypoint_label_uses_highest_existing_suffix():
    page = makePage()
    page.routeDraft.document = {
        'waypoints': [
            {'label': '', 'type': 'walk'},
            {'label': 'walk001', 'type': 'walk'},
            {'label': 'walk003', 'type': 'walk'},
            {'label': 'custom', 'type': 'walk'},
            {'label': 'useRope009', 'type': 'useRope'},
        ],
    }

    assert CavebotPage._getNextWaypointLabel(page, 'walk') == 'walk004'
    assert CavebotPage._getNextWaypointLabel(page, 'useRope') == 'useRope010'


def test_save_active_route_saves_and_applies(monkeypatch):
    page = makePage()
    page.context.activateRoute.side_effect = lambda *args, **kwargs: setattr(
        page.context,
        'routeApplicationPending',
        False,
    )
    monkeypatch.setattr(
        cavebot_page_module.messagebox,
        'askyesno',
        MagicMock(return_value=True),
    )

    CavebotPage.saveRoute(page)

    page.routeDraft.save.assert_called_once_with(page.routeStore)
    page.context.activateRoute.assert_called_once_with(
        'route-a',
        routeStore=page.routeStore,
    )
    assert page.context.routeApplicationPending is False
    page.refreshRouteChoices.assert_called_once_with()
    page.refreshActiveRouteStatus.assert_called_once_with()


def test_save_active_route_failure_to_apply_blocks_play_until_retry(monkeypatch):
    page = makePage()
    page.context.activateRoute.side_effect = OSError('apply failed')
    showError = MagicMock()
    monkeypatch.setattr(
        cavebot_page_module.messagebox,
        'askyesno',
        MagicMock(return_value=True),
    )
    monkeypatch.setattr(cavebot_page_module.messagebox, 'showerror', showError)

    CavebotPage.saveRoute(page)

    page.routeDraft.save.assert_called_once_with(page.routeStore)
    assert page.context.routeApplicationPending is True
    showError.assert_called_once()
    page.refreshActiveRouteStatus.assert_called_once_with()


def test_route_editing_is_blocked_while_gameplay_is_running(monkeypatch):
    page = makePage()
    page.context.context['pause'] = False
    showError = MagicMock()
    monkeypatch.setattr(cavebot_page_module.messagebox, 'showerror', showError)

    assert CavebotPage._requirePaused(page) is False

    showError.assert_called_once()
