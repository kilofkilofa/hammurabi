"""Unit tests for the optional agriculture rule set in :mod:`hammurabi.tech`.

The tree is pure data, so these tests pin its shape — the four branches, the
prerequisites, the price ladder and the capstone — as much as the arithmetic that
folds the unlocked nodes into the farming settings the rules are handed. The
*lifetime* the ladder is meant to fill is measured, not asserted here: see
``tests/test_simulation.py`` and ``docs/balancing.md``.
"""

from __future__ import annotations

import pytest

from hammurabi import config, tech
from hammurabi.models import Agriculture

#: Every key of the tree, in the order the UI prints it.
ALL_KEYS = tuple(item.key for item in tech.TECH_TREE)

#: The four branches, as the modules and the documents name them.
FIELD_KEYS = ("fallow", "manuring", "rotation", "flood_farming", "seed_corn")
SEED_KEYS = ("plough", "heavy_plough", "seed_drill")
STORE_KEYS = ("granaries", "silos", "vaults")
LABOUR_KEYS = ("draft_teams", "iron_ploughshares", "harvest_crews")

#: The nodes that are open from the first year.
OPENING_KEYS = ("plough", "fallow", "granaries")

#: A key that is not in the tree, for the error paths.
UNKNOWN = "taxes"

#: The price of every node, frozen. Retuning the ladder is a deliberate change:
#: this table, ``docs/plan.md`` and the measured batches all have to follow.
DOCUMENTED_COSTS = (
    ("plough", 400),
    ("fallow", 600),
    ("granaries", 850),
    ("manuring", 1250),
    ("draft_teams", 1850),
    ("heavy_plough", 2700),
    ("rotation", 3950),
    ("silos", 5800),
    ("iron_ploughshares", 8500),
    ("seed_drill", 12450),
    ("flood_farming", 18200),
    ("vaults", 26700),
    ("harvest_crews", 39100),
    ("seed_corn", 57250),
    ("almanac", 83900),
)


def _unlocked(*keys: str) -> frozenset[str]:
    """Return the keys as the frozen set a state stores."""
    return frozenset(keys)


# --- The shape of the tree ---------------------------------------------------


def test_the_tree_is_the_four_documented_branches_and_a_capstone() -> None:
    """The branches carry the tree; the capstone closes it, last of all."""
    assert set(ALL_KEYS) == set(
        FIELD_KEYS + SEED_KEYS + STORE_KEYS + LABOUR_KEYS + ("almanac",)
    )
    assert len(set(ALL_KEYS)) == len(ALL_KEYS)
    assert ALL_KEYS[-1] == "almanac"


def test_the_first_node_of_a_branch_is_what_the_next_one_needs() -> None:
    """Every rung waits for the rung below it, and only for that."""
    chain = {
        "manuring": "fallow",
        "rotation": "manuring",
        "flood_farming": "rotation",
        "seed_corn": "flood_farming",
        "heavy_plough": "plough",
        "seed_drill": "heavy_plough",
        "silos": "granaries",
        "vaults": "silos",
        "iron_ploughshares": "draft_teams",
        "harvest_crews": "iron_ploughshares",
    }
    for key, needs in chain.items():
        assert tech.FARMING.node(key).requires == _unlocked(needs)
    for key in OPENING_KEYS:
        assert tech.FARMING.node(key).requires == frozenset()


def test_every_node_is_reachable_from_the_opening_nodes() -> None:
    """No rung is stranded: each is open once the ones below it are unlocked."""
    unlocked: set[str] = set()
    while True:
        opened = {item.key for item in tech.FARMING.available(frozenset(unlocked))}
        if not opened:
            break
        unlocked |= opened
    assert unlocked == set(ALL_KEYS)


def test_the_printed_order_is_a_valid_plan() -> None:
    """A node never needs a rung printed below it, so the table can be followed.

    This is what lets ``docs/balancing.md`` speak of the order a city buys the
    tree in: the order of the table is one a ruler can actually pay for.
    """
    for rank, item in enumerate(tech.TECH_TREE):
        for need in item.requires:
            assert ALL_KEYS.index(need) < rank, f"{item.key} needs {need} later"


def test_the_capstone_waits_for_the_deepest_yield_and_the_best_storage() -> None:
    """The almanac closes the tree: without either branch it is not on offer."""
    almanac = tech.FARMING.node("almanac")
    assert almanac.requires == _unlocked("seed_corn", "vaults")
    assert "almanac" not in [item.key for item in tech.FARMING.available(_unlocked())]
    assert "almanac" not in [
        item.key for item in tech.FARMING.available(_unlocked(*FIELD_KEYS))
    ]
    assert "almanac" not in [
        item.key for item in tech.FARMING.available(_unlocked(*STORE_KEYS))
    ]
    assert "almanac" in [
        item.key for item in tech.FARMING.available(_unlocked(*(FIELD_KEYS + STORE_KEYS)))
    ]



