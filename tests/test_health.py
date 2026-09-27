"""Unit tests for the optional health rule set in :mod:`hammurabi.health`.

The tree is pure data, so these tests pin its shape — the four branches, the
prerequisites, the price ladder and the capstone — as much as the arithmetic that
folds the unlocked measures into the public health the rules are handed. What the
tree is *worth* is measured, not asserted here: see ``tests/test_simulation.py`` and
``docs/balancing.md``, which record how far a reign actually climbs it.
"""

from __future__ import annotations

import pytest

from hammurabi import config, health
from hammurabi.models import Health

#: Every key of the tree, in the order the UI prints it.
ALL_KEYS = tuple(item.key for item in health.HEALTH_TREE)

#: The four branches, as the module and the documents name them.
WATER_KEYS = ("wells", "drained_streets", "brick_drains")
HEALER_KEYS = (
    "herb_gatherers",
    "physicians",
    "doctors",
    "healing_houses",
    "temple_hospital",
)
NURSERY_KEYS = (
    "midwives",
    "wet_nurses",
    "milk_herds",
    "birthing_houses",
    "foundling_home",
    "palace_nursery",
)
FOOD_KEYS = ("milled_grain", "kitchen_gardens", "oil_presses", "fish_ponds")

#: The measures that are open from the first year: one of each branch.
OPENING_KEYS = ("wells", "herb_gatherers", "midwives", "milled_grain")

#: A key that is not in the tree, for the error paths.
UNKNOWN = "irrigation"

#: The price of every measure, frozen. Retuning the ladder is a deliberate change:
#: this table, ``docs/plan.md`` and the measured batches all have to follow.
DOCUMENTED_COSTS = (
    ("wells", 100),
    ("herb_gatherers", 140),
    ("midwives", 190),
    ("milled_grain", 250),
    ("drained_streets", 330),
    ("physicians", 450),
    ("wet_nurses", 610),
    ("kitchen_gardens", 820),
    ("brick_drains", 1100),
    ("doctors", 1500),
    ("milk_herds", 2000),
    ("oil_presses", 2700),
    ("healing_houses", 3700),
    ("birthing_houses", 4900),
    ("fish_ponds", 6700),
    ("temple_hospital", 9000),
    ("foundling_home", 12000),
    ("palace_nursery", 16000),
    ("house_of_life", 22000),
)


def _unlocked(*keys: str) -> frozenset[str]:
    """Return the keys as the frozen set a state stores."""
    return frozenset(keys)


# --- The shape of the tree ---------------------------------------------------


def test_the_tree_is_the_documented_branches_and_a_capstone() -> None:
    """Three water rungs, five healers, six nursery rungs, four of food, one top."""
    assert set(ALL_KEYS) == set(
        WATER_KEYS + HEALER_KEYS + NURSERY_KEYS + FOOD_KEYS + ("house_of_life",)
    )
    assert len(set(ALL_KEYS)) == len(ALL_KEYS)
    assert (len(WATER_KEYS), len(HEALER_KEYS), len(NURSERY_KEYS), len(FOOD_KEYS)) == (
        3,
        5,
        6,
        4,
    )
    assert len(ALL_KEYS) == 19
    assert ALL_KEYS[-1] == "house_of_life"


def test_the_first_measure_of_a_branch_is_what_the_next_one_needs() -> None:
    """Every rung waits for the rung below it, and only for that."""
    chain = {
        "drained_streets": "wells",
        "brick_drains": "drained_streets",
        "physicians": "herb_gatherers",
        "doctors": "physicians",
        "healing_houses": "doctors",
        "temple_hospital": "healing_houses",
        "wet_nurses": "midwives",
        "milk_herds": "wet_nurses",
        "birthing_houses": "milk_herds",
        "foundling_home": "birthing_houses",
        "palace_nursery": "foundling_home",
        "kitchen_gardens": "milled_grain",
        "oil_presses": "kitchen_gardens",
        "fish_ponds": "oil_presses",
    }
    for key, needs in chain.items():
        assert health.HEALTH.node(key).requires == _unlocked(needs)
    for key in OPENING_KEYS:
        assert health.HEALTH.node(key).requires == frozenset()


def test_every_measure_is_reachable_from_the_opening_ones() -> None:
    """No rung is stranded: each is open once the ones below it are unlocked."""
    unlocked: set[str] = set()
    while True:
        opened = {item.key for item in health.HEALTH.available(frozenset(unlocked))}
        if not opened:
            break
        unlocked |= opened
    assert unlocked == set(ALL_KEYS)


def test_the_printed_order_is_a_valid_plan() -> None:
    """A measure never needs a rung printed below it, so the table can be followed."""
    for rank, item in enumerate(health.HEALTH_TREE):
        for need in item.requires:
            assert ALL_KEYS.index(need) < rank, f"{item.key} needs {need} later"


