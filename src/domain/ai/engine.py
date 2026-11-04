"""ИИ противников: паттерны и преследование (спека gameplay)."""

import random

from domain.entities.enemy import Enemy, EnemyType
from domain.entities.world import Coord, Level, Room

_ORTHOGONAL = ((0, -1), (-1, 0), (1, 0), (0, 1))
_EIGHT_DIRECTIONS = _ORTHOGONAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def decide_enemy_action(
    level: Level,
    enemy: Enemy,
    enemy_pos: Coord,
    rng: random.Random,
) -> None:
    """Выполняет паттерн вне радиуса враждебности."""
    if level.player_pos is None:
        return

    dist = abs(enemy_pos.x - level.player_pos.x) + abs(enemy_pos.y - level.player_pos.y)
    if dist <= enemy.hostility:
        return

    room = next((room for room in level.rooms if room.is_interior(enemy_pos)), None)
    if room is None:
        return
    if enemy.enemy_type is EnemyType.ZOMBIE:
        _random_step(level, enemy_pos, room, _ORTHOGONAL, rng)
    elif enemy.enemy_type is EnemyType.VAMPIRE:
        _random_step(level, enemy_pos, room, _EIGHT_DIRECTIONS, rng)
    elif enemy.enemy_type is EnemyType.SNAKE_MAGE:
        _snake_step(level, enemy, enemy_pos, room)


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


def _snake_step(level: Level, enemy: Enemy, enemy_pos: Coord, room: Room) -> None:
    for dy in (1, -1):
        new_pos = Coord(enemy_pos.x + enemy.pattern_side, enemy_pos.y + dy)
        if _available(level, room, new_pos):
            _move(level, enemy_pos, new_pos)
            enemy.pattern_side *= -1
            return


def _available(level: Level, room: Room, coord: Coord) -> bool:
    return (
        room.is_interior(coord)
        and level.passable(coord)
        and coord != level.player_pos
        and coord not in level.enemies
    )


def _move(level: Level, old_pos: Coord, new_pos: Coord) -> None:
    level.enemies[new_pos] = level.enemies.pop(old_pos)
