from domain.entities.session import (
    START_AGILITY,
    START_HEALTH,
    START_MAX_HEALTH,
    START_STRENGTH,
    SessionStats,
    default_session,
)


def test_new_session_defaults():
    session = default_session()
    assert session.level_number == 1
    assert session.character.max_health == START_MAX_HEALTH
    assert session.character.health == START_HEALTH
    assert session.character.agility == START_AGILITY
    assert session.character.strength == START_STRENGTH
    assert session.stats == SessionStats()
    assert session.sleep_turns == 0


def test_all_stats_counters_start_at_zero():
    stats = SessionStats()
    for value in vars(stats).values():
        assert value == 0


def test_treasure_amount_is_accumulated():
    session = default_session()
    session.record_treasure(7)
    session.record_treasure(3)
    assert session.stats.treasures_collected == 10


def test_event_counters_increment():
    session = default_session()
    session.record_enemy_defeated()
    session.record_food_eaten()
    session.record_elixir_drunk()
    session.record_scroll_read()
    session.record_player_attack(hit=True)
    session.record_player_attack(hit=False)
    session.record_hit_taken()
    session.record_walked(4)
    stats = session.stats
    assert stats.enemies_defeated == 1
    assert stats.food_eaten == 1
    assert stats.elixirs_drunk == 1
    assert stats.scrolls_read == 1
    assert stats.hits_dealt == 1
    assert stats.missed_attacks == 1
    assert stats.hits_taken == 1
    assert stats.cells_walked == 4


def test_sleep_is_released_after_tick():
    session = default_session()
    session.sleep_turns = 1
    session.tick_sleep()
    assert session.sleep_turns == 0
    session.tick_sleep()
    assert session.sleep_turns == 0


def test_domain_entities_have_no_presentation_or_storage_imports():
    import ast
    from pathlib import Path

    forbidden_roots = {"curses", "os", "shutil", "pathlib", "json", "pickle", "sqlite3"}
    sources = sorted(Path("src/domain/entities").glob("*.py"))
    assert sources  # пакет на месте
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]] if node.level == 0 else []
            else:
                continue
            violation = forbidden_roots & set(names)
            assert not violation, f"запрещённый импорт {sorted(violation)} в {path}"
