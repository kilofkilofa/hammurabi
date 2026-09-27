"""Unit tests for the pure game rules in :mod:`hammurabi.rules`."""

from __future__ import annotations

import pytest

from hammurabi import config, rules
from hammurabi.models import Verdict
from hammurabi.random_source import SeededRandom
from tests.support import StubRandom


# --- Fidelity to the documented rules ----------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("START_POPULATION", 95),
        ("START_BUSHELS", 2800),
        ("START_ACRES", 1000),
        ("TERM_YEARS", 10),
        ("MARATHON_TERM_YEARS", 100),
        ("MAX_TERM_YEARS", 1000),
        ("START_IMMIGRANTS", 5),
        ("START_RATS_ATE", 200),
        ("LAND_PRICE_MIN", 17),
        ("LAND_PRICE_MAX", 26),
        ("BUSHELS_PER_PERSON", 20),
        ("ACRES_PER_SEED_BUSHEL", 2),
        ("ACRES_PER_WORKER", 10),
        ("YIELD_MIN", 1),
        ("YIELD_MAX", 5),
        ("PLAGUE_ROLL_OFFSET", 0.3),
        ("START_PLAGUE_ROLL", 1),
        ("IMPEACHMENT_STARVATION_RATIO", 0.45),
        ("VERDICT_ASSASSIN_SHARE", 0.8),
        ("TECH_YIELD_BONUS_PER_NODE", 1),
        ("TECH_YIELD_BONUS_ALMANAC", 1),
        ("TECH_MAX_YIELD_BONUS", 6),
        (
            "TECH_ACRES_PER_SEED",
            {"plough": 3, "heavy_plough": 4, "seed_drill": 5},
        ),
        (
            "TECH_ACRES_PER_WORKER",
            {"draft_teams": 12, "iron_ploughshares": 14, "harvest_crews": 16},
        ),
        (
            "TECH_RAT_DIVISOR",
            {"granaries": 2, "silos": 3, "vaults": 4, "almanac": 5},
        ),
    ],
)
def test_config_matches_documented_rules(name: str, expected: object) -> None:
    assert getattr(config, name) == expected


# --- Random events -----------------------------------------------------------


def test_land_price_stays_within_the_documented_range() -> None:
    rng = SeededRandom(seed=1)
    prices = [rules.land_price(rng) for _ in range(500)]
    assert all(
        config.LAND_PRICE_MIN <= price <= config.LAND_PRICE_MAX for price in prices
    )
    assert len(set(prices)) > 1  # the price actually varies


def test_harvest_yield_stays_within_the_documented_range() -> None:
    rng = SeededRandom(seed=2)
    yields = [rules.harvest_yield(rng) for _ in range(500)]
    assert all(config.YIELD_MIN <= value <= config.YIELD_MAX for value in yields)
    assert len(set(yields)) > 1


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.0, True),
        (0.05, True),
        (0.15, True),
        (0.19, True),
        (0.2, False),
        (0.9, False),
    ],
)
def test_plague_strikes_when_the_roll_is_not_positive(
    value: float, expected: bool
) -> None:
    roll = rules.plague_roll(StubRandom(randoms=[value]))

    assert rules.plague_strikes(roll) is expected


def test_the_starting_plague_roll_keeps_the_first_year_safe() -> None:
    # The listing starts from ``Q=1`` (line 110).
    assert rules.plague_strikes(config.START_PLAGUE_ROLL) is False


def test_the_plague_roll_covers_minus_three_to_sixteen() -> None:
    # ``INT(10 * (2 * RND(1) - .3))`` covers -3 to 16.
    rolls = [
        rules.plague_roll(StubRandom(randoms=[value / 100]))
        for value in range(100)
    ]

    assert min(rolls) == -3
    assert max(rolls) == 16


def test_the_plague_strikes_for_one_fifth_of_the_rolls() -> None:
    # The listing's comment calls it "a 15% chance" (line 541), but its own
    # expression strikes for every draw below 0.2.
    rolls = [
        rules.plague_roll(StubRandom(randoms=[value / 100]))
        for value in range(100)
    ]

    assert sum(1 for roll in rolls if rules.plague_strikes(roll)) == 20


def test_plague_kills_half_of_the_population() -> None:
    assert rules.plague_survivors(101) == 50
    assert rules.plague_survivors(100) == 50


@pytest.mark.parametrize("roll", [1, 3, 5])
def test_rats_do_not_strike_on_odd_rolls(roll: int) -> None:
    assert rules.rats_eaten(StubRandom(integers=[roll]), store=1000) == 0


