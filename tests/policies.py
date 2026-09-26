"""Player policies for the simulation tests, plus the record they keep.

The engine plays against any :class:`~hammurabi.game.UI`, so a policy here plays
a whole term straight from the state the engine hands it: no terminal, no
typing, and every game reproducible from its seed. Each policy changes exactly
one decision of the baseline, so a seeded batch of games covers every branch of
the engine, and each policy remembers the answers it gave so a test can check
the year's bookkeeping.

The measured results quoted in ``docs/balancing.md`` come from these policies.
"""

from __future__ import annotations

from hammurabi import config, rules
from hammurabi.game import Game
from hammurabi.models import GameState
from hammurabi.random_source import SeededRandom
from tests.support import CarefulUI

#: One accepted answer: what was asked, the number given, and the figures the
#: engine showed next to the question (bushels in store, people in the city).
Answer = tuple[str, int, int, int]


class Policy(CarefulUI):
    """A careful ruler who records every answer they gave.

    The baseline behaviour is :class:`~tests.support.CarefulUI`: no land changes
    hands, everybody the store can feed is fed, and as much land is sown as land,
    seed and labour allow. A subclass changes a single ``_choose_*`` decision.

    Attributes:
        answers: Every accepted answer, in the order the engine asked for it.
    """

    def __init__(self) -> None:
        super().__init__()
        self.answers: list[Answer] = []

    def ask_acres_to_buy(self, state: GameState, *, price: int) -> int:
        """Record and answer the question about buying land."""
        return self._record(
            "buy", self._choose_acres_to_buy(state, price=price), state
        )

    def ask_acres_to_sell(self, state: GameState, *, price: int) -> int:
        """Record and answer the question about selling land."""
        return self._record(
            "sell", self._choose_acres_to_sell(state, price=price), state
        )

    def ask_bushels_to_feed(self, state: GameState) -> int:
        """Record and answer the feeding question with the careful answer."""
        return self._record("feed", super().ask_bushels_to_feed(state), state)

    def ask_acres_to_plant(self, state: GameState) -> int:
        """Record and answer the sowing question with the careful answer."""
        return self._record("plant", super().ask_acres_to_plant(state), state)

    def _choose_acres_to_buy(self, state: GameState, *, price: int) -> int:
        """Buy nothing; a policy that trades land overrides this."""
        return 0

    def _choose_acres_to_sell(self, state: GameState, *, price: int) -> int:
        """Sell nothing; a policy that trades land overrides this."""
        return 0

    def _record(self, question: str, answer: int, state: GameState) -> int:
        """Store ``answer`` with the figures shown next to it, and return it."""
        self.answers.append((question, answer, state.bushels, state.population))
        return answer


class CarefulPolicy(Policy):
    """The baseline ruler: no land changes hands at all."""


class TraderPolicy(Policy):
    """Buy land whenever the grain left after food and seed can pay for it."""

    def _choose_acres_to_buy(self, state: GameState, *, price: int) -> int:
        """Spend what is spare after feeding the city and sowing its land."""
        food = state.population * config.BUSHELS_PER_PERSON
        sowable = min(state.acres, rules.max_plantable_acres(state.population))
        spare = max(0, state.bushels - food - rules.seed_cost(sowable))
        return spare // price


class SellerPolicy(Policy):
    """Never buy; sell land for grain when the price is high."""

    #: Sell only when an acre fetches at least this much; half of the 17-26 band
    #: lies above it.
    HIGH_PRICE = 22
    #: Acres offered in such a year, as long as one acre stays with the city.
    SALE = 50

    def _choose_acres_to_sell(self, state: GameState, *, price: int) -> int:
        """Sell a slice of the land when the price is at least ``HIGH_PRICE``."""
        if price < self.HIGH_PRICE:
            return 0
        return min(state.acres - 1, self.SALE)


class StarverPolicy(Policy):
    """Feed nobody at all: an impeachment in the very first year."""

    def ask_bushels_to_feed(self, state: GameState) -> int:
        """Record and answer the feeding question with nothing."""
        return self._record("feed", 0, state)


def play_game(seed: int, policy: type[Policy] = CarefulPolicy) -> tuple[Game, Policy]:
    """Play one whole term with ``policy``, seeded with ``seed``.

    Args:
        seed: Seed for the game's random source.
        policy: The policy class to play the term with.

    Returns:
        The finished game and the policy, so that a test can read the verdict,
        the final state and the recorded answers.
    """
    ui = policy()
    game = Game(SeededRandom(seed=seed), ui)
    game.play()
    return game, ui
