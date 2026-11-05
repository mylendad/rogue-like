import pytest

from domain.entities.character import BACKPACK_CAPACITY, Backpack, Character
from domain.entities.item import Item, ItemType


def test_character_has_all_four_stats():
    character = Character()
    assert character.max_health == 10
    assert character.health == 10
    assert character.agility == 5
    assert character.strength == 5


def test_character_health_cannot_exceed_max():
    with pytest.raises(ValueError):
        Character(health=11, max_health=10)


def test_character_valid_health_accepted():
    character = Character(health=3, max_health=10)
    assert character.health == 3


def test_character_is_player():
    assert Character().is_player is True


def test_character_speed_is_derived_from_current_agility():
    character = Character()
    assert character.speed == 1
    character.agility = 10
    assert character.speed == 2


def item_of(item_type: ItemType) -> Item:
    fills: dict[ItemType, dict] = {
        ItemType.TREASURE: {"worth": 1},
        ItemType.FOOD: {"health_gain": 1},
        ItemType.ELIXIR: {"max_health_bonus": 1, "agility_bonus": 1, "strength_bonus": 1},
        ItemType.SCROLL: {"max_health_bonus": 1, "agility_bonus": 1, "strength_bonus": 1},
        ItemType.WEAPON: {"strength_bonus": 1},
    }
    return Item(item_type=item_type, subtype="тест", **fills[item_type])


def test_backpack_accepts_nine_items_of_type():
    backpack = Backpack()
    for _ in range(BACKPACK_CAPACITY):
        assert backpack.add(item_of(ItemType.SCROLL)) is True
    assert len(backpack.items_of(ItemType.SCROLL)) == BACKPACK_CAPACITY


def test_backpack_rejects_tenth_item_of_type():
    backpack = Backpack()
    for _ in range(BACKPACK_CAPACITY):
        backpack.add(item_of(ItemType.ELIXIR))
    extra = Item(
        item_type=ItemType.ELIXIR,
        subtype="тест",
        max_health_bonus=1,
        agility_bonus=1,
        strength_bonus=1,
    )
    assert backpack.add(extra) is False
    assert len(backpack.items_of(ItemType.ELIXIR)) == BACKPACK_CAPACITY


def test_backpack_types_are_independent():
    backpack = Backpack()
    for _ in range(BACKPACK_CAPACITY):
        backpack.add(item_of(ItemType.FOOD))
    assert backpack.add(item_of(ItemType.TREASURE)) is True
