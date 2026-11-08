from domain.entities.item import ItemType
from presentation import input as keymap


def test_wasd_directions():
    assert keymap.direction_for_key(ord("w")) == (0, -1)
    assert keymap.direction_for_key(ord("a")) == (-1, 0)
    assert keymap.direction_for_key(ord("s")) == (0, 1)
    assert keymap.direction_for_key(ord("d")) == (1, 0)


def test_item_keys():
    assert keymap.item_type_for_key(ord("h")) is ItemType.WEAPON
    assert keymap.item_type_for_key(ord("j")) is ItemType.FOOD
    assert keymap.item_type_for_key(ord("k")) is ItemType.ELIXIR
    assert keymap.item_type_for_key(ord("e")) is ItemType.SCROLL


def test_item_number_keys():
    assert keymap.item_index_for_key(ord("1")) == 0
    assert keymap.item_index_for_key(ord("9")) == 8
    assert keymap.item_index_for_key(ord("0")) is None


def test_special_keys_and_unknown():
    assert keymap.MENU_KEY == ord("m")
    assert keymap.STATS_KEY == ord("t")
    assert keymap.QUIT_KEY == ord("q")
    assert keymap.CANCEL_KEY == 27
    assert keymap.direction_for_key(ord("x")) is None
    assert keymap.item_type_for_key(ord("x")) is None
