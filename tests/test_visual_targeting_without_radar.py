import numpy as np

from src.gameplay import cavebot as cavebot_gameplay
from src.gameplay.core.middlewares import gameWindow as game_window_middleware
from src.gameplay.core.tasks.attackClosestCreature import AttackClosestCreatureTask
from src.gameplay.core.tasks.orchestrator import TasksOrchestrator
from src.gameplay.core.tasks.walkToTargetCreature import WalkToTargetCreatureTask


def make_context(*, targeting=True, cavebot=False):
    return {
        "targeting": {
            "enabled": targeting,
        },
        "cavebot": {"enabled": cavebot},
        "battleList": {
            "creatures": [{"name": "Bug"}],
            "beingAttackedCreatureCategory": None,
        },
        "gameWindow": {
            "coordinate": (100, 100),
            "image": np.zeros((704, 960), dtype=np.uint8),
            "creatures": [],
            "monsters": [],
            "players": [],
            "walkedPixelsInSqm": 0,
        },
        "radar": {"coordinate": None},
        "comingFromDirection": None,
    }


def test_visual_targeting_fallback_depends_only_on_targeting():
    assert game_window_middleware.canUseVisualTargetingWithoutRadar(
        make_context()
    )
    assert game_window_middleware.canUseVisualTargetingWithoutRadar(
        make_context(cavebot=True)
    )
    assert not game_window_middleware.canUseVisualTargetingWithoutRadar(
        make_context(targeting=False)
    )


def test_game_window_maps_monsters_without_radar_in_visual_mode(monkeypatch):
    context = make_context()
    captured = {}
    monster = {"name": "Bug", "type": "monster"}

    monkeypatch.setattr(
        game_window_middleware,
        "getBeingAttackedCreatureCategory",
        lambda creatures: None,
    )

    def fake_get_creatures(
        battle_list_creatures,
        direction,
        game_window_coordinate,
        game_window_image,
        coordinate,
        **kwargs,
    ):
        captured["coordinate"] = coordinate
        return [monster]

    monkeypatch.setattr(
        game_window_middleware,
        "getCreatures",
        fake_get_creatures,
    )

    result = game_window_middleware.setGameWindowCreaturesMiddleware(context)

    assert captured["coordinate"] == (
        game_window_middleware.VISUAL_TARGETING_FALLBACK_COORDINATE
    )
    assert result["gameWindow"]["monsters"] == [monster]


def test_game_window_keeps_visual_targeting_without_radar_when_cavebot_is_enabled(monkeypatch):
    context = make_context(cavebot=True)
    captured = {}

    def fake_get_creatures(*args, **kwargs):
        captured['coordinate'] = args[4]
        return []

    monkeypatch.setattr(
        game_window_middleware,
        "getBeingAttackedCreatureCategory",
        lambda creatures: None,
    )
    monkeypatch.setattr(
        game_window_middleware,
        "getCreatures",
        fake_get_creatures,
    )

    game_window_middleware.setGameWindowCreaturesMiddleware(context)

    assert captured['coordinate'] == (
        game_window_middleware.VISUAL_TARGETING_FALLBACK_COORDINATE
    )



class FakeTasksOrchestrator:
    def __init__(self):
        self.rootTask = None

    def getCurrentTask(self, context):
        return None

    def setRootTask(self, context, task):
        self.rootTask = task


def test_active_visual_target_does_not_use_pathfinding_without_radar(monkeypatch):
    context = make_context()
    monster = {"name": "Bug", "slot": (7, 4)}
    context["gameWindow"]["monsters"] = [monster]
    context["cavebot"].update({
        "isAttackingSomeCreature": True,
        "targetCreature": monster,
        "closestCreature": monster,
    })
    context["tasksOrchestrator"] = FakeTasksOrchestrator()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("pathfinding não deve receber Radar=None")

    monkeypatch.setattr(
        cavebot_gameplay,
        "hasTargetToCreature",
        fail_if_called,
    )

    result = cavebot_gameplay.resolveCavebotTasks(
        context,
        allowChase=False,
    )

    assert result is context
    assert context["tasksOrchestrator"].rootTask is not None
    assert context["tasksOrchestrator"].rootTask.name == "attackClosestCreature"
    assert context["tasksOrchestrator"].rootTask.allowChase is False


def test_losing_radar_replaces_chase_root_and_releases_keys(monkeypatch):
    context = make_context(cavebot=True)
    monster = {"name": "Bug", "slot": (7, 4)}
    context["gameWindow"]["monsters"] = [monster]
    context["cavebot"].update({
        "isAttackingSomeCreature": True,
        "targetCreature": monster,
        "closestCreature": monster,
    })

    orchestrator = TasksOrchestrator()
    chaseRoot = AttackClosestCreatureTask(allowChase=True)
    chaseRoot.status = 'running'
    walkTask = WalkToTargetCreatureTask()
    walkTask.status = 'running'
    walkTask.setParentTask(chaseRoot).setRootTask(chaseRoot)
    chaseRoot.tasks.clear()
    chaseRoot.tasks.append(walkTask)
    orchestrator.rootTask = chaseRoot
    context["tasksOrchestrator"] = orchestrator

    released = []
    monkeypatch.setattr(
        'src.gameplay.core.tasks.walkToTargetCreature.releaseKeys',
        lambda currentContext: released.append(True) or currentContext,
    )

    cavebot_gameplay.resolveCavebotTasks(
        context,
        allowChase=False,
    )

    assert released == [True]
    assert orchestrator.rootTask is not chaseRoot
    assert orchestrator.rootTask.name == 'attackClosestCreature'
    assert orchestrator.rootTask.allowChase is False
