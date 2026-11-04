"""Противник (спека entities)."""

from dataclasses import dataclass
from enum import Enum


class EnemyType(str, Enum):
    """5 типов противников Rogue."""

    ZOMBIE = "zombie"
    VAMPIRE = "vampire"
    GHOST = "ghost"
    OGRE = "ogre"
    SNAKE_MAGE = "snake_mage"


ENEMY_TYPES: tuple[EnemyType, ...] = tuple(EnemyType)


@dataclass
class Enemy:
    """Противник: тип, здоровье, ловкость, сила, скорость, враждебность.

    Враждебность задаёт расстояние, с которого противник начинает
    преследовать игрока. Поля после враждебности — состояние поведения ИИ
    (первый удар игрока, сторона зигзага, видимость, ритм атаки огра).
    Значения типов совпадают с ключами реестра спецправил
    боевого движка (`domain.combat.special.SPECIAL_RULES`).
    """

    enemy_type: EnemyType
    health: int
    agility: int
    strength: int
    speed: int = 1
    hostility: int = 1
    player_has_attacked: bool = False
    pattern_side: int = 1
    visible: bool = True
    resting: bool = False
    counter_pending: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.enemy_type, EnemyType):
            raise ValueError(f"неизвестный тип противника: {self.enemy_type!r}")

    @property
    def is_player(self) -> bool:
        return False
