"""Shared test doubles for the Hammurabi test suite.

Keeping the scripted random source, the recording UI, the buffer-backed console
and the scripted console reader in one module means the rule tests, the engine
tests and the UI tests use exactly the same doubles.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Sequence
from io import StringIO
from typing import TypeVar

from rich.console import Console

from hammurabi import config, rules, tech
from hammurabi.models import GameState, Verdict

_Value = TypeVar("_Value")


class StubRandom:
    """A scripted :class:`~hammurabi.random_source.RandomSource`.

    ``randoms`` and ``integers`` are consumed in order by :meth:`random` and
    :meth:`randint`. ``randint`` also asserts that the scripted value lies inside
    the requested bounds, which documents the range each rule expects.
    """

    def __init__(
        self,
        *,
        randoms: Iterable[float] = (),
        integers: Iterable[int] = (),
    ) -> None:
        self._randoms = iter(randoms)
        self._integers = iter(integers)

    def random(self) -> float:
        """Return the next scripted float."""
        return next(self._randoms)

    def randint(self, low: int, high: int) -> int:
        """Return the next scripted integer, checking it fits ``[low, high]``."""
        value = next(self._integers)
        assert low <= value <= high, f"{value} outside [{low}, {high}]"
        return value


def repeat_last(values: Iterable[_Value]) -> Iterator[_Value]:
    """Return an iterator over ``values`` that keeps repeating the last one.

    Short scripts are enough for long games, but the last value must be an
    answer the engine accepts, otherwise its validation loop never ends.
    """
    items = list(values)
    if not items:
        raise ValueError("a scripted answer list must not be empty")
    yield from items
    while True:
        yield items[-1]


class FakeUI:
    """A recording, scripted :class:`~hammurabi.game.UI` implementation.

    Every answer script is consumed in order and its last value is repeated
    forever. All calls are appended to :attr:`calls` as tuples and rejected
    answers are collected in :attr:`errors`.
    """

    def __init__(
        self,
        *,
        buy: Iterable[int] = (0,),
        sell: Iterable[int] = (0,),
        feed: Iterable[int] = (0,),
        plant: Iterable[int] = (0,),
        research: Iterable[str | None] = (None,),
    ) -> None:
        self._buy = repeat_last(buy)
        self._sell = repeat_last(sell)
        self._feed = repeat_last(feed)
        self._plant = repeat_last(plant)
        self._research = repeat_last(research)
        self.calls: list[tuple[object, ...]] = []
        self.errors: list[str] = []
        self.intro_shown = 0

    def names(self) -> list[str]:
        """Return the names of the recorded calls, in order."""
        return [str(call[0]) for call in self.calls]

    def show_intro(self, state: GameState) -> None:
        self.intro_shown += 1
        self.calls.append(("intro", state.year))

    def show_report(self, state: GameState) -> None:
        self.calls.append(
            (
                "report",
                state.year,
                state.starved_this_year,
                state.immigrants_this_year,
                state.population,
            )
        )

    def show_plague(self, *, before: int, after: int) -> None:
        self.calls.append(("plague", before, after))

    def show_status(self, state: GameState) -> None:
        self.calls.append(("status", state.population, state.bushels))

    def show_land_price(self, price: int) -> None:
        self.calls.append(("price", price))

    def ask_acres_to_buy(self, state: GameState, *, price: int) -> int:
        self.calls.append(("ask_buy", price, state.bushels))
        return next(self._buy)

    def ask_acres_to_sell(self, state: GameState, *, price: int) -> int:
        self.calls.append(("ask_sell", price, state.acres))
        return next(self._sell)

    def ask_bushels_to_feed(self, state: GameState) -> int:
        self.calls.append(("ask_feed", state.population, state.bushels))
        return next(self._feed)

    def ask_acres_to_plant(self, state: GameState) -> int:
        self.calls.append(("ask_plant", state.population, state.bushels))
        return next(self._plant)

    def ask_research(
        self, state: GameState, choices: Sequence[tech.Tech]
    ) -> str | None:
        self.calls.append(
            (
                "ask_research",
                state.year,
                state.bushels,
                tuple(item.key for item in choices),
            )
        )
        return next(self._research)

    def show_research(self, researched: tech.Tech) -> None:
        self.calls.append(("research", researched.key, researched.cost))

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def show_impeachment(self, state: GameState) -> None:
        self.calls.append(("impeachment", state.year, state.starved_this_year))

    def show_summary(self, state: GameState, verdict: Verdict) -> None:
        self.calls.append(("summary", state.year, verdict))


class CarefulUI(FakeUI):
    """A player who trades no land, feeds everyone and sows all they can.

    It is rule-aware on purpose: the engine tests use it to play whole games
    without scripting a term of answers by hand.
    """

    def ask_bushels_to_feed(self, state: GameState) -> int:
        self.calls.append(("ask_feed", state.population, state.bushels))
        wanted = state.population * config.BUSHELS_PER_PERSON
        return min(wanted, state.bushels)

    def ask_acres_to_plant(self, state: GameState) -> int:
        self.calls.append(("ask_plant", state.population, state.bushels))
        affordable = state.bushels * config.ACRES_PER_SEED_BUSHEL
        return min(
            state.acres,
            affordable,
            rules.max_plantable_acres(state.population),
        )


def plain_console(width: int = 100) -> tuple[Console, StringIO]:
    """Return a console that renders plain text into an in-memory buffer.

    Args:
        width: Terminal width the output is wrapped at.

    Returns:
        The console and the buffer it writes to.
    """
    buffer = StringIO()
    return Console(file=buffer, width=width, force_terminal=False), buffer


def render(buffer: StringIO) -> str:
    """Return the buffered output with all runs of whitespace collapsed.

    A ``rich`` console wraps long lines, so a sentence may be split over several
    lines. Collapsing the whitespace lets a test assert on the sentence as the
    player reads it.
    """
    return " ".join(buffer.getvalue().split())


# The three figures the console UI repeats in its questions; see ``ui.py``.
_STORE = re.compile(r"you have (\d+) bushels")
_LAND = re.compile(r"you own (\d+) acres")
_PEOPLE = re.compile(r"(\d+) people live in the city")


def careful_console_answers(question: str) -> str:
    """Answer a console question the way a careful ruler would.

    :class:`CarefulUI` plays from the state it is handed; this reader plays from
    the other side of the keyboard, reading the figures each question repeats.
    It never buys or sells land, feeds everyone it can afford and sows as much as
    land, seed and labour allow. It lets the tests play whole games through the
    real :class:`~hammurabi.ui.ConsoleUI`.

    Args:
        question: The question the UI printed, hints included.

    Returns:
        The answer, as the player would have typed it.
    """
    if "wish to research" in question:
        # The scripted player founds no school: 0 is the engine's accepted answer
        # for "research nothing this year", and a research node key cannot be
        # read from the question text alone.
        return "0"
    if "wish to buy" in question or "wish to sell" in question:
        return "0"
    store = int(_STORE.search(question).group(1))
    people = int(_PEOPLE.search(question).group(1))
    if "wish to feed" in question:
        return str(min(store, people * config.BUSHELS_PER_PERSON))
    return str(
        min(
            int(_LAND.search(question).group(1)),
            store * config.ACRES_PER_SEED_BUSHEL,
            rules.max_plantable_acres(people),
        )
    )

