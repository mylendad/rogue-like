import random

from tests.doubles import FakeCombatant, FakeWeapon

from domain.combat.engine import strike_damage


def test_damage_without_weapon_is_strength_only():
    attacker = FakeCombatant(strength=10)
    damage = strike_damage(attacker, None, random.Random(42))
    base = 10 // 2  # 5
    assert base <= damage <= base + base // 4


def test_weapon_raises_damage_for_same_target():
    attacker = FakeCombatant(strength=10)
    bare = strike_damage(attacker, None, random.Random(42))
    armed = strike_damage(attacker, FakeWeapon(strength_bonus=5), random.Random(42))
    assert armed > bare


def test_weapon_contributes_exact_bonus_under_same_seed():
    attacker = FakeCombatant(strength=10)
    bare = strike_damage(attacker, FakeWeapon(strength_bonus=0), random.Random(123))
    armed = strike_damage(attacker, FakeWeapon(strength_bonus=7), random.Random(123))
    assert armed == bare + 7


def test_damage_deterministic_under_seed():
    attacker = FakeCombatant(strength=10)
    weapon = FakeWeapon(strength_bonus=5)
    a = strike_damage(attacker, weapon, random.Random(777))
    b = strike_damage(attacker, weapon, random.Random(777))
    assert a == b
