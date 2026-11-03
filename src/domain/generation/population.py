"""Наполнение уровня противниками и предметами (design.md D7, D8).

Строит сущности по строке таблицы наполнения и размещает их на
свободных интерьерных клетках комнат. Противники не попадают в
стартовую комнату (спека level-generation, «Позиционирование акторов»).
"""

import random

from domain.entities.enemy import Enemy, EnemyType
from domain.entities.item import Item, ItemType
from domain.entities.world import Coord, Room
from domain.generation.config import (
    ELIXIR_BONUSES,
    ENEMY_BASE_STATS,
    FOOD_HEALTH_GAIN,
    SCROLL_BONUSES,
    WEAPON_STRENGTH_BONUS,
    LevelFill,
)


class GenerationError(RuntimeError):
    """Наполнение уровня по текущей конфигурации невозможно."""


def populate(
    rooms: list[Room],
    fill: LevelFill,
    *,
    player_pos: Coord,
    transition: Coord,
    rng: random.Random,
) -> tuple[dict[Coord, Enemy], dict[Coord, Item]]:
    """Противники и предметы на свободных интерьерных клетках (D8).

    Клетка спавна игрока и клетка перехода считаются занятыми;
    клетки не переиспользуются.
    """
    occupied = {player_pos, transition}
    enemies: dict[Coord, Enemy] = {}
    items: dict[Coord, Item] = {}

    enemy_cells = _free_cells(rooms, rng, skip_start=True, occupied=occupied)
    enemy_counts: list[tuple[EnemyType, int]] = [
        (EnemyType.ZOMBIE, fill.zombies),
        (EnemyType.VAMPIRE, fill.vampires),
        (EnemyType.GHOST, fill.ghosts),
        (EnemyType.OGRE, fill.ogres),
        (EnemyType.SNAKE_MAGE, fill.snake_mages),
    ]
    wanted = sum(n for _, n in enemy_counts)
    if len(enemy_cells) < wanted:
        raise GenerationError("не хватает интерьерных клеток для противников")
    enemy_coords = [enemy_cells.pop() for _ in range(wanted)]
    for enemy_type, coord in zip(_repeat_types(enemy_counts), enemy_coords, strict=True):
        enemies[coord] = _make_enemy(enemy_type, fill)

    item_cells = _free_cells(
        rooms,
        rng,
        skip_start=False,
        occupied=occupied | enemies.keys(),
    )
    item_batches: list[tuple[int, Item]] = [
        (fill.treasures, _make_treasure(fill)),
        (fill.food, _make_food()),
        (fill.elixirs, _make_elixir()),
        (fill.scrolls, _make_scroll()),
        (fill.weapons, _make_weapon()),
    ]
    for n, sample in item_batches:
        if len(item_cells) < n:
            raise GenerationError("не хватает интерьерных клеток для предметов")
        for _ in range(n):
            items[item_cells.pop()] = sample
    return enemies, items


def _repeat_types(counts: list[tuple[EnemyType, int]]) -> list[EnemyType]:
    """Разворачивает (тип, N) в N повторов типа в порядке таблицы."""
    ordered: list[EnemyType] = []
    for enemy_type, n in counts:
        ordered.extend([enemy_type] * n)
    return ordered


def _free_cells(
    rooms: list[Room],
    rng: random.Random,
    *,
    skip_start: bool,
    occupied: set[Coord],
) -> list[Coord]:
    """Свободные интерьерные клетки комнат в случайном порядке (D8)."""
    cells: list[Coord] = []
    for room in rooms:
        if skip_start and room.is_start:
            continue
        cells.extend(cell for cell in room.interior_cells() if cell not in occupied)
    rng.shuffle(cells)
    return cells


def _make_enemy(enemy_type: EnemyType, fill: LevelFill) -> Enemy:
    base = ENEMY_BASE_STATS[enemy_type]
    power = fill.enemy_power
    return Enemy(
        enemy_type=enemy_type,
        health=max(1, round(base.health * power)),
        agility=max(1, round(base.agility * power)),
        strength=max(1, round(base.strength * power)),
        speed=base.speed,
        hostility=base.hostility,
    )


def _make_treasure(fill: LevelFill) -> Item:
    return Item(item_type=ItemType.TREASURE, subtype="trophy", worth=fill.treasure_worth)


def _make_food() -> Item:
    return Item(item_type=ItemType.FOOD, subtype="ration", health_gain=FOOD_HEALTH_GAIN)


def _make_elixir() -> Item:
    return Item(
        item_type=ItemType.ELIXIR,
        subtype="tonic",
        max_health_bonus=ELIXIR_BONUSES[0],
        agility_bonus=ELIXIR_BONUSES[1],
        strength_bonus=ELIXIR_BONUSES[2],
    )


def _make_scroll() -> Item:
    return Item(
        item_type=ItemType.SCROLL,
        subtype="scroll",
        max_health_bonus=SCROLL_BONUSES[0],
        agility_bonus=SCROLL_BONUSES[1],
        strength_bonus=SCROLL_BONUSES[2],
    )


def _make_weapon() -> Item:
    return Item(
        item_type=ItemType.WEAPON,
        subtype="sword",
        strength_bonus=WEAPON_STRENGTH_BONUS,
    )
