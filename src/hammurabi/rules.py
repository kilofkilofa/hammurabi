"""Pure game rules.

These functions implement the rules documented in ``docs/plan.md`` section 4.
They contain no terminal I/O, never mutate state and hold no globals, so they
are trivial to unit test. Randomness enters only through an injected
:class:`~hammurabi.random_source.RandomSource`, which keeps every rule
deterministic and reproducible.
"""

from __future__ import annotations

from hammurabi import config
from hammurabi.models import Verdict
from hammurabi.random_source import RandomSource

# --- Random events -----------------------------------------------------------


def land_price(rng: RandomSource) -> int:
    """Return this year's land price in bushels per acre (17-26)."""
    return rng.randint(config.LAND_PRICE_MIN, config.LAND_PRICE_MAX)


def harvest_yield(rng: RandomSource, *, bonus: int = 0) -> int:
    """Return this year's harvest in bushels per planted acre (1-5).

    Args:
        rng: Source of the roll.
        bonus: Bushels added to the roll, which is how the farming technologies
            of the agriculture rule set raise a harvest. It defaults to the
            classic game, where nothing is added.

    Returns:
        The harvest in bushels per planted acre.
    """
    return rng.randint(config.YIELD_MIN, config.YIELD_MAX) + bonus


def plague_roll(rng: RandomSource, *, resistance: int = 0) -> int:
    """Return the vintage plague roll ``INT(10 * (2 * RND(1) - .3))``.

    The listing draws this at the end of a year (line 542) to decide the year
    that follows. The roll ranges from -3 to 16 and is not positive for 20% of
    the draws, which is when the plague strikes.

    The water branch of the health rule set shifts the offset before the roll is
    taken, so the plague finds fewer years: one point of resistance moves the
    offset by a tenth, which takes five years in a hundred out of the plague.
    Shifting the offset rather than the roll itself is what makes that step
    possible at all, because the roll is whole and its own steps are five years
    wide near zero; a shift is also what keeps the deepest drains from abolishing
    the plague, which no rung of the tree may do.

    Args:
        rng: Source of the draw.
        resistance: Points of public-health resistance in force; ``0`` in the
            classic game, which draws exactly the vintage roll.

    Returns:
        The roll carried over to the next year.
    """
    shift = resistance * config.PLAGUE_RESISTANCE_OFFSET
    return int(10 * (2 * rng.random() - config.PLAGUE_ROLL_OFFSET + shift))


def plague_strikes(roll: int) -> bool:
    """Return whether the plague strikes for the given ``roll``.

    Mirrors ``227 IF Q>0 THEN 230``: the plague strikes unless the roll carried over
    from the previous year is positive. The public-health measures of the health rule
    set can only make that roll more often positive, which is why they enter through
    :func:`plague_roll` and not here.
    """
    return roll <= 0


def plague_survivors(
    population: int, *, survivor_percent: int = config.PLAGUE_SURVIVOR_PERCENT
) -> int:
    """Return the population left after a plague year.

    The classic rule buries half the city; the healer branch of the health rule set
    raises the share who live through the year, until one in twenty is buried. The
    multiplication happens before the division, so the classic fifty percent is the
    listing's ``P // 2`` for every population, odd ones included.

    Args:
        population: People alive before the plague.
        survivor_percent: Share of them who live through it.

    Returns:
        The people left after the plague.
    """
    return population * survivor_percent // 100


def rats_eaten(rng: RandomSource, store: int, *, divisor: int = 1) -> int:
    """Return the bushels eaten by rats this year.

    A fresh roll of 1-5 is made. On an odd roll nothing is eaten; on an even
    roll the rats eat ``store / roll / divisor``, i.e. a half or a quarter of
    the grain left in the store after feeding and seeding (but before the
    harvest), and less still once granaries or the almanac are unlocked.

    Args:
        rng: Source of the roll.
        store: Bushels currently in the store.
        divisor: Further divisor for the rats' share; ``1`` in the classic game,
            ``2`` with granaries and ``4`` with the Nippur almanac.

    Returns:
        The bushels lost to rats (never negative).
    """
    roll = rng.randint(config.RAT_ROLL_MIN, config.RAT_ROLL_MAX)
    if roll % 2 != 0:
        return 0
    return store // roll // divisor


