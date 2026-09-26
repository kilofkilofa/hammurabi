"""Data structures shared by the game.

``GameState`` holds the complete mutable state of a single game. The engine in
``game.py`` is the only component allowed to mutate it; the rules in ``rules.py``
treat it as input and never change it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hammurabi import config


class Verdict(Enum):
    """Final evaluation of the ruler after the term.

    The order follows the original game: worse verdicts are checked first.
    """

    IMPEACHED = "impeached"  # starved too many people, removed from office
    TYRANT = "tyrant"  # cruel and heavy-handed, compared to Nero and Ivan IV
    MEDIOCRE = "mediocre"  # "could have been better, but wasn't too bad"
    FANTASTIC = "fantastic"  # an outstanding performance


@dataclass
class GameState:
    """The complete mutable state of one game.

    Attributes:
        year: Number of years elapsed (2 means the game is in its second year).
        term_years: Length of the term being played, in years: the classic ten
            unless the marathon was chosen.
        population: People currently living in the city.
        acres: Acres of land owned.
        bushels: Bushels of grain in the store.
        starved_this_year: People who starved during the last year.
        immigrants_this_year: People who arrived during the last year.
        rats_ate_this_year: Bushels eaten by rats during the last year.
        yield_per_acre: Harvest of the last year in bushels per planted acre.
        plague_this_year: Whether the plague struck at the start of this year.
        plague_roll: Roll carried over from the previous year (``Q`` in the
            listing) that decides whether the plague strikes this year; a
            positive value means the year is safe.
        total_starved: People lost to starvation across the whole term.
        starved_percent_avg: Running average starvation percentage per year.
        would_be_assassins: People who would like to see the ruler
            assassinated; drawn only when the term ends on the mediocre
            verdict, which is the one that names the figure in the listing.
        game_over: Whether the game has finished.
        verdict: Final evaluation, set once ``game_over`` is true.
    """

    year: int = 0
    term_years: int = config.TERM_YEARS
    population: int = config.START_POPULATION
    acres: int = config.START_ACRES
    bushels: int = config.START_BUSHELS
    starved_this_year: int = 0
    immigrants_this_year: int = config.START_IMMIGRANTS
    rats_ate_this_year: int = config.START_RATS_ATE
    yield_per_acre: int = config.START_YIELD_PER_ACRE
    plague_this_year: bool = False
    plague_roll: int = config.START_PLAGUE_ROLL
    total_starved: int = 0
    starved_percent_avg: float = 0.0
    would_be_assassins: int = 0
    game_over: bool = False
    verdict: Verdict | None = None

    @property
    def acres_per_person(self) -> float:
        """Return owned acres per person (``0.0`` when the city is empty)."""
        if self.population <= 0:
            return 0.0
        return self.acres / self.population