def test_every_node_costs_the_documented_grain() -> None:
    """Each price is the constant ``config.py`` documents for it."""
    assert [(item.key, item.cost) for item in tech.TECH_TREE] == list(
        DOCUMENTED_COSTS
    )
    assert {item.key: item.cost for item in tech.TECH_TREE} == config.TECH_COSTS
    assert sorted(config.TECH_COSTS) == sorted(ALL_KEYS)


def test_the_prices_climb_a_ladder_of_about_half_again_a_rung() -> None:
    """The ladder is what stretches the programme over a lifetime.

    Every rung costs around half as much again as the one below it, which keeps
    the first nodes within reach of the opening years and the last ones out of
    reach of anything but decades of surplus.
    """
    rungs = [cost for _key, cost in DOCUMENTED_COSTS]
    assert rungs == sorted(rungs), "the ladder must be printed cheapest first"
    for lower, upper in zip(rungs, rungs[1:]):
        assert 1.4 <= upper / lower <= 1.55, f"{lower} -> {upper} leaves the ladder"


def test_the_first_year_can_afford_every_opening_node() -> None:
    """The tree opens with rungs the starting store can pay for out of hand."""
    offered = tech.FARMING.offers(_unlocked(), bushels=config.START_BUSHELS)
    assert [offer.node.key for offer in offered] == list(OPENING_KEYS)
    assert all(offer.node.cost <= config.START_BUSHELS for offer in offered)


def test_every_node_has_a_name_and_an_effect_for_the_player() -> None:
    for item in tech.TECH_TREE:
        assert item.name
        assert item.effect


def test_the_effects_name_the_figures_they_change() -> None:
    """The line the player reads quotes the constant behind it."""
    for key, rate in config.TECH_ACRES_PER_SEED.items():
        assert str(rate) in tech.FARMING.node(key).effect
    for key, rate in config.TECH_ACRES_PER_WORKER.items():
        assert str(rate) in tech.FARMING.node(key).effect
    for key, divisor in config.TECH_RAT_DIVISOR.items():
        assert f"1/{divisor}" in tech.FARMING.node(key).effect
    for key in FIELD_KEYS:
        assert (
            f"+{config.TECH_YIELD_BONUS_PER_NODE} bushel per acre"
            in tech.FARMING.node(key).effect
        )
    assert (
        f"+{config.TECH_YIELD_BONUS_ALMANAC} bushel per acre"
        in tech.FARMING.node("almanac").effect
    )


def test_the_second_rung_of_a_branch_quotes_the_first_one() -> None:
    """A deeper rung reads as the step it is: the rate it leaves behind."""
    seeds = config.TECH_ACRES_PER_SEED
    workers = config.TECH_ACRES_PER_WORKER
    assert (
        f"{seeds['plough']} -> {seeds['heavy_plough']}"
        in tech.FARMING.node("heavy_plough").effect
    )
    assert (
        f"{workers['draft_teams']} -> {workers['iron_ploughshares']}"
        in tech.FARMING.node("iron_ploughshares").effect
    )


def test_an_unknown_key_is_reported() -> None:
    with pytest.raises(KeyError):
        tech.FARMING.node(UNKNOWN)


def test_every_node_has_a_price() -> None:
    """The price of a node is the one ``config.py`` lists for its key."""
    assert all(item.cost for item in tech.TECH_TREE)


# --- What may be researched --------------------------------------------------


def test_the_sprouting_nodes_are_open_from_the_first_year() -> None:
    assert tuple(item.key for item in tech.FARMING.available(_unlocked())) == OPENING_KEYS


def test_a_node_waits_for_its_prerequisite() -> None:
    assert "manuring" not in [item.key for item in tech.FARMING.available(_unlocked())]
    assert "manuring" in [item.key for item in tech.FARMING.available(_unlocked("fallow"))]
    assert "silos" in [item.key for item in tech.FARMING.available(_unlocked("granaries"))]
    assert "rotation" not in [item.key for item in tech.FARMING.available(_unlocked("fallow"))]


