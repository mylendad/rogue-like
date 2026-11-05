"""Тесты наполнения (design.md D7-D8; задачи 6.1, 6.2)."""

import random
from domain.entities.enemy import EnemyType
from domain.generation import generate_level, config


def test_population_counts_and_stats() -> None:
    # 6.1
    lv = 5
    fill = config.LEVEL_CONTENT[lv]
    level = generate_level(lv, random.Random(7))

    # Counts
    enemy_types = [e.enemy_type for e in level.enemies.values()]
    assert enemy_types.count(EnemyType.ZOMBIE) == fill.zombies

    # Stats scaling
    zombie = next(e for e in level.enemies.values() if e.enemy_type == EnemyType.ZOMBIE)
    base = config.ENEMY_BASE_STATS[EnemyType.ZOMBIE]
    assert zombie.health == max(1, round(base.health * fill.enemy_power))


def test_placement_rules() -> None:
    # 6.2
    level = generate_level(1, random.Random(8))
    start = next(r for r in level.rooms if r.is_start)

    # Enemies not in start
    for coord, enemy in level.enemies.items():
        assert not start.is_interior(coord), "враг в стартовой комнате"

    # Unique coords
    all_coords = list(level.enemies.keys()) + list(level.items.keys())
    assert len(all_coords) == len(set(all_coords))

    # Passable interior
    for coord in all_coords:
        assert level.passable(coord)
        assert any(r.is_interior(coord) for r in level.rooms)
