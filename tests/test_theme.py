from domain.entities.enemy import EnemyType
from domain.entities.item import ItemType
from presentation import theme


def test_enemy_symbols_match_readme():
    assert theme.ENEMY_SYMBOLS[EnemyType.ZOMBIE] == "z"
    assert theme.ENEMY_SYMBOLS[EnemyType.VAMPIRE] == "v"
    assert theme.ENEMY_SYMBOLS[EnemyType.GHOST] == "g"
    assert theme.ENEMY_SYMBOLS[EnemyType.OGRE] == "O"
    assert theme.ENEMY_SYMBOLS[EnemyType.SNAKE_MAGE] == "s"


def test_environment_and_items_are_distinguishable():
    chars = {
        theme.SYM_PLAYER,
        theme.SYM_WALL,
        theme.SYM_FLOOR,
        theme.SYM_DOOR,
        *theme.ITEM_SYMBOLS.values(),
    }
    assert len(theme.ITEM_SYMBOLS) == len(ItemType)
    assert theme.SYM_WALL != theme.SYM_FLOOR
    assert theme.SYM_PLAYER not in theme.ITEM_SYMBOLS.values()
    assert len(chars) >= 8


def test_enemy_colors_are_defined():
    assert theme.COLOR_ZOMBIE != theme.COLOR_VAMPIRE
    assert theme.COLOR_GHOST != theme.COLOR_OGRE
    assert theme.COLOR_SNAKE_MAGE != theme.COLOR_ITEM
