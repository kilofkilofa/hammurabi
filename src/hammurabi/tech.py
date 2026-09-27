"""The optional agriculture rule set: the tech tree that improves a harvest.

The classic game has no research at all. This module holds the optional farming
rule set of ``docs/plan.md`` section 4 as pure data, so the engine can decide what
a ruler may start without knowing a single rule number, and it never touches
state, the RNG or the terminal: :func:`settings` merely folds the unlocked nodes
into the :class:`~hammurabi.models.Agriculture` values the rules take as
arguments.

Fifteen nodes stand in four branches that meet in a capstone. The ox-drawn plough
leads to the heavy plough and the seed drill, the fallow fields to manuring,
rotation, flood farming and the selected seed corn, the granaries to the sealed
silos and the temple vaults, and the tools of the field hands to the draft teams,
the iron ploughshares and the harvest crews. The **Nippur almanac**, which reads
the flood from the stars, needs the deepest yield and the best storage at once.

The prices climb by about a third a step, which is what turns the programme into
the work of a lifetime: a node a year is what a century in office affords, but the
later nodes cost what many harvests leave over, so the measured plan of
``docs/balancing.md`` needs eighty to ninety years to buy the whole tree. Every
price, rate and bonus is a constant in ``config.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from hammurabi import config
from hammurabi.models import Agriculture


@dataclass(frozen=True)
class TechDelta:
    """What one node of the tree adds to the farming technology in force.

    The harvest bonus of a field node is *added* to the running total, while every
    other field names the **rate** the node reaches: there the best unlocked value
    wins, so a later node supersedes an earlier one instead of stacking with it —
    the seed drill sows five acres a bushel where the ox-drawn plough sowed three,
    and the almanac leaves the rats a fifth where the vaults left them a quarter.

    Attributes:
        yield_bonus: Bushels added to every harvest roll.
        acres_per_seed: Acres one bushel of seed sows; ``0`` when the node does
            not touch the rate.
        acres_per_worker: Acres one person can tend; ``0`` when untouched.
        rat_divisor: Divisor applied to the rats' share of the store; ``0`` when
            untouched.
    """

    yield_bonus: int = 0
    acres_per_seed: int = 0
    acres_per_worker: int = 0
    rat_divisor: int = 0


@dataclass(frozen=True)
class Tech:
    """One node of the agriculture tree.

    Attributes:
        key: Stable identifier, the key stored in ``GameState.unlocked``.
        name: Name shown to the player.
        requires: Keys that must already be unlocked.
        effect: One line describing the node, for the UI to print.
        delta: What the node contributes to the farming technology: a bonus that
            adds up, or a rate that supersedes the one below it.
    """

    key: str
    name: str
    requires: frozenset[str]
    effect: str
    delta: TechDelta

    @property
    def cost(self) -> int:
        """Bushels of grain the research costs (``config.TECH_COSTS``)."""
        return config.TECH_COSTS[self.key]


#: The tree in the order the UI lists it, which is also the order a city that means
#: to last buys it: the cheap tools and stores of the opening years first, the
#: deeper rungs after them and the Nippur almanac last of all. The first three
#: nodes are open from the first year; every other node waits for its
#: prerequisites, and the capstone needs the deepest yield and the best storage at
#: once.
TECH_TREE: tuple[Tech, ...] = (
    Tech(
        key="plough",
        name="Ox-drawn plough",
        requires=frozenset(),
        effect=(
            f"{config.ACRES_PER_SEED_BUSHEL} -> "
            f"{config.TECH_ACRES_PER_SEED['plough']} acres per bushel of seed"
        ),
        delta=TechDelta(acres_per_seed=config.TECH_ACRES_PER_SEED["plough"]),
    ),
    Tech(
        key="fallow",
        name="Fallow fields",
        requires=frozenset(),
        effect=f"+{config.TECH_YIELD_BONUS_PER_NODE} bushel per acre",
        delta=TechDelta(yield_bonus=config.TECH_YIELD_BONUS_PER_NODE),
    ),
    Tech(
        key="granaries",
        name="Granaries",
        requires=frozenset(),
        effect=(
            f"the rats eat 1/{config.TECH_RAT_DIVISOR['granaries']} of their share"
        ),
        delta=TechDelta(rat_divisor=config.TECH_RAT_DIVISOR["granaries"]),
    ),
    Tech(
        key="manuring",
        name="Manured fields",
        requires=frozenset({"fallow"}),
        effect=f"+{config.TECH_YIELD_BONUS_PER_NODE} bushel per acre",
        delta=TechDelta(yield_bonus=config.TECH_YIELD_BONUS_PER_NODE),
    ),
    Tech(
        key="draft_teams",
        name="Draft teams",
        requires=frozenset({"plough"}),
        effect=(
            f"{config.ACRES_PER_WORKER} -> "
            f"{config.TECH_ACRES_PER_WORKER['draft_teams']} acres per person"
        ),
        delta=TechDelta(
            acres_per_worker=config.TECH_ACRES_PER_WORKER["draft_teams"]
        ),
    ),
    Tech(
        key="heavy_plough",
        name="Heavy plough",
        requires=frozenset({"plough"}),
        effect=(
            f"{config.TECH_ACRES_PER_SEED['plough']} -> "
            f"{config.TECH_ACRES_PER_SEED['heavy_plough']} acres per bushel of seed"
        ),
        delta=TechDelta(acres_per_seed=config.TECH_ACRES_PER_SEED["heavy_plough"]),
    ),
    Tech(
        key="rotation",
        name="Crop rotation",
        requires=frozenset({"manuring"}),
        effect=f"+{config.TECH_YIELD_BONUS_PER_NODE} bushel per acre",
        delta=TechDelta(yield_bonus=config.TECH_YIELD_BONUS_PER_NODE),
    ),
    Tech(
        key="silos",
        name="Sealed silos",
        requires=frozenset({"granaries"}),
        effect=f"the rats eat 1/{config.TECH_RAT_DIVISOR['silos']} of their share",
        delta=TechDelta(rat_divisor=config.TECH_RAT_DIVISOR["silos"]),
    ),
    Tech(
        key="iron_ploughshares",
        name="Iron ploughshares",
        requires=frozenset({"draft_teams"}),
        effect=(
            f"{config.TECH_ACRES_PER_WORKER['draft_teams']} -> "
            f"{config.TECH_ACRES_PER_WORKER['iron_ploughshares']} acres per person"
        ),
        delta=TechDelta(
            acres_per_worker=config.TECH_ACRES_PER_WORKER["iron_ploughshares"]
        ),
    ),
    Tech(
        key="seed_drill",
        name="Seed drill",
        requires=frozenset({"heavy_plough"}),
        effect=(
            f"{config.TECH_ACRES_PER_SEED['heavy_plough']} -> "
            f"{config.TECH_ACRES_PER_SEED['seed_drill']} acres per bushel of seed"
        ),
        delta=TechDelta(acres_per_seed=config.TECH_ACRES_PER_SEED["seed_drill"]),
    ),
    Tech(
        key="flood_farming",
        name="Flood farming",
        requires=frozenset({"rotation"}),
        effect=f"+{config.TECH_YIELD_BONUS_PER_NODE} bushel per acre",
        delta=TechDelta(yield_bonus=config.TECH_YIELD_BONUS_PER_NODE),
    ),
    Tech(
        key="vaults",
        name="Temple vaults",
        requires=frozenset({"silos"}),
        effect=f"the rats eat 1/{config.TECH_RAT_DIVISOR['vaults']} of their share",
        delta=TechDelta(rat_divisor=config.TECH_RAT_DIVISOR["vaults"]),
    ),
    Tech(
        key="harvest_crews",
        name="Harvest crews",
        requires=frozenset({"iron_ploughshares"}),
        effect=(
            f"{config.TECH_ACRES_PER_WORKER['iron_ploughshares']} -> "
            f"{config.TECH_ACRES_PER_WORKER['harvest_crews']} acres per person"
        ),
        delta=TechDelta(
            acres_per_worker=config.TECH_ACRES_PER_WORKER["harvest_crews"]
        ),
    ),
    Tech(
        key="seed_corn",
        name="Selected seed corn",
        requires=frozenset({"flood_farming"}),
        effect=f"+{config.TECH_YIELD_BONUS_PER_NODE} bushel per acre",
        delta=TechDelta(yield_bonus=config.TECH_YIELD_BONUS_PER_NODE),
    ),
    Tech(
        key="almanac",
        name="Nippur almanac",
        requires=frozenset({"seed_corn", "vaults"}),
        effect=(
            f"+{config.TECH_YIELD_BONUS_ALMANAC} bushel per acre, the rats eat "
            f"1/{config.TECH_RAT_DIVISOR['almanac']} of their share"
        ),
        delta=TechDelta(
            yield_bonus=config.TECH_YIELD_BONUS_ALMANAC,
            rat_divisor=config.TECH_RAT_DIVISOR["almanac"],
        ),
    ),
)

def node(key: str) -> Tech:
    """Return the tree node called ``key``.

    Args:
        key: Identifier of the node, as stored in ``GameState.unlocked``.

    Returns:
        The matching :class:`Tech`.

    Raises:
        KeyError: If the tree has no such node.
    """
    for item in TECH_TREE:
        if item.key == key:
            return item
    raise KeyError(key)


def available(unlocked: frozenset[str]) -> tuple[Tech, ...]:
    """Return the nodes whose prerequisites are met and that are still open.

    ``unlocked`` is read as a set and never changed; tree order is kept, so the
    first entry is the one the UI lists first.
    """
    return tuple(
        item
        for item in TECH_TREE
        if item.key not in unlocked and item.requires <= unlocked
    )


def can_research(key: str, *, unlocked: frozenset[str], bushels: int) -> bool:
    """Return whether ``key`` may be started with ``bushels`` in the store.

    A node may be started when its prerequisites are met, it is not unlocked yet
    and the grain in store covers its cost.

    Args:
        key: Identifier of the node the ruler wants to start.
        unlocked: Keys of the technologies already unlocked.
        bushels: Grain in store, which the research is paid from.

    Returns:
        ``True`` when the research may start.

    Raises:
        KeyError: If the tree has no node called ``key``.
    """
    item = node(key)
    return item in available(unlocked) and item.cost <= bushels


def offers(unlocked: frozenset[str], *, bushels: int) -> tuple[Tech, ...]:
    """Return the nodes the ruler may start this year, in tree order.

    The engine asks for research only when this is not empty, so a ruler who
    cannot afford anything is never asked a question with no answer.
    """
    return tuple(
        item
        for item in available(unlocked)
        if can_research(item.key, unlocked=unlocked, bushels=bushels)
    )


def settings(unlocked: frozenset[str]) -> Agriculture:
    """Return the farming technology the unlocked nodes add up to.

    A classic game passes an empty set and gets the vintage rates back. The harvest
    bonuses of the field nodes add up, and for every other setting the best value
    among the unlocked nodes is the one in force; a key that is not in the tree is
    ignored, so a stale or mistyped key cannot raise here — :func:`node` is what
    reports an unknown key.

    Args:
        unlocked: Keys of the technologies already unlocked.

    Returns:
        The :class:`~hammurabi.models.Agriculture` values for the rules to use.
    """
    yield_bonus = 0
    acres_per_seed = config.ACRES_PER_SEED_BUSHEL
    acres_per_worker = config.ACRES_PER_WORKER
    rat_divisor = 1
    for item in TECH_TREE:
        if item.key not in unlocked:
            continue
        delta = item.delta
        yield_bonus += delta.yield_bonus
        acres_per_seed = max(acres_per_seed, delta.acres_per_seed)
        acres_per_worker = max(acres_per_worker, delta.acres_per_worker)
        rat_divisor = max(rat_divisor, delta.rat_divisor)
    return Agriculture(
        yield_bonus=yield_bonus,
        acres_per_seed=acres_per_seed,
        acres_per_worker=acres_per_worker,
        rat_divisor=rat_divisor,
    )