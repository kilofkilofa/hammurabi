"""The game engine.

:class:`Game` owns a single :class:`~hammurabi.models.GameState` and runs the
yearly loop described in ``docs/architecture.md`` section 5: it reports the
situation, settles the plague and the land trade, feeds the people, sows and
harvests grain, lets the rats and the immigrants in, rolls the plague for the
next year and finally tallies the hunger.

The steps and their order are implemented from the behaviour the 1978 BASIC
listing documents, quirks included: the plague roll is drawn at the end of a year
for the year that follows, so the first year is always plague-free; the
population is only reduced at the very end of the year; and the term closes with
the report the listing opens after its last year before it scores the ruler.

The engine performs no I/O of its own. Everything the player sees or answers
travels through an injected :class:`UI`, and all randomness comes from an
injected :class:`~hammurabi.random_source.RandomSource`. That keeps a game
reproducible from a seed and testable without a terminal.

The classic rule set is what a fresh :class:`~hammurabi.models.GameState` asks
for. When ``GameState.agriculture`` or ``GameState.health`` is true the engine also
lets the ruler pay for one node of the matching tree — :mod:`hammurabi.tech` for the
farming one, :mod:`hammurabi.health` for the public-health one — a year; the unlocked
nodes are read into farming and health settings at the top of a year, so research
takes effect in the year that follows. The research moment is the same for both rule
sets, so with both in play one question a year covers both trees. Research costs no
random draw, so a seed produces exactly the same events with and without a rule set,
and a bonus only ever changes the figures the rules are handed.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar

from hammurabi import config, health, rules, tech
from hammurabi.models import Agriculture, GameState, Health, Verdict
from hammurabi.random_source import RandomSource

#: Type of an answer the engine asks for until it can accept it. The four
#: questions answer with a number, the research question with a node key.
_Answer = TypeVar("_Answer")


class UI(Protocol):
    """The player-facing surface driven by :class:`Game`.

    The engine owns every rule and every decision; an implementation only draws
    what it is handed and returns the numbers the player typed. Implementations
    must not mutate the :class:`~hammurabi.models.GameState` they receive.
    """

    def show_intro(self, state: GameState) -> None:
        """Announce the game and the ruler's starting position."""

    def show_report(self, state: GameState) -> None:
        """Open the year: its number, last year's starvation and arrivals."""

    def show_plague(self, *, before: int, after: int) -> None:
        """Report that the plague halved the population."""

    def show_status(self, state: GameState) -> None:
        """Report population, land, last harvest, rats and grain in store."""

    def show_land_price(self, price: int) -> None:
        """Report this year's land price in bushels per acre."""

    def ask_acres_to_buy(self, state: GameState, *, price: int) -> int:
        """Return how many acres the player wants to buy (``0`` for none)."""

    def ask_acres_to_sell(self, state: GameState, *, price: int) -> int:
        """Return how many acres the player wants to sell (``0`` for none)."""

    def ask_bushels_to_feed(self, state: GameState) -> int:
        """Return how many bushels the player wants to feed the people."""

    def ask_acres_to_plant(self, state: GameState) -> int:
        """Return how many acres the player wants to sow with seed."""

    def ask_research(
        self, state: GameState, choices: Sequence[tech.Offer]
    ) -> str | None:
        """Return the key of the technology to research, or ``None`` for none.

        Asked only when a rule set is in play and ``choices``, the nodes the store can
        pay for, is not empty. ``choices`` may mix the farming and the public-health
        trees, and every offer names the programme it comes from.
        """

    def show_research(self, researched: tech.Node) -> None:
        """Report that the ruler has started to research ``researched``."""

    def show_error(self, message: str) -> None:
        """Explain why the last answer was rejected; the engine asks again."""

    def show_impeachment(self, state: GameState) -> None:
        """Report that the ruler was impeached and the game is over."""

    def show_summary(self, state: GameState, verdict: Verdict) -> None:
        """Report the term statistics and the final verdict."""


def _not_enough_grain(bushels: int) -> str:
    """Return the message shown when the store cannot cover a request."""
    return f"Think again. You have only {bushels} bushels of grain."


def _plant_error(acres: int, state: GameState) -> str:
    """Return the message explaining why ``acres`` cannot be sown."""
    if acres < 0:
        return "Think again. Acres must be a whole number, zero or more."
    if acres > state.acres:
        return f"Think again. You own only {state.acres} acres."
    if rules.seed_cost(acres) > state.bushels:
        return _not_enough_grain(state.bushels)
    return f"But you have only {state.population} people to tend the fields. Now then,"


