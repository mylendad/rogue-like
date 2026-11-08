"""Туман войны и прямая видимость (спека curses-rendering)."""

from domain.entities.world import Coord, Level, Room

VISIBILITY_RADIUS = 5


def compute_visibility(level: Level, player_pos: Coord) -> set[Coord]:
    """Вычисляет множество видимых клеток из позиции игрока с учётом комнат и LOS."""
    visible: set[Coord] = set()
    if level is None:
        return visible

    # Найти комнату игрока, если в комнате
    player_room: Room | None = None
    for room in level.rooms:
        if room.contains(player_pos):
            player_room = room
            break

    if player_room is not None:
        # Вся комната игрока видна
        for c in player_room.all_cells():
            visible.add(c)

    # LOS лучи во всех направлениях в пределах радиуса
    for r in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS + 1):
        for c in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS + 1):
            if r * r + c * c > VISIBILITY_RADIUS * VISIBILITY_RADIUS:
                continue
            target = Coord(player_pos.x + c, player_pos.y + r)
            if not (0 <= target.x < level.width and 0 <= target.y < level.height):
                continue
            if _has_line_of_sight(level, player_pos, target):
                visible.add(target)

    return visible


def _has_line_of_sight(level: Level, start: Coord, end: Coord) -> bool:
    """Алгоритм Брезенхема с проверкой непроходимости (стен)."""
    x0, y0 = start.x, start.y
    x1, y1 = end.x, end.y

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    curr_x, curr_y = x0, y0
    while True:
        if curr_x == x1 and curr_y == y1:
            return True
        # Если встретили стену (не проходима и не дверь), линия заблокирована
        c = Coord(curr_x, curr_y)
        if c != start and not level.passable(c):
            return False

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy
