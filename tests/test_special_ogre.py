import random

from tests.doubles import FakeCombatant, first_seed

from domain.combat.engine import resolve_attack


def test_ogre_flags_rest_and_counter_after_hit():
    ogre = FakeCombatant(enemy_type="ogre", strength=8)
    player = FakeCombatant(is_player=True, health=50)
    result = resolve_attack(ogre, player, None, random.Random(first_seed()))
    assert result.hit
    assert result.effects.rest_and_counter


def test_ogre_flags_rest_and_counter_after_miss_too():
    ogre = FakeCombatant(enemy_type="ogre", strength=8)
    player = FakeCombatant(is_player=True, health=50)
    result = resolve_attack(
        ogre,
        player,
        None,
        random.Random(first_seed(want=False)),
    )
    assert not result.hit
    assert result.effects.rest_and_counter


def test_guaranteed_counterattack_forces_hit_without_new_cycle():
    ogre = FakeCombatant(enemy_type="ogre", strength=8)
    player = FakeCombatant(is_player=True, health=50)
    counter = resolve_attack(
        ogre,
        player,
        None,
        random.Random(first_seed(want=False)),
        force_hit=True,
    )
    assert counter.hit
    assert counter.damage > 0
    assert not counter.effects.rest_and_counter


def test_player_attacking_ogre_gets_no_rest_chain():
    ogre = FakeCombatant(enemy_type="ogre", health=50)
    player = FakeCombatant(is_player=True, strength=8)
    result = resolve_attack(player, ogre, None, random.Random(first_seed()))
    assert result.hit
    assert not result.effects.rest_and_counter
