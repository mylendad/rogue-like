import random

from tests.doubles import FakeCombatant, FakeWeapon, first_seed

from domain.combat.engine import AttackResult, Move, attack_or_move


def test_attack_by_moving_into_enemy_cell():
    player = FakeCombatant(is_player=True, strength=10)
    enemy = FakeCombatant(health=10)
    moves = []
    result = attack_or_move(
        player,
        enemy,
        FakeWeapon(strength_bonus=2),
        random.Random(first_seed()),
        move_into=lambda: moves.append(1),
    )
    assert isinstance(result, AttackResult)
    assert result.hit
    assert moves == []


def test_free_cell_performs_move_not_attack():
    player = FakeCombatant(is_player=True, strength=10)
    moves = []
    result = attack_or_move(player, None, None, random.Random(1), move_into=lambda: moves.append(1))
    assert isinstance(result, Move)
    assert moves == [1]


def test_first_player_strike_flag_reaches_attack():
    player = FakeCombatant(is_player=True, strength=10)
    vampire = FakeCombatant(enemy_type="vampire", health=10)
    result = attack_or_move(
        player,
        vampire,
        None,
        random.Random(1),
        first_player_strike=True,
    )
    assert isinstance(result, AttackResult)
    assert not result.hit
