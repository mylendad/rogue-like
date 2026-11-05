import random
import statistics

from tests.doubles import FakeCombatant

from domain.combat.engine import roll_treasure


def mean_treasure(lo: FakeCombatant, hi: FakeCombatant, seeds: int = 300) -> float:
    with_lo = statistics.mean(roll_treasure(lo, random.Random(s)) for s in range(seeds))
    with_hi = statistics.mean(roll_treasure(hi, random.Random(s)) for s in range(seeds))
    assert with_hi > with_lo
    return with_hi


def test_treasure_correlates_with_hostility():
    lo = FakeCombatant(hostility=1)
    hi = FakeCombatant(hostility=10)
    mean_treasure(lo, hi)


def test_treasure_correlates_with_strength():
    mean_treasure(FakeCombatant(strength=1), FakeCombatant(strength=10))


def test_treasure_correlates_with_agility():
    mean_treasure(FakeCombatant(agility=1), FakeCombatant(agility=10))


def test_treasure_correlates_with_health():
    mean_treasure(FakeCombatant(health=1), FakeCombatant(health=10))


def test_treasure_lower_bound_at_least_one():
    tiny = FakeCombatant(hostility=0, strength=1, agility=0, health=1)
    for seed in range(100):
        assert roll_treasure(tiny, random.Random(seed)) >= 1


def test_treasure_spread_stays_random():
    enemy = FakeCombatant()
    values = {roll_treasure(enemy, random.Random(s)) for s in range(100)}
    assert len(values) > 1


def test_killed_enemy_fills_treasure_in_result():
    from domain.combat.engine import resolve_attack

    enemy = FakeCombatant(health=1, hostility=4)
    result = resolve_attack(
        FakeCombatant(is_player=True, strength=10),
        enemy,
        None,
        random.Random(1),
        force_hit=True,
    )
    assert result.killed
    assert result.treasure is not None


def test_treasure_roll_deterministic_under_seed():
    enemy = FakeCombatant()
    assert roll_treasure(enemy, random.Random(5)) == roll_treasure(enemy, random.Random(5))