def immigrants(rng: RandomSource, *, acres: int, bushels: int, population: int) -> int:
    """Return how many immigrants arrive this year.

    Mirrors the reference formula ``INT(C * (20 * A + S) / P / 100 + 1)`` where
    ``C`` is a fresh roll of 1-5, ``A`` the acres, ``S`` the grain in store and
    ``P`` the population.

    Args:
        rng: Source of the roll.
        acres: Acres owned.
        bushels: Bushels in the store.
        population: Current population.

    Returns:
        The number of newcomers, or ``0`` if the city has no people left.
    """
    if population <= 0:
        return 0
    factor = rng.randint(config.IMMIGRATION_ROLL_MIN, config.IMMIGRATION_ROLL_MAX)
    value = (
        factor
        * (config.IMMIGRATION_LAND_WEIGHT * acres + bushels)
        / population
        / config.IMMIGRATION_DIVISOR
        + config.IMMIGRATION_BASE
    )
    return int(value)


# --- Food, seed and labour ---------------------------------------------------


def people_fed(
    bushels_fed: int, *, bushels_per_person: int = config.BUSHELS_PER_PERSON
) -> int:
    """Return how many people ``bushels_fed`` can feed.

    The classic rule spends twenty bushels on a person for a year; the food branch of
    the health tree brings that rate down, and for this rate a lower value is the
    better medicine.

    Args:
        bushels_fed: Bushels the ruler set aside for the people.
        bushels_per_person: Bushels that feed one person for one year.

    Returns:
        The number of people the grain can feed.
    """
    return bushels_fed // bushels_per_person


def births(population: int, *, fed: int, per_thousand: int = 0) -> int:
    """Return how many children are born this year.

    The classic game has no birth rule, so the default of zero keeps it exactly as
    the listing left it. The health rule set raises the rate through its nursery
    branch, but only in a year in which the city fed itself: a hungry year is no time
    for a nursery, and this is also what keeps the rule from deepening a famine the
    ruler is already being judged for.

    Args:
        population: People living in the city this year.
        fed: People the grain of the year could feed.
        per_thousand: Children born for every thousand people; ``0`` in the classic
            game.

    Returns:
        The children born this year, who join the city at the start of the next one.
    """
    if per_thousand <= 0 or population <= 0 or fed < population:
        return 0
    return population * per_thousand // 1000


def starvation(population: int, fed: int) -> int:
    """Return how many people starve when only ``fed`` people can be fed."""
    return max(0, population - fed)


def counts_towards_starvation(population: int, fed: int) -> bool:
    """Return whether the year must be tallied in the starvation figures.

    Mirrors ``550 IF P<C THEN 210``: when the ruler feeds more grain than the
    people need, the listing jumps straight to the next year, so that year adds
    nothing to the running average, to the total of people starved or to the
    population.

    Args:
        population: People alive before the feeding.
        fed: People the grain could feed.

    Returns:
        ``True`` when the year counts.
    """
    return fed <= population


def seed_cost(
    acres_planted: int, *, acres_per_seed: int = config.ACRES_PER_SEED_BUSHEL
) -> int:
    """Return the bushels of seed needed for ``acres_planted``.

    The classic rule sows two acres per bushel; the ox-drawn plough sows three,
    which is why the rate is an argument rather than a constant read here.

    Args:
        acres_planted: Acres to sow.
        acres_per_seed: Acres one bushel of seed sows.

    Returns:
        The bushels of seed, rounded down exactly as in the listing.
    """
    return acres_planted // acres_per_seed


def max_plantable_acres(
    population: int, *, acres_per_worker: int = config.ACRES_PER_WORKER
) -> int:
    """Return the most acres the population can tend (``rate * P - 1``).

    Args:
        population: People available to work the fields.
        acres_per_worker: Acres one person can tend; the classic ten, twelve
            once draft teams are unlocked.

    Returns:
        The labour limit, never negative.
    """
    return max(0, acres_per_worker * population - 1)


def harvest(acres_planted: int, yield_per_acre: int) -> int:
    """Return the bushels harvested from ``acres_planted``."""
    return acres_planted * yield_per_acre


