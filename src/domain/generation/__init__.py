"""Доменный модуль генерации уровней (спека level-generation)."""

from domain.generation.generator import generate_level
from domain.generation.population import GenerationError

__all__ = ["GenerationError", "generate_level"]
