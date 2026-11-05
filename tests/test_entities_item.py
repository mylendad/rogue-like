from typing import cast

import pytest

from domain.combat.engine import Weapon, strike_damage
from domain.entities.item import REQUIRED_MODIFIERS, Item, ItemType
from tests.doubles import FakeCombatant
import random


def test_item_type_makes_exhaustive_set():
    assert {t.value for t in ItemType} == {"treasure", "food", "elixir", "scroll", "weapon"}


@pytest.mark.parametrize(
    ("item_type", "kwargs"),
    [
        (ItemType.TREASURE, {"worth": 15}),
        (ItemType.FOOD, {"health_gain": 2}),
        (ItemType.ELIXIR, {"max_health_bonus": 1, "agility_bonus": 2, "strength_bonus": 1}),
        (ItemType.SCROLL, {"max_health_bonus": 1, "agility_bonus": 1, "strength_bonus": 1}),
        (ItemType.WEAPON, {"strength_bonus": 2}),
    ],
)
def test_item_with_required_modifiers_is_created(item_type: ItemType, kwargs: dict):
    item = Item(item_type=item_type, subtype="тест", **kwargs)
    assert item.item_type is item_type
    for name in REQUIRED_MODIFIERS[item_type]:
        assert getattr(item, name) is not None


@pytest.mark.parametrize(
    ("item_type", "kwargs"),
    [
        (ItemType.TREASURE, {}),
        (ItemType.FOOD, {}),
        (ItemType.ELIXIR, {"max_health_bonus": 1, "strength_bonus": 1}),
        (ItemType.SCROLL, {"agility_bonus": 1}),
        (ItemType.WEAPON, {}),
    ],
)
def test_item_with_missing_required_modifier_is_rejected(item_type: ItemType, kwargs: dict):
    with pytest.raises(ValueError):
        Item(item_type=item_type, subtype="тест", **kwargs)


def test_item_unknown_type_is_rejected():
    with pytest.raises(ValueError):
        Item(item_type="sword", subtype="тест", worth=1)  # type: ignore[arg-type]


def test_treasure_stores_worth():
    item = Item(item_type=ItemType.TREASURE, subtype="золото", worth=100)
    assert item.worth == 100


def test_weapon_item_satisfies_combat_weapon_protocol():
    weapon = cast(Weapon, Item(item_type=ItemType.WEAPON, subtype="нож", strength_bonus=2))
    attacker = FakeCombatant(strength=4)
    with_weapon = {strike_damage(attacker, weapon, random.Random(s)) for s in range(50)}
    without = {strike_damage(attacker, None, random.Random(s)) for s in range(50)}
    assert max(with_weapon) > max(without)
