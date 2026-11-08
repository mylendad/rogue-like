"""Разбор клавиш управления (спека game-controls)."""

import curses

from domain.entities.item import ItemType

MENU_KEY = ord("m")
STATS_KEY = ord("t")
QUIT_KEY = ord("q")
CANCEL_KEY = 27


def direction_for_key(key: int) -> tuple[int, int] | None:
    if key in (ord("w"), ord("W"), curses.KEY_UP):
        return (0, -1)
    if key in (ord("s"), ord("S"), curses.KEY_DOWN):
        return (0, 1)
    if key in (ord("a"), ord("A"), curses.KEY_LEFT):
        return (-1, 0)
    if key in (ord("d"), ord("D"), curses.KEY_RIGHT):
        return (1, 0)
    return None


def item_type_for_key(key: int) -> ItemType | None:
    if key in (ord("h"), ord("H")):
        return ItemType.WEAPON
    if key in (ord("j"), ord("J")):
        return ItemType.FOOD
    if key in (ord("k"), ord("K")):
        return ItemType.ELIXIR
    if key in (ord("e"), ord("E")):
        return ItemType.SCROLL
    return None


def item_index_for_key(key: int) -> int | None:
    if ord("1") <= key <= ord("9"):
        return key - ord("1")
    return None
