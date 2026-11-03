"""Генератор уровней по спеке level-generation (design.md D3-D6, D9).

Секции 3x3 со случайными комнатами, корridorный граф со случайным
остовным деревом и L-образной геометрией, стартовая/конечная комната,
проверка связности с регенерацией.
"""

import random

from domain.entities.world import Corridor, Coord, Level, Room
from domain.generation import config
from domain.generation.population import GenerationError, populate

MAX_ATTEMPTS = config.MAX_ATTEMPTS


def generate_level(level_number: int, rng: random.Random) -> Level:
    """Новый уровень с наполнением по глубине (сцены спеки level-generation)."""
    fill = config.level_fill(level_number)
    for _ in range(MAX_ATTEMPTS):
        level = _build_attempt(fill, rng)
        if level is not None:
            return level
    raise GenerationError(
        f"не удалось собрать связный уровень за {MAX_ATTEMPTS} попыток"
    )


def _build_attempt(fill: config.LevelFill, rng: random.Random) -> Level | None:
    """Одна попытка генерации; None — попытка не прошла проверку связности."""
    rooms = _generate_rooms(rng)
    start_room, end_room = _pick_start_and_end(rooms, rng)
    spawn = _random_interior(start_room, rng)
    transition = _random_interior(end_room, rng)
    corridors = _generate_corridors(rooms, rng)
    level = Level(
        rooms=rooms,
        corridors=corridors,
        transition=transition,
        player_pos=spawn,
        enemies={},
        items={},
    )
    if not _connected(level, spawn, transition):
        return None
    enemies, items = populate(
        rooms, fill, player_pos=spawn, transition=transition, rng=rng
    )
    level.enemies = enemies
    level.items = items
    return level


def _generate_rooms(rng: random.Random) -> list[Room]:
    """По комнате в каждой из 9 секций, размер/положение через rng (D3).

    Секционная сетка 3x3 построчная: индекс секции = row * 3 + col.
    """
    rooms: list[Room] = []
    for index in range(9):
        row, col = divmod(index, 3)
        section_x = col * config.SECTION_SIZE
        section_y = row * config.SECTION_SIZE
        width = rng.randint(config.ROOM_MIN, config.ROOM_MAX)
        height = rng.randint(config.ROOM_MIN, config.ROOM_MAX)
        x = rng.randint(section_x + 1, section_x + config.SECTION_SIZE - 1 - width)
        y = rng.randint(section_y + 1, section_y + config.SECTION_SIZE - 1 - height)
        rooms.append(Room(x=x, y=y, width=width, height=height))
    return rooms


def _pick_start_and_end(
    rooms: list[Room], rng: random.Random
) -> tuple[Room, Room]:
    """Ровно одна стартовая и одна конечная комната (сцена «Точки входа»)."""
    indices = rng.sample(range(9), k=2)
    start_room = rooms[indices[0]]
    end_room = rooms[indices[1]]
    start_room.is_start = True
    end_room.is_end = True
    return start_room, end_room


def _random_interior(room: Room, rng: random.Random) -> Coord:
    interior = room.interior_cells()
    return rng.choice(interior)


def _room_neighbours() -> list[tuple[int, int]]:
    """Пары соседних секций сетки 3x3 (горизонталь и вертикаль)."""
    pairs: list[tuple[int, int]] = []
    for row in range(3):
        for col in range(3):
            here = row * 3 + col
            if col < 2:
                pairs.append((here, here + 1))
            if row < 2:
                pairs.append((here, here + 3))
    return pairs


def _generate_corridors(rooms: list[Room], rng: random.Random) -> list[Corridor]:
    """Случайный остов + дополнительные рёбра, геометрия по D4."""
    graph = _room_neighbours()
    tree = _spanning_tree(graph, rng)
    unused = [edge for edge in graph if edge not in tree]
    extra = rng.sample(unused, k=min(config.EXTRA_EDGES, len(unused)))
    corridors: list[Corridor] = []
    for a_index, b_index in sorted(tree | set(extra)):
        first, second = rooms[a_index], rooms[b_index]
        doors, cells = _corridor_geometry(first, second, rng)
        first.doors = tuple(set(first.doors) | set(doors))
        second.doors = tuple(set(second.doors) | set(doors))
        corridors.append(Corridor(cells=tuple(cells), connects=(a_index, b_index)))
    return corridors


