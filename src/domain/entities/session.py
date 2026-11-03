"""Игровая сессия (спека entities)."""

from dataclasses import dataclass, field

from domain.entities.character import (
    START_AGILITY,
    START_HEALTH,
    START_MAX_HEALTH,
    START_SPEED,
    START_STRENGTH,
    Character,
)
from domain.entities.world import Level


@dataclass
class SessionStats:
    """Совокупная статистика прохождения (спека entities)."""

    treasures_collected: int = 0
    enemies_defeated: int = 0
    food_eaten: int = 0
    elixirs_drunk: int = 0
    scrolls_read: int = 0
    hits_dealt: int = 0
    hits_taken: int = 0
    cells_walked: int = 0


@dataclass
class GameSession:
    """Сессия: уровень, персонаж, статистика. Ничего не знает об отображении."""

    character: Character
    level_number: int = 1
    level: Level | None = None
    stats: SessionStats = field(default_factory=SessionStats)
    sleep_turns: int = 0

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

    def record_hit(self, *, dealt: bool) -> None:
        if dealt:
            self.stats.hits_dealt += 1
        else:
            self.stats.hits_taken += 1

    def record_walked(self, cells: int = 1) -> None:
        self.stats.cells_walked += cells

    def tick_sleep(self) -> None:
        """Снимает усыпление (спецэффект боя) по прошествии хода."""
        if self.sleep_turns > 0:
            self.sleep_turns -= 1


def default_session() -> GameSession:
    """Новая сессия: персонаж со стартовыми характеристиками, уровень 1."""
    character = Character(
        health=START_HEALTH,
        max_health=START_MAX_HEALTH,
        agility=START_AGILITY,
        strength=START_STRENGTH,
        speed=START_SPEED,
    )
    return GameSession(character=character)
