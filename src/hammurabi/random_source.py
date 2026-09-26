"""Seedable source of randomness.

The engine receives a :class:`RandomSource` instead of calling the ``random``
module directly. This is the single seam through which randomness enters the
game, which keeps a game reproducible from a seed and lets the tests inject a
stub with a scripted sequence of values.
"""

from __future__ import annotations

import random
from typing import Protocol, runtime_checkable


@runtime_checkable
class RandomSource(Protocol):
    """The minimal random number interface the game depends on."""

    def random(self) -> float:
        """Return a float in the half-open interval ``[0.0, 1.0)``."""
        ...

    def randint(self, low: int, high: int) -> int:
        """Return an integer in the inclusive interval ``[low, high]``."""
        ...


class SeededRandom:
    """Deterministic :class:`RandomSource` backed by :class:`random.Random`."""

    def __init__(self, seed: int | None = None) -> None:
        """Create the source, remembering ``seed`` for reproducibility.

        Args:
            seed: Seed for the underlying generator. ``None`` draws fresh
                entropy, matching :class:`random.Random`.
        """
        self.seed = seed
        self._rng = random.Random(seed)

    def random(self) -> float:
        """Return a float in ``[0.0, 1.0)`` from the underlying generator."""
        return self._rng.random()

    def randint(self, low: int, high: int) -> int:
        """Return an integer in ``[low, high]`` from the underlying generator."""
        return self._rng.randint(low, high)
