"""Игровой цикл и curses-обёртка (спека curses-rendering)."""

from typing import Any, Callable

import curses
import random

from domain.entities.item import Item, ItemType
from domain.entities.session import GameSession, default_session
from domain.generation.generator import generate_level
from presentation import input as keymap
from presentation.renderer import Renderer, init_colors


def _ensure_level(
    session: GameSession,
    rng: random.Random,
    level_factory: Callable[[int, random.Random], Any] = generate_level,
) -> None:
    if session.level is None and not session.game_over:
        level = level_factory(session.level_number, rng)
        session.level = level
        session.character.pos = level.player_pos
        if level.player_pos is not None:
            level.player_pos = session.character.pos


def _choose_item(
    stdscr: Any,
    renderer: Renderer,
    session: GameSession,
    item_type: ItemType,
) -> Item | None:
    items = session.character.backpack.items_of(item_type)
    if not items:
        return None
    message = ""
    while True:
        renderer.render(
            stdscr,
            session,
            mode="select_item",
            item_type=item_type,
            message=message,
        )
        key = stdscr.getch()
        if key == keymap.CANCEL_KEY:
            return None
        index = keymap.item_index_for_key(key)
        if index is None or index >= len(items):
            message = "Некорректный номер. Esc — отмена."
            continue
        return items[index]


def _apply_item(session: GameSession, item: Item) -> bool:
    if item.item_type is ItemType.FOOD:
        session.use_food(item)
    elif item.item_type is ItemType.ELIXIR:
        session.use_elixir(item)
    elif item.item_type is ItemType.SCROLL:
        session.use_scroll(item)
    elif item.item_type is ItemType.WEAPON:
        return session.equip_weapon(item)
    else:
        return False
    return True


def _confirm_quit(
    stdscr: Any,
    renderer: Renderer,
    session: GameSession,
) -> bool:
    renderer.render(stdscr, session, message="Выйти из игры? y/n")
    while True:
        key = stdscr.getch()
        if key in (ord("y"), ord("Y")):
            return True
        if key in (keymap.CANCEL_KEY, ord("n"), ord("N")):
            return False


def run(
    stdscr: Any,
    *,
    session: GameSession | None = None,
    rng: random.Random | None = None,
    renderer: Any | None = None,
    level_factory: Callable[[int, random.Random], Any] = generate_level,
    setup_curses: bool = True,
) -> None:
    if setup_curses:
        curses.curs_set(0)
        stdscr.keypad(True)
        init_colors()

    if rng is None:
        rng = random.Random()
    if session is None:
        session = default_session()
    if renderer is None:
        renderer = Renderer()
    message = ""

    _ensure_level(session, rng, level_factory)

    while True:
        _ensure_level(session, rng, level_factory)
        if session.game_over:
            break

        renderer.render(stdscr, session, message=message)
        message = ""
        key = stdscr.getch()

        if key in (curses.KEY_RESIZE,):
            continue

        direction = keymap.direction_for_key(key)
        if direction is not None:
            dx, dy = direction
            result = session.try_move_or_attack(dx, dy, rng=rng)
            if result:
                session.perform_turn(rng=rng)
            continue

        item_type = keymap.item_type_for_key(key)
        if item_type is not None:
            items = session.character.backpack.items_of(item_type)
            if not items:
                message = "Предметов этого типа нет."
                continue
            item = _choose_item(stdscr, renderer, session, item_type)
            if item is None:
                continue
            chosen: Item = item
            session.perform_turn(
                lambda: _apply_item(session, chosen),
                rng=rng,
            )
            continue

        if key == keymap.STATS_KEY:
            renderer.render(stdscr, session, mode="stats")
            while True:
                pressed = stdscr.getch()
                if pressed in (keymap.STATS_KEY, keymap.CANCEL_KEY):
                    break
            continue

        if key == keymap.MENU_KEY:
            renderer.render(stdscr, session, mode="menu")
            pressed = stdscr.getch()
            if pressed == keymap.QUIT_KEY:
                if _confirm_quit(stdscr, renderer, session):
                    return
            continue

        if key == keymap.QUIT_KEY:
            if _confirm_quit(stdscr, renderer, session):
                return
            continue

    renderer.render_final(stdscr, session)
    stdscr.getch()
