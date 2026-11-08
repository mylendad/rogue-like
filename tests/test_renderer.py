import curses

from domain.entities.enemy import Enemy, EnemyType
from domain.entities.session import default_session
from domain.entities.world import Coord, Corridor, Level, Room
from presentation.renderer import Renderer
from tests.doubles import chain_corridors


class FakeWindow:
    def __init__(self, height: int, width: int) -> None:
        self.height = height
        self.width = width
        self.text: list[str] = []
        self.chars: list[str] = []

    def erase(self) -> None:
        self.text = []
        self.chars = []

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        self.text.append(text)

    def addch(self, y: int, x: int, ch: str, attr: int = 0) -> None:
        self.chars.append(ch)

    def refresh(self) -> None:
        pass


def make_level() -> Level:
    rooms = [Room(0, 0, 7, 7, is_start=True)]
    rooms += [Room(8 + i * 4, 0, 3, 3) for i in range(7)]
    rooms.append(Room(40, 0, 5, 5, is_end=True))
    corridor = Corridor(
        cells=(Coord(6, 2), Coord(7, 2), Coord(8, 2)),
        connects=(0, 1),
    )
    return Level(
        rooms=rooms,
        corridors=[corridor, *chain_corridors(rooms)],
        transition=Coord(41, 1),
    )


def make_session():
    session = default_session()
    level = make_level()
    session.level = level
    session.character.pos = Coord(1, 1)
    level.player_pos = Coord(1, 1)
    return session


def test_invisible_ghost_not_drawn(monkeypatch):
    monkeypatch.setattr(curses, "color_pair", lambda n: n)
    session = make_session()
    level = session.level
    assert level is not None
    ghost = Enemy(
        enemy_type=EnemyType.GHOST,
        health=5,
        agility=5,
        strength=2,
        speed=1,
        hostility=1,
        visible=True,
    )
    level.enemies[Coord(2, 2)] = ghost
    window = FakeWindow(30, 100)
    renderer = Renderer()
    renderer.render(window, session)
    assert "g" in window.chars

    ghost.visible = False
    renderer.render(window, session)
    assert "g" not in window.chars


def test_renderer_redraws_after_resize(monkeypatch):
    monkeypatch.setattr(curses, "color_pair", lambda n: n)
    session = make_session()
    window = FakeWindow(30, 100)
    renderer = Renderer()
    renderer.render(window, session)
    window.height = 24
    window.width = 80
    renderer.render(window, session)
    assert any("HP:" in line for line in window.text)


def test_visited_rooms_reset_between_levels(monkeypatch):
    monkeypatch.setattr(curses, "color_pair", lambda n: n)
    renderer = Renderer()
    window = FakeWindow(30, 100)
    first = make_session()
    renderer.render(window, first)
    assert renderer.visited_rooms == {0}

    second = make_session()
    level = second.level
    assert level is not None
    second.character.pos = Coord(9, 1)
    level.player_pos = Coord(9, 1)
    renderer.render(window, second)
    assert renderer.visited_rooms == {1}