def test_the_capstone_waits_for_the_deepest_measure_of_every_branch() -> None:
    """The House of Life closes the tree: without a branch it is not on offer."""
    capstone = health.HEALTH.node("house_of_life")
    assert capstone.requires == _unlocked(
        "brick_drains", "temple_hospital", "palace_nursery", "fish_ponds"
    )
    branches = (WATER_KEYS, HEALER_KEYS, NURSERY_KEYS, FOOD_KEYS)
    for omitted in branches:
        unlocked = tuple(
            key for branch in branches if branch is not omitted for key in branch
        )
        assert "house_of_life" not in [
            item.key for item in health.HEALTH.available(_unlocked(*unlocked))
        ], f"the capstone opens without the {omitted[0]} branch"
    every_branch = tuple(key for branch in branches for key in branch)
    assert "house_of_life" in [
        item.key for item in health.HEALTH.available(_unlocked(*every_branch))
    ]


# --- The ladder --------------------------------------------------------------


def test_every_measure_costs_the_documented_grain() -> None:
    """Each price is the constant ``config.py`` documents for it."""
    assert [(item.key, item.cost) for item in health.HEALTH_TREE] == list(
        DOCUMENTED_COSTS
    )
    assert {item.key: item.cost for item in health.HEALTH_TREE} == config.HEALTH_COSTS
    assert sorted(config.HEALTH_COSTS) == sorted(ALL_KEYS)


def test_the_ladder_climbs_by_about_a_third_and_is_the_modest_programme() -> None:
    """The prices rise by about a third a step, as the farming ladder does."""
    rungs = [cost for _key, cost in DOCUMENTED_COSTS]
    assert rungs == sorted(rungs), "the ladder must be printed cheapest first"
    for lower, upper in zip(rungs, rungs[1:]):
        assert 1.3 <= upper / lower <= 1.45, f"{lower} -> {upper} leaves the ladder"
    assert sum(rungs) < sum(config.TECH_COSTS.values()), (
        "the health tree is the modest programme of the two"
    )


def test_the_first_year_can_afford_every_opening_measure() -> None:
    """The tree opens with rungs the starting store can pay for out of hand."""
    offered = health.HEALTH.offers(_unlocked(), bushels=config.START_BUSHELS)
    assert [offer.node.key for offer in offered] == list(OPENING_KEYS)
    assert all(offer.node.cost <= config.START_BUSHELS for offer in offered)


def test_every_measure_has_a_name_and_an_effect_for_the_player() -> None:
    for item in health.HEALTH_TREE:
        assert item.name
        assert item.effect


def test_the_effects_name_the_figures_they_change() -> None:
    """Every rate a rung reaches is printed next to it, so the table cannot lie."""
    for key, rate in config.HEALTH_SURVIVOR_PERCENT.items():
        assert f"{rate}%" in health.HEALTH.node(key).effect
    for key, rate in config.HEALTH_BIRTHS_PER_THOUSAND.items():
        assert f"+{rate} births" in health.HEALTH.node(key).effect
    for key, rate in config.HEALTH_BUSHELS_PER_PERSON.items():
        assert f"{rate} bushels per person" in health.HEALTH.node(key).effect
    for key, rate in config.HEALTH_RESISTANCE.items():
        assert f"+{rate}" in health.HEALTH.node(key).effect
    # The capstone carries two rates, and the table names both of them.
    capstone = health.HEALTH.node("house_of_life").effect
    assert f"+{config.HEALTH_BIRTHS_PER_THOUSAND['house_of_life']} births" in capstone
    assert f"{config.HEALTH_SURVIVOR_PERCENT['house_of_life']}%" in capstone


def test_an_unknown_key_is_reported() -> None:
    with pytest.raises(KeyError):
        health.HEALTH.node(UNKNOWN)


def test_every_measure_has_a_price() -> None:
    """The price of a measure is the one ``config.py`` lists for its key."""
    assert all(item.cost for item in health.HEALTH_TREE)
    assert len(config.HEALTH_COSTS) == len(health.HEALTH_TREE)


# --- What may be researched --------------------------------------------------


def test_the_opening_measures_are_open_from_the_first_year() -> None:
    assert (
        tuple(item.key for item in health.HEALTH.available(_unlocked()))
        == OPENING_KEYS
    )


def test_a_measure_waits_for_its_prerequisite() -> None:
    assert "physicians" not in [
        item.key for item in health.HEALTH.available(_unlocked())
    ]
    assert "physicians" in [
        item.key for item in health.HEALTH.available(_unlocked("herb_gatherers"))
    ]
    assert "fish_ponds" not in [
        item.key for item in health.HEALTH.available(_unlocked("kitchen_gardens"))
    ]