@pytest.mark.parametrize(("roll", "expected"), [(2, 500), (4, 250)])
def test_rats_eat_the_store_divided_by_the_even_roll(roll: int, expected: int) -> None:
    assert rules.rats_eaten(StubRandom(integers=[roll]), store=1000) == expected


def test_immigrants_follow_the_reference_formula() -> None:
    # factor=5, acres=1000, bushels=2800, population=100
    # -> int(5 * (20*1000 + 2800) / 100 / 100 + 1) = int(12.4) = 12
    stub = StubRandom(integers=[5])
    assert rules.immigrants(stub, acres=1000, bushels=2800, population=100) == 12


def test_immigrants_without_population_is_zero() -> None:
    assert rules.immigrants(StubRandom(), acres=1000, bushels=2800, population=0) == 0


# --- Food, seed, labour and harvest ------------------------------------------


@pytest.mark.parametrize(
    ("bushels", "expected"),
    [(0, 0), (19, 0), (20, 1), (39, 1), (40, 2), (2000, 100)],
)
def test_people_fed_uses_twenty_bushels_per_person(bushels: int, expected: int) -> None:
    assert rules.people_fed(bushels) == expected


def test_starvation_counts_unfed_people() -> None:
    assert rules.starvation(100, 80) == 20


def test_starvation_is_zero_when_everyone_is_fed() -> None:
    assert rules.starvation(100, 120) == 0


@pytest.mark.parametrize(
    ("acres", "expected"), [(0, 0), (1, 0), (2, 1), (3, 1), (10, 5)]
)
def test_seed_cost_is_one_bushel_per_two_acres(acres: int, expected: int) -> None:
    assert rules.seed_cost(acres) == expected


@pytest.mark.parametrize(
    ("population", "expected"), [(0, 0), (1, 9), (95, 949), (100, 999)]
)
def test_max_plantable_acres_is_ten_per_person_minus_one(
    population: int, expected: int
) -> None:
    assert rules.max_plantable_acres(population) == expected


def test_harvest_multiplies_acres_by_the_yield() -> None:
    assert rules.harvest(500, 3) == 1500
    assert rules.harvest(0, 5) == 0


def test_not_impeached_at_exactly_45_percent() -> None:
    assert rules.is_impeached(100, 45) is False


def test_impeached_above_45_percent() -> None:
    assert rules.is_impeached(100, 46) is True


# --- Validation helpers ------------------------------------------------------


def test_can_buy_land_requires_enough_grain() -> None:
    assert rules.can_buy_land(10, 20, 200) is True
    assert rules.can_buy_land(11, 20, 200) is False
    assert rules.can_buy_land(-1, 20, 200) is False


def test_can_sell_land_must_keep_one_acre() -> None:
    assert rules.can_sell_land(999, 1000) is True
    assert rules.can_sell_land(0, 1000) is True
    assert rules.can_sell_land(1000, 1000) is False
    assert rules.can_sell_land(-1, 1000) is False


def test_can_feed_people_within_the_store() -> None:
    assert rules.can_feed_people(2800, 2800) is True
    assert rules.can_feed_people(0, 2800) is True
    assert rules.can_feed_people(2801, 2800) is False
    assert rules.can_feed_people(-1, 2800) is False


def test_can_plant_respects_land_seed_and_labour() -> None:
    assert rules.can_plant(500, owned=1000, bushels=2800, population=100) is True
    # more acres than owned land
    assert rules.can_plant(1001, owned=1000, bushels=2800, population=100) is False
    # not enough grain for the seed
    assert rules.can_plant(500, owned=1000, bushels=10, population=100) is False
    # labour limit for 100 people is 999 acres
    assert rules.can_plant(999, owned=1000, bushels=2800, population=100) is True
    assert rules.can_plant(1000, owned=1000, bushels=2800, population=100) is False


# --- Scoring -----------------------------------------------------------------


def test_acreage_per_person() -> None:
    assert rules.acreage_per_person(1000, 100) == pytest.approx(10.0)


def test_acreage_per_person_without_population_is_zero() -> None:
    assert rules.acreage_per_person(1000, 0) == 0.0


def test_counts_towards_starvation_only_when_the_food_was_needed() -> None:
    # ``550 IF P<C THEN 210``: feeding more people than are alive skips the year.
    assert rules.counts_towards_starvation(100, 100) is True
    assert rules.counts_towards_starvation(100, 95) is True
    assert rules.counts_towards_starvation(100, 101) is False


