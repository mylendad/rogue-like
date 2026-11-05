import random

from domain.combat.engine import resolve_attack
from domain.entities.character import Character
from domain.entities.enemy import Enemy, EnemyType


def test_character_works_in_engine_as_combatant():
    player = Character(health=10, max_health=10, agility=5, strength=6)
    enemy = Enemy(enemy_type=EnemyType.ZOMBIE, health=8, agility=4, strength=3, speed=1)
    result = resolve_attack(player, enemy, None, random.Random(0), force_hit=True)
    assert result.hit is True
    assert result.damage > 0
    assert enemy.health == 8


def test_enemy_works_in_engine_as_combatant():
    player = Character(health=10, max_health=10, agility=5, strength=6)
    enemy = Enemy(
        enemy_type=EnemyType.SNAKE_MAGE, health=6, agility=6, strength=5, speed=2, hostility=4
    )
    result = resolve_attack(enemy, player, None, random.Random(0), force_hit=True)
    assert result.hit is True
    assert result.damage > 0
    assert player.health == 10
