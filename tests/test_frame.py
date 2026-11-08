import curses

from domain.entities.item import Item, ItemType
from domain.entities.session import RunResult, default_session
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


def test_small_terminal_message(monkeypatch):
    monkeypatch.setattr(curses, "color_pair", lambda n: n)
    window = FakeWindow(10, 30)
    Renderer().render(window, make_session())
    assert any("Терминал слишком мал" in line for line in window.text)


def test_hud_values_and_resize(monkeypatch):
    monkeypatch.setattr(curses, "color_pair", lambda n: n)
    session = make_session()
    session.stats.treasures_collected = 12
    renderer = Renderer()
    window = FakeWindow(30, 100)
    renderer.render(window, session)
    assert any("Level: 1" in line and "Treasures: 12" in line for line in window.text)

    window.height = 24
    window.width = 80
    renderer.render(window, session)
    assert any("HP:" in line for line in window.text)


def test_stats_screen_rows(monkeypatch):
    monkeypatch.setattr(curses, "color_pair", lambda n: n)
    session = make_session()
    session.run_results.append(
        RunResult(
            treasures_collected=30,
            reached_level=5,
            enemies_defeated=2,
            food_eaten=1,
            elixirs_drunk=1,
            scrolls_read=1,
            hits_dealt=4,
            missed_attacks=1,
            hits_taken=2,
            cells_walked=40,
            success=False,
        )
    )
    window = FakeWindow(30, 100)
    Renderer().render(window, session, mode="stats")
    assert any("Сокровища" in line for line in window.text)
    assert any("30" in line and "Смерть" in line for line in window.text)


def test_item_selection_list(monkeypatch):
    monkeypatch.setattr(curses, "color_pair", lambda n: n)
    session = make_session()
    session.character.backpack.add(
        Item(item_type=ItemType.FOOD, subtype="ration", health_gain=2)
    )
    window = FakeWindow(30, 100)
    Renderer().render(window, session, mode="select_item", item_type=ItemType.FOOD)
    assert any("ration" in line for line in window.text)
    assert any("1." in line for line in window.text)
