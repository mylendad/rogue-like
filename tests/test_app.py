import random

from domain.combat.engine import resolve_attack
from domain.entities.enemy import Enemy, EnemyType
from domain.entities.item import Item, ItemType
from domain.entities.session import default_session
from domain.entities.world import Coord, Corridor, Level, Room
from presentation.app import run


class FakeWindow:
    def __init__(self, keys: list[int]) -> None:
        self.keys = list(keys)

    def getch(self) -> int:
        if not self.keys:
            raise AssertionError("сценарий ввода исчерпан")
        return self.keys.pop(0)

    def keypad(self, flag: bool) -> None:
        pass

    def erase(self) -> None:
        pass

    def refresh(self) -> None:
        pass


class FakeRenderer:
    def __init__(self) -> None:
        self.modes: list[str] = []
        self.final_called = False

    def render(self, stdscr, session, *, mode="game", item_type=None, message="") -> None:
        self.modes.append(mode)

    def render_final(self, stdscr, session) -> None:
        self.final_called = True


def make_level() -> Level:
    rooms = [Room(0, 0, 7, 7, is_start=True)]
    rooms += [Room(8 + i * 4, 0, 3, 3) for i in range(7)]
    rooms.append(Room(40, 0, 5, 5, is_end=True))
    corridor = Corridor(
        cells=(Coord(6, 2), Coord(7, 2), Coord(8, 2)),
        connects=(0, 1),
    )
    level = Level(rooms=rooms, corridors=[corridor], transition=Coord(41, 1))
    level.player_pos = Coord(1, 1)
    return level


def make_session():
    session = default_session()
    level = make_level()
    session.level = level
    session.character.pos = Coord(1, 1)
    return session


def level_factory(level_number: int, rng: random.Random) -> Level:
    return make_level()


def test_app_move_and_quit():
    session = make_session()
    renderer = FakeRenderer()
    run(
        FakeWindow([ord("d"), ord("q"), ord("y")]),
        session=session,
        renderer=renderer,
        level_factory=level_factory,
        setup_curses=False,
    )
    assert session.character.pos == Coord(2, 1)
    assert renderer.final_called is False


def test_app_item_cancel_does_not_consume_turn():
    session = make_session()
    session.character.health = 5
    food = Item(item_type=ItemType.FOOD, subtype="ration", health_gain=2)
    session.character.backpack.add(food)
    renderer = FakeRenderer()
    run(
        FakeWindow([ord("j"), 27, ord("q"), ord("y")]),
        session=session,
        renderer=renderer,
        level_factory=level_factory,
        setup_curses=False,
    )
    assert food in session.character.backpack.items_of(ItemType.FOOD)
    assert session.character.health == 5
    assert session.stats.food_eaten == 0
    assert "select_item" in renderer.modes


def test_app_item_use_and_stats_screen():
    session = make_session()
    session.character.health = 5
    food = Item(item_type=ItemType.FOOD, subtype="ration", health_gain=2)
    session.character.backpack.add(food)
    renderer = FakeRenderer()
    run(
        FakeWindow([ord("j"), ord("1"), ord("t"), ord("t"), ord("q"), ord("y")]),
        session=session,
        renderer=renderer,
        level_factory=level_factory,
        setup_curses=False,
    )
    assert food not in session.character.backpack.items_of(ItemType.FOOD)
    assert session.character.health == 7
    assert session.stats.food_eaten == 1
    assert "stats" in renderer.modes


def test_app_menu_exit():
    session = make_session()
    renderer = FakeRenderer()
    run(
        FakeWindow([ord("m"), ord("q"), ord("y")]),
        session=session,
        renderer=renderer,
        level_factory=level_factory,
        setup_curses=False,
    )
    assert "menu" in renderer.modes
    assert renderer.final_called is False


def test_app_level_transition():
    session = make_session()
    level = session.level
    assert level is not None
    level.transition = Coord(2, 1)
    renderer = FakeRenderer()
    run(
        FakeWindow([ord("d"), ord("q"), ord("y")]),
        session=session,
        renderer=renderer,
        level_factory=level_factory,
        setup_curses=False,
    )
    assert session.level_number == 2
    assert session.level is not None


def test_app_death_records_result_and_restarts():
    session = make_session()
    level = session.level
    assert level is not None
    session.character.health = 1
    enemy = Enemy(
        enemy_type=EnemyType.ZOMBIE,
        health=100,
        agility=100,
        strength=100,
        speed=1,
        hostility=10,
    )
    level.enemies[Coord(2, 1)] = enemy
    session.character.backpack.add(
        Item(item_type=ItemType.FOOD, subtype="ration", health_gain=2)
    )
    seed = None
    for candidate in range(1000):
        if resolve_attack(enemy, session.character, None, random.Random(candidate)).hit:
            seed = candidate
            break
    assert seed is not None

    renderer = FakeRenderer()
    run(
        FakeWindow([ord("j"), ord("1"), ord("q"), ord("y")]),
        session=session,
        rng=random.Random(seed),
        renderer=renderer,
        level_factory=level_factory,
        setup_curses=False,
    )
    assert len(session.run_results) == 1
    assert session.run_results[0].success is False
    assert session.stats.treasures_collected == 0


def test_app_last_level_ends_without_new_run():
    session = make_session()
    level = session.level
    assert level is not None
    session.level_number = 21
    level.transition = Coord(2, 1)
    renderer = FakeRenderer()
    run(
        FakeWindow([ord("d"), ord("x")]),
        session=session,
        renderer=renderer,
        level_factory=level_factory,
        setup_curses=False,
    )
    assert session.game_over is True
    assert len(session.run_results) == 1
    assert session.run_results[0].success is True
    assert renderer.final_called is True