def _spanning_tree(
    graph: list[tuple[int, int]], rng: random.Random
) -> set[tuple[int, int]]:
    """Перебор ребер случайного остовного дерева (Prim, D4)."""
    visited = {0}
    spanning: set[tuple[int, int]] = set()
    frontier = [edge for edge in graph if edge[0] in visited or edge[1] in visited]
    while len(visited) < 9:
        edge = rng.choice(frontier)
        a, b = sorted(edge)
        if a in visited and b in visited:
            frontier.remove(edge)
            continue
        spanning.add((a, b))
        frontier.remove(edge)
        visited.add(b if a in visited else a)
        frontier = [
            candidate
            for candidate in graph
            if candidate not in spanning
            and (candidate[0] in visited or candidate[1] in visited)
        ]
    return spanning


def _corridor_geometry(
    first: Room, second: Room, rng: random.Random
) -> tuple[tuple[Coord, Coord], list[Coord]]:
    """Двери и клетки коридора между соседними секциями (D4).

    Л-трасса идёт по «улице» вдоль границ секций: комнаты стоят в
    отступе от границ секций, поэтому трасса не пересекает чужие
    стены; конец пути — дверной проём в стене второй комнаты.
    """
    if second.x > first.x:  # вторая комната восточнее
        door_first = Coord(first.x2, rng.randint(first.y + 1, first.y2 - 1))
        door_second = Coord(second.x, rng.randint(second.y + 1, second.y2 - 1))
        corner = Coord(door_second.x - 1, door_first.y)
        cells = _straight(door_first, corner)
        cells += _straight(corner, Coord(door_second.x - 1, door_second.y))[1:]
        cells.append(door_second)
        return (door_first, door_second), cells
    if second.x < first.x:  # вторая комната западнее
        door_first = Coord(first.x, rng.randint(first.y + 1, first.y2 - 1))
        door_second = Coord(second.x2, rng.randint(second.y + 1, second.y2 - 1))
        corner = Coord(door_second.x + 1, door_first.y)
        cells = _straight(door_first, corner)
        cells += _straight(corner, Coord(door_second.x + 1, door_second.y))[1:]
        cells.append(door_second)
        return (door_first, door_second), cells
    if second.y > first.y:  # вторая комната южнее
        door_first = Coord(rng.randint(first.x + 1, first.x2 - 1), first.y2)
        door_second = Coord(rng.randint(second.x + 1, second.x2 - 1), second.y)
        corner = Coord(door_first.x, door_second.y - 1)
        cells = _straight(door_first, corner)
        cells += _straight(corner, Coord(door_second.x, door_second.y - 1))[1:]
        cells.append(door_second)
        return (door_first, door_second), cells
    door_first = Coord(rng.randint(first.x + 1, first.x2 - 1), first.y)
    door_second = Coord(rng.randint(second.x + 1, second.x2 - 1), second.y2)
    corner = Coord(door_first.x, door_second.y + 1)
    cells = _straight(door_first, corner)
    cells += _straight(corner, Coord(door_second.x, door_second.y + 1))[1:]
    cells.append(door_second)
    return (door_first, door_second), cells


def _straight(from_coord: Coord, to_coord: Coord) -> list[Coord]:
    """Горизонтальный или вертикальный отрезок, концы включительно."""
    if from_coord.y == to_coord.y:
        step = 1 if to_coord.x >= from_coord.x else -1
        return [Coord(x, from_coord.y) for x in range(from_coord.x, to_coord.x + step, step)]
    if from_coord.x == to_coord.x:
        step = 1 if to_coord.y >= from_coord.y else -1
        return [Coord(from_coord.x, y) for y in range(from_coord.y, to_coord.y + step, step)]
    return []


def _connected(level: Level, spawn: Coord, transition: Coord) -> bool:
    """BFS по проходимым клеткам: интерьеры всех комнат + переход (D5)."""
    targets = {transition}
    for room in level.rooms:
        targets.add(room.interior_cells()[0])
    seen = {spawn}
    front = [spawn]
    while front and targets:
        nxt = []
        for here in front:
            targets.discard(here)
            for x, y in ((here.x + 1, here.y), (here.x - 1, here.y), (here.x, here.y + 1), (here.x, here.y - 1)):
                neighbour = Coord(x, y)
                if neighbour not in seen and level.passable(neighbour):
                    seen.add(neighbour)
                    nxt.append(neighbour)
        front = nxt
    return not targets
