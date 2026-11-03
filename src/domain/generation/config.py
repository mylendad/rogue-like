"""Конфигурация генерации уровней (design.md D1, D3, D7).

Только данные: геометрические константы, базовые характеристики
противников, шаблоны предметов и таблица наполнения по уровням.
Число правится фазой 4 без изменения алгоритмов.
"""

from dataclasses import dataclass

from domain.entities.enemy import EnemyType

#: Сторона одной секции сетки 3x3, в клетках.
SECTION_SIZE = 20

#: Полный размер уровня — 3 секции в ряд.
LEVEL_SIZE = SECTION_SIZE * 3

#: Минимальная сторона комнаты (стены + минимум 2 клетки пола).
ROOM_MIN = 4

#: Максимальная сторона комнаты; комната не выходит за секцию и
#: оставляет «улицу» шириной 1 для коридоров вдоль границ секций.
ROOM_MAX = SECTION_SIZE - 2

#: Дополнительные рёбра поверх остовного дерева (циклы подземелья).
EXTRA_EDGES = 3

#: Лимит попыток генерации, после которого уровень не собран.
MAX_ATTEMPTS = 100

#: Самый глубокий уровень (сценарий «Полное прохождение», спека gameplay).
LAST_LEVEL = 21


@dataclass(frozen=True)
class EnemyStats:
    """Базовые характеристики противника до масштабирования по глубине."""

    health: int
    agility: int
    strength: int
    speed: int
    hostility: int


#: Базовые характеристики 5 типов противников (значения калибруются фазой 4).
ENEMY_BASE_STATS: dict[EnemyType, EnemyStats] = {
    EnemyType.ZOMBIE: EnemyStats(health=8, agility=3, strength=4, speed=1, hostility=3),
    EnemyType.VAMPIRE: EnemyStats(health=10, agility=5, strength=5, speed=2, hostility=5),
    EnemyType.GHOST: EnemyStats(health=6, agility=6, strength=3, speed=1, hostility=4),
    EnemyType.OGRE: EnemyStats(health=12, agility=2, strength=7, speed=1, hostility=3),
    EnemyType.SNAKE_MAGE: EnemyStats(health=7, agility=4, strength=4, speed=2, hostility=5),
}

#: Модификаторы предметов (design.md D7; калибруются фазой 4).
FOOD_HEALTH_GAIN = 2
ELIXIR_BONUSES: tuple[int, int, int] = (1, 1, 1)  # max_health, agility, strength
SCROLL_BONUSES: tuple[int, int, int] = (1, 1, 1)  # max_health, agility, strength
WEAPON_STRENGTH_BONUS = 2


@dataclass(frozen=True)
class LevelFill:
    """Наполнение уровня по глубине (design.md D7).

    Порядок позиционных полей: счётчики противников (зомби, вампиры,
    привидения, огры, змее-маги), множитель глубины `enemy_power`,
    счётчики полезных предметов (еда, эликсиры, свитки, оружие),
    число сокровищ и ценность одного сокровища.
    """

    zombies: int
    vampires: int
    ghosts: int
    ogres: int
    snake_mages: int
    enemy_power: float
    food: int
    elixirs: int
    scrolls: int
    weapons: int
    treasures: int
    treasure_worth: int


#: Таблица наполнения 1..21 (design.md D7; калибруется фазой 4).
LEVEL_CONTENT: dict[int, LevelFill] = {
    1: LevelFill(2, 0, 0, 0, 0, 1.0, 2, 2, 1, 1, 2, 5),
    2: LevelFill(2, 0, 0, 0, 0, 1.0, 2, 2, 1, 1, 2, 5),
    3: LevelFill(2, 0, 1, 0, 0, 1.05, 2, 1, 1, 1, 3, 6),
    4: LevelFill(2, 0, 1, 0, 0, 1.1, 1, 1, 1, 1, 3, 6),
    5: LevelFill(2, 1, 1, 0, 0, 1.15, 1, 1, 1, 1, 4, 7),
    6: LevelFill(2, 1, 1, 0, 0, 1.2, 1, 1, 1, 1, 4, 7),
    7: LevelFill(2, 1, 1, 0, 0, 1.25, 1, 1, 1, 1, 4, 8),
    8: LevelFill(2, 1, 1, 1, 0, 1.3, 1, 1, 1, 0, 5, 9),
    9: LevelFill(2, 1, 1, 1, 0, 1.35, 1, 1, 1, 0, 5, 9),
    10: LevelFill(2, 1, 2, 1, 0, 1.4, 1, 1, 0, 0, 6, 10),
    11: LevelFill(2, 1, 2, 1, 1, 1.5, 1, 1, 0, 0, 6, 12),
    12: LevelFill(2, 2, 2, 1, 1, 1.5, 1, 1, 0, 0, 7, 12),
    13: LevelFill(2, 2, 2, 1, 1, 1.6, 1, 1, 0, 0, 7, 14),
    14: LevelFill(2, 2, 2, 1, 1, 1.6, 1, 1, 0, 0, 7, 14),
    15: LevelFill(2, 2, 2, 2, 1, 1.7, 1, 1, 0, 0, 8, 16),
    16: LevelFill(2, 2, 3, 2, 1, 1.8, 1, 0, 0, 0, 8, 18),
    17: LevelFill(2, 2, 3, 2, 1, 1.8, 1, 0, 0, 0, 9, 18),
    18: LevelFill(2, 3, 3, 2, 1, 2.0, 1, 0, 0, 0, 10, 22),
    19: LevelFill(2, 3, 3, 2, 2, 2.1, 1, 0, 0, 0, 11, 26),
    20: LevelFill(2, 3, 3, 3, 2, 2.3, 1, 0, 0, 0, 12, 30),
    21: LevelFill(3, 3, 3, 3, 2, 2.5, 1, 0, 0, 0, 14, 35),
}


def level_fill(level_number: int) -> LevelFill:
    """Строка таблицы наполнения для уровня (только 1..LAST_LEVEL)."""
    try:
        return LEVEL_CONTENT[level_number]
    except KeyError:
        raise ValueError(f"номер уровня вне диапазона 1..{LAST_LEVEL}: {level_number}") from None
