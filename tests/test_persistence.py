import json
from pathlib import Path

import pytest

from datalayer.json_storage import JsonProgressStorage, default_save_path
from domain.entities.session import (
    CharacterProgress,
    ProgressSnapshot,
    RunResult,
    StatsProgress,
    default_session,
    session_from_progress,
)
from domain.generation.config import LAST_LEVEL
from presentation.app import _initial_session, _persist_after_action


def make_result(treasures: int = 5, *, success: bool = False) -> RunResult:
    return RunResult(
        treasures_collected=treasures,
        reached_level=3,
        enemies_defeated=2,
        food_eaten=1,
        elixirs_drunk=1,
        scrolls_read=1,
        hits_dealt=8,
        missed_attacks=1,
        hits_taken=2,
        cells_walked=30,
        success=success,
    )


def make_snapshot(
    completed_level: int = 3,
    *,
    runs: tuple[RunResult, ...] = (),
    treasures: int = 12,
) -> ProgressSnapshot:
    return ProgressSnapshot(
        completed_level=completed_level,
        treasures_collected=treasures,
        character=CharacterProgress(health=8, max_health=12, agility=6, strength=7),
        stats=StatsProgress(
            treasures_collected=treasures,
            enemies_defeated=4,
            food_eaten=2,
            elixirs_drunk=1,
            scrolls_read=1,
            hits_dealt=10,
            missed_attacks=3,
            hits_taken=4,
            cells_walked=55,
        ),
        runs=runs,
    )


def test_snapshot_progress_captures_session_state():
    session = default_session()
    session.level_number = 4
    session.character.health = 7
    session.character.max_health = 11
    session.character.agility = 6
    session.character.strength = 8
    session.stats.treasures_collected = 15
    session.stats.enemies_defeated = 3
    session.run_results.append(make_result(15))

    snapshot = session.snapshot_progress(completed_level=3)

    assert snapshot.completed_level == 3
    assert snapshot.treasures_collected == 15
    assert snapshot.character.health == 7
    assert snapshot.character.max_health == 11
    assert snapshot.character.agility == 6
    assert snapshot.character.strength == 8
    assert snapshot.stats.enemies_defeated == 3
    assert snapshot.runs == (session.run_results[0],)


def test_session_from_progress_restores_level_points_and_character():
    snapshot = make_snapshot(completed_level=3, runs=(make_result(),), treasures=12)

    session = session_from_progress(snapshot)

    assert session.level_number == 4
    assert session.level is None
    assert session.character.health == 8
    assert session.character.max_health == 12
    assert session.character.agility == 6
    assert session.character.strength == 7
    assert session.character.pos is None
    assert session.character.weapon is None
    assert session.character.backpack.items_by_type == {}
    assert session.stats.treasures_collected == 12
    assert session.stats.cells_walked == 55
    assert session.run_results == [make_result()]


@pytest.mark.parametrize("completed_level", [0, LAST_LEVEL])
def test_session_from_progress_starts_new_run_without_unfinished_progress(completed_level):
    snapshot = make_snapshot(completed_level=completed_level, runs=(make_result(),))

    session = session_from_progress(snapshot)

    assert session.level_number == 1
    assert session.stats.treasures_collected == 0
    assert session.character.health == 10
    assert session.run_results == [make_result()]


def test_json_storage_roundtrip(tmp_path):
    path = tmp_path / "save.json"
    storage = JsonProgressStorage(path)
    snapshot = make_snapshot(runs=(make_result(), make_result(9, success=True)))

    storage.save(snapshot)
    loaded = storage.load()

    assert loaded == snapshot


def test_storage_path_defaults_and_override(tmp_path, monkeypatch):
    monkeypatch.delenv("ROGUE_SAVE_PATH", raising=False)
    assert default_save_path() == Path.home() / ".local/share/rogue-like/save.json"
    explicit = tmp_path / "custom.json"
    assert JsonProgressStorage(explicit).path == explicit

    monkeypatch.setenv("ROGUE_SAVE_PATH", str(tmp_path / "env.json"))
    assert JsonProgressStorage().path == tmp_path / "env.json"


