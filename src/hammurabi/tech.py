"""The optional rule sets' research machinery, and the farming tree.

The classic game has no research at all. This module holds what the optional rule
sets share — the :class:`Node` and :class:`TechTree` types and the :class:`Offer`
the UI is handed — together with the farming tree of ``docs/plan.md`` section 4 as
pure data, so the engine can decide what a ruler may start without knowing a single
rule number. It never touches state, the RNG or the terminal: :func:`settings`
merely folds the unlocked nodes into the
:class:`~hammurabi.models.Agriculture` values the rules take as arguments, while
the public-health tree of :mod:`hammurabi.health` folds its own nodes into
``Health`` the same way.

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

:func:`enabled_trees` is the single place that maps the rule-set flags of
:class:`~hammurabi.models.GameState` to the trees they play, and :func:`offers`
gathers what every tree in play can sell this year. The engine and the UI both ask
those two, so neither of them has to know which rule set a tree belongs to.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from hammurabi import config
from hammurabi.models import Agriculture, GameState


class Node(Protocol):
    """What the shared research machinery needs from a node of any tree.

    Both the farming :class:`Tech` and the public-health
    :class:`~hammurabi.health.HealthNode` answer to this, which is what lets one
    :class:`TechTree` type carry either rule set; the machinery never looks at the
    delta a node holds, because that is the rule set's own business.
    """

    key: str
    name: str
    requires: frozenset[str]
    effect: str
    cost: int


#: A node of one particular tree, so a tree can promise what it hands out.
NodeT = TypeVar("NodeT", bound=Node)


@dataclass(frozen=True)
class Offer(Generic[NodeT]):
    """One node a ruler may start this year, and the programme offering it.

    The engine offers every node that the trees in play have open and the store can
    pay for. ``programme`` is the label of the tree the node belongs to, which is
    how the UI tells a farming node from a public-health one when both rule sets are
    played at once.
    """

    programme: str
    node: NodeT


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


@dataclass(frozen=True)
class TechTree(Generic[NodeT]):
    """One rule set's ladder of nodes, with the questions the engine asks of it.

    The two rule sets are played the same way, so both are a tree of nodes plus the
    handful of questions the engine and the UI ask about them; which rule set a tree
    belongs to is decided by :func:`enabled_trees`, not here.

    Attributes:
        key: Name of the rule set, matching the flag of
            :class:`~hammurabi.models.GameState` that turns it on.
        label: What the UI calls the people who research it (``"farmers"``).
        nodes: The nodes in the order the UI lists them, which is also a plan a city
            that means to last can pay for rung by rung.
    """

    key: str
    label: str
    nodes: tuple[NodeT, ...]

    @property
    def size(self) -> int:
        """Return how many nodes the tree holds, capstone included."""
        return len(self.nodes)

    def node(self, key: str) -> NodeT:
        """Return the node of this tree called ``key``.

        Args:
            key: Identifier of the node, as stored in ``GameState.unlocked``.

        Returns:
            The matching node.

        Raises:
            KeyError: If the tree has no such node.
        """
        for item in self.nodes:
            if item.key == key:
                return item
        raise KeyError(key)

    def available(self, unlocked: frozenset[str]) -> tuple[NodeT, ...]:
        """Return the nodes whose prerequisites are met and that are still open.

        ``unlocked`` is read as a set and never changed; tree order is kept, so the
        first entry is the one the UI lists first.
        """
        return tuple(
            item
            for item in self.nodes
            if item.key not in unlocked and item.requires <= unlocked
        )

    def can_research(
        self, key: str, *, unlocked: frozenset[str], bushels: int
    ) -> bool:
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
        item = self.node(key)
        return item in self.available(unlocked) and item.cost <= bushels

    def offers(
        self, unlocked: frozenset[str], *, bushels: int
    ) -> tuple[Offer[NodeT], ...]:
        """Return the nodes of this tree the ruler may start this year, in order.

        The engine asks for research only when this is not empty, so a ruler who
        cannot afford anything is never asked a question with no answer.
        """
        return tuple(
            Offer(programme=self.label, node=item)
            for item in self.available(unlocked)
            if self.can_research(item.key, unlocked=unlocked, bushels=bushels)
        )

    def mastered(self, unlocked: frozenset[str]) -> tuple[NodeT, ...]:
        """Return the unlocked nodes of this tree, in tree order.

        The UI counts them for its progress line and names them in the closing
        report; keys that belong to another tree are ignored.
        """
        return tuple(item for item in self.nodes if item.key in unlocked)


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

#: The farming tree of the ``--agriculture`` rule set: the fifteen nodes a ruler
#: buys out of the grain in store, and the ladder of :data:`config.TECH_COSTS` that
#: prices them.
FARMING: TechTree[Tech] = TechTree(
    key="agriculture", label="farmers", nodes=TECH_TREE
)


def enabled_trees(state: GameState) -> tuple[TechTree, ...]:
    """Return the trees the rule-set flags of ``state`` put in play.

    ``health`` is imported here rather than at the top of the module because that
    module imports :class:`TechTree` from this one, so a module-level import would
    close a cycle. This is the only place that maps a rule set to its tree: the
    engine asks it what may be researched, the UI asks it what to print, and a
    classic game gets nothing back.
    """
    from hammurabi import health

    trees: list[TechTree] = []
    if state.agriculture:
        trees.append(FARMING)
    if state.health:
        trees.append(health.HEALTH)
    return tuple(trees)


def offers(
    trees: Sequence[TechTree], unlocked: frozenset[str], *, bushels: int
) -> tuple[Offer, ...]:
    """Return every node the trees in play may start this year, in tree order.

    The trees are asked in the order :func:`enabled_trees` hands them out, so a game
    that plays one rule set gets exactly the list it would have had before the other
    tree existed. The engine asks for research only when this is not empty, so a
    ruler who cannot afford anything is never asked a question with no answer.
    """
    return tuple(
        offer for tree in trees for offer in tree.offers(unlocked, bushels=bushels)
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