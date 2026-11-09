import random

from domain.combat.engine import resolve_attack
from domain.entities.enemy import Enemy, EnemyType
from domain.entities.world import Coord, Corridor, Level, Room
from domain.entities.session import default_session
from tests.doubles import chain_corridors


def make_level() -> Level:
    rooms = [Room(0, 0, 7, 7, is_start=True)]
    rooms += [Room(8 + i * 4, 0, 3, 3) for i in range(7)]
    rooms.append(Room(40, 0, 5, 5, is_end=True))
    corridor = Corridor(
        cells=(Coord(6, 2), Coord(7, 2), Coord(8, 2)),
        connects=(0, 1),
    )
    return Level(
        rooms=rooms,
        corridors=[corridor, *chain_corridors(rooms)],
        transition=Coord(41, 1),
    )


def make_session(pos: Coord = Coord(1, 1)):
    session = default_session()
    level = make_level()
    session.level = level
    session.character.pos = pos
    level.player_pos = pos
    return session


def test_move_one_cell():
    session = make_session()
    assert session.try_move_or_attack(1, 0) is True
    assert session.character.pos == Coord(2, 1)
    assert session.stats.cells_walked == 1


def test_move_multiple_cells_with_speed():
    session = make_session()
    session.character.agility = 10
    assert session.character.speed == 2
    assert session.try_move_or_attack(1, 0) is True
    assert session.character.pos == Coord(3, 1)
    assert session.stats.cells_walked == 2


def test_partial_move_before_wall():
    session = make_session(Coord(4, 1))
    session.character.agility = 10
    assert session.try_move_or_attack(1, 0) is True
    assert session.character.pos == Coord(5, 1)
    assert session.stats.cells_walked == 1


def test_wall_adjacent_does_not_consume_turn():
    session = make_session()
    assert session.try_move_or_attack(0, -1) is False
    assert session.character.pos == Coord(1, 1)
    assert session.stats.cells_walked == 0


def test_attack_after_partial_move():
    session = make_session()
    level = session.level
    assert level is not None
    session.character.agility = 10
    enemy = Enemy(
        enemy_type=EnemyType.ZOMBIE,
        health=10,
        agility=1,
        strength=1,
        speed=1,
        hostility=1,
    )
    level.enemies[Coord(3, 1)] = enemy

    assert session.try_move_or_attack(1, 0) is True
    assert session.character.pos == Coord(2, 1)
    assert session.stats.hits_dealt + session.stats.missed_attacks == 1


def test_kill_enemy():
    session = make_session()
    level = session.level
    assert level is not None
    enemy = Enemy(
        enemy_type=EnemyType.ZOMBIE,
        health=1,
        agility=1,
        strength=1,
        speed=1,
        hostility=1,
    )
    level.enemies[Coord(2, 1)] = enemy
    session.character.strength = 100
    session.character.agility = 100

    seed = None
    for candidate in range(1000):
        if resolve_attack(
            session.character,
            enemy,
            session.character.weapon,
            random.Random(candidate),
        ).hit:
            seed = candidate
            break
    assert seed is not None

    assert session.try_move_or_attack(1, 0, rng=random.Random(seed)) is True
    assert Coord(2, 1) not in level.enemies
    assert session.stats.enemies_defeated == 1
    assert session.stats.treasures_collected > 0
