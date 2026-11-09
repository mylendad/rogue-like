import random

from tests.doubles import FakeCombatant, first_seed

from domain.combat.engine import resolve_attack
from domain.combat.special import SPECIAL_RULES, special_rule_for
from domain.entities.character import Character
from domain.entities.enemy import Enemy, EnemyType


def test_registry_contains_five_enemy_types_contract():
    assert set(SPECIAL_RULES) == {"vampire", "ogre", "snake_mage"}
    assert special_rule_for("zombie") is None
    assert special_rule_for("ghost") is None


def test_lookup_by_enum_like_value():
    class EnemyType:
        VAMPIRE = "vampire"

    assert special_rule_for(EnemyType.VAMPIRE) is SPECIAL_RULES["vampire"]


def test_vampire_first_player_strike_always_misses():
    vampire = FakeCombatant(enemy_type="vampire", health=10)
    result = resolve_attack(
        FakeCombatant(is_player=True, strength=20),
        vampire,
        None,
        random.Random(1),
        first_player_strike=True,
        force_hit=True,
    )
    assert not result.hit
    assert result.damage == 0
    assert result.treasure is None


def test_vampire_successful_attack_drains_player_max_hp():
    vampire = FakeCombatant(enemy_type="vampire", strength=8)
    player = FakeCombatant(is_player=True, health=20)
    result = resolve_attack(
        vampire,
        player,
        None,
        random.Random(1),
        force_hit=True,
    )
    assert result.hit
    assert result.effects.max_hp_drain == 1


def test_other_enemies_do_not_drain():
    zombie = FakeCombatant(enemy_type="zombie", strength=8)
    player = FakeCombatant(is_player=True, health=20)
    result = resolve_attack(zombie, player, None, random.Random(1), force_hit=True)
    assert result.hit
    assert result.effects.max_hp_drain == 0


def test_player_back_at_vampire_after_first_strike_can_hit():
    vampire = FakeCombatant(enemy_type="vampire", health=10)
    result = resolve_attack(
        FakeCombatant(strength=10),
        vampire,
        None,
        random.Random(first_seed()),
        force_hit=True,
    )
    assert result.hit


def test_first_strike_is_tracked_independently_per_vampire():
    player = Character(strength=20)
    first = Enemy(enemy_type=EnemyType.VAMPIRE, health=20, agility=3, strength=3)
    second = Enemy(enemy_type=EnemyType.VAMPIRE, health=20, agility=3, strength=3)

    assert not resolve_attack(player, first, None, random.Random(0), force_hit=True).hit
    assert resolve_attack(player, first, None, random.Random(0), force_hit=True).hit
    assert not resolve_attack(player, second, None, random.Random(0), force_hit=True).hit
