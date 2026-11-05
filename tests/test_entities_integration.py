import random

from domain.combat.engine import resolve_attack
from domain.entities.enemy import Enemy, EnemyType
from domain.entities.session import default_session
from domain.entities.world import Coord, Corridor, Level, Room
from tests.doubles import FakeCombatant, chain_corridors


def level_with_grid() -> Level:
    rooms: list[Room] = []
    for row in range(3):
        for col in range(3):
            x = col * 8
            y = row * 6
            dooked = (Coord(x, y + 1), Coord(x + 5, y + 1))
            is_start = row == 0 and col == 0
            is_end = row == 2 and col == 2
            rooms.append(
                Room(x=x, y=y, width=6, height=5, doors=dooked, is_start=is_start, is_end=is_end)
            )
    corridors = [
        Corridor(cells=tuple(Coord(cx, 1) for cx in range(6, 8)), connects=(0, 1)),
        Corridor(cells=tuple(Coord(cx, 13) for cx in range(6, 8)), connects=(3, 4)),
        Corridor(cells=tuple(Coord(cx, 19) for cx in range(6, 8)), connects=(6, 7)),
    ]
    corridors += chain_corridors(rooms)
    return Level(rooms=rooms, corridors=corridors, transition=Coord(18, 14))


def test_full_beat_character_enemy_in_session_level():
    session = default_session()
    character = session.character
    level = level_with_grid()
    enemy = Enemy(
        enemy_type=EnemyType.ZOMBIE, health=2, agility=3, strength=3, speed=1, hostility=4
    )
    coord = Coord(2, 1)
    level.enemies[coord] = enemy

    rng = random.Random(0)
    player_alive = True
    for _ in range(1000):
        result = resolve_attack(character, enemy, None, rng)
        if result.hit:
            session.record_player_attack(hit=True)
            enemy.health -= result.damage
        else:
            session.record_player_attack(hit=False)
        if enemy.health <= 0:
            level.remove_enemy_at(coord)
            session.record_enemy_defeated()
            assert result.treasure is not None
            session.record_treasure(result.treasure)
            break
        back = resolve_attack(enemy, character, None, rng)
        if back.hit:
            session.record_hit_taken()
            character.health -= back.damage
            if character.health <= 0:
                player_alive = False
                break
    assert not player_alive or coord not in level.enemies
    assert session.stats.enemies_defeated == 1
    assert session.stats.hits_dealt + session.stats.hits_taken > 0
    assert session.stats.treasures_collected > 0


def test_session_stats_track_hits_taken_from_enemy():
    session = default_session()
    character = session.character
    enemy = FakeCombatant(agility=50, strength=0)
    rng = random.Random(0)
    for _ in range(50):
        back = resolve_attack(enemy, character, None, rng, force_hit=True)
        if back.hit:
            session.record_hit_taken()
            break
    assert session.stats.hits_taken >= 1
