from domain.entities.world import Coord, Corridor, Level, Room
from domain.entities.session import default_session, RunResult
from tests.doubles import chain_corridors


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


def test_run_result_capture_on_death():
    session = default_session()
    session.level = make_level()
    session.character.pos = Coord(1, 1)
    session.stats.treasures_collected = 15
    session.stats.enemies_defeated = 3
    session.level_number = 3
    session.character.health = 0

    session._handle_death()

    assert len(session.run_results) == 1
    res = session.run_results[0]
    assert res.treasures_collected == 15
    assert res.enemies_defeated == 3
    assert res.reached_level == 3
    assert res.success is False
    assert session.stats.treasures_collected == 0
    assert session.level_number == 1


def test_run_result_capture_on_victory():
    session = default_session()
    session.level_number = 21
    session.level = make_level()
    session.stats.treasures_collected = 100

    session._advance_level()

    assert session.game_over is True
    assert len(session.run_results) == 1
    assert session.run_results[0].success is True
    assert session.run_results[0].reached_level == 21


def test_saved_result_is_immutable_snapshot():
    session = default_session()
    session.stats.treasures_collected = 7
    session._handle_death()
    first = session.run_results[0]

    session.stats.treasures_collected = 99
    session._handle_death()

    assert first.treasures_collected == 7
    assert session.run_results[0] is first
    assert session.run_results[1].treasures_collected == 99


def test_run_result_frozen():
    res = RunResult(
        treasures_collected=10,
        reached_level=2,
        enemies_defeated=1,
        food_eaten=0,
        elixirs_drunk=0,
        scrolls_read=0,
        hits_dealt=2,
        missed_attacks=0,
        hits_taken=1,
        cells_walked=5,
        success=True,
    )
    try:
        res.treasures_collected = 20  # type: ignore[misc]
        raise AssertionError("RunResult должен быть неизменяемым")
    except AttributeError:
        pass