def test_can_research_needs_the_prerequisites_and_the_grain() -> None:
    wells = config.HEALTH_COSTS["wells"]
    assert health.HEALTH.can_research("wells", unlocked=_unlocked(), bushels=wells)
    assert not health.HEALTH.can_research(
        "wells", unlocked=_unlocked(), bushels=wells - 1
    )
    assert not health.HEALTH.can_research(
        "drained_streets",
        unlocked=_unlocked(),
        bushels=config.HEALTH_COSTS["drained_streets"],
    )
    assert not health.HEALTH.can_research(
        "wells", unlocked=_unlocked("wells"), bushels=wells
    )


def test_can_research_reports_an_unknown_key() -> None:
    with pytest.raises(KeyError):
        health.HEALTH.can_research(UNKNOWN, unlocked=_unlocked(), bushels=10**6)


def test_offers_lists_what_the_store_can_pay_for_in_tree_order() -> None:
    costs = config.HEALTH_COSTS
    assert health.HEALTH.offers(_unlocked(), bushels=0) == ()
    assert [
        offer.node.key
        for offer in health.HEALTH.offers(_unlocked(), bushels=costs["midwives"])
    ] == ["wells", "herb_gatherers", "midwives"]
    assert [
        offer.node.key
        for offer in health.HEALTH.offers(_unlocked(), bushels=10**6)
    ] == list(OPENING_KEYS)
    # Every offer names the programme it comes from, which is how the UI tells the
    # two rule sets apart when both are played.
    assert {
        offer.programme
        for offer in health.HEALTH.offers(_unlocked(), bushels=10**6)
    } == {"healers"}


# --- The health the rules are handed -----------------------------------------


def test_the_classic_game_builds_nothing() -> None:
    """An empty tree is the vintage game: half the city, no births, twenty bushels."""
    assert health.healers(frozenset()) == Health()


def test_each_measure_raises_the_rate_it_documents() -> None:
    for key, rate in config.HEALTH_SURVIVOR_PERCENT.items():
        assert health.healers(_unlocked(key)).plague_survivor_percent == rate
    for key, rate in config.HEALTH_RESISTANCE.items():
        assert health.healers(_unlocked(key)).plague_resistance == rate
    for key, rate in config.HEALTH_BIRTHS_PER_THOUSAND.items():
        assert health.healers(_unlocked(key)).births_per_thousand == rate
    for key, rate in config.HEALTH_BUSHELS_PER_PERSON.items():
        assert health.healers(_unlocked(key)).bushels_per_person == rate


def test_a_deeper_rate_supersedes_the_measure_below_it() -> None:
    """Rates do not stack; the best rung unlocked is the one in force."""
    survivors = config.HEALTH_SURVIVOR_PERCENT
    healers = health.healers(_unlocked("herb_gatherers", "physicians"))
    assert healers.plague_survivor_percent == survivors["physicians"]
    assert healers.plague_survivor_percent != (
        survivors["herb_gatherers"] + survivors["physicians"]
    )
    births = health.healers(_unlocked("wet_nurses", "milk_herds")).births_per_thousand
    assert births == config.HEALTH_BIRTHS_PER_THOUSAND["milk_herds"]


def test_the_feeding_rate_is_the_one_rate_where_less_wins() -> None:
    """Milled grain and fish ponds both count; the smaller rate feeds more people."""
    ponds = health.healers(_unlocked(*FOOD_KEYS)).bushels_per_person
    assert ponds == config.HEALTH_BUSHELS_PER_PERSON["fish_ponds"]
    assert ponds == min(config.HEALTH_BUSHELS_PER_PERSON.values())
    assert health.healers(_unlocked("milled_grain")).bushels_per_person == (
        config.HEALTH_BUSHELS_PER_PERSON["milled_grain"]
    )


def test_the_capstone_is_the_most_the_tree_can_give() -> None:
    full = health.healers(_unlocked(*ALL_KEYS))
    assert full.plague_survivor_percent == max(config.HEALTH_SURVIVOR_PERCENT.values())
    assert full.plague_resistance == max(config.HEALTH_RESISTANCE.values())
    assert full.births_per_thousand == max(
        config.HEALTH_BIRTHS_PER_THOUSAND.values()
    )
    assert full.bushels_per_person == min(config.HEALTH_BUSHELS_PER_PERSON.values())


def test_no_measure_abolishes_the_plague_or_kills_nobody() -> None:
    """The tree's ceilings leave both the plague and the feeding possible."""
    full = health.healers(_unlocked(*ALL_KEYS))
    assert 0 < full.plague_survivor_percent < 100, "somebody must die of it"
    assert full.plague_resistance < 4, "the plague must always be able to come"
    assert full.bushels_per_person > 0, "feeding must cost something"


def test_a_key_the_tree_does_not_know_is_ignored() -> None:
    """A stale key cannot raise here; :meth:`health.HEALTH.node` reports one."""
    assert health.healers(_unlocked(UNKNOWN)) == Health()
    assert health.healers(_unlocked("wells", UNKNOWN)) == health.healers(
        _unlocked("wells")
    )
    assert health.healers(_unlocked("plough")) == Health(), (
        "a farming key must not change the public health"
    )
