"""Player policies for the simulation tests, plus the record they keep.

The engine plays against any :class:`~hammurabi.game.UI`, so a policy here plays
a whole term straight from the state the engine hands it: no terminal, no
typing, and every game reproducible from its seed. Each policy changes exactly
one decision of the baseline, so a seeded batch of games covers every branch of
the engine, and each policy remembers the answers it gave so a test can check
the year's bookkeeping.

The measured results quoted in ``docs/balancing.md`` come from these policies.
:class:`FarmerPolicy` is the one that plays the optional agriculture rule set: it
sows at the rate the unlocked technology allows and pays for its research out of
the grain left after the food and the seed of the year, never out of the grain the
city needs — which is the whole trade-off that rule set asks about.
"""

from __future__ import annotations

from collections.abc import Sequence

from hammurabi import config, rules, tech
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

    def ask_research(
        self, state: GameState, choices: Sequence[tech.Tech]
    ) -> str | None:
        """Record and answer the research question, then decide through a hook."""
        self.calls.append(
            ("ask_research", state.year, tuple(item.key for item in choices))
        )
        return self._choose_research(choices)

    def _choose_acres_to_buy(self, state: GameState, *, price: int) -> int:
        """Buy nothing; a policy that trades land overrides this."""
        return 0

    def _choose_acres_to_sell(self, state: GameState, *, price: int) -> int:
        """Sell nothing; a policy that trades land overrides this."""
        return 0

    def _choose_research(self, choices: Sequence[tech.Tech]) -> str | None:
        """Research nothing; the policies that farm override this."""
        return None

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


class FarmerPolicy(Policy):
    """A careful ruler who farms the tech tree as well as the fields.

    Three decisions differ from the baseline, and they belong together. The
    sowing uses the rates the unlocked tree allows, so the plough's acres per
    bushel and the harvest crews' labour are actually used; the research buys the
    most valuable node the year can afford, a bushel added to every acre first
    because that is what feeds a growing city; and no research is ever paid for
    out of the grain the city needs — only the surplus left after the food and
    the seed of the year. That last rule is what makes the measurements
    comparable: a ruler who empties the store for a cheaper plough starves, and
    ``docs/balancing.md`` records what the discipline is worth in the decade, in
    the century, and over the eighty-five years the whole tree needs.

    Attributes:
        researched: Keys of the technologies unlocked, in the order bought.
        bought: The year each technology was bought, as ``(year, key)``.
    """

    def __init__(self) -> None:
        super().__init__()
        self.researched: list[str] = []
        self.bought: list[tuple[int, str]] = []

    def ask_acres_to_plant(self, state: GameState) -> int:
        """Record the question, then sow what the unlocked technology allows."""
        self.calls.append(("ask_plant", state.population, state.bushels))
        return self._record("plant", self._sowable(state), state)

    def ask_research(
        self, state: GameState, choices: Sequence[tech.Tech]
    ) -> str | None:
        """Buy the best node the surplus of the year can pay for, or nothing.

        The nodes are ranked as they were in the older measurements: the harvest
        bonus first, then the rats' divisor, then the cheapest, which is the order
        a city that must feed itself would put them in.
        """
        self.calls.append(
            ("ask_research", state.year, tuple(item.key for item in choices))
        )
        surplus = self._surplus(state)
        affordable = [item for item in choices if item.cost <= surplus]
        if not affordable:
            return None
        chosen = min(
            affordable,
            key=lambda item: (
                -item.delta.yield_bonus,
                -item.delta.rat_divisor,
                item.cost,
            ),
        )
        self.researched.append(chosen.key)
        self.bought.append((state.year, chosen.key))
        return chosen.key

    def _sowable(self, state: GameState) -> int:
        """Return the acres the land, the seed and the labour of the year allow."""
        settings = tech.settings(state.unlocked)
        return min(
            state.acres,
            state.bushels * settings.acres_per_seed,
            rules.max_plantable_acres(
                state.population, acres_per_worker=settings.acres_per_worker
            ),
        )

    def _surplus(self, state: GameState) -> int:
        """Return the grain left once the year's food and seed are set aside."""
        settings = tech.settings(state.unlocked)
        food = state.population * config.BUSHELS_PER_PERSON
        sowable = min(
            state.acres,
            rules.max_plantable_acres(
                state.population, acres_per_worker=settings.acres_per_worker
            ),
        )
        return state.bushels - food - rules.seed_cost(
            sowable, acres_per_seed=settings.acres_per_seed
        )


def play_game(
    seed: int,
    policy: type[Policy] = CarefulPolicy,
    *,
    term_years: int = config.TERM_YEARS,
    agriculture: bool = False,
) -> tuple[Game, Policy]:
    """Play one whole term with ``policy``, seeded with ``seed``.

    Args:
        seed: Seed for the game's random source.
        policy: The policy class to play the term with.
        term_years: Length of the term in years, so that a batch can play the
            marathon as well as the classic ten years.
        agriculture: Whether to play the optional agriculture rule set, which is
            the only thing that lets a policy research the tech tree.

    Returns:
        The finished game and the policy, so that a test can read the verdict,
        the final state and the recorded answers.
    """
    ui = policy()
    game = Game(
        SeededRandom(seed=seed),
        ui,
        state=GameState(term_years=term_years, agriculture=agriculture),
    )
    game.play()
    return game, ui
