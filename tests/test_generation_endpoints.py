"""Тесты конечных точек и достижимости (design.md D6, задачи 5.1, 5.2)."""

import random
from domain.generation import generate_level, generator


def test_start_end_correctly_marked() -> None:
    level = generate_level(1, random.Random(42))
    starts = [r for r in level.rooms if r.is_start]
    ends = [r for r in level.rooms if r.is_end]
    assert len(starts) == 1
    assert len(ends) == 1
    assert starts[0] != ends[0]


def test_spawn_and_transition_in_interiors() -> None:
    level = generate_level(1, random.Random(42))
    start_room = next(r for r in level.rooms if r.is_start)
    end_room = next(r for r in level.rooms if r.is_end)
    assert level.player_pos is not None
    assert start_room.is_interior(level.player_pos)
    assert end_room.is_interior(level.transition)


def test_reachability_for_multiple_seeds() -> None:
    for seed in range(100):
        level = generate_level(1, random.Random(seed))
        assert level.player_pos is not None
        assert generator._connected(level, level.player_pos, level.transition), (
            f"seed {seed} disconnected"
        )
