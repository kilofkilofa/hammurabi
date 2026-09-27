"""Player policies for the simulation tests, plus the record they keep.

The engine plays against any :class:`~hammurabi.game.UI`, so a policy here plays
a whole term straight from the state the engine hands it: no terminal, no
typing, and every game reproducible from its seed. Each policy changes exactly
one decision of the baseline, so a seeded batch of games covers every branch of
the engine, and each policy remembers the answers it gave so a test can check
the year's bookkeeping.

The measured results quoted in ``docs/balancing.md`` come from these policies.
:class:`FarmerPolicy` is the one that plays the optional agriculture rule set: it
sows at the rate the technology in force allows and pays for its research out of
the grain the year leaves spare — the store the year opens with, less the food the
people need and the seed the land needs — never out of the grain the city needs,
which is the whole trade-off that rule set asks about.
:class:`HealerPolicy` plays the optional health rule set the same way, ranking the
rungs by the people they save from the plague instead of by the harvest they add.
"""

from __future__ import annotations

from collections.abc import Sequence

from hammurabi import config, health, rules, tech
from hammurabi.game import Game
from hammurabi.models import GameState
from hammurabi.random_source import SeededRandom
from tests.support import CarefulUI

#: One accepted answer: what was asked, the number given, and the figures the
#: engine showed next to the question (bushels in store, people in the city).
Answer = tuple[str, int, int, int]

#: The value of every rate a node's delta may carry in the classic game. A policy
#: ranks the offers of both rule sets with one key, so a rate a node does not touch
#: has to answer with the classic value rather than with an error.
CLASSIC_RATES: dict[str, int] = {
    "yield_bonus": 0,
    "rat_divisor": 1,
    "plague_survivor_percent": config.PLAGUE_SURVIVOR_PERCENT,
    "plague_resistance": 0,
    "births_per_thousand": 0,
    "bushels_per_person": config.BUSHELS_PER_PERSON,
}


def rate(node: tech.Node, name: str) -> int:
    """Return the rate ``name`` that ``node`` reaches, classic when it says nothing.

    A node of the farming tree carries no plague survivor share and a node of the
    health tree carries no harvest bonus, so a policy that may be offered both needs
    a default for the rates the node is silent about.
    """
    return getattr(node.delta, name, CLASSIC_RATES[name])


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
        self, state: GameState, choices: Sequence[tech.Offer]
    ) -> str | None:
        """Record and answer the research question, then decide through a hook."""
        self.calls.append(
            ("ask_research", state.year, tuple(offer.node.key for offer in choices))
        )
        return self._choose_research(choices)

    def _choose_acres_to_buy(self, state: GameState, *, price: int) -> int:
        """Buy nothing; a policy that trades land overrides this."""
        return 0

    def _choose_acres_to_sell(self, state: GameState, *, price: int) -> int:
        """Sell nothing; a policy that trades land overrides this."""
        return 0

    def _choose_research(self, choices: Sequence[tech.Offer]) -> str | None:
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
    sowing uses the rates the technology in force allows, so the plough's acres per
    bushel and the harvest crews' labour are actually used; the research buys the
    most valuable node the year can afford, a bushel added to every acre first
    because that is what feeds a growing city; and no research is ever paid for
    out of the grain the city needs — only the surplus the year leaves once the
    food the people need and the seed the land needs are set aside. That last rule
    is what makes the measurements comparable: a ruler who empties the store for a
    cheaper plough starves, and ``docs/balancing.md`` records what the discipline
    is worth in the decade, in the century, and over the eighty-five years the
    whole tree needs.

    Because the question is put at the start of the year — before the land trade,
    the feeding and the sowing — a node bought this year is already in
    ``state.unlocked`` when the year's later questions are put, while the engine
    still plays the figures it read before the question. Every rate this policy
    takes from the tree therefore comes from :meth:`_in_force`, not from
    ``state.unlocked``, or it would sow and feed at a rate the engine will not
    accept until next year.

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
        self, state: GameState, choices: Sequence[tech.Offer]
    ) -> str | None:
        """Buy the best node the surplus of the year can pay for, or nothing.

        The nodes are ranked as they were in the older measurements: the harvest
        bonus first, then the rats' divisor, then the cheapest, which is the order
        a city that must feed itself would put them in.
        """
        self.calls.append(
            ("ask_research", state.year, tuple(offer.node.key for offer in choices))
        )
        surplus = self._surplus(state)
        affordable = [offer for offer in choices if offer.node.cost <= surplus]
        if not affordable:
            return None
        chosen = min(
            affordable,
            key=lambda offer: (
                -rate(offer.node, "yield_bonus"),
                -rate(offer.node, "rat_divisor"),
                offer.node.cost,
            ),
        )
        self.researched.append(chosen.node.key)
        self.bought.append((state.year, chosen.node.key))
        return chosen.node.key

    def _in_force(self, state: GameState) -> frozenset[str]:
        """Return the technology in force this year, without what was just bought.

        The engine reads the tree before it puts the research question, so a node
        paid for during the year only pays off from the next one; a policy that
        sows or feeds at the rates of the year has to drop it as well, or it would
        answer with a rate the engine refuses until the year is out. The question
        itself is put before anything is bought, so this is ``state.unlocked``
        while the offer is being chosen.
        """
        return state.unlocked - {
            key for year, key in self.bought if year == state.year
        }

    def _sowable(self, state: GameState) -> int:
        """Return the acres the land, the seed and the labour of the year allow."""
        settings = tech.settings(self._in_force(state))
        return min(
            state.acres,
            state.bushels * settings.acres_per_seed,
            rules.max_plantable_acres(
                state.population, acres_per_worker=settings.acres_per_worker
            ),
        )

    def _surplus(self, state: GameState) -> int:
        """Return the grain left once the year's food and seed are set aside."""
        in_force = self._in_force(state)
        settings = tech.settings(in_force)
        food = state.population * health.healers(in_force).bushels_per_person
        sowable = min(
            state.acres,
            rules.max_plantable_acres(
                state.population, acres_per_worker=settings.acres_per_worker
            ),
        )
        return state.bushels - food - rules.seed_cost(
            sowable, acres_per_seed=settings.acres_per_seed
        )


