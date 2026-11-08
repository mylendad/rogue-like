import random
from dataclasses import dataclass
from typing import Callable, ClassVar, Protocol, cast

from domain.combat import special


class Combatant(Protocol):
    @property
    def is_player(self) -> bool: ...

    @property
    def health(self) -> int: ...

    @property
    def agility(self) -> int: ...

    @property
    def speed(self) -> int: ...

    @property
    def strength(self) -> int: ...


class Weapon(Protocol):
    @property
    def strength_bonus(self) -> int: ...


HIT_SMOOTHING = 2


@dataclass(frozen=True)
class AttackEffects:
    sleep_target: bool = False
    max_hp_drain: int = 0
    rest_and_counter: bool = False


NO_EFFECTS = AttackEffects()


@dataclass(frozen=True)
class AttackResult:
    hit: bool
    damage: int
    killed: bool
    treasure: int | None
    effects: AttackEffects = NO_EFFECTS


@dataclass(frozen=True)
class Move:
    """Маркер перемещения. Синглтон: все вызовы возвращают один экземпляр."""

    _instance: ClassVar[object] = None

    def __new__(cls) -> "Move":
        instance = cls._instance
        if instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
        return cast(Move, instance)


MOVE = Move()


def hit_probability(attacker: Combatant, defender: Combatant) -> float:
    offence = attacker.agility + attacker.speed
    defence = defender.agility + defender.speed
    c = HIT_SMOOTHING
    return (offence + c) / (offence + defence + 2 * c)


def strike_damage(attacker: Combatant, weapon: Weapon | None, rng: random.Random) -> int:
    base = attacker.strength // 2 + (weapon.strength_bonus if weapon else 0)
    return base + rng.randint(0, max(0, base // 4))


def roll_treasure(enemy: Combatant, rng: random.Random) -> int:
    """D7: корреляция величины сокровища со сложностью побеждённого."""
    loot_power = getattr(enemy, "hostility", 0) + enemy.strength + enemy.agility + enemy.health
    low = max(1, loot_power // 2)
    return rng.randint(low, max(low, loot_power))


def resolve_attack(
    attacker: Combatant,
    defender: Combatant,
    weapon: Weapon | None,
    rng: random.Random,
    *,
    first_player_strike: bool = False,
    force_hit: bool = False,
) -> AttackResult:
    """Полный цикл удара: попадание, урон, применение.

    Движок чистый: здоровье цели вычитает вызывающий код по `result.damage`;
    `result.killed` предвычислен как `defender.health - damage <= 0`.
    Эффекты (`sleep_target`, `max_hp_drain`, `rest_and_counter`) применяет
    вызывающий код. Усыпление и дренаж относятся к цели-игроку, цепочка
    «отдых + гарантированная контратака» относится к атакующему огру и
    подавляется при `force_hit=True`, чтобы контратака не порождала новый
    цикл. Гарантированную контратаку выполняет вызывающий код повторным
    вызовом с `force_hit=True`.
    """

    def rule_of(who: Combatant) -> special.SpecialRule | None:
        return special.special_rule_for(getattr(who, "enemy_type", None))

    defender_rule = rule_of(defender)
    if attacker.is_player and defender_rule is not None and defender_rule.skip_first_hit:
        has_attacked = getattr(defender, "player_has_attacked", None)
        if first_player_strike or has_attacked is False:
            if has_attacked is False:
                setattr(defender, "player_has_attacked", True)
            return AttackResult(hit=False, damage=0, killed=False, treasure=None)

    attacker_rule = rule_of(attacker)
    if not force_hit and rng.random() >= hit_probability(attacker, defender):
        miss_effects = NO_EFFECTS
        if attacker_rule is not None and attacker_rule.rest_and_counter:
            miss_effects = AttackEffects(rest_and_counter=True)
        return AttackResult(hit=False, damage=0, killed=False, treasure=None, effects=miss_effects)

    damage = strike_damage(attacker, weapon, rng)
    killed = defender.health - damage <= 0

    sleep_target = False
    max_hp_drain = 0
    rest_and_counter = False
    if attacker_rule is not None:
        if not force_hit and attacker_rule.rest_and_counter:
            rest_and_counter = True
        if defender.is_player:
            max_hp_drain = attacker_rule.max_hp_drain
            if attacker_rule.sleep_chance > 0 and rng.random() < attacker_rule.sleep_chance:
                sleep_target = True

    treasure = None
    if killed and not defender.is_player:
        treasure = roll_treasure(defender, rng)

    return AttackResult(
        hit=True,
        damage=damage,
        killed=killed,
        treasure=treasure,
        effects=AttackEffects(
            sleep_target=sleep_target,
            max_hp_drain=max_hp_drain,
            rest_and_counter=rest_and_counter,
        ),
    )


def attack_or_move(
    player: Combatant,
    enemy: Combatant | None,
    weapon: Weapon | None,
    rng: random.Random,
    *,
    first_player_strike: bool = False,
    move_into: Callable[[], None] | None = None,
) -> AttackResult | Move:
    """D8: перемещение в направлении противника превращается в атаку.

    Наличие противника определяет вызывающий код (движок не знает сетку
    уровня): `enemy` — сущность на целевой клетке или None. При пустой
    клетке выполняется `move_into` и возвращается `Move()`.
    """
    if enemy is None:
        if move_into is not None:
            move_into()
        return MOVE
    return resolve_attack(player, enemy, weapon, rng, first_player_strike=first_player_strike)
