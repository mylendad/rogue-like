"""Отрисовка игрового поля, интерфейса (HUD), меню и статистики в curses."""

from typing import Any

import curses
from domain.entities.enemy import EnemyType
from domain.entities.item import ItemType
from domain.entities.session import GameSession
from domain.entities.world import Coord
from presentation.theme import (
    COLOR_FLOOR,
    COLOR_GHOST,
    COLOR_HUD,
    COLOR_ITEM,
    COLOR_OGRE,
    COLOR_PLAYER,
    COLOR_SNAKE_MAGE,
    COLOR_VAMPIRE,
    COLOR_WALL,
    COLOR_ZOMBIE,
    ENEMY_SYMBOLS,
    ITEM_SYMBOLS,
    SYM_DOOR,
    SYM_FLOOR,
    SYM_PLAYER,
    SYM_WALL,
)
from presentation.view import compute_visibility

MIN_HEIGHT = 20
MIN_WIDTH = 60


def init_colors() -> None:
    """Инициализация цветовых пар curses."""
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(COLOR_PLAYER, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_ZOMBIE, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_VAMPIRE, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_GHOST, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_OGRE, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_SNAKE_MAGE, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_ITEM, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_WALL, curses.COLOR_BLUE, -1)
    curses.init_pair(COLOR_FLOOR, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_HUD, curses.COLOR_CYAN, -1)