class HealerPolicy(FarmerPolicy):
    """A careful ruler who tends the public health instead of the fields.

    The sowing and the research discipline are the farmer's: the tree's own rates
    decide how much land is sown, and nothing is ever paid for out of the grain the
    city needs. What changes is the ranking, because the two programmes answer
    different questions. Feeding a person out of fewer bushels comes first, because
    that is what keeps a growing city alive; then the people the healer branch saves
    from the plague, the plagues the water branch keeps away, and last the children
    the nursery branch brings, which raise the demand for bread rather than the
    supply. A rung of the farming tree, which touches none of those, is bought only
    when it is the cheapest thing on the table. The measured plan of that policy is in
    ``docs/balancing.md``.
    """

    def ask_bushels_to_feed(self, state: GameState) -> int:
        """Record and answer the feeding question at the health in force.

        A city that mills its grain and digs fish ponds needs fewer bushels for the
        same people, and the grain not spent on bread is what pays for the rest of the
        programme. Feeding at the classic twenty would throw that away twice over: the
        listing keeps no surplus for a year in which everybody was fed, so the extra
        bushels simply disappear. A measure paid for this year is not in force yet —
        the engine feeds the city at the rate it read before the question — so it is
        the rate of :meth:`_in_force` that fills the granary rather than the rate of
        the whole tree.
        """
        self.calls.append(("ask_feed", state.population, state.bushels))
        rate = health.healers(self._in_force(state)).bushels_per_person
        return self._record(
            "feed", min(state.population * rate, state.bushels), state
        )

    def ask_research(
        self, state: GameState, choices: Sequence[tech.Offer]
    ) -> str | None:
        """Buy the best rung of either tree the surplus of the year can pay for."""
        self.calls.append(
            ("ask_research", state.year, tuple(offer.node.key for offer in choices))
        )
        surplus = self._surplus(state)
        affordable = [offer for offer in choices if offer.node.cost <= surplus]
        if not affordable:
            return None
        chosen = min(
            affordable,
            key=lambda offer: (
                rate(offer.node, "bushels_per_person"),
                -rate(offer.node, "plague_survivor_percent"),
                -rate(offer.node, "plague_resistance"),
                -rate(offer.node, "births_per_thousand"),
                offer.node.cost,
            ),
        )
        self.researched.append(chosen.node.key)
        self.bought.append((state.year, chosen.node.key))
        return chosen.node.key


def play_game(
    seed: int,
    policy: type[Policy] = CarefulPolicy,
    *,
    term_years: int = config.TERM_YEARS,
    agriculture: bool = False,
    health: bool = False,
) -> tuple[Game, Policy]:
    """Play one whole term with ``policy``, seeded with ``seed``.

    Args:
        seed: Seed for the game's random source.
        policy: The policy class to play the term with.
        term_years: Length of the term in years, so that a batch can play the
            marathon as well as the classic ten years.
        agriculture: Whether to play the optional agriculture rule set, which is
            the only thing that lets a policy research the farming tree.
        health: Whether to play the optional health rule set. With both rule sets on,
            the year still holds one research moment, so the offer covers both trees.

    Returns:
        The finished game and the policy, so that a test can read the verdict,
        the final state and the recorded answers.
    """
    ui = policy()
    game = Game(
        SeededRandom(seed=seed),
        ui,
        state=GameState(
            term_years=term_years, agriculture=agriculture, health=health
        ),
    )
    game.play()
    return game, ui
