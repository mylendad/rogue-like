"""Доменный модуль генерации уровней."""

from domain.generation.generator import generate_level
from domain.generation.population import GenerationError

__all__ = ["GenerationError", "generate_level"]
