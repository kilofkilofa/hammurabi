"""Hammurabi — a faithful Python port of the classic 1978 BASIC game.

The package is deliberately split so that the game rules are pure functions,
the engine is free of terminal I/O, and only ``ui`` and ``main`` touch the
console. See ``docs/architecture.md`` for the full design.
"""

__version__ = "1.0.0"

__all__ = ["__version__"]