class Renderer:
    def __init__(self) -> None:
        self.visited_rooms: set[int] = set()
        self._level: object | None = None

    def render(
        self,
        stdscr: Any,
        session: GameSession,
        *,
        mode: str = "game",
        item_type: ItemType | None = None,
        message: str = "",
    ) -> None:
        stdscr.erase()
        max_h, max_w = stdscr.getmaxyx()

        if max_h < MIN_HEIGHT or max_w < MIN_WIDTH:
            msg = "Терминал слишком мал! Увеличьте окно."
            try:
                stdscr.addstr(max_h // 2, max(0, (max_w - len(msg)) // 2), msg)
            except curses.error:
                pass
            stdscr.refresh()
            return

        level = session.level
        player = session.character
        player_pos = player.pos or Coord(0, 0)

        if level is not None:
            if level is not self._level:
                self._level = level
                self.visited_rooms.clear()

            # Обновить посещённые комнаты
            for idx, room in enumerate(level.rooms):
                if room.contains(player_pos):
                    self.visited_rooms.add(idx)

            visible_coords = compute_visibility(level, player_pos)

            # Расчёт видимой области камеры
            hud_height = 4
            view_h = max_h - hud_height
            view_w = max_w

            cam_x = max(0, min(level.width - view_w, player_pos.x - view_w // 2))
            cam_y = max(0, min(level.height - view_h, player_pos.y - view_h // 2))

            for y in range(view_h):
                map_y = cam_y + y
                if map_y >= level.height:
                    break
                for x in range(view_w):
                    map_x = cam_x + x
                    if map_x >= level.width:
                        break

                    coord = Coord(map_x, map_y)
                    ch = " "
                    color = 0

                    if coord in visible_coords:
                        if coord == player_pos:
                            ch = SYM_PLAYER
                            color = curses.color_pair(COLOR_PLAYER)
                        elif coord in level.enemies:
                            enemy = level.enemies[coord]
                            # Пропустить невидимое привидение вне боя
                            if enemy.enemy_type == EnemyType.GHOST and not enemy.visible:
                                ch = SYM_FLOOR
                                color = curses.color_pair(COLOR_FLOOR)
                            else:
                                ch = ENEMY_SYMBOLS.get(enemy.enemy_type, "E")
                                color = self._enemy_color(enemy.enemy_type)
                        elif coord in level.items:
                            item = level.items[coord]
                            ch = ITEM_SYMBOLS.get(item.item_type, "*")
                            color = curses.color_pair(COLOR_ITEM)
                        elif coord == level.transition:
                            ch = ">"
                            color = curses.color_pair(COLOR_PLAYER)
                        else:
                            is_door = False
                            is_wall = False
                            for room in level.rooms:
                                if room.contains(coord):
                                    is_door = room.is_door(coord)
                                    is_wall = room.is_on_border(coord) and not is_door
                                    break
                            if is_door:
                                ch = SYM_DOOR
                                color = curses.color_pair(COLOR_WALL)
                            elif is_wall:
                                ch = SYM_WALL
                                color = curses.color_pair(COLOR_WALL)
                            elif level.passable(coord):
                                ch = SYM_FLOOR
                                color = curses.color_pair(COLOR_FLOOR)

                    else:
                        # Проверить, относится ли клетка к посещённой комнате (только стены!)
                        for idx, room in enumerate(level.rooms):
                            if idx in self.visited_rooms and room.contains(coord):
                                if room.is_on_border(coord):
                                    ch = SYM_WALL
                                    color = curses.color_pair(COLOR_WALL)
                                break

                    try:
                        stdscr.addch(y, x, ch, color)
                    except curses.error:
                        pass

        # Отрисовка HUD
        self._render_hud(stdscr, session, max_h, max_w, message)

        # Отрисовка оверлеев
        if mode == "menu":
            self._render_menu(stdscr, max_h, max_w)
        elif mode == "stats":
            self._render_stats(stdscr, session, max_h, max_w)
        elif mode == "select_item" and item_type is not None:
            self._render_item_select(stdscr, session, item_type, max_h, max_w)

        stdscr.refresh()

    def _enemy_color(self, enemy_type: EnemyType) -> int:
        mapping = {
            EnemyType.ZOMBIE: COLOR_ZOMBIE,
            EnemyType.VAMPIRE: COLOR_VAMPIRE,
            EnemyType.GHOST: COLOR_GHOST,
            EnemyType.OGRE: COLOR_OGRE,
            EnemyType.SNAKE_MAGE: COLOR_SNAKE_MAGE,
        }
        return curses.color_pair(mapping.get(enemy_type, COLOR_FLOOR))

    def _render_hud(
        self,
        stdscr: Any,
        session: GameSession,
        max_h: int,
        max_w: int,
        message: str,
    ) -> None:
        p = session.character
        hud_start_y = max_h - 4
        try:
            line1 = f"Level: {session.level_number} | HP: {p.health}/{p.max_health} | Agility: {p.agility} | Strength: {p.strength} | Treasures: {session.stats.treasures_collected}"
            stdscr.addstr(hud_start_y, 0, line1[: max_w - 1], curses.color_pair(COLOR_HUD))

            bp = p.backpack
            food_count = len(bp.items_of(ItemType.FOOD))
            elixir_count = len(bp.items_of(ItemType.ELIXIR))
            scroll_count = len(bp.items_of(ItemType.SCROLL))
            weapon_count = len(bp.items_of(ItemType.WEAPON))
            line2 = f"Backpack: Food:{food_count} Elixirs:{elixir_count} Scrolls:{scroll_count} Weapons:{weapon_count}"
            stdscr.addstr(hud_start_y + 1, 0, line2[: max_w - 1], curses.color_pair(COLOR_HUD))

            w_name = p.weapon.subtype if p.weapon else "None"
            line3 = f"Equipped Weapon: {w_name} | {message}"
            stdscr.addstr(hud_start_y + 2, 0, line3[: max_w - 1], curses.color_pair(COLOR_HUD))
        except curses.error:
            pass

    def _render_menu(self, stdscr: Any, max_h: int, max_w: int) -> None:
        lines = [
            "=== МЕНЮ ИГРЫ ===",
            "WASD - Движение / Атака",
            "h - Надеть оружие",
            "j - Съесть еду",
            "k - Выпить эликсир",
            "e - Прочитать свиток",
            "t - Статистика попыток",
            "Esc / q - Выход",
            " ",
            "Нажмите любую клавишу для продолжения...",
        ]
        start_y = max(0, (max_h - len(lines)) // 2)
        for i, line in enumerate(lines):
            try:
                start_x = max(0, (max_w - len(line)) // 2)
                stdscr.addstr(start_y + i, start_x, line, curses.A_BOLD)
            except curses.error:
                pass

    def _render_item_select(
        self,
        stdscr: Any,
        session: GameSession,
        item_type: ItemType,
        max_h: int,
        max_w: int,
    ) -> None:
        items = session.character.backpack.items_of(item_type)
        type_names = {
            ItemType.WEAPON: "Оружие",
            ItemType.FOOD: "Еда",
            ItemType.ELIXIR: "Эликсиры",
            ItemType.SCROLL: "Свитки",
        }
        title = f"=== Выберите {type_names.get(item_type, 'предмет')} (1-{len(items)}) ==="
        lines = [title]
        if not items:
            lines.append("Рюкзак пуст!")
        else:
            for idx, item in enumerate(items, 1):
                lines.append(f"{idx}. {item.subtype}")
        lines.append("Esc - Отмена")

        start_y = max(0, (max_h - len(lines)) // 2)
        for i, line in enumerate(lines):
            try:
                start_x = max(0, (max_w - len(line)) // 2)
                stdscr.addstr(start_y + i, start_x, line, curses.A_BOLD)
            except curses.error:
                pass

    def _render_stats(
        self,
        stdscr: Any,
        session: GameSession,
        max_h: int,
        max_w: int,
    ) -> None:
        lines = [
            "=== ТАБЛИЦА РЕКОРДОВ И СТАТИСТИКА ПОПЫТОК ===",
            "  Сокровища | Уровень | Убито | Еда | Эликсиры | Свитки | Удары (попал/промах/урон)",
            "-" * 75,
        ]
        sorted_results = sorted(session.run_results, key=lambda r: r.treasures_collected, reverse=True)
        if not sorted_results:
            lines.append("  Нет завершённых попыток.")
        else:
            for r in sorted_results[:10]:
                status = "Успех" if r.success else "Смерть"
                row = f"  {r.treasures_collected:9d} | {r.reached_level:7d} | {r.enemies_defeated:5d} | {r.food_eaten:3d} | {r.elixirs_drunk:8d} | {r.scrolls_read:6d} | {r.hits_dealt}/{r.missed_attacks}/{r.hits_taken} ({status})"
                lines.append(row)
        lines.append(" ")
        lines.append("Нажмите t или Esc для возврата в игру")

        start_y = max(0, (max_h - len(lines)) // 2)
        for i, line in enumerate(lines):
            try:
                start_x = max(0, (max_w - len(line)) // 2)
                stdscr.addstr(start_y + i, start_x, line[: max_w - 1])
            except curses.error:
                pass

    def render_final(
        self,
        stdscr: Any,
        session: GameSession,
    ) -> None:
        stdscr.erase()
        max_h, max_w = stdscr.getmaxyx()
        lines = [
            "=== ПОДЗЕМЕЛЬЕ ПРОЙДЕНО! ===",
            "",
            f"Собрано сокровищ: {session.stats.treasures_collected}",
            f"Побеждено противников: {session.stats.enemies_defeated}",
            "",
            "Нажмите любую клавишу для выхода.",
        ]
        start_y = max(0, (max_h - len(lines)) // 2)
        for i, line in enumerate(lines):
            try:
                start_x = max(0, (max_w - len(line)) // 2)
                stdscr.addstr(start_y + i, start_x, line, curses.A_BOLD)
            except curses.error:
                pass
        stdscr.refresh()
