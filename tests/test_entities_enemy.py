import pytest

from domain.combat.special import SPECIAL_RULES
from domain.entities.enemy import ENEMY_TYPES, Enemy, EnemyType


def test_enemy_type_registry_matches_special_rules():
    rule_types = {EnemyType(name) for name in SPECIAL_RULES}
    assert rule_types <= set(ENEMY_TYPES)


@pytest.mark.parametrize("enemy_type", list(ENEMY_TYPES))
def test_each_enemy_type_has_filled_stats(enemy_type: EnemyType):
    enemy = Enemy(enemy_type=enemy_type, health=7, agility=3, strength=4, speed=2, hostility=5)
    assert enemy.enemy_type is enemy_type
    assert enemy.health == 7
    assert enemy.agility == 3
    assert enemy.strength == 4
    assert enemy.speed == 2
    assert enemy.hostility == 5


def test_enemy_has_speed_and_hostility_defaults():
    enemy = Enemy(enemy_type=EnemyType.ZOMBIE, health=5, agility=2, strength=3)
    assert enemy.speed == 1
    assert enemy.hostility == 1


def test_enemy_rejects_unknown_type():
    with pytest.raises(ValueError):
        Enemy(enemy_type="dragon", health=5, agility=2, strength=3)  # type: ignore[arg-type]


def test_all_five_types_present():
    assert len(ENEMY_TYPES) == 5
    assert set(ENEMY_TYPES) == {
        EnemyType.ZOMBIE,
        EnemyType.VAMPIRE,
        EnemyType.GHOST,
        EnemyType.OGRE,
        EnemyType.SNAKE_MAGE,
    }


def test_enemy_is_not_player():
    assert Enemy(enemy_type=EnemyType.GHOST, health=5, agility=2, strength=3).is_player is False
