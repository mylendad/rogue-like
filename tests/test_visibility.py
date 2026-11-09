from domain.entities.world import Coord, Corridor, Level, Room
from presentation.view import VISIBILITY_RADIUS, compute_visibility
from tests.doubles import chain_corridors


def make_corridor_level() -> Level:
    rooms = [Room(0, 0, 3, 3, is_start=True)]
    rooms += [Room(30 + i * 3, 10, 3, 3) for i in range(7)]
    rooms.append(Room(20, 0, 3, 3, is_end=True))
    cells = tuple(Coord(x, 1) for x in range(2, 8))
    cells += tuple(Coord(x, 1) for x in range(9, 21))
    corridor = Corridor(cells=cells, connects=(0, 8))
    return Level(
        rooms=rooms,
        corridors=[corridor, *chain_corridors(rooms)],
        transition=Coord(21, 1),
    )


def test_room_fully_visible():
    level = make_corridor_level()
    visible = compute_visibility(level, Coord(1, 1))
    start = level.rooms[0]
    assert all(cell in visible for cell in start.all_cells())


def test_direct_corridor_cell_visible_within_radius():
    level = make_corridor_level()
    visible = compute_visibility(level, Coord(14, 1))
    assert Coord(14 + VISIBILITY_RADIUS, 1) in visible


def test_cell_beyond_radius_hidden():
    level = make_corridor_level()
    visible = compute_visibility(level, Coord(14, 1))
    assert Coord(14 + VISIBILITY_RADIUS + 1, 1) not in visible
    assert Coord(14 + VISIBILITY_RADIUS, 1) in visible


def test_wall_blocks_corridor_turn():
    level = make_corridor_level()
    visible = compute_visibility(level, Coord(5, 1))
    assert Coord(7, 1) in visible
    assert Coord(9, 1) not in visible
