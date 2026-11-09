"""Доменный словарь игры.

Сессия (`domain.entities.session`) не переэкспортируется здесь: она
оркестрирует ИИ (`domain.ai.engine`), и её эагер-импорт создаёт цикл
ai.engine → entities → session → ai.engine.
"""

from domain.entities.character import BACKPACK_CAPACITY, Backpack, Character
from domain.entities.enemy import ENEMY_TYPES, Enemy, EnemyType
from domain.entities.item import REQUIRED_MODIFIERS, Item, ItemType
from domain.entities.world import ROOMS_PER_LEVEL, Coord, Corridor, Level, Room

__all__ = [
    "BACKPACK_CAPACITY",
    "ENEMY_TYPES",
    "ROOMS_PER_LEVEL",
    "Backpack",
    "Character",
    "Coord",
    "Corridor",
    "Enemy",
    "EnemyType",
    "Item",
    "ItemType",
    "Level",
    "REQUIRED_MODIFIERS",
    "Room",
]
