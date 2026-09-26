"""The ten-year game engine.

:class:`Game` owns a single :class:`~hammurabi.models.GameState` and runs the
yearly loop described in ``docs/architecture.md`` section 5: it reports the
situation, settles the plague and the land trade, feeds the people, sows and
harvests grain, lets the rats and the immigrants in, rolls the plague for the
next year and finally tallies the hunger.

The steps and their order follow the 1978 BASIC listing line by line, quirks
included: the plague roll is drawn at the end of a year for the year that
follows, so the first year is always plague-free; the population is only reduced
at the very end of the year; and the term closes with the report the listing
opens for its eleventh year before it scores the ruler.

The engine performs no I/O of its own. Everything the player sees or answers
travels through an injected :class:`UI`, and all randomness comes from an
injected :class:`~hammurabi.random_source.RandomSource`. That keeps a game
reproducible from a seed and testable without a terminal.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from hammurabi import config, rules
from hammurabi.models import GameState, Verdict
from hammurabi.random_source import RandomSource


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

    def show_error(self, message: str) -> None:
        """Explain why the last answer was rejected; the engine asks again."""

    def show_impeachment(self, state: GameState) -> None:
        """Report that the ruler was impeached and the game is over."""

    def show_summary(self, state: GameState, verdict: Verdict) -> None:
        """Report the ten-year statistics and the final verdict."""


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
    """Plays one ten-year term of Hammurabi.

    Args:
        rng: Source of all randomness; inject a seeded source to reproduce a
            game exactly.
        ui: Surface used to report the situation and collect the player's
            decisions.
        state: Optional starting state, useful in tests; a fresh game starts
            when it is omitted.
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

        Years are played until the tenth has been completed or the ruler is
        impeached. The outcome is also left in ``state.verdict``, so calling
        ``play`` again on a finished game changes nothing.

        Returns:
            The final verdict, or ``None`` if the game has not finished.
        """
        if not self.state.game_over:
            self.ui.show_intro(self.state)
        while not self.state.game_over and self.state.year < config.TERM_YEARS:
            self.play_year()
        if not self.state.game_over:
            self._closing_report()
            self._evaluate_term()
        return self.state.verdict

    def play_year(self) -> None:
        """Play exactly one year of the term.

        The steps follow the original listing line by line: open the year with
        its report, trade land, feed the people, sow and harvest, let the rats
        and the immigrants in, roll the plague for the year to come and finally
        tally the hunger.

        The population is only reduced in that last step, exactly as in the
        listing (``555 P=C``). Sowing and the immigration formula therefore
        still use the people who are about to starve.

        Raises:
            RuntimeError: If the term is over or the ruler was impeached.
        """
        if self.state.game_over or self.state.year >= config.TERM_YEARS:
            raise RuntimeError("cannot play another year: the term is over")

        self._open_year()
        self._trade_land()
        fed = self._feed_people()
        acres_planted = self._plant_grain()
        self._harvest_and_rats(acres_planted)
        self._invite_immigrants()
        self._roll_plague_for_next_year()
        self._settle_starvation(fed)

    def _open_year(self) -> None:
        """Advance the calendar, present the report and settle the arrivals."""
        state = self.state
        state.year += 1
        state.plague_this_year = False

        # The report announces what happened in the year that just ended.
        self.ui.show_report(state)

        # The immigrants announced in the report join the city straight away.
        state.population += state.immigrants_this_year

        # The plague was decided by the roll made at the end of last year.
        if rules.plague_strikes(state.plague_roll):
            before = state.population
            state.population = rules.plague_survivors(before)
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
        answer: Callable[[], int],
        accepted: Callable[[int], bool],
        complaint: Callable[[int], str],
    ) -> int:
        """Ask ``answer`` until it is accepted, or give up after too many tries.

        A rejected answer is explained through :meth:`UI.show_error` and the
        question is put again, which is what a patient ruler expects. The retry
        loop is bounded by ``config.MAX_ANSWER_ATTEMPTS``, so a UI that can never
        produce a valid number (a closed stdin, a scripted test double) stops the
        game with an error instead of spinning the engine forever.

        Args:
            answer: Callable asking the player and returning their number.
            accepted: Predicate deciding whether a number may be used.
            complaint: Callable explaining, for the rejected number, why not.

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

    def _feed_people(self) -> int:
        """Spend the grain set aside to feed the city.

        The grain leaves the store here, but the population is left untouched
        until :meth:`_settle_starvation` closes the year, as in the listing.

        Returns:
            How many people the grain could feed.
        """
        state = self.state
        bushels = self._ask_bushels_to_feed()
        state.bushels -= bushels
        return rules.people_fed(bushels)

    def _ask_bushels_to_feed(self) -> int:
        """Ask for grain to feed the people, repeating until it is affordable."""
        state = self.state
        return self._ask_until_accepted(
            lambda: self.ui.ask_bushels_to_feed(state),
            lambda bushels: rules.can_feed_people(bushels, state.bushels),
            lambda _bushels: _not_enough_grain(state.bushels),
        )

    def _plant_grain(self) -> int:
        """Ask for acres to sow, pay for the seed and return the area sown."""
        acres = self._ask_acres_to_plant()
        self.state.bushels -= rules.seed_cost(acres)
        return acres

    def _ask_acres_to_plant(self) -> int:
        """Ask for acres to sow, repeating until land, seed and labour allow."""
        state = self.state
        return self._ask_until_accepted(
            lambda: self.ui.ask_acres_to_plant(state),
            lambda acres: rules.can_plant(
                acres,
                owned=state.acres,
                bushels=state.bushels,
                population=state.population,
            ),
            lambda acres: _plant_error(acres, state),
        )

    def _harvest_and_rats(self, acres_planted: int) -> None:
        """Bring in the harvest and let the rats at the grain already stored.

        The rats raid what is left in the store after feeding and sowing, but
        before the new harvest is added, exactly as in the original game.
        """
        state = self.state
        store_before_harvest = state.bushels
        state.yield_per_acre = rules.harvest_yield(self.rng)
        state.rats_ate_this_year = rules.rats_eaten(self.rng, store_before_harvest)
        state.bushels += rules.harvest(acres_planted, state.yield_per_acre)
        state.bushels -= state.rats_ate_this_year

    def _invite_immigrants(self) -> None:
        """Work out how many newcomers the next year's report will announce."""
        state = self.state
        state.immigrants_this_year = rules.immigrants(
            self.rng,
            acres=state.acres,
            bushels=state.bushels,
            population=state.population,
        )

    def _roll_plague_for_next_year(self) -> None:
        """Roll the plague that will decide the year to come (listing 542).

        The listing rolls here, after the immigrants have been worked out, and
        does so even in a year in which nobody starved.
        """
        self.state.plague_roll = rules.plague_roll(self.rng)

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

    def _closing_report(self) -> None:
        """Apply the report the listing opens after the tenth year.

        ``270 IF Z=11 THEN 860`` sends the listing back to the top of its loop
        once the term is over, so it reports an eleventh year before it scores
        the ruler: the last immigration joins the city (``218 P=P+I``) and the
        plague roll made at the end of year ten is resolved (``227``). Both
        change the acres per person the verdict is built on, so both are applied
        here. The phantom report itself is not drawn - only a plague gets its
        classic message, because it changes the figures the player is about to
        be judged on.
        """
        state = self.state
        state.population += state.immigrants_this_year
        if rules.plague_strikes(state.plague_roll):
            before = state.population
            state.population = rules.plague_survivors(before)
            state.plague_this_year = True
            self.ui.show_plague(before=before, after=state.population)

    def _evaluate_term(self) -> None:
        """Score the completed ten-year term and end the game.

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

