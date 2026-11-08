"""Игровая сессия."""

import random
from dataclasses import dataclass, field
from typing import Callable, Literal

from domain.ai.engine import decide_enemy_action
from domain.combat.engine import resolve_attack
from domain.entities.character import (
    START_AGILITY,
    START_HEALTH,
    START_MAX_HEALTH,
    START_STRENGTH,
    Backpack,
    Character,
)
from domain.entities.item import Item, ItemType
from domain.entities.world import Coord, Level
from domain.generation.config import LAST_LEVEL

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


@dataclass(frozen=True)
class RunResult:
    """Снимок результатов попытки."""

    treasures_collected: int
    reached_level: int
    enemies_defeated: int
    food_eaten: int
    elixirs_drunk: int
    scrolls_read: int
    hits_dealt: int
    missed_attacks: int
    hits_taken: int
    cells_walked: int
    success: bool


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
    run_results: list[RunResult] = field(default_factory=list)
    game_over: bool = False

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

    def use_food(self, item: Item) -> None:
        """Применяет еду: восстанавливает здоровье не выше максимума."""
        if item.item_type is not ItemType.FOOD:
            raise ValueError("предмет не является едой")
        items = self.character.backpack.items_of(ItemType.FOOD)
        if item not in items:
            raise ValueError("еда отсутствует в рюкзаке")
        gain = item.health_gain or 0
        self.character.health = min(self.character.max_health, self.character.health + gain)
        items.remove(item)
        self.record_food_eaten()

    def use_elixir(self, item: Item, attribute: ElixirAttribute | None = None) -> None:
        """Применяет один модификатор эликсира без суммирования повторов."""
        if item.item_type is not ItemType.ELIXIR:
            raise ValueError("предмет не является эликсиром")
        items = self.character.backpack.items_of(ItemType.ELIXIR)
        if item not in items:
            raise ValueError("эликсир отсутствует в рюкзаке")

        if attribute is None:
            if "max_health" in item.subtype:
                attribute = "max_health"
            elif "agility" in item.subtype:
                attribute = "agility"
            elif "strength" in item.subtype:
                attribute = "strength"
            elif (item.max_health_bonus or 0) > 0:
                attribute = "max_health"
            elif (item.agility_bonus or 0) > 0:
                attribute = "agility"
            elif (item.strength_bonus or 0) > 0:
                attribute = "strength"
            else:
                attribute = "max_health"

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

    def use_scroll(self, item: Item) -> None:
        """Применяет свиток: постоянно повышает характеристику из подтипа."""
        if item.item_type is not ItemType.SCROLL:
            raise ValueError("предмет не является свитком")
        items = self.character.backpack.items_of(ItemType.SCROLL)
        if item not in items:
            raise ValueError("свиток отсутствует в рюкзаке")

        if "max_health" in item.subtype or (item.max_health_bonus or 0) > 0:
            bonus = item.max_health_bonus or 0
            self.character.max_health += bonus
            self.character.health += bonus
        elif "agility" in item.subtype or (item.agility_bonus or 0) > 0:
            bonus = item.agility_bonus or 0
            self.character.agility += bonus
        elif "strength" in item.subtype or (item.strength_bonus or 0) > 0:
            bonus = item.strength_bonus or 0
            self.character.strength += bonus

        items.remove(item)
        self.record_scroll_read()

    def equip_weapon(self, item: Item) -> bool:
        """Сменяет текущее оружие. Старое падает на соседнюю свободную клетку."""
        if item.item_type is not ItemType.WEAPON:
            raise ValueError("предмет не является оружием")
        items = self.character.backpack.items_of(ItemType.WEAPON)
        if item not in items:
            raise ValueError("оружие отсутствует в рюкзаке")

        old_weapon = self.character.weapon
        free_coord: Coord | None = None
        if old_weapon is not None:
            if self.character.pos is None or self.level is None:
                return False
            pos = self.character.pos
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    c = Coord(pos.x + dx, pos.y + dy)
                    if (
                        self.level.passable(c)
                        and c not in self.level.enemies
                        and c not in self.level.items
                    ):
                        free_coord = c
                        break
                if free_coord is not None:
                    break
            if free_coord is None:
                return False

        if old_weapon is not None and free_coord is not None and self.level is not None:
            self.level.items[free_coord] = old_weapon

        items.remove(item)
        self.character.weapon = item
        return True

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

    def try_move_or_attack(
        self,
        dx: int,
        dy: int,
        *,
        rng: random.Random | None = None,
    ) -> bool:
        """Шагает в направлении; при встрече с врагом атакует из последней клетки.

        Возвращает True, если действие израсходовало ход.
        """
        if self.level is None or self.character.pos is None:
            return False
        if dx not in (-1, 0, 1) or dy not in (-1, 0, 1) or (dx == 0 and dy == 0):
            return False
        if rng is None:
            rng = random.Random()

        moved = False
        for _ in range(self.character.speed):
            current = self.character.pos
            if current is None:
                break
            target = Coord(current.x + dx, current.y + dy)

            enemy = self.level.enemies.get(target)
            if enemy is not None:
                result = resolve_attack(self.character, enemy, self.character.weapon, rng)
                self.record_player_attack(hit=result.hit)
                if result.hit:
                    enemy.health -= result.damage
                    if enemy.health <= 0:
                        self.level.remove_enemy_at(target)
                        self.record_enemy_defeated()
                        if result.treasure is not None:
                            self.record_treasure(result.treasure)
                return True

            if not self.level.passable(target):
                return moved

            self.character.pos = target
            self.level.player_pos = target
            self.record_walked()
            self.pick_up_item()
            moved = True

            if target == self.level.transition:
                self._advance_level()
                break

        return moved

    def _snapshot_result(self, *, success: bool) -> RunResult:
        return RunResult(
            treasures_collected=self.stats.treasures_collected,
            reached_level=self.level_number,
            enemies_defeated=self.stats.enemies_defeated,
            food_eaten=self.stats.food_eaten,
            elixirs_drunk=self.stats.elixirs_drunk,
            scrolls_read=self.stats.scrolls_read,
            hits_dealt=self.stats.hits_dealt,
            missed_attacks=self.stats.missed_attacks,
            hits_taken=self.stats.hits_taken,
            cells_walked=self.stats.cells_walked,
            success=success,
        )

    def _advance_level(self) -> None:
        if self.level_number >= LAST_LEVEL:
            self.run_results.append(self._snapshot_result(success=True))
            self.game_over = True
            self.level = None
            return
        self.level_number += 1
        self.level = None

    def perform_turn(
        self,
        player_action: Callable[[], bool | None] | None = None,
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
            if player_action() is False:
                return
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
        """Фиксирует результат и сбрасывает сессию к новой попытке."""
        self.run_results.append(self._snapshot_result(success=False))
        self.character.health = START_HEALTH
        self.character.max_health = START_MAX_HEALTH
        self.character.agility = START_AGILITY
        self.character.strength = START_STRENGTH
        self.character.pos = None
        self.character.weapon = None
        self.character.backpack = Backpack()
        self.level_number = 1
        self.level = None
        self.stats = SessionStats()
        self.sleep_turns = 0
        self.elixir_effects.clear()
        self.game_over = False


def default_session() -> GameSession:
    """Новая сессия: персонаж со стартовыми характеристиками, уровень 1."""
    character = Character(
        health=START_HEALTH,
        max_health=START_MAX_HEALTH,
        agility=START_AGILITY,
        strength=START_STRENGTH,
    )
    return GameSession(character=character)
