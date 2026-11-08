"""JSON-хранилище прогресса и истории прохождений."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from domain.entities.character import (
    START_AGILITY,
    START_HEALTH,
    START_MAX_HEALTH,
    START_STRENGTH,
)
from domain.entities.session import (
    CharacterProgress,
    ProgressSnapshot,
    RunResult,
    StatsProgress,
)

SCHEMA_VERSION = 1


class _InvalidData(Exception):
    pass


def default_save_path() -> Path:
    override = os.environ.get("ROGUE_SAVE_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".local" / "share" / "rogue-like" / "save.json"


class JsonProgressStorage:
    """Хранит снимок прогресса и историю попыток в JSON-файле."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path is not None else default_save_path()

    def load(self) -> ProgressSnapshot | None:
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None
        return _decode(data)

    def save(self, snapshot: ProgressSnapshot) -> None:
        payload = _encode(snapshot)
        temp_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, raw_path = tempfile.mkstemp(
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
            )
            temp_path = Path(raw_path)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temp_path, self.path)
            temp_path = None
        except OSError:
            return
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink()
                except OSError:
                    pass


def _encode(snapshot: ProgressSnapshot) -> dict[str, object]:
    return {
        "version": SCHEMA_VERSION,
        "progress": {
            "completed_level": snapshot.completed_level,
            "treasures_collected": snapshot.treasures_collected,
            "character": asdict(snapshot.character),
            "stats": asdict(snapshot.stats),
        },
        "runs": [asdict(run) for run in snapshot.runs],
    }


def _decode(data: object) -> ProgressSnapshot | None:
    if not isinstance(data, dict):
        return None
    try:
        if _require_int(data, "version") != SCHEMA_VERSION:
            return None
        runs = _decode_runs(data.get("runs"))
        progress = data.get("progress")
        if progress is None:
            return ProgressSnapshot(
                completed_level=0,
                treasures_collected=0,
                character=CharacterProgress(
                    health=START_HEALTH,
                    max_health=START_MAX_HEALTH,
                    agility=START_AGILITY,
                    strength=START_STRENGTH,
                ),
                stats=StatsProgress(),
                runs=runs,
            )
        decoded = _decode_progress(progress)
        return ProgressSnapshot(
            completed_level=decoded.completed_level,
            treasures_collected=decoded.treasures_collected,
            character=decoded.character,
            stats=decoded.stats,
            runs=runs,
        )
    except _InvalidData:
        return None


def _decode_progress(value: object) -> ProgressSnapshot:
    if not isinstance(value, dict):
        raise _InvalidData
    completed_level = _require_int(value, "completed_level")
    treasures = _require_int(value, "treasures_collected")
    if completed_level < 0 or treasures < 0:
        raise _InvalidData

    character_value = value.get("character")
    if not isinstance(character_value, dict):
        raise _InvalidData
    health = _require_int(character_value, "health")
    max_health = _require_int(character_value, "max_health")
    agility = _require_int(character_value, "agility")
    strength = _require_int(character_value, "strength")
    if health < 0 or max_health < 1 or health > max_health:
        raise _InvalidData
    if agility < 0 or strength < 0:
        raise _InvalidData

    stats_value = value.get("stats")
    if not isinstance(stats_value, dict):
        raise _InvalidData
    stats = StatsProgress(
        treasures_collected=_require_int(stats_value, "treasures_collected"),
        enemies_defeated=_require_int(stats_value, "enemies_defeated"),
        food_eaten=_require_int(stats_value, "food_eaten"),
        elixirs_drunk=_require_int(stats_value, "elixirs_drunk"),
        scrolls_read=_require_int(stats_value, "scrolls_read"),
        hits_dealt=_require_int(stats_value, "hits_dealt"),
        missed_attacks=_require_int(stats_value, "missed_attacks"),
        hits_taken=_require_int(stats_value, "hits_taken"),
        cells_walked=_require_int(stats_value, "cells_walked"),
    )
    if any(
        field < 0
        for field in (
            stats.treasures_collected,
            stats.enemies_defeated,
            stats.food_eaten,
            stats.elixirs_drunk,
            stats.scrolls_read,
            stats.hits_dealt,
            stats.missed_attacks,
            stats.hits_taken,
            stats.cells_walked,
        )
    ):
        raise _InvalidData

    return ProgressSnapshot(
        completed_level=completed_level,
        treasures_collected=treasures,
        character=CharacterProgress(
            health=health,
            max_health=max_health,
            agility=agility,
            strength=strength,
        ),
        stats=stats,
    )


def _decode_runs(value: object) -> tuple[RunResult, ...]:
    if not isinstance(value, list):
        raise _InvalidData
    runs = []
    for item in value:
        runs.append(_decode_run(item))
    return tuple(runs)


def _decode_run(value: object) -> RunResult:
    if not isinstance(value, dict):
        raise _InvalidData
    result = RunResult(
        treasures_collected=_require_int(value, "treasures_collected"),
        reached_level=_require_int(value, "reached_level"),
        enemies_defeated=_require_int(value, "enemies_defeated"),
        food_eaten=_require_int(value, "food_eaten"),
        elixirs_drunk=_require_int(value, "elixirs_drunk"),
        scrolls_read=_require_int(value, "scrolls_read"),
        hits_dealt=_require_int(value, "hits_dealt"),
        missed_attacks=_require_int(value, "missed_attacks"),
        hits_taken=_require_int(value, "hits_taken"),
        cells_walked=_require_int(value, "cells_walked"),
        success=_require_bool(value, "success"),
    )
    if any(
        field < 0
        for field in (
            result.treasures_collected,
            result.reached_level,
            result.enemies_defeated,
            result.food_eaten,
            result.elixirs_drunk,
            result.scrolls_read,
            result.hits_dealt,
            result.missed_attacks,
            result.hits_taken,
            result.cells_walked,
        )
    ):
        raise _InvalidData
    return result


def _require_int(mapping: Mapping[str, object], key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise _InvalidData
    return value


def _require_bool(mapping: Mapping[str, object], key: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise _InvalidData
    return value
