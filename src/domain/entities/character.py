"""Персонаж и рюкзак (спека entities)."""

from dataclasses import dataclass, field

from domain.entities.item import Item, ItemType

START_HEALTH = 10
START_MAX_HEALTH = 10
START_AGILITY = 5
START_STRENGTH = 5

BACKPACK_CAPACITY = 9


@dataclass
class Character:
    """Персонаж: здоровье, макс. здоровье, ловкость, сила (спека entities).

    Скорость не названа в спеке `entities`, но требуется протоколом
    `Combatant` боевого движка (формула попадания использует скорость
    обеих сторон); значение по умолчанию задаётся здесь.
    """

    health: int = START_HEALTH
    max_health: int = START_MAX_HEALTH
    agility: int = START_AGILITY
    strength: int = START_STRENGTH
    speed: int = 1
    backpack: "Backpack" = field(default_factory=lambda: Backpack())

    def __post_init__(self) -> None:
        if self.health > self.max_health:
            raise ValueError("health не может превышать max_health")

    @property
    def is_player(self) -> bool:
        return True


@dataclass
class Backpack:
    """Рюкзак: до 9 предметов каждого типа (спека entities)."""

    items_by_type: dict[ItemType, list[Item]] = field(default_factory=dict)

    def add(self, item: Item) -> bool:
        basket = self.items_by_type.setdefault(item.item_type, [])
        if len(basket) >= BACKPACK_CAPACITY:
            return False
        basket.append(item)
        return True

    def items_of(self, item_type: ItemType) -> list[Item]:
        return self.items_by_type.get(item_type, [])
