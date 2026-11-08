
from domain.entities.item import Item, ItemType
from domain.entities.world import Coord, Corridor, Level, Room
from domain.entities.session import default_session


def make_level() -> Level:
    rooms = [Room(0, 0, 7, 7, is_start=True)]
    rooms += [Room(8 + i * 4, 0, 3, 3) for i in range(7)]
    rooms.append(Room(40, 0, 5, 5, is_end=True))
    corridor = Corridor(
        cells=(Coord(6, 2), Coord(7, 2), Coord(8, 2)),
        connects=(0, 1),
    )
    return Level(rooms=rooms, corridors=[corridor], transition=Coord(41, 1))


def test_food_consumption():
    session = default_session()
    session.character.health = 5
    food = Item(item_type=ItemType.FOOD, subtype="ration", health_gain=3)
    session.character.backpack.add(food)
    session.use_food(food)
    assert session.character.health == 8
    assert food not in session.character.backpack.items_of(ItemType.FOOD)
    assert session.stats.food_eaten == 1


def test_food_does_not_exceed_max_health():
    session = default_session()
    session.character.health = 9
    food = Item(item_type=ItemType.FOOD, subtype="ration", health_gain=5)
    session.character.backpack.add(food)
    session.use_food(food)
    assert session.character.health == session.character.max_health


def test_scroll_permanent_bonus():
    session = default_session()
    scroll = Item(
        item_type=ItemType.SCROLL,
        subtype="scroll_strength",
        max_health_bonus=0,
        agility_bonus=0,
        strength_bonus=2,
    )
    session.character.backpack.add(scroll)
    session.use_scroll(scroll)
    assert session.character.strength == 7
    assert scroll not in session.character.backpack.items_of(ItemType.SCROLL)
    assert session.stats.scrolls_read == 1


def test_elixir_fixed_effect():
    session = default_session()
    elixir = Item(
        item_type=ItemType.ELIXIR,
        subtype="elixir_agility",
        max_health_bonus=0,
        agility_bonus=3,
        strength_bonus=0,
    )
    session.character.backpack.add(elixir)
    session.use_elixir(elixir)
    assert session.character.agility == 8
    assert session.elixir_effects["agility"].bonus == 3
    assert elixir not in session.character.backpack.items_of(ItemType.ELIXIR)
    assert session.stats.elixirs_drunk == 1


def test_weapon_equip_and_drop():
    session = default_session()
    level = make_level()
    session.level = level
    pos = Coord(1, 1)
    session.character.pos = pos
    level.player_pos = pos
    sword1 = Item(item_type=ItemType.WEAPON, subtype="sword1", strength_bonus=2)
    sword2 = Item(item_type=ItemType.WEAPON, subtype="sword2", strength_bonus=4)
    session.character.weapon = sword1
    session.character.backpack.add(sword2)

    assert session.equip_weapon(sword2) is True
    assert session.character.weapon == sword2
    assert sword2 not in session.character.backpack.items_of(ItemType.WEAPON)
    assert sword1 in level.items.values()


def test_weapon_swap_cancelled_without_space():
    session = default_session()
    level = make_level()
    session.level = level
    pos = Coord(1, 1)
    session.character.pos = pos
    level.player_pos = pos
    for coord in (Coord(1, 2), Coord(2, 1), Coord(2, 2)):
        level.items[coord] = Item(item_type=ItemType.TREASURE, subtype="block", worth=1)
    sword1 = Item(item_type=ItemType.WEAPON, subtype="sword1", strength_bonus=2)
    sword2 = Item(item_type=ItemType.WEAPON, subtype="sword2", strength_bonus=4)
    session.character.weapon = sword1
    session.character.backpack.add(sword2)

    assert session.equip_weapon(sword2) is False
    assert session.character.weapon == sword1
    assert sword2 in session.character.backpack.items_of(ItemType.WEAPON)
