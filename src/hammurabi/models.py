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


@dataclass(frozen=True)
class Agriculture:
    """The farming technology in force in a game.

    The classic game plays with the defaults below and never researches
    anything. The optional agriculture rule set raises them through the tech tree
    in :mod:`hammurabi.tech`; the engine reads the resulting values once a year
    and passes them to the rules as plain arguments, so ``rules.py`` never has to
    know which rule set is being played.

    Attributes:
        yield_bonus: Bushels added to every harvest roll (classic: none).
        acres_per_seed: Acres one bushel of seed sows (classic: 2).
        acres_per_worker: Acres one person can tend (classic: 10).
        rat_divisor: Extra divisor applied to the rats' share of the store
            (classic: 1, i.e. the rats eat ``store / roll``).
    """

    yield_bonus: int = 0
    acres_per_seed: int = config.ACRES_PER_SEED_BUSHEL
    acres_per_worker: int = config.ACRES_PER_WORKER
    rat_divisor: int = 1


@dataclass(frozen=True)
class Health:
    """The public health of the city.

    The classic game plays with the defaults below and builds nothing: the plague
    kills half the city, nobody is born and twenty bushels feed a person for a year.
    The optional health rule set raises these values through the tech tree in
    :mod:`hammurabi.health`; the engine reads the resulting values once a year and
    passes them to the rules as plain arguments, so ``rules.py`` never has to know
    which rule set is being played.

    Attributes:
        plague_survivor_percent: Share of the people who live through a plague year
            (classic: 50).
        plague_resistance: Added to the plague roll, so that the plague comes less
            often (classic: 0).
        births_per_thousand: Children born for every thousand people in a year the
            city fed itself (classic: 0).
        bushels_per_person: Bushels that feed one person for one year (classic: 20).
    """

    plague_survivor_percent: int = config.PLAGUE_SURVIVOR_PERCENT
    plague_resistance: int = 0
    births_per_thousand: int = 0
    bushels_per_person: int = config.BUSHELS_PER_PERSON


@dataclass
class GameState:
    """The complete mutable state of one game.

    Attributes:
        year: Number of years elapsed (2 means the game is in its second year).
        term_years: Length of the term being played, in years: the classic ten
            unless the marathon was chosen.
        agriculture: Whether the optional agriculture rule set is in play, in
            which case the ruler may research the farming technologies of
            :mod:`hammurabi.tech` while the term runs.
        health: Whether the optional health rule set is in play, in which case the
            ruler may research the public-health measures of
            :mod:`hammurabi.health` with the same yearly question. With both rule
            sets in play one question a year covers both trees.
        unlocked: Keys of the technologies researched so far, from either rule set;
            empty in every classic game.
        population: People currently living in the city.
        acres: Acres of land owned.
        bushels: Bushels of grain in the store.
        starved_this_year: People who starved during the last year.
        immigrants_this_year: People who arrived during the last year.
        born_this_year: Children born during the last year; ``0`` in a classic
            game, and in a year the city could not feed itself.
        rats_ate_this_year: Bushels eaten by rats during the last year.
        yield_per_acre: Harvest of the last year in bushels per planted acre.
        spare_bushels: Grain the ruler may spend on research this year: the store
            the opening report showed, less the food the people need and the seed
            the land needs, as ruled by :func:`hammurabi.rules.spare_grain` and
            written before the land trade because that is when the question is put.
            ``0`` in a classic game, which never researches, and in the first year
            of a term, which puts no research question.
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
    agriculture: bool = False
    health: bool = False
    unlocked: frozenset[str] = frozenset()
    population: int = config.START_POPULATION
    acres: int = config.START_ACRES
    bushels: int = config.START_BUSHELS
    starved_this_year: int = 0
    immigrants_this_year: int = config.START_IMMIGRANTS
    born_this_year: int = 0
    rats_ate_this_year: int = config.START_RATS_ATE
    yield_per_acre: int = config.START_YIELD_PER_ACRE
    spare_bushels: int = 0
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
