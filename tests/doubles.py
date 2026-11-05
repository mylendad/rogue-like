import random
from dataclasses import dataclass

from domain.entities.world import Corridor, Room


@dataclass
class FakeWeapon:
    strength_bonus: int = 3


@dataclass
class FakeCombatant:
    is_player: bool = False
    health: int = 10
    max_health: int = 10
    agility: int = 5
    speed: int = 2
    strength: int = 6
    enemy_type: str = "zombie"
    hostility: int = 5


def chain_corridors(rooms: list[Room]) -> list[Corridor]:
    """Минимальный связный граф комнат для тестовых уровней."""
    return [
        Corridor(
            cells=(rooms[index].interior_cells()[0],),
            connects=(index, index + 1),
        )
        for index in range(len(rooms) - 1)
    ]


def first_seed(rng_seed: int = 0, want: bool = True) -> int:
    """Первый сид, при котором первый бросок random() даёт want-исход попадания."""
    from domain.combat.engine import hit_probability

    attacker = FakeCombatant(agility=5, speed=2)
    defender = FakeCombatant(agility=5, speed=2)
    probability = hit_probability(attacker, defender)
    seed = rng_seed
    for _ in range(100000):
        if (random.Random(seed).random() < probability) == want:
            return seed
        seed += 1
    raise AssertionError("seed not found")
