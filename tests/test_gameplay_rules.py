import random

from domain.ai.engine import decide_enemy_action
from domain.entities.enemy import Enemy, EnemyType
from domain.entities.item import Item, ItemType
from domain.entities.session import GameSession, default_session
from domain.entities.world import Coord, Corridor, Level, Room
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


def session_on_level() -> GameSession:
    session = default_session()
    session.level = make_level()
    session.character.pos = Coord(1, 1)
    session.level.player_pos = session.character.pos
    return session


def make_elixir(bonus: int = 2) -> Item:
    return Item(
        item_type=ItemType.ELIXIR,
        subtype="test",
        max_health_bonus=bonus,
        agility_bonus=bonus,
        strength_bonus=bonus,
    )


def make_enemy(enemy_type: EnemyType) -> Enemy:
    return Enemy(enemy_type=enemy_type, health=10, agility=3, strength=3, hostility=1)


def test_elixir_expires_after_ten_turns_including_use():
    session = session_on_level()
    elixir = make_elixir()
    session.character.backpack.add(elixir)

    session.perform_turn(lambda: session.use_elixir(elixir, "agility"), rng=random.Random(0))

    assert session.character.agility == 7
    assert session.elixir_effects["agility"].remaining_turns == 9
    for _ in range(8):
        session.perform_turn(rng=random.Random(0))
    assert session.character.agility == 7

    session.perform_turn(rng=random.Random(0))
    assert session.character.agility == 5
    assert session.elixir_effects == {}
    assert session.stats.elixirs_drunk == 1


def test_same_elixir_extends_duration_without_stacking_bonus():
    session = session_on_level()
    first, second = make_elixir(), make_elixir()
    session.character.backpack.add(first)
    session.character.backpack.add(second)

    session.perform_turn(lambda: session.use_elixir(first, "agility"), rng=random.Random(0))
    session.perform_turn(lambda: session.use_elixir(second, "agility"), rng=random.Random(0))

    assert session.character.agility == 7
    assert session.elixir_effects["agility"].remaining_turns == 18


def test_different_elixir_effects_are_independent():
    session = session_on_level()
    agility, strength = make_elixir(), make_elixir(3)
    session.character.backpack.add(agility)
    session.character.backpack.add(strength)

    session.perform_turn(lambda: session.use_elixir(agility, "agility"), rng=random.Random(0))
    session.perform_turn(lambda: session.use_elixir(strength, "strength"), rng=random.Random(0))

    assert session.character.agility == 7
    assert session.character.strength == 8
    assert session.elixir_effects["agility"].remaining_turns == 8
    assert session.elixir_effects["strength"].remaining_turns == 9


def test_max_health_elixir_clamps_health_on_expiry():
    session = session_on_level()
    elixir = make_elixir(3)
    session.character.backpack.add(elixir)

    session.perform_turn(lambda: session.use_elixir(elixir, "max_health"), rng=random.Random(0))
    session.character.health = 13
    for _ in range(9):
        session.perform_turn(rng=random.Random(0))

    assert session.character.max_health == 10
    assert session.character.health == 10


def test_derived_speed_limits_movement_distance():
    session = session_on_level()
    assert session.character.pos is not None

    session.try_move(Coord(3, 1))
    assert session.character.pos == Coord(1, 1)

    session.character.agility = 10
    session.try_move(Coord(3, 1))
    assert session.character.pos == Coord(3, 1)
    assert session.stats.cells_walked == 2


def test_full_backpack_leaves_item_on_map():
    session = session_on_level()
    for _ in range(9):
        session.character.backpack.add(make_elixir())
    extra = make_elixir()
    assert session.level is not None
    assert session.character.pos is not None
    session.level.items[session.character.pos] = extra

    assert session.pick_up_item() is False
    assert session.level.items[session.character.pos] is extra
    assert len(session.character.backpack.items_of(ItemType.ELIXIR)) == 9


def test_zombie_walks_orthogonally_before_pursuit():
    level = make_level()
    level.player_pos = Coord(1, 1)
    enemy_pos = Coord(3, 3)
    level.enemies[enemy_pos] = make_enemy(EnemyType.ZOMBIE)

    decide_enemy_action(level, level.enemies[enemy_pos], enemy_pos, random.Random(0))

    new_pos = next(iter(level.enemies))
    assert abs(new_pos.x - enemy_pos.x) + abs(new_pos.y - enemy_pos.y) == 1
    assert level.rooms[0].is_interior(new_pos)


def test_vampire_walks_to_any_neighbour_before_pursuit():
    level = make_level()
    level.player_pos = Coord(1, 1)
    enemy_pos = Coord(3, 3)
    level.enemies[enemy_pos] = make_enemy(EnemyType.VAMPIRE)

    decide_enemy_action(level, level.enemies[enemy_pos], enemy_pos, random.Random(0))

    new_pos = next(iter(level.enemies))
    assert new_pos != enemy_pos
    assert max(abs(new_pos.x - enemy_pos.x), abs(new_pos.y - enemy_pos.y)) == 1
    assert level.rooms[0].is_interior(new_pos)


def test_snake_mage_alternates_horizontal_side():
    level = make_level()
    level.player_pos = Coord(1, 1)
    first_pos = Coord(3, 3)
    mage = make_enemy(EnemyType.SNAKE_MAGE)
    level.enemies[first_pos] = mage

    decide_enemy_action(level, mage, first_pos, random.Random(0))
    second_pos = next(iter(level.enemies))
    decide_enemy_action(level, mage, second_pos, random.Random(0))
    third_pos = next(iter(level.enemies))

    first_step = (second_pos.x - first_pos.x, second_pos.y - first_pos.y)
    second_step = (third_pos.x - second_pos.x, third_pos.y - second_pos.y)
    assert abs(first_step[0]) == abs(first_step[1]) == 1
    assert abs(second_step[0]) == abs(second_step[1]) == 1
    assert first_step[0] == -second_step[0]


def test_sleep_skips_only_player_action_and_last_one_turn():
    session = session_on_level()
    assert session.level is not None
    enemy_pos = Coord(3, 3)
    session.level.enemies[enemy_pos] = make_enemy(EnemyType.ZOMBIE)
    session.sleep_turns = 1
    actions: list[str] = []

    session.perform_turn(lambda: actions.append("first"), rng=random.Random(0))

    assert actions == []
    assert session.sleep_turns == 0
    assert enemy_pos not in session.level.enemies

    session.perform_turn(lambda: actions.append("second"), rng=random.Random(0))
    assert actions == ["second"]
