import random

from tests.doubles import FakeCombatant, first_seed

from domain.combat.engine import resolve_attack
from domain.combat.special import SLEEP_CHANCE


def sleep_outcome(seed: int) -> bool:
    mage = FakeCombatant(enemy_type="snake_mage", strength=8)
    player = FakeCombatant(is_player=True, health=50)
    result = resolve_attack(mage, player, None, random.Random(seed), force_hit=True)
    return result.effects.sleep_target


def test_snake_mage_can_put_player_to_sleep():
    assert any(sleep_outcome(seed) for seed in range(200))


def test_snake_mage_does_not_always_put_player_to_sleep():
    assert not all(sleep_outcome(seed) for seed in range(200))


def test_sleep_is_deterministic_for_a_seed():
    assert sleep_outcome(first_seed()) == sleep_outcome(first_seed())


def test_no_sleep_for_non_player_target():
    mage = FakeCombatant(enemy_type="snake_mage", strength=8)
    enemy = FakeCombatant(health=30)
    result = resolve_attack(mage, enemy, None, random.Random(1), force_hit=True)
    assert result.hit
    assert not result.effects.sleep_target


def test_no_sleep_on_miss():
    mage = FakeCombatant(enemy_type="snake_mage")
    player = FakeCombatant(is_player=True, health=50)
    result = resolve_attack(
        mage,
        player,
        None,
        random.Random(first_seed(want=False)),
    )
    assert not result.hit
    assert not result.effects.sleep_target


def test_sleep_chance_constant_within_spec_expectation():
    assert 0 < SLEEP_CHANCE < 1
