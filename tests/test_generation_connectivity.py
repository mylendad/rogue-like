"""Тесты связности и регенерации (design.md D5; задача 4.3)."""

import random

import pytest

from domain.generation import generator, generate_level
from domain.generation.population import GenerationError


def test_level_connects_all_rooms_and_transition() -> None:
    level = generate_level(1, random.Random(5))
    spawn = level.player_pos
    assert spawn is not None
    assert generator._connected(level, spawn, level.transition)


def test_regeneration_after_failed_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Связность не прошла с первой попытки — вторая собирает уровень (D5)."""
    checks = iter([False, True])
    monkeypatch.setattr(generator, "_connected", lambda *args: next(checks))
    level = generate_level(1, random.Random(1))
    assert level.rooms and level.corridors


def test_attempt_limit_exhaustion_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Исчерпан лимит попыток — GenerationError (D5)."""
    monkeypatch.setattr(generator, "_connected", lambda *args: False)
    monkeypatch.setattr(generator, "MAX_ATTEMPTS", 3)
    with pytest.raises(GenerationError):
        generate_level(1, random.Random(2))
