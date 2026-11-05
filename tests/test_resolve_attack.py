import random

from tests.doubles import FakeCombatant, FakeWeapon, first_seed

from domain.combat.engine import AttackResult, resolve_attack


def test_full_cycle_hit():
    defender = FakeCombatant(health=10)
    result = resolve_attack(
        FakeCombatant(strength=10),
        defender,
        FakeWeapon(strength_bonus=2),
        random.Random(1),
        force_hit=True,
    )
    assert isinstance(result, AttackResult)
    assert result.hit
    assert result.damage > 0
    assert defender.health - result.damage > 0
    assert not result.killed


def test_miss_changes_nothing():
    defender = FakeCombatant(health=10)
    result = resolve_attack(
        FakeCombatant(strength=10),
        defender,
        None,
        random.Random(first_seed(want=False)),
    )
    assert not result.hit
    assert result.damage == 0
    assert not result.killed
    assert result.treasure is None
    assert result.effects.sleep_target is False
    assert result.effects.max_hp_drain == 0


def test_death_of_enemy_target():
    defender = FakeCombatant(health=2, hostility=4)
    result = resolve_attack(
        FakeCombatant(strength=10),
        defender,
        None,
        random.Random(1),
        force_hit=True,
    )
    assert result.hit
    assert defender.health - result.damage <= 0
    assert result.killed
    assert result.treasure is not None


def test_death_of_player_yields_no_treasure():
    player = FakeCombatant(is_player=True, health=1)
    result = resolve_attack(
        FakeCombatant(strength=20),
        player,
        None,
        random.Random(1),
        force_hit=True,
    )
    assert result.killed
    assert result.treasure is None


def test_deterministic_under_seed():
    attacker = FakeCombatant(strength=10)
    defender = FakeCombatant(health=10)
    seed = first_seed()
    a = resolve_attack(attacker, defender, None, random.Random(seed), force_hit=True)
    b = resolve_attack(attacker, defender, None, random.Random(seed), force_hit=True)
    assert a == b
