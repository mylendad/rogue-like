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


def test_auto_pickup_on_move():
    session = default_session()
    level = make_level()
    session.level = level
    pos = Coord(1, 1)
    session.character.pos = pos
    level.player_pos = pos

    item = Item(item_type=ItemType.TREASURE, subtype="gem", worth=10)
    level.items[Coord(2, 1)] = item

    assert session.try_move_or_attack(1, 0) is True
    assert Coord(2, 1) not in level.items
    assert item in session.character.backpack.items_of(ItemType.TREASURE)
    assert session.character.pos == Coord(2, 1)


def test_full_backpack_pickup_keeps_item_and_counts_move():
    session = default_session()
    level = make_level()
    session.level = level
    pos = Coord(1, 1)
    session.character.pos = pos
    level.player_pos = pos

    for i in range(9):
        session.character.backpack.add(
            Item(item_type=ItemType.TREASURE, subtype=f"gem{i}", worth=1)
        )

    item = Item(item_type=ItemType.TREASURE, subtype="extra", worth=10)
    level.items[Coord(2, 1)] = item

    assert session.try_move_or_attack(1, 0) is True
    assert Coord(2, 1) in level.items
    assert item not in session.character.backpack.items_of(ItemType.TREASURE)
    assert session.character.pos == Coord(2, 1)
    assert session.stats.cells_walked == 1
