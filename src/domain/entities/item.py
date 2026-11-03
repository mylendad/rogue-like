"""Предмет (спека entities)."""

from dataclasses import dataclass
from enum import Enum


class ItemType(str, Enum):
    """Типы предметов Rogue: сокровище, еда, эликсир, свиток, оружие."""

    TREASURE = "treasure"
    FOOD = "food"
    ELIXIR = "elixir"
    SCROLL = "scroll"
    WEAPON = "weapon"


#: Модификаторы, обязательные (заполненные) для каждого типа предмета.
REQUIRED_MODIFIERS: dict[ItemType, tuple[str, ...]] = {
    ItemType.TREASURE: ("worth",),
    ItemType.FOOD: ("health_gain",),
    ItemType.ELIXIR: ("max_health_bonus", "agility_bonus", "strength_bonus"),
    ItemType.SCROLL: ("max_health_bonus", "agility_bonus", "strength_bonus"),
    ItemType.WEAPON: ("strength_bonus",),
}


@dataclass
class Item:
    """Предмет: тип, подтип и применимые модификаторы (спека entities).

    Модификаторы, неприменимые к типу, игнорируются (передавать их
    бессмысленно, но допустимо — они не проверяются). Совместимость с
    боевым движком: предмет типа «оружие» удовлетворяет протоколу
    `Weapon` через поле `strength_bonus`.
    """

    item_type: ItemType
    subtype: str
    health_gain: int | None = None
    max_health_bonus: int | None = None
    agility_bonus: int | None = None
    strength_bonus: int | None = None
    worth: int | None = None

    def __post_init__(self) -> None:
        try:
            required = REQUIRED_MODIFIERS[self.item_type]
        except KeyError:
            raise ValueError(f"неизвестный тип предмета: {self.item_type!r}") from None
        for name in required:
            if getattr(self, name) is None:
                raise ValueError(f"для типа {self.item_type.value} не заполнен модификатор {name}")
