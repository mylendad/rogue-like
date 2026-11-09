import random

from tests.doubles import FakeCombatant, FakeWeapon, first_seed

from domain.combat.engine import AttackResult, attack_or_move, resolve_attack


def test_full_battle_player_kills_zombie_and_collects_treasure():
    rng = random.Random(2026)
    player = FakeCombatant(is_player=True, health=40, strength=12)
    weapon = FakeWeapon(strength_bonus=3)
    enemy = FakeCombatant(health=20, hostility=6, strength=5, agility=3, speed=2)
    session_treasure = 0
    first_strike = True
    strikes = 0
    while True:
        outcome = attack_or_move(player, enemy, weapon, rng, first_player_strike=first_strike)
        first_strike = False
        assert isinstance(outcome, AttackResult)
        if not outcome.hit:
            continue
        strikes += 1
        enemy.health -= outcome.damage
        session_treasure += outcome.treasure or 0
        if outcome.killed:
            break
    assert enemy.health <= 0
    assert strikes >= 1
    assert session_treasure >= 1


def test_specials_coexist_in_one_run():
    rng = random.Random(7)
    player = FakeCombatant(is_player=True, health=100, max_health=100, strength=10)
    enemies = [
        FakeCombatant(enemy_type="vampire", health=30, strength=6),
        FakeCombatant(enemy_type="ogre", health=30, strength=6),
        FakeCombatant(enemy_type="snake_mage", health=30, strength=6),
    ]
    drains = 0
    sleeps = 0
    for enemy in enemies:
        first_strike = enemy.enemy_type == "vampire"
        while enemy.health > 0:
            outcome = attack_or_move(player, enemy, None, rng, first_player_strike=first_strike)
            first_strike = False
            assert isinstance(outcome, AttackResult)
            if not outcome.hit:
                continue
            enemy.health -= outcome.damage
            sleeps += 1 if outcome.effects.sleep_target else 0
            back = resolve_attack(enemy, player, None, rng, force_hit=True)
            player.health -= back.damage
            player.max_health -= back.effects.max_hp_drain
            drains += back.effects.max_hp_drain
    assert player.health > 0
    assert drains >= 1


def test_ogre_rest_and_counter_applied_by_caller():
    rng = random.Random(first_seed())
    ogre = FakeCombatant(enemy_type="ogre", health=50, strength=8)
    player = FakeCombatant(is_player=True, health=100)
    attack = resolve_attack(ogre, player, None, rng)
    assert attack.effects.rest_and_counter
    hp = player.health - attack.damage
    hp -= 1  # ход отдыха: огр пропускает ход
    counter = resolve_attack(ogre, player, None, rng, force_hit=True)
    hp -= counter.damage
    assert hp < player.health
    assert not counter.effects.rest_and_counter


def test_vampire_full_cycle_first_strike_miss_then_drain():
    rng = random.Random(first_seed())
    vampire = FakeCombatant(enemy_type="vampire", health=30, strength=6)
    player = FakeCombatant(is_player=True, health=30, max_health=30)
    outcome = attack_or_move(player, vampire, None, rng, first_player_strike=True)
    assert isinstance(outcome, AttackResult)
    assert not outcome.hit
    outcome = attack_or_move(player, vampire, None, rng)
    assert isinstance(outcome, AttackResult)
    while not outcome.hit:
        outcome = attack_or_move(player, vampire, None, rng)
        assert isinstance(outcome, AttackResult)
    assert not outcome.killed
    vampire.health -= outcome.damage
    back = resolve_attack(vampire, player, None, rng, force_hit=True)
    assert back.effects.max_hp_drain == 1