def test_would_be_assassins_follows_the_reference_formula() -> None:
    # ``INT(P * .8 * RND(1))`` with 100 people and a draw of 0.25.
    stub = StubRandom(randoms=[0.25])

    assert rules.would_be_assassins(stub, 100) == 20


    result = rules.update_starvation_average(
        0.0, year=1, starved=10, population=100
    )
    assert result == pytest.approx(10.0)


def test_starvation_average_is_a_running_mean() -> None:
    result = rules.update_starvation_average(
        10.0, year=2, starved=0, population=100
    )
    assert result == pytest.approx(5.0)


def test_starvation_average_without_population_is_zero() -> None:
    assert rules.update_starvation_average(0.0, year=1, starved=0, population=0) == 0.0


@pytest.mark.parametrize(
    ("starved", "acres_per_person", "expected"),
    [
        (34, 10.0, Verdict.IMPEACHED),
        (0, 6.9, Verdict.IMPEACHED),
        (33, 7.0, Verdict.TYRANT),  # boundaries are exclusive
        (11, 20.0, Verdict.TYRANT),
        (0, 8.9, Verdict.TYRANT),
        (3.1, 20.0, Verdict.MEDIOCRE),
        (0, 9.9, Verdict.MEDIOCRE),
        (3.0, 10.0, Verdict.FANTASTIC),  # boundaries are exclusive
        (0.0, 10.0, Verdict.FANTASTIC),
    ],
)
def test_evaluate_verdict(
    starved: float, acres_per_person: float, expected: Verdict
) -> None:
    assert rules.evaluate_verdict(starved, acres_per_person) is expected


# --- Random source -----------------------------------------------------------


def test_seeded_random_reproduces_the_same_sequence() -> None:
    first = SeededRandom(seed=1234)
    second = SeededRandom(seed=1234)
    assert [first.randint(1, 5) for _ in range(20)] == [
        second.randint(1, 5) for _ in range(20)
    ]


def test_seeded_random_floats_are_in_the_unit_interval() -> None:
    rng = SeededRandom(seed=99)
    assert all(0.0 <= rng.random() < 1.0 for _ in range(50))


# --- The optional farming technology -----------------------------------------
#
# The agriculture rule set reaches the rules through keyword arguments that
# default to the classic values, so a caller that passes nothing keeps playing
# the 1978 game. Each test below pins one of those seams.


def test_harvest_yield_adds_the_technology_bonus() -> None:
    rng = StubRandom(integers=[3])
    assert rules.harvest_yield(rng, bonus=config.TECH_YIELD_BONUS_PER_NODE) == (
        3 + config.TECH_YIELD_BONUS_PER_NODE
    )


def test_harvest_yield_has_no_bonus_by_default() -> None:
    assert rules.harvest_yield(StubRandom(integers=[5])) == 5


def test_rats_eat_a_divisor_less_with_granaries() -> None:
    granary = StubRandom(integers=[4])
    divisor = config.TECH_RAT_DIVISOR["granaries"]
    assert rules.rats_eaten(granary, 1000, divisor=divisor) == 1000 // 4 // divisor


def test_rats_eat_the_classic_share_by_default() -> None:
    assert rules.rats_eaten(StubRandom(integers=[4]), 1000) == 250


def test_seed_cost_uses_the_rate_it_is_given() -> None:
    plough = config.TECH_ACRES_PER_SEED["plough"]
    assert rules.seed_cost(999, acres_per_seed=plough) == 333
    assert rules.seed_cost(999) == 499  # the classic two acres per bushel


def test_max_plantable_acres_uses_the_rate_it_is_given() -> None:
    draft = config.TECH_ACRES_PER_WORKER["draft_teams"]
    assert rules.max_plantable_acres(100, acres_per_worker=draft) == 1199
    assert rules.max_plantable_acres(100) == 999


def test_can_plant_follows_the_technology_it_is_given() -> None:
    classic = {"owned": 1000, "bushels": 400, "population": 100}
    plough = config.TECH_ACRES_PER_SEED["plough"]
    draft = config.TECH_ACRES_PER_WORKER["draft_teams"]
    assert not rules.can_plant(999, **classic)
    assert rules.can_plant(999, **classic, acres_per_seed=plough)
    assert rules.can_plant(
        1000,
        owned=1000,
        bushels=1000,
        population=100,
        acres_per_worker=draft,
    )