def test_atomic_write_leaves_only_target_file(tmp_path):
    path = tmp_path / "save.json"
    storage = JsonProgressStorage(path)

    storage.save(make_snapshot())

    assert sorted(item.name for item in tmp_path.iterdir()) == ["save.json"]
    with path.open(encoding="utf-8") as handle:
        assert json.load(handle)["version"] == 1


def test_save_does_not_raise_when_path_is_unwritable(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    storage = JsonProgressStorage(blocker / "save.json")

    storage.save(make_snapshot())


@pytest.mark.parametrize(
    "content",
    [
        "{",
        json.dumps({"version": 1}),
        json.dumps({"version": 99, "runs": []}),
        json.dumps({"version": 1, "runs": [{"treasures_collected": "x"}]}),
    ],
)
def test_load_returns_none_for_broken_storage(tmp_path, content):
    path = tmp_path / "save.json"
    path.write_text(content, encoding="utf-8")

    assert JsonProgressStorage(path).load() is None


def test_load_returns_none_for_missing_storage(tmp_path):
    assert JsonProgressStorage(tmp_path / "missing.json").load() is None


def test_history_is_replaced_without_duplicates(tmp_path):
    path = tmp_path / "save.json"
    storage = JsonProgressStorage(path)
    first = make_result(5)
    second = make_result(9)
    storage.save(make_snapshot(runs=(first,)))

    loaded = storage.load()
    assert loaded is not None
    storage.save(
        ProgressSnapshot(
            completed_level=loaded.completed_level,
            treasures_collected=loaded.treasures_collected,
            character=loaded.character,
            stats=loaded.stats,
            runs=loaded.runs + (second,),
        )
    )

    reloaded = storage.load()
    assert reloaded is not None
    assert reloaded.runs == (first, second)


def test_initial_session_loads_saved_progress(tmp_path):
    path = tmp_path / "save.json"
    storage = JsonProgressStorage(path)
    storage.save(make_snapshot(completed_level=5, runs=(make_result(),)))

    session = _initial_session(storage)

    assert session.level_number == 6
    assert session.character.health == 8
    assert session.stats.treasures_collected == 12
    assert len(session.run_results) == 1


@pytest.mark.parametrize("broken", [False, True])
def test_initial_session_starts_new_game_on_missing_or_broken_storage(tmp_path, broken):
    path = tmp_path / "save.json"
    if broken:
        path.write_text("{", encoding="utf-8")

    session = _initial_session(JsonProgressStorage(path))

    assert session.level_number == 1
    assert session.stats.treasures_collected == 0
    assert session.run_results == []


def test_persist_after_level_transition_saves_completed_level(tmp_path):
    storage = JsonProgressStorage(tmp_path / "save.json")
    session = default_session()
    session.level_number = 4
    session.stats.treasures_collected = 17

    _persist_after_action(storage, session, level_before=3, results_before=0)

    loaded = storage.load()
    assert loaded is not None
    assert loaded.completed_level == 3
    assert loaded.treasures_collected == 17
    assert loaded.stats.treasures_collected == 17


@pytest.mark.parametrize("success", [False, True])
def test_persist_after_run_end_clears_progress_and_keeps_history(tmp_path, success):
    storage = JsonProgressStorage(tmp_path / "save.json")
    previous = make_result(4)
    result = make_result(11, success=success)
    session = default_session()
    session.run_results.extend([previous, result])
    session.stats.treasures_collected = 99

    _persist_after_action(storage, session, level_before=2, results_before=1)

    loaded = storage.load()
    assert loaded is not None
    assert loaded.completed_level == 0
    assert loaded.runs == (previous, result)


def test_persistence_snapshot_is_independent_of_session_lists():
    session = default_session()
    session.run_results.append(make_result(3))
    snapshot = session.snapshot_progress(completed_level=1)

    session.run_results.append(make_result(8))

    assert snapshot.runs == (make_result(3),)
