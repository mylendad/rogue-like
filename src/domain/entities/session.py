"""Игровая сессия."""

import random
from dataclasses import dataclass, field
from typing import Callable, Literal

from domain.ai.engine import decide_enemy_action
from domain.entities.character import (
    START_AGILITY,
    START_HEALTH,
    START_MAX_HEALTH,
    START_STRENGTH,
    Character,
)
from domain.entities.item import Item, ItemType
from domain.entities.world import Coord, Level

ELIXIR_DURATION = 10
ElixirAttribute = Literal["max_health", "agility", "strength"]


@dataclass
class SessionStats:
    """Совокупная статистика прохождения."""

    treasures_collected: int = 0
    enemies_defeated: int = 0
    food_eaten: int = 0
    elixirs_drunk: int = 0
    scrolls_read: int = 0
    hits_dealt: int = 0
    missed_attacks: int = 0
    hits_taken: int = 0
    cells_walked: int = 0


@dataclass
class ElixirEffect:
    bonus: int
    remaining_turns: int


@dataclass
class GameSession:
    """Сессия: уровень, персонаж, статистика. Ничего не знает об отображении."""

    character: Character
    level_number: int = 1
    level: Level | None = None
    stats: SessionStats = field(default_factory=SessionStats)
    sleep_turns: int = 0
    elixir_effects: dict[str, ElixirEffect] = field(default_factory=dict)

    def record_treasure(self, amount: int) -> None:
        self.stats.treasures_collected += amount

    def record_enemy_defeated(self) -> None:
        self.stats.enemies_defeated += 1

    def record_food_eaten(self) -> None:
        self.stats.food_eaten += 1

    def record_elixir_drunk(self) -> None:
        self.stats.elixirs_drunk += 1

    def record_scroll_read(self) -> None:
        self.stats.scrolls_read += 1

    def record_player_attack(self, *, hit: bool) -> None:
        if hit:
            self.stats.hits_dealt += 1
        else:
            self.stats.missed_attacks += 1

    def record_hit_taken(self) -> None:
        self.stats.hits_taken += 1

    def record_walked(self, cells: int = 1) -> None:
        self.stats.cells_walked += cells

    def tick_sleep(self) -> None:
        """Снимает усыпление (спецэффект боя) по прошествии хода."""
        if self.sleep_turns > 0:
            self.sleep_turns -= 1

    def use_elixir(self, item: Item, attribute: ElixirAttribute) -> None:
        """Применяет один модификатор эликсира без суммирования повторов."""
        if item.item_type is not ItemType.ELIXIR:
            raise ValueError("предмет не является эликсиром")
        items = self.character.backpack.items_of(ItemType.ELIXIR)
        if item not in items:
            raise ValueError("эликсир отсутствует в рюкзаке")
        bonus = getattr(item, f"{attribute}_bonus")
        if bonus is None:
            raise ValueError(f"эликсир не изменяет {attribute}")

        effect = self.elixir_effects.get(attribute)
        if effect is None:
            setattr(self.character, attribute, getattr(self.character, attribute) + bonus)
            self.elixir_effects[attribute] = ElixirEffect(bonus, ELIXIR_DURATION)
        else:
            effect.remaining_turns += ELIXIR_DURATION
        items.remove(item)
        self.record_elixir_drunk()

    def _tick_elixirs(self) -> None:
        for attribute, effect in list(self.elixir_effects.items()):
            effect.remaining_turns -= 1
            if effect.remaining_turns > 0:
                continue
            value = getattr(self.character, attribute) - effect.bonus
            setattr(self.character, attribute, value)
            if attribute == "max_health":
                self.character.health = min(self.character.health, value)
            del self.elixir_effects[attribute]

    def pick_up_item(self) -> bool:
        """Подбирает предмет под персонажем, оставляя его на карте при отказе."""
        if self.level is None or self.character.pos is None:
            return False
        item = self.level.items.get(self.character.pos)
        if item is None or not self.character.backpack.add(item):
            return False
        del self.level.items[self.character.pos]
        return True

    def try_move(self, new_pos: Coord) -> None:
        """Перемещает персонажа на расстояние не больше его скорости."""
        if self.level is None:
            return
        start = self.character.pos
        distance = 1
        if start is None:
            if not self.level.passable(new_pos):
                return
        else:
            dx, dy = new_pos.x - start.x, new_pos.y - start.y
            if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                return
            distance = max(abs(dx), abs(dy))
            if distance == 0 or distance > self.character.speed:
                return
            step_x, step_y = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
            for step in range(1, distance + 1):
                coord = Coord(start.x + step_x * step, start.y + step_y * step)
                if not self.level.passable(coord):
                    return

        self.character.pos = new_pos
        self.level.player_pos = new_pos
        self.pick_up_item()
        if new_pos == self.level.transition:
            self._advance_level()
        self.record_walked(distance)

    def _advance_level(self) -> None:
        self.level_number += 1
        self.level = None

    def perform_turn(
        self,
        player_action: Callable[[], None] | None = None,
        *,
        rng: random.Random | None = None,
    ) -> None:
        """Выполняет действие игрока, ходы врагов и завершает полный ход."""
        if self.level is None or self.character.health <= 0:
            return
        if rng is None:
            rng = random.Random()

        sleeping = self.sleep_turns > 0
        if not sleeping and player_action is not None:
            player_action()
        if self.level is not None and self.character.health > 0:
            for coord, enemy in list(self.level.enemies.items()):
                result = decide_enemy_action(self.level, enemy, coord, rng, player=self.character)
                if result is not None and result.hit:
                    self.character.health -= result.damage
                    self.record_hit_taken()
                    if result.effects.max_hp_drain:
                        self.character.max_health -= result.effects.max_hp_drain
                        self.character.health = min(
                            self.character.health, self.character.max_health
                        )
                    if result.effects.sleep_target:
                        self.sleep_turns += 1
                    if self.character.health <= 0:
                        break
        if sleeping:
            self.tick_sleep()
        self._tick_elixirs()

        if self.character.health <= 0:
            self._handle_death()

    def _handle_death(self) -> None:
        """Сброс сессии к новой (по спеке gameplay)."""
        self.character.health = START_HEALTH
        self.character.max_health = START_MAX_HEALTH
        self.character.agility = START_AGILITY
        self.character.strength = START_STRENGTH
        self.level_number = 1
        self.level = None
        self.stats = SessionStats()
        self.sleep_turns = 0
        self.elixir_effects.clear()


def default_session() -> GameSession:
    """Новая сессия: персонаж со стартовыми характеристиками, уровень 1."""
    character = Character(
        health=START_HEALTH,
        max_health=START_MAX_HEALTH,
        agility=START_AGILITY,
        strength=START_STRENGTH,
    )
    return GameSession(character=character)
