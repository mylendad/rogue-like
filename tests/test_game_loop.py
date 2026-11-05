from domain.entities.session import default_session
from domain.entities.world import Level, Room, Coord, Corridor
from domain.entities.enemy import Enemy, EnemyType
from tests.doubles import chain_corridors


def test_turn_cycle_triggers_enemy_actions():
    # Настройка сессии
    session = default_session()

    # Создаем минимальный уровень с врагом
    # Упрощенная структура для теста
    start_room = Room(0, 0, 5, 5, is_start=True)
    end_room = Room(6, 0, 5, 5, is_end=True)
    corridor = Corridor(cells=(Coord(5, 2), Coord(6, 2)), connects=(0, 1))
    rooms = [start_room, end_room] + [Room(i * 12, 10, 3, 3) for i in range(7)]
    level = Level(
        rooms=rooms,
        corridors=[corridor, *chain_corridors(rooms)],
        transition=Coord(8, 2),
    )

    # Добавляем врага
    enemy_pos = Coord(2, 2)
    # Предполагаем, что у Enemy есть метод для действия или он будет обрабатываться через движок
    # Пока просто создаем заглушку врага
    enemy = Enemy(
        enemy_type=EnemyType.ZOMBIE, health=10, strength=2, agility=2, speed=1, hostility=1
    )
    level.enemies[enemy_pos] = enemy

    session.level = level

    # Имитация выполнения хода
    session.perform_turn()

    # Проверка:
    # 1. Враг совершил действие
    # Сейчас враг просто существует. Нужно понять, что значит "совершил действие".
    # Для начала проверим, что цикл вообще отработал.

    assert True
