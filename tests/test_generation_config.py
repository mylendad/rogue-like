"""Тесты конфигурации генерации (design.md D3, D7; задачи 2.1, 2.2)."""

import pytest

from domain.entities.enemy import ENEMY_TYPES, EnemyType
from domain.generation import config


# 2.1: базовые характеристики противников


def test_enemy_base_stats_cover_all_types() -> None:
    assert set(config.ENEMY_BASE_STATS) == set(ENEMY_TYPES)


@pytest.mark.parametrize(
    ("enemy_type",),
    [(enemy_type,) for enemy_type in ENEMY_TYPES],
)
def test_enemy_base_stats_positive(enemy_type: EnemyType) -> None:
    stats = config.ENEMY_BASE_STATS[enemy_type]
    for name in ("health", "agility", "strength", "speed", "hostility"):
        assert getattr(stats, name) >= 1, f"{enemy_type}: {name} должен быть >= 1"


# 2.2: таблица наполнения 1..21 и монотонность по глубине


def test_level_content_covers_all_levels() -> None:
    assert sorted(config.LEVEL_CONTENT) == list(range(1, config.LAST_LEVEL + 1))


def _enemies_total(fill: config.LevelFill) -> int:
    return fill.zombies + fill.vampires + fill.ghosts + fill.ogres + fill.snake_mages


def test_fill_enemies_never_decrease_with_depth() -> None:
    total = [_enemies_total(config.LEVEL_CONTENT[n]) for n in range(1, config.LAST_LEVEL + 1)]
    assert total == sorted(total)


def test_fill_treasures_never_decrease_with_depth() -> None:
    counts = [config.LEVEL_CONTENT[n].treasures for n in range(1, config.LAST_LEVEL + 1)]
    assert counts == sorted(counts)


def test_fill_enemy_power_never_decreases_with_depth() -> None:
    powers = [config.LEVEL_CONTENT[n].enemy_power for n in range(1, config.LAST_LEVEL + 1)]
    assert powers == sorted(powers)


def test_fill_useful_items_never_increase_with_depth() -> None:
    def useful(fill: config.LevelFill) -> int:
        return fill.food + fill.elixirs + fill.scrolls + fill.weapons

    counts = [useful(config.LEVEL_CONTENT[n]) for n in range(1, config.LAST_LEVEL + 1)]
    assert counts == sorted(counts, reverse=True)


def test_level_fill_out_of_range_raises() -> None:
    with pytest.raises(ValueError):
        config.level_fill(0)
    with pytest.raises(ValueError):
        config.level_fill(config.LAST_LEVEL + 1)
