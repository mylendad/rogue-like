"""Контракт хранения прогресса, не зависящий от файловой системы."""

from typing import Protocol

from domain.entities.session import ProgressSnapshot


class ProgressStorage(Protocol):
    """Хранилище снимков прогресса и истории попыток."""

    def load(self) -> ProgressSnapshot | None:
        """Возвращает сохранённый снимок или None, если сохранения нет."""
        ...

    def save(self, snapshot: ProgressSnapshot) -> None:
        """Сохраняет снимок."""
        ...
