"""Тесты комнат и коридоров генерации (design.md D3, D4; задачи 3.1, 4.1, 4.2)."""

import random

from domain.entities.world import ROOMS_PER_LEVEL
from domain.generation import generator
from domain.generation.config import ROOM_MAX, ROOM_MIN, SECTION_SIZE


def _section_bounds(index: int) -> tuple[int, int]:
    row, col = divmod(index, 3)
    return (col * SECTION_SIZE, row * SECTION_SIZE)


# 3.1: 9 комнат, не выходят за секции, размеры в константах


def test_generate_rooms_nine_rooms_within_sections() -> None:
    rooms = generator._generate_rooms(random.Random(7))
    assert len(rooms) == ROOMS_PER_LEVEL
    for index, room in enumerate(rooms):
        sx, sy = _section_bounds(index)
        assert sx <= room.x and room.x2 <= sx + SECTION_SIZE - 1
        assert sy <= room.y and room.y2 <= sy + SECTION_SIZE - 1
        assert ROOM_MIN <= room.width <= ROOM_MAX
        assert ROOM_MIN <= room.height <= ROOM_MAX


def test_generate_rooms_deterministic_per_seed() -> None:
    rooms_a = generator._generate_rooms(random.Random(42))
    rooms_b = generator._generate_rooms(random.Random(42))
    assert rooms_a == rooms_b


# 4.1: остовное дерево связывает все 9 комнат


def test_generate_corridors_connect_all_rooms() -> None:
    rooms = generator._generate_rooms(random.Random(7))
    corridors = generator._generate_corridors(rooms, random.Random(7))
    linked = {room for corridor in corridors for room in corridor.connects}
    assert linked == set(range(ROOMS_PER_LEVEL)) or linked == {0, 1, 2, 3, 4, 5, 6, 7, 8}
    for corridor in corridors:
        a, b = corridor.connects
        assert 0 <= a < 9 and 0 <= b < 9 and a != b


# 4.2: геометрия коридоров непуста и заканчивается дверьми


def test_corridor_geometry_ends_at_doors() -> None:
    rooms = generator._generate_rooms(random.Random(3))
    corridors = generator._generate_corridors(rooms, random.Random(3))
    for corridor in corridors:
        cells = corridor.cells
        assert cells
        a, b = corridor.connects
        room_a, room_b = rooms[a], rooms[b]
        assert room_a.is_door(cells[0]) or room_b.is_door(cells[0])
        assert room_a.is_door(cells[-1]) or room_b.is_door(cells[-1])
        # шаг между соседними клетками пути — по одной оси за раз
        for here, there in zip(cells, cells[1:]):
            assert abs(here.x - there.x) + abs(here.y - there.y) == 1


def test_corridors_store_only_their_own_doors() -> None:
    rooms = generator._generate_rooms(random.Random(7))
    corridors = generator._generate_corridors(rooms, random.Random(7))
    for corridor in corridors:
        a, b = corridor.connects
        assert rooms[a].is_door(corridor.cells[0])
        assert rooms[b].is_door(corridor.cells[-1])
    for room in rooms:
        for door in room.doors:
            assert room.is_on_border(door)


def test_corridors_deterministic_per_seed() -> None:
    rooms = generator._generate_rooms(random.Random(11))
    corridors_a = generator._generate_corridors(rooms, random.Random(11))
    rooms2 = generator._generate_rooms(random.Random(11))
    corridors_b = generator._generate_corridors(rooms2, random.Random(11))
    assert [(c.cells, c.connects) for c in corridors_a] == [
        (c.cells, c.connects) for c in corridors_b
    ]
