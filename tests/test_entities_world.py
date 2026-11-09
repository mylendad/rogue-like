import pytest

from domain.entities.enemy import Enemy, EnemyType
from domain.entities.item import Item, ItemType
from domain.entities.world import ROOMS_PER_LEVEL, Coord, Corridor, Level, Room
from tests.doubles import chain_corridors


def make_plain_room(
    x: int, y: int, width: int = 6, height: int = 5, doors: tuple[Coord, ...] = ()
) -> Room:
    return Room(x=x, y=y, width=width, height=height, doors=doors)


def make_level_grid() -> tuple[list[Room], list[Corridor], Coord]:
    """Сетка 3x3 маленьких комнат с горизонтальными коридорами."""
    rooms: list[Room] = []
    for row in range(3):
        for col in range(3):
            x = col * 8
            y = row * 6
            doors = (Coord(x, y + 1), Coord(x + 5, y + 1))
            is_start = row == 0 and col == 0
            is_end = row == 2 and col == 2
            room = Room(x=x, y=y, width=6, height=5, doors=doors, is_start=is_start, is_end=is_end)
            rooms.append(room)
    corridors = [
        Corridor(cells=tuple(Coord(x, 1) for x in range(6, 8)), connects=(0, 1)),
        Corridor(cells=tuple(Coord(x, 13) for x in range(6, 8)), connects=(3, 4)),
        Corridor(cells=tuple(Coord(x, 19) for x in range(6, 8)), connects=(6, 7)),
    ]
    corridors += chain_corridors(rooms)
    return rooms, corridors, Coord(18, 14)


def level_factory() -> Level:
    rooms, corridors, transition = make_level_grid()
    return Level(rooms=rooms, corridors=corridors, transition=transition)


def test_room_geometry_interior_and_border_distinguishable():
    room = make_plain_room(0, 0, 6, 5)
    assert room.is_interior(Coord(1, 1))
    assert room.is_interior(Coord(4, 3))
    assert not room.is_interior(Coord(0, 0))
    assert not room.is_interior(Coord(5, 4))
    assert room.is_on_border(Coord(0, 2))
    assert not room.is_on_border(Coord(1, 1))


def test_room_requires_space_for_walls_and_floor():
    with pytest.raises(ValueError):
        make_plain_room(0, 0, 2, 5)
    with pytest.raises(ValueError):
        make_plain_room(0, 0, 6, 2)


def test_room_counts_doors_only_on_border():
    room = make_plain_room(0, 0, 6, 5, doors=(Coord(0, 2), Coord(3, 3)))
    assert room.is_door(Coord(0, 2))
    assert not room.is_door(Coord(3, 3))
    assert not room.is_door(Coord(0, 1))


def test_corridor_keeps_own_geometry():
    cells = (Coord(0, 0), Coord(1, 0), Coord(2, 0))
    corridor = Corridor(cells=cells, connects=(0, 1))
    assert corridor.is_that_corridor(Coord(1, 0))
    assert not corridor.is_that_corridor(Coord(2, 1))
    with pytest.raises(ValueError):
        Corridor(cells=(), connects=(0, 1))


def test_valid_level_is_accepted():
    level = level_factory()
    assert len(level.rooms) == ROOMS_PER_LEVEL


def test_level_rejects_wrong_room_count():
    rooms, corridors, transition = make_level_grid()
    rooms.pop()
    with pytest.raises(ValueError):
        Level(rooms=rooms, corridors=corridors, transition=transition)


def test_level_rejects_no_corridors():
    rooms, _, transition = make_level_grid()
    with pytest.raises(ValueError):
        Level(rooms=rooms, corridors=[], transition=transition)


def test_level_rejects_corridor_with_invalid_room_index():
    rooms, corridors, transition = make_level_grid()
    corridors[0] = Corridor(cells=corridors[0].cells, connects=(0, 99))
    with pytest.raises(ValueError):
        Level(rooms=rooms, corridors=corridors, transition=transition)


def test_level_rejects_corridor_connecting_room_to_itself():
    rooms, corridors, transition = make_level_grid()
    corridors[0] = Corridor(cells=corridors[0].cells, connects=(0, 0))
    with pytest.raises(ValueError):
        Level(rooms=rooms, corridors=corridors, transition=transition)


def test_level_rejects_double_start():
    rooms, corridors, transition = make_level_grid()
    rooms[5].is_start = True
    with pytest.raises(ValueError):
        Level(rooms=rooms, corridors=corridors, transition=transition)


def test_level_rejects_transition_outside_end_room():
    rooms, corridors, transition = make_level_grid()
    bad = Coord(0, 1)
    with pytest.raises(ValueError):
        Level(rooms=rooms, corridors=corridors, transition=bad)


def test_level_transitions_cell_must_be_inside_end_room_interior():
    rooms, corridors, _ = make_level_grid()
    wall_corner = Coord(16, 10)  # угол конечной комнаты (стена)
    with pytest.raises(ValueError):
        Level(rooms=rooms, corridors=corridors, transition=wall_corner)


def test_level_placements_store_entities():
    level = level_factory()
    enemy = Enemy(enemy_type=EnemyType.ZOMBIE, health=5, agility=2, strength=3)
    item = Item(item_type=ItemType.TREASURE, subtype="золото", worth=5)
    level.player_pos = Coord(1, 1)
    level.enemies[Coord(9, 1)] = enemy
    level.items[Coord(2, 2)] = item
    assert level.player_pos == Coord(1, 1)
    assert level.enemies[Coord(9, 1)] is enemy
    assert level.items[Coord(2, 2)] is item


def test_removed_enemy_is_gone_from_level():
    level = level_factory()
    enemy = Enemy(enemy_type=EnemyType.GHOST, health=5, agility=2, strength=3)
    coord = Coord(9, 1)
    level.enemies[coord] = enemy
    removed = level.remove_enemy_at(coord)
    assert removed is enemy
    assert level.remove_enemy_at(coord) is None


def test_passable_coords():
    level = level_factory()
    assert level.passable(Coord(1, 1))  # пол комнаты
    assert level.passable(Coord(0, 1))  # дверь-проём в стене
    assert level.passable(Coord(6, 1))  # клетка коридора
    assert not level.passable(Coord(0, 0))  # стена комнаты
    assert not level.passable(Coord(4, 10))  # незанятая клетка вне комнат/коридоров
