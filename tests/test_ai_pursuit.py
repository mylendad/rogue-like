import random

from domain.ai.engine import decide_enemy_action
from domain.combat.engine import resolve_attack
from domain.entities.character import Character
from domain.entities.enemy import Enemy, EnemyType
from domain.entities.session import default_session
from domain.entities.world import Coord, Corridor, Level, Room
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


def make_enemy(enemy_type: EnemyType, **kwargs) -> Enemy:
    return Enemy(enemy_type=enemy_type, health=10, agility=3, strength=3, **kwargs)


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def enemy_hit_seed(enemy: Enemy, player: Character) -> int:
    for seed in range(100000):
        if resolve_attack(enemy, player, None, random.Random(seed)).hit:
            return seed
    raise AssertionError("seed not found")


def enemy_sleep_seed(enemy: Enemy, player: Character) -> int:
    for seed in range(100000):
        result = resolve_attack(enemy, player, None, random.Random(seed))
        if result.hit and result.effects.sleep_target:
            return seed
    raise AssertionError("seed not found")


def test_enemy_pursues_player_within_hostility():
    level = make_level()
    level.player_pos = Coord(1, 1)
    enemy_pos = Coord(3, 3)
    zombie = make_enemy(EnemyType.ZOMBIE, hostility=10)
    level.enemies[enemy_pos] = zombie

    decide_enemy_action(level, zombie, enemy_pos, random.Random(0))

    new_pos = next(iter(level.enemies))
    assert manhattan(new_pos, level.player_pos) < manhattan(enemy_pos, level.player_pos)


def test_ghost_teleports_in_room_and_toggles_visibility():
    level = make_level()
    level.player_pos = Coord(41, 1)
    enemy_pos = Coord(3, 3)
    ghost = make_enemy(EnemyType.GHOST, hostility=1)
    level.enemies[enemy_pos] = ghost
    assert ghost.visible

    decide_enemy_action(level, ghost, enemy_pos, random.Random(0))
    first_pos = next(iter(level.enemies))
    assert first_pos != enemy_pos
    assert level.rooms[0].is_interior(first_pos)
    assert not ghost.visible

    decide_enemy_action(level, ghost, first_pos, random.Random(1))
    assert ghost.visible
    assert level.rooms[0].is_interior(next(iter(level.enemies)))


def test_ogre_moves_two_cells_straight_in_room():
    level = make_level()
    level.player_pos = Coord(41, 1)
    enemy_pos = Coord(3, 3)
    ogre = make_enemy(EnemyType.OGRE, hostility=1)
    level.enemies[enemy_pos] = ogre

    decide_enemy_action(level, ogre, enemy_pos, random.Random(0))

    new_pos = next(iter(level.enemies))
    dx, dy = new_pos.x - enemy_pos.x, new_pos.y - enemy_pos.y
    assert max(abs(dx), abs(dy)) == 2
    assert dx == 0 or dy == 0 or abs(dx) == abs(dy)
    assert level.rooms[0].is_interior(new_pos)


def test_adjacent_enemy_attacks_instead_of_moving():
    level = make_level()
    level.player_pos = Coord(1, 1)
    enemy_pos = Coord(2, 1)
    zombie = make_enemy(EnemyType.ZOMBIE, hostility=10)
    level.enemies[enemy_pos] = zombie
    player = Character()

    seed = enemy_hit_seed(zombie, player)
    result = decide_enemy_action(level, zombie, enemy_pos, random.Random(seed), player=player)

    assert result is not None and result.hit
    player.health -= result.damage
    assert player.health < 10
    assert next(iter(level.enemies)) == enemy_pos


def test_ogre_rests_then_guaranteed_counterattack():
    level = make_level()
    level.player_pos = Coord(1, 1)
    enemy_pos = Coord(2, 1)
    ogre = make_enemy(EnemyType.OGRE, hostility=10)
    level.enemies[enemy_pos] = ogre
    player = Character()

    seed = enemy_hit_seed(ogre, player)
    first = decide_enemy_action(level, ogre, enemy_pos, random.Random(seed), player=player)
    assert first is not None and first.hit
    player.health -= first.damage
    assert ogre.resting
    assert not ogre.counter_pending
    health_after_first = player.health

    second = decide_enemy_action(level, ogre, enemy_pos, random.Random(seed), player=player)
    assert second is None
    assert player.health == health_after_first
    assert not ogre.resting
    assert ogre.counter_pending

    third = decide_enemy_action(level, ogre, enemy_pos, random.Random(0), player=player)
    assert third is not None and third.hit
    player.health -= third.damage
    assert player.health < health_after_first
    assert not ogre.resting
    assert not ogre.counter_pending


def test_session_applies_vampire_damage_and_max_health_drain():
    session = default_session()
    session.level = make_level()
    session.character.pos = Coord(1, 1)
    session.level.player_pos = Coord(1, 1)
    enemy_pos = Coord(2, 1)
    vampire = make_enemy(EnemyType.VAMPIRE, hostility=10)
    session.level.enemies[enemy_pos] = vampire

    seed = enemy_hit_seed(vampire, session.character)
    session.perform_turn(rng=random.Random(seed))

    assert session.character.max_health == 9
    assert session.character.health == 9
    assert session.stats.hits_taken == 1


def test_snake_mage_sleep_skips_next_player_action():
    session = default_session()
    session.level = make_level()
    session.character.pos = Coord(1, 1)
    session.level.player_pos = Coord(1, 1)
    enemy_pos = Coord(2, 1)
    mage = make_enemy(EnemyType.SNAKE_MAGE, hostility=10)
    session.level.enemies[enemy_pos] = mage

    seed = enemy_sleep_seed(mage, session.character)
    session.perform_turn(rng=random.Random(seed))
    assert session.sleep_turns == 1

    session.level.enemies.clear()
    actions: list[str] = []
    session.perform_turn(lambda: actions.append("act"), rng=random.Random(seed))
    assert actions == []
    assert session.sleep_turns == 0