def is_impeached(population: int, starved: int) -> bool:
    """Return whether starving more than 45% in one year ends the game."""
    return starved > config.IMPEACHMENT_STARVATION_RATIO * population


# --- Validation helpers (used by the engine and the UI) ----------------------


def can_buy_land(acres: int, price: int, bushels: int) -> bool:
    """Return whether ``acres`` can be bought at ``price`` with ``bushels``."""
    return acres >= 0 and acres * price <= bushels


def can_sell_land(acres: int, owned: int) -> bool:
    """Return whether ``acres`` can be sold, keeping at least one acre."""
    return 0 <= acres < owned


def can_feed_people(bushels_fed: int, bushels: int) -> bool:
    """Return whether ``bushels_fed`` is a non-negative amount we can afford."""
    return 0 <= bushels_fed <= bushels


def can_plant(
    acres: int,
    *,
    owned: int,
    bushels: int,
    population: int,
    acres_per_seed: int = config.ACRES_PER_SEED_BUSHEL,
    acres_per_worker: int = config.ACRES_PER_WORKER,
) -> bool:
    """Return whether ``acres`` may be planted given land, seed and labour.

    The seed and labour limits follow the farming technologies in force: the
    classic game passes nothing and gets the vintage rates, while the
    agriculture rule set passes what its tech tree has unlocked.

    Args:
        acres: Acres the player wants to sow.
        owned: Acres the city owns.
        bushels: Bushels in the store.
        population: People available to work the fields.
        acres_per_seed: Acres one bushel of seed sows.
        acres_per_worker: Acres one person can tend.

    Returns:
        ``True`` when the land, the seed and the labour all allow ``acres``.
    """
    return (
        0 <= acres <= owned
        and seed_cost(acres, acres_per_seed=acres_per_seed) <= bushels
        and acres <= max_plantable_acres(population, acres_per_worker=acres_per_worker)
    )


# --- Scoring -----------------------------------------------------------------


def acreage_per_person(acres: int, population: int) -> float:
    """Return owned acres per person (``0.0`` when the city is empty)."""
    if population <= 0:
        return 0.0
    return acres / population


def would_be_assassins(rng: RandomSource, population: int) -> int:
    """Return how many people would like to see the ruler assassinated.

    Only the mediocre verdict uses this figure; the listing fills it in from
    ``INT(P * .8 * RND(1))`` (line 965).

    Args:
        rng: Source of the roll.
        population: People living in the city at the end of the term.

    Returns:
        The number of would-be assassins (never negative).
    """
    return int(population * config.VERDICT_ASSASSIN_SHARE * rng.random())


def update_starvation_average(
    previous: float, *, year: int, starved: int, population: int
) -> float:
    """Return the running average percentage of people starved per year.

    Mirrors ``P1 = ((Z - 1) * P1 + D * 100 / P) / Z`` for the given ``year``.

    Args:
        previous: The average from the previous year.
        year: The current year number (1-based).
        starved: People who starved this year.
        population: Population used to compute the percentage.

    Returns:
        The updated running average; ``0.0`` for non-positive years.
    """
    if year <= 0:
        return 0.0
    percent = 0.0 if population <= 0 else starved * 100.0 / population
    return ((year - 1) * previous + percent) / year


def evaluate_verdict(starved_percent_avg: float, acres_per_person: float) -> Verdict:
    """Return the final verdict for the given end-of-term statistics.

    Args:
        starved_percent_avg: Average percentage of the population starved per
            year.
        acres_per_person: Acres owned per person at the end of the term.

    Returns:
        The matching :class:`~hammurabi.models.Verdict`.
    """
    if (
        starved_percent_avg > config.VERDICT_STARVATION_CRITICAL
        or acres_per_person < config.VERDICT_ACRES_CRITICAL
    ):
        return Verdict.IMPEACHED
    if (
        starved_percent_avg > config.VERDICT_STARVATION_POOR
        or acres_per_person < config.VERDICT_ACRES_POOR
    ):
        return Verdict.TYRANT
    if (
        starved_percent_avg > config.VERDICT_STARVATION_MEDIOCRE
        or acres_per_person < config.VERDICT_ACRES_MEDIOCRE
    ):
        return Verdict.MEDIOCRE
    return Verdict.FANTASTIC

