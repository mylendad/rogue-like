from tests.doubles import FakeCombatant

from domain.combat.engine import hit_probability


def test_probability_grows_with_attacker_agility():
    defender = FakeCombatant(agility=5, speed=2)
    weak = hit_probability(FakeCombatant(agility=1, speed=2), defender)
    strong = hit_probability(FakeCombatant(agility=10, speed=2), defender)
    assert strong > weak


def test_probability_grows_with_attacker_speed():
    defender = FakeCombatant(agility=5, speed=2)
    slow = hit_probability(FakeCombatant(agility=5, speed=0), defender)
    fast = hit_probability(FakeCombatant(agility=5, speed=5), defender)
    assert fast > slow


def test_probability_drops_with_defender_agility():
    attacker = FakeCombatant(agility=5, speed=2)
    easy = hit_probability(attacker, FakeCombatant(agility=1, speed=2))
    hard = hit_probability(attacker, FakeCombatant(agility=10, speed=2))
    assert hard < easy


def test_probability_drops_with_defender_speed():
    attacker = FakeCombatant(agility=5, speed=2)
    easy = hit_probability(attacker, FakeCombatant(agility=5, speed=0))
    hard = hit_probability(attacker, FakeCombatant(agility=5, speed=5))
    assert hard < easy


def test_probability_always_between_zero_and_one():
    cases = [
        (FakeCombatant(agility=1, speed=0), FakeCombatant(agility=20, speed=20)),
        (FakeCombatant(agility=20, speed=20), FakeCombatant(agility=1, speed=0)),
        (FakeCombatant(agility=5, speed=2), FakeCombatant(agility=5, speed=2)),
    ]
    for attacker, defender in cases:
        assert 0 < hit_probability(attacker, defender) < 1
