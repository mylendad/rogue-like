"""Тема и символы/цвета для curses-рендеринга."""

from domain.entities.enemy import EnemyType
from domain.entities.item import ItemType

# Обозначения символов
SYM_PLAYER = "@"
SYM_WALL = "#"
SYM_FLOOR = "."
SYM_CORRIDOR = "."
SYM_DOOR = "+"

ENEMY_SYMBOLS = {
    EnemyType.ZOMBIE: "z",
    EnemyType.VAMPIRE: "v",
    EnemyType.GHOST: "g",
    EnemyType.OGRE: "O",
    EnemyType.SNAKE_MAGE: "s",
}

ITEM_SYMBOLS = {
    ItemType.TREASURE: "$",
    ItemType.FOOD: "%",
    ItemType.ELIXIR: "!",
    ItemType.SCROLL: "?",
    ItemType.WEAPON: "/",
}

# Цветовые пары (будут инициализированы в renderer)
COLOR_PLAYER = 1
COLOR_ZOMBIE = 2
COLOR_VAMPIRE = 3
COLOR_GHOST = 4
COLOR_OGRE = 5
COLOR_SNAKE_MAGE = 6
COLOR_ITEM = 7
COLOR_WALL = 8
COLOR_FLOOR = 9
COLOR_HUD = 10
