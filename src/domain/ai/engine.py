"""ИИ противников: паттерны, преследование и атаки."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from domain.combat.engine import AttackResult, resolve_attack
from domain.entities.enemy import Enemy, EnemyType
from domain.entities.world import Coord, Level, Room

if TYPE_CHECKING:
    from domain.entities.character import Character

_ORTHOGONAL = ((0, -1), (-1, 0), (1, 0), (0, 1))
_EIGHT_DIRECTIONS = _ORTHOGONAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))
_TWO_CELL_STEPS = (
    (0, -2),
    (0, 2),
    (-2, 0),
    (2, 0),
    (-2, -2),
    (-2, 2),
    (2, -2),
    (2, 2),
)


def decide_enemy_action(
    level: Level,
    enemy: Enemy,
    enemy_pos: Coord,
    rng: random.Random,
    player: Character | None = None,
) -> AttackResult | None:
    """Ход противника: паттерн вне радиуса враждебности, внутри — погоня.

    По соседней с игроком клетке противник атакует вместо перемещения.
    Возвращает результат атаки или None; урон и боевые эффекты применяет
    вызывающий код. Отдыхающий огр пропускает ход, затем гарантированно
    контратакует.
    """
    if level.player_pos is None:
        return None

    if enemy.resting:
        enemy.resting = False
        enemy.counter_pending = True
        return None

    player_pos = level.player_pos
    if _manhattan(enemy_pos, player_pos) <= enemy.hostility:
        if enemy.enemy_type is EnemyType.GHOST:
            enemy.visible = True
        if player is not None and _adjacent(enemy_pos, player_pos):
            return _attack(enemy, player, rng)
        _pursue(level, enemy_pos, player_pos, rng)
        return None

    room = next((room for room in level.rooms if room.is_interior(enemy_pos)), None)
    if room is None:
        return None
    if enemy.enemy_type is EnemyType.ZOMBIE:
        _random_step(level, enemy_pos, room, _ORTHOGONAL, rng)
    elif enemy.enemy_type is EnemyType.VAMPIRE:
        _random_step(level, enemy_pos, room, _EIGHT_DIRECTIONS, rng)
    elif enemy.enemy_type is EnemyType.GHOST:
        _ghost_step(level, enemy, enemy_pos, room, rng)
    elif enemy.enemy_type is EnemyType.OGRE:
        _ogre_step(level, enemy_pos, room, rng)
    elif enemy.enemy_type is EnemyType.SNAKE_MAGE:
        _snake_step(level, enemy, enemy_pos, room)
    return None


def _attack(enemy: Enemy, player: Character, rng: random.Random) -> AttackResult:
    force_hit = enemy.counter_pending
    enemy.counter_pending = False
    result = resolve_attack(enemy, player, None, rng, force_hit=force_hit)
    if result.effects.rest_and_counter:
        enemy.resting = True
    return result


def _pursue(
    level: Level,
    enemy_pos: Coord,
    player_pos: Coord,
    rng: random.Random,
) -> None:
    candidates: list[Coord] = []
    for dx, dy in _EIGHT_DIRECTIONS:
        coord = Coord(enemy_pos.x + dx, enemy_pos.y + dy)
        if _free(level, coord):
            candidates.append(coord)
    if not candidates:
        return
    best = min(_manhattan(coord, player_pos) for coord in candidates)
    if best > _manhattan(enemy_pos, player_pos):
        return
    target = rng.choice([c for c in candidates if _manhattan(c, player_pos) == best])
    _move(level, enemy_pos, target)


def _random_step(
    level: Level,
    enemy_pos: Coord,
    room: Room,
    directions: tuple[tuple[int, int], ...],
    rng: random.Random,
) -> None:
    candidates = [
        Coord(enemy_pos.x + dx, enemy_pos.y + dy)
        for dx, dy in directions
        if _available(level, room, Coord(enemy_pos.x + dx, enemy_pos.y + dy))
    ]
    if candidates:
        _move(level, enemy_pos, rng.choice(candidates))


def _ghost_step(
    level: Level,
    enemy: Enemy,
    enemy_pos: Coord,
    room: Room,
    rng: random.Random,
) -> None:
    candidates = [
        coord for coord in room.interior_cells() if coord != enemy_pos and _free(level, coord)
    ]
    if candidates:
        _move(level, enemy_pos, rng.choice(candidates))
    enemy.visible = not enemy.visible


def _ogre_step(level: Level, enemy_pos: Coord, room: Room, rng: random.Random) -> None:
    candidates = []
    for dx, dy in _TWO_CELL_STEPS:
        middle = Coord(enemy_pos.x + dx // 2, enemy_pos.y + dy // 2)
        target = Coord(enemy_pos.x + dx, enemy_pos.y + dy)
        if _available(level, room, middle) and _available(level, room, target):
            candidates.append(target)
    if candidates:
        _move(level, enemy_pos, rng.choice(candidates))


def _snake_step(level: Level, enemy: Enemy, enemy_pos: Coord, room: Room) -> None:
    for dy in (1, -1):
        new_pos = Coord(enemy_pos.x + enemy.pattern_side, enemy_pos.y + dy)
        if _available(level, room, new_pos):
            _move(level, enemy_pos, new_pos)
            enemy.pattern_side *= -1
            return


def _available(level: Level, room: Room, coord: Coord) -> bool:
    return room.is_interior(coord) and _free(level, coord)


def _free(level: Level, coord: Coord) -> bool:
    return level.passable(coord) and coord != level.player_pos and coord not in level.enemies


def _adjacent(a: Coord, b: Coord) -> bool:
    return max(abs(a.x - b.x), abs(a.y - b.y)) == 1


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def _move(level: Level, old_pos: Coord, new_pos: Coord) -> None:
    level.enemies[new_pos] = level.enemies.pop(old_pos)