class Game:
    """Plays one term of Hammurabi.

    Args:
        rng: Source of all randomness; inject a seeded source to reproduce a
            game exactly.
        ui: Surface used to report the situation and collect the player's
            decisions.
        state: Optional starting state, useful in tests; a fresh game starts
            when it is omitted. Its ``term_years`` decides how long the term
            lasts.
    """

    def __init__(
        self,
        rng: RandomSource,
        ui: UI,
        state: GameState | None = None,
    ) -> None:
        self.rng = rng
        self.ui = ui
        self.state = state if state is not None else GameState()

    def play(self) -> Verdict | None:
        """Play the term to its end and return the final verdict.

        Years are played until the term has been completed or the ruler is
        impeached. The outcome is also left in ``state.verdict``, so calling
        ``play`` again on a finished game changes nothing.

        Returns:
            The final verdict, or ``None`` if the game has not finished.
        """
        if not self.state.game_over:
            self.ui.show_intro(self.state)
        while not self.state.game_over and self.state.year < self.state.term_years:
            self.play_year()
        if not self.state.game_over:
            self._closing_report(health.healers(self.state.unlocked))
            self._evaluate_term()
        return self.state.verdict

    def play_year(self) -> None:
        """Play exactly one year of the term.

        The steps follow the order the original listing documents: open the year with
        its report, trade land, feed the people, sow and harvest, let the rats and the
        newcomers in, roll the plague for the year to come and finally tally the
        hunger. With a rule set in play the ruler may also start one research between
        the harvest and the newcomers, because research is paid out of the grain the
        year actually produced.

        The population is only reduced in that last step, exactly as in the listing
        (``555 P=C``). Sowing, the immigration formula and the births the next report
        announces therefore still use the people who are about to starve.

        Raises:
            RuntimeError: If the term is over or the ruler was impeached.
        """
        if self.state.game_over or self.state.year >= self.state.term_years:
            raise RuntimeError("cannot play another year: the term is over")

        # The technology in force this year: research started in an earlier year, so
        # a node unlocked now only pays off from the next one.
        settings = tech.settings(self.state.unlocked)
        health_settings = health.healers(self.state.unlocked)

        self._open_year(health_settings)
        self._trade_land()
        fed = self._feed_people(health_settings)
        acres_planted = self._plant_grain(settings)
        self._harvest_and_rats(acres_planted, settings)
        self._research()
        self._invite_immigrants()
        self._bear_children(health_settings, fed)
        self._roll_plague_for_next_year(health_settings)
        self._settle_starvation(fed)

    def _open_year(self, settings: Health) -> None:
        """Advance the calendar, present the report and settle the arrivals.

        The children and the newcomers announced in the report join the city straight
        away. The plague was decided by the roll made at the end of last year; the
        public health in force decides how many it claims and, through the resistance
        of the wells and the drains, whether it comes at all.
        """
        state = self.state
        state.year += 1
        state.plague_this_year = False

        # The report announces what happened in the year that just ended.
        self.ui.show_report(state)

        # The children and immigrants of the report join the city straight away.
        state.population += state.immigrants_this_year + state.born_this_year

        # The plague was decided by the roll made at the end of last year.
        if rules.plague_strikes(state.plague_roll):
            before = state.population
            state.population = rules.plague_survivors(
                before, survivor_percent=settings.plague_survivor_percent
            )
            state.plague_this_year = True
            self.ui.show_plague(before=before, after=state.population)

        self.ui.show_status(state)

    def _trade_land(self) -> None:
        """Trade land at the single price fixed for the year.

        As in the original game the ruler either buys or sells in a year, never
        both: the price does not move within a year, so trading twice would be
        pointless. Buying nothing moves on to the selling question.
        """
        price = rules.land_price(self.rng)
        self.ui.show_land_price(price)

        bought = self._ask_acres_to_buy(price)
        if bought > 0:
            self.state.acres += bought
            self.state.bushels -= bought * price
            return

        sold = self._ask_acres_to_sell(price)
        self.state.acres -= sold
        self.state.bushels += sold * price

    def _ask_until_accepted(
        self,
        answer: Callable[[], _Answer],
        accepted: Callable[[_Answer], bool],
        complaint: Callable[[_Answer], str],
    ) -> _Answer:
        """Ask ``answer`` until it is accepted, or give up after too many tries.

        A rejected answer is explained through :meth:`UI.show_error` and the
        question is put again, which is what a patient ruler expects. The retry
        loop is bounded by ``config.MAX_ANSWER_ATTEMPTS``, so a UI that can never
        produce a valid answer (a closed stdin, a scripted test double) stops the
        game with an error instead of spinning the engine forever.

        Args:
            answer: Callable asking the player and returning their answer.
            accepted: Predicate deciding whether an answer may be used.
            complaint: Callable explaining, for a rejected answer, why not.

        Returns:
            The first answer accepted by ``accepted``.

        Raises:
            RuntimeError: If ``config.MAX_ANSWER_ATTEMPTS`` answers in a row are
                rejected.
        """
        for _ in range(config.MAX_ANSWER_ATTEMPTS):
            value = answer()
            if accepted(value):
                return value
            self.ui.show_error(complaint(value))
        raise RuntimeError(
            f"gave up after {config.MAX_ANSWER_ATTEMPTS} rejected answers in a row"
        )

    def _ask_acres_to_buy(self, price: int) -> int:
        """Ask for acres to buy, repeating until the store can pay for them."""
        state = self.state
        return self._ask_until_accepted(
            lambda: self.ui.ask_acres_to_buy(state, price=price),
            lambda acres: rules.can_buy_land(acres, price, state.bushels),
            lambda _acres: _not_enough_grain(state.bushels),
        )

    def _ask_acres_to_sell(self, price: int) -> int:
        """Ask for acres to sell, repeating until one acre would remain."""
        state = self.state
        return self._ask_until_accepted(
            lambda: self.ui.ask_acres_to_sell(state, price=price),
            lambda acres: rules.can_sell_land(acres, state.acres),
            lambda _acres: f"Think again. You own only {state.acres} acres.",
        )

    def _feed_people(self, settings: Health) -> int:
        """Spend the grain set aside to feed the city.

        The grain leaves the store here, but the population is left untouched
        until :meth:`_settle_starvation` closes the year, as in the listing. The
        public health of the year decides how many people a bushel feeds.

        Args:
            settings: The public health in force this year.

        Returns:
            How many people the grain could feed.
        """
        state = self.state
        bushels = self._ask_bushels_to_feed()
        state.bushels -= bushels
        return rules.people_fed(
            bushels, bushels_per_person=settings.bushels_per_person
        )

    def _ask_bushels_to_feed(self) -> int:
        """Ask for grain to feed the people, repeating until it is affordable."""
        state = self.state
        return self._ask_until_accepted(
            lambda: self.ui.ask_bushels_to_feed(state),
            lambda bushels: rules.can_feed_people(bushels, state.bushels),
            lambda _bushels: _not_enough_grain(state.bushels),
        )

    def _plant_grain(self, settings: Agriculture) -> int:
        """Ask for acres to sow, pay for the seed and return the area sown."""
        acres = self._ask_acres_to_plant(settings)
        self.state.bushels -= rules.seed_cost(
            acres, acres_per_seed=settings.acres_per_seed
        )
        return acres

    def _ask_acres_to_plant(self, settings: Agriculture) -> int:
        """Ask for acres to sow, repeating until land, seed and labour allow."""
        state = self.state
        return self._ask_until_accepted(
            lambda: self.ui.ask_acres_to_plant(state),
            lambda acres: rules.can_plant(
                acres,
                owned=state.acres,
                bushels=state.bushels,
                population=state.population,
                acres_per_seed=settings.acres_per_seed,
                acres_per_worker=settings.acres_per_worker,
            ),
            lambda acres: _plant_error(acres, state),
        )

    def _harvest_and_rats(self, acres_planted: int, settings: Agriculture) -> None:
        """Bring in the harvest and let the rats at the grain already stored.

        The rats raid what is left in the store after feeding and sowing, but
        before the new harvest is added, exactly as in the original game. The
        farming technology of the year raises the harvest and shrinks the rats'
        share; neither adds a random draw.
        """
        state = self.state
        store_before_harvest = state.bushels
        state.yield_per_acre = rules.harvest_yield(self.rng, bonus=settings.yield_bonus)
        state.rats_ate_this_year = rules.rats_eaten(
            self.rng, store_before_harvest, divisor=settings.rat_divisor
        )
        state.bushels += rules.harvest(acres_planted, state.yield_per_acre)
        state.bushels -= state.rats_ate_this_year

    def _research(self) -> None:
        """Let the ruler pay for one node of the trees in play.

        The question is put only when a rule set is in play, at least one node is open
        and the grain left after the harvest covers it, so a ruler who cannot afford
        anything is never asked a question they cannot answer. When both rule sets are
        played, the table covers both trees, because a year holds one research moment
        however many programmes it serves and every node on it says which programme
        offers it. The cost leaves the store at once and the node is unlocked for the
        years that follow; answering ``None`` leaves the grain alone.
        """
        state = self.state
        trees = tech.enabled_trees(state)
        if not trees:
            return
        choices = tech.offers(trees, state.unlocked, bushels=state.bushels)
        if not choices:
            return

        offered = {offer.node.key: offer for offer in choices}
        key = self._ask_until_accepted(
            lambda: self.ui.ask_research(state, choices),
            lambda key: key is None or key in offered,
            lambda key: (
                f"Think again. '{key}' is not one of the technologies on offer; "
                "answer 0 to research nothing this year."
            ),
        )
        if key is None:
            return
        researched = offered[key]
        state.bushels -= researched.node.cost
        state.unlocked = state.unlocked | {researched.node.key}
        self.ui.show_research(researched.node)

    def _invite_immigrants(self) -> None:
        """Work out how many newcomers the next year's report will announce."""
        state = self.state
        state.immigrants_this_year = rules.immigrants(
            self.rng,
            acres=state.acres,
            bushels=state.bushels,
            population=state.population,
        )

    def _bear_children(self, settings: Health, fed: int) -> None:
        """Work out how many children the next year's report will announce.

        Nobody is born in a year in which the city could not feed itself (see
        :func:`hammurabi.rules.births`), and a classic game has no birth rule at all.
        The children join the city at the start of the next year, exactly as the
        immigrants do.
        """
        state = self.state
        state.born_this_year = rules.births(
            state.population, fed=fed, per_thousand=settings.births_per_thousand
        )

    def _roll_plague_for_next_year(self, settings: Health) -> None:
        """Roll the plague that will decide the year to come (listing 542).

        The listing rolls here, after the immigrants have been worked out, and
        does so even in a year in which nobody starved. The public health of the
        year shifts the roll, so the wells and the drains paid for this year already
        make the plague find fewer years to come.
        """
        self.state.plague_roll = rules.plague_roll(
            self.rng, resistance=settings.plague_resistance
        )

    def _settle_starvation(self, fed: int) -> None:
        """Tally the year's hunger and shrink the population.

        Mirrors the tail of the listing (lines 550-555). A year in which the
        ruler fed more grain than the people needed skips the tally entirely, so
        it does not even count as a year without starvation.

        Args:
            fed: How many people the grain could feed.
        """
        state = self.state
        if not rules.counts_towards_starvation(state.population, fed):
            state.starved_this_year = 0
            return

        starved = rules.starvation(state.population, fed)
        state.starved_this_year = starved
        if rules.is_impeached(state.population, starved):
            self._impeach()
            return

        # The percentage is measured against the population before the deaths.
        state.starved_percent_avg = rules.update_starvation_average(
            state.starved_percent_avg,
            year=state.year,
            starved=starved,
            population=state.population,
        )
        state.total_starved += starved
        state.population = fed

    def _impeach(self) -> None:
        """End the game at once with the impeached verdict."""
        self.state.verdict = Verdict.IMPEACHED
        self.state.game_over = True
        self.ui.show_impeachment(self.state)

    def _closing_report(self, settings: Health) -> None:
        """Apply the report the listing opens after the last year of the term.

        ``270 IF Z=11 THEN 860`` sends the listing back to the top of its loop
        once the term is over, so it reports an eleventh year before it scores
        the ruler: the last children and immigrants join the city (``218 P=P+I``)
        and the plague roll made at the end of the term is resolved (``227``). Both
        change the acres per person the verdict is built on, so both are applied
        here. The phantom report itself is not drawn - only a plague gets its
        classic message, because it changes the figures the player is about to
        be judged on. The public health read here is the one in force at the end of
        the term, so the last research of the reign still counts.

        Args:
            settings: The public health in force at the end of the term.
        """
        state = self.state
        state.population += state.immigrants_this_year + state.born_this_year
        if rules.plague_strikes(state.plague_roll):
            before = state.population
            state.population = rules.plague_survivors(
                before, survivor_percent=settings.plague_survivor_percent
            )
            state.plague_this_year = True
            self.ui.show_plague(before=before, after=state.population)

    def _evaluate_term(self) -> None:
        """Score the completed term and end the game.

        The mediocre verdict names how many people would like to see the ruler
        assassinated (``INT(P * .8 * RND(1))``, listing line 965). The figure is
        drawn here because the engine owns all randomness; the UI only renders
        what it finds in the state.
        """
        verdict = rules.evaluate_verdict(
            self.state.starved_percent_avg,
            self.state.acres_per_person,
        )
        if verdict is Verdict.MEDIOCRE:
            self.state.would_be_assassins = rules.would_be_assassins(
                self.rng, self.state.population
            )
        self.state.verdict = verdict
        self.state.game_over = True
        self.ui.show_summary(self.state, verdict)

