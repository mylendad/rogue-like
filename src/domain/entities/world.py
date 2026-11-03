"""Уровень, комната, коридор (спека entities).

Генерация уровней — фаза 3; здесь сущность уровня, которая принимает
готовые комнаты и коридоры, валидирует структуру и отвечает на запросы
проходимости.
"""

from dataclasses import dataclass, field

from domain.entities.enemy import Enemy
from domain.entities.item import Item

ROOMS_PER_LEVEL = 9


@dataclass(frozen=True)
class Coord:
    """Клетка сетки уровня."""

    x: int
    y: int


@dataclass
class Room:
    """Комната: положение и размер со стенами по границе, пол внутри.

    Двери-проёмы — клетки границы, считающиеся проходимыми.
    """

    x: int
    y: int
    width: int
    height: int
    doors: tuple[Coord, ...] = ()
    is_start: bool = False
    is_end: bool = False

    def __post_init__(self) -> None:
        if self.width < 3 or self.height < 3:
            raise ValueError("комната должна иметь стены и минимум одну клетку пола")

    @property
    def x2(self) -> int:
        return self.x + self.width - 1

    @property
    def y2(self) -> int:
        return self.y + self.height - 1

    def interior_cells(self) -> tuple[Coord, ...]:
        return tuple(
            Coord(x, y)
            for x in range(self.x + 1, self.x2)
            for y in range(self.y + 1, self.y2)
        )

    def wall_cells(self) -> tuple[Coord, ...]:
        cells: list[Coord] = []
        for x in range(self.x, self.x2 + 1):
            cells.append(Coord(x, self.y))
            cells.append(Coord(x, self.y2))
        for y in range(self.y + 1, self.y2):
            cells.append(Coord(self.x, y))
            cells.append(Coord(self.x2, y))
        return tuple(cells)

    def is_interior(self, coord: Coord) -> bool:
        return self.x < coord.x < self.x2 and self.y < coord.y < self.y2

    def is_on_border(self, coord: Coord) -> bool:
        on_x = self.y <= coord.y <= self.y2 and coord.x in (self.x, self.x2)
        on_y = self.x <= coord.x <= self.x2 and coord.y in (self.y, self.y2)
        return on_x or on_y

    def is_door(self, coord: Coord) -> bool:
        return coord in self.doors and self.is_on_border(coord)


@dataclass
class Corridor:
    """Коридор: собственная геометрия (набор клеток), соединяет две комнаты."""

    cells: tuple[Coord, ...]
    connects: tuple[int, int]

    def __post_init__(self) -> None:
        if not self.cells:
            raise ValueError("коридор должен иметь геометрию")

    def is_that_corridor(self, coord: Coord) -> bool:
        return coord in self.cells


@dataclass
class Level:
    """Уровень: 9 комнат, коридоры, размещения и переход.

    Хранит персонажа, противников и предметы по координатам. Валидация
    структуры по спеке `entities`: ровно 9 комнат, хотя бы один
    коридор, ровно одна стартовая и одна конечная комната, клетка
    перехода внутри конечной комнаты.
    """

    rooms: list[Room]
    corridors: list[Corridor]
    transition: Coord
    player_pos: Coord | None = None
    enemies: dict[Coord, Enemy] = field(default_factory=dict)
    items: dict[Coord, Item] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.rooms) != ROOMS_PER_LEVEL:
            raise ValueError(f"уровень должен состоять ровно из {ROOMS_PER_LEVEL} комнат")
        if not self.corridors:
            raise ValueError("уровень должен иметь хотя бы один коридор")
        starts = [room for room in self.rooms if room.is_start]
        ends = [room for room in self.rooms if room.is_end]
        if len(starts) != 1:
            raise ValueError("уровень должен иметь ровно одну стартовую комнату")
        if len(ends) != 1:
            raise ValueError("уровень должен иметь ровно одну конечную комнату")
        if not ends[0].is_interior(self.transition):
            raise ValueError("клетка перехода должна лежать в конечной комнате")

    def passable(self, coord: Coord) -> bool:
        """Проходимость клетки (спека entities, сценарий «Проходимость»)."""
        for room in self.rooms:
            if room.is_interior(coord) or room.is_door(coord):
                return True
        return any(corridor.is_that_corridor(coord) for corridor in self.corridors)

    def remove_enemy_at(self, coord: Coord) -> Enemy | None:
        return self.enemies.pop(coord, None)