def test_can_research_needs_the_prerequisites_and_the_grain() -> None:
    fallow = config.TECH_COSTS["fallow"]
    assert tech.FARMING.can_research("fallow", unlocked=_unlocked(), bushels=fallow)
    assert not tech.FARMING.can_research("fallow", unlocked=_unlocked(), bushels=fallow - 1)
    assert not tech.FARMING.can_research(
        "manuring", unlocked=_unlocked(), bushels=config.TECH_COSTS["manuring"]
    )
    assert not tech.FARMING.can_research(
        "fallow", unlocked=_unlocked("fallow"), bushels=fallow
    )


def test_can_research_reports_an_unknown_key() -> None:
    with pytest.raises(KeyError):
        tech.FARMING.can_research(UNKNOWN, unlocked=_unlocked(), bushels=10_000_000)


def test_offers_lists_what_the_store_can_pay_for_in_tree_order() -> None:
    costs = config.TECH_COSTS
    # A small store limits the list; so does the tree itself, however full the
    # store is: only what is unlocked and paid for is ever put on the table.
    assert tech.FARMING.offers(_unlocked(), bushels=0) == ()
    assert [
        offer.node.key for offer in tech.FARMING.offers(_unlocked(), bushels=costs["plough"])
    ] == ["plough"]
    assert [
        offer.node.key for offer in tech.FARMING.offers(_unlocked(), bushels=costs["rotation"])
    ] == list(OPENING_KEYS)


# --- The settings the rules are handed ---------------------------------------


def test_the_classic_game_researches_nothing() -> None:
    """An empty tree is the vintage game, rates and all."""
    assert tech.settings(frozenset()) == Agriculture()


def test_each_node_raises_the_setting_it_documents() -> None:
    for key, rate in config.TECH_ACRES_PER_SEED.items():
        assert tech.settings(_unlocked(key)).acres_per_seed == rate
    for key, rate in config.TECH_ACRES_PER_WORKER.items():
        assert tech.settings(_unlocked(key)).acres_per_worker == rate
    for key, divisor in config.TECH_RAT_DIVISOR.items():
        assert tech.settings(_unlocked(key)).rat_divisor == divisor
    for key in FIELD_KEYS:
        assert tech.settings(_unlocked(key)).yield_bonus == (
            config.TECH_YIELD_BONUS_PER_NODE
        )
    assert tech.settings(_unlocked("almanac")).yield_bonus == (
        config.TECH_YIELD_BONUS_ALMANAC
    )


def test_the_field_nodes_add_up_to_the_documented_maximum() -> None:
    """The five rungs of the fields and the almanac are the whole harvest."""
    fields = tech.settings(_unlocked(*FIELD_KEYS))
    assert fields.yield_bonus == 5 * config.TECH_YIELD_BONUS_PER_NODE
    assert tech.settings(_unlocked(*ALL_KEYS)).yield_bonus == (
        config.TECH_MAX_YIELD_BONUS
    )
    assert config.TECH_MAX_YIELD_BONUS == (
        5 * config.TECH_YIELD_BONUS_PER_NODE + config.TECH_YIELD_BONUS_ALMANAC
    )


def test_a_deeper_rate_supersedes_the_rung_below_it() -> None:
    """Rates do not stack; the best rung unlocked is the one in force."""
    divisors = config.TECH_RAT_DIVISOR
    stores = tech.settings(_unlocked("granaries", "vaults"))
    assert stores.rat_divisor == divisors["vaults"]
    assert stores.rat_divisor != divisors["granaries"] + divisors["vaults"]
    seeds = tech.settings(_unlocked("plough", "seed_drill"))
    assert seeds.acres_per_seed == config.TECH_ACRES_PER_SEED["seed_drill"]
    workers = tech.settings(_unlocked("draft_teams", "harvest_crews"))
    assert workers.acres_per_worker == config.TECH_ACRES_PER_WORKER["harvest_crews"]


def test_the_whole_tree_is_the_most_the_farming_can_give() -> None:
    full = tech.settings(_unlocked(*ALL_KEYS))
    assert full.yield_bonus == config.TECH_MAX_YIELD_BONUS
    assert full.acres_per_seed == config.TECH_ACRES_PER_SEED["seed_drill"]
    assert full.acres_per_worker == config.TECH_ACRES_PER_WORKER["harvest_crews"]
    assert full.rat_divisor == config.TECH_RAT_DIVISOR["almanac"]


def test_a_key_the_tree_does_not_know_is_ignored() -> None:
    """A stale key cannot raise here; :func:`tech.node` is what reports one."""
    assert tech.settings(_unlocked(UNKNOWN)) == Agriculture()
    assert tech.settings(_unlocked("plough", UNKNOWN)) == tech.settings(
        _unlocked("plough")
    )

