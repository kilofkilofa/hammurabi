"""The optional health rule set: the tech tree that keeps a city alive.

The classic game knows no medicine at all. A plague year buries half the city,
nobody is born, and twenty bushels feed one person for a year. This module holds the
optional rule set of ``docs/plan.md`` section 4 as pure data: nineteen nodes the ruler
pays for out of the grain in store, researched with the same yearly question as the
farming tree of :mod:`hammurabi.tech`. :func:`healers` folds the unlocked nodes into
the :class:`~hammurabi.models.Health` values the rules take as arguments, and the
module never touches state, the RNG or the terminal.

Nineteen nodes stand in four branches that meet in a capstone. The wells, the drained
streets and the brick-lined drains keep the plague out of the city, so that it comes
five years in a hundred less often for every rung. The herb gatherers, the physicians,
the doctors, the healing houses and the temple hospital save the sick, until one in
ten dies where the classic game buried half the city. The midwives, the wet nurses,
the milk herds, the birthing houses, the foundling home and the palace nursery bring
children into the city. The milled grain, the kitchen gardens, the oil presses and the
fish ponds make a bushel feed more people. The **House of Life**, which needs the
deepest rung of every branch at once, is the last word in medicine: one in twenty dies
and it outdoes the palace nursery itself.

The prices climb by about a third a step, like the farming ladder, and the branches
are woven so that the youngest treasury can already open any one of them. The measured
plan of ``docs/balancing.md`` needs eighty to ninety years to buy the whole tree, the
same lifetime the farming programme takes. Every price, rate and bonus is a constant
in ``config.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from hammurabi import config, tech
from hammurabi.models import Health


@dataclass(frozen=True)
class HealthDelta:
    """What one node of the health tree does to the health in force.

    Every field names the **rate the node reaches**, exactly as the farming deltas
    do: the plague survivor share, the plague resistance and the birth rate are read
    as the best unlocked value, and the bushels that feed a person as the smallest,
    because fewer bushels per person is the better medicine. A node that does not
    touch a rate carries the classic value of that rate, so that it can take part in
    the comparison without changing it.

    Attributes:
        plague_survivor_percent: Share of the people who live through a plague year;
            the classic half when the node does not touch it.
        plague_resistance: Added to the plague roll; ``0`` when untouched.
        births_per_thousand: Children born per thousand people; ``0`` when untouched.
        bushels_per_person: Bushels that feed one person for a year; the classic
            twenty when the node does not touch it.
    """

    plague_survivor_percent: int = config.PLAGUE_SURVIVOR_PERCENT
    plague_resistance: int = 0
    births_per_thousand: int = 0
    bushels_per_person: int = config.BUSHELS_PER_PERSON


@dataclass(frozen=True)
class HealthNode:
    """One node of the health tree.

    Attributes:
        key: Stable identifier, the key stored in ``GameState.unlocked``.
        name: Name shown to the player.
        requires: Keys that must already be unlocked.
        effect: One line describing the node, for the UI to print.
        delta: What the node contributes to the public health: the rate it reaches.
    """

    key: str
    name: str
    requires: frozenset[str]
    effect: str
    delta: HealthDelta

    @property
    def cost(self) -> int:
        """Bushels of grain the research costs (``config.HEALTH_COSTS``)."""
        return config.HEALTH_COSTS[self.key]


#: The tree in the price order the UI lists it, which is also a plan a city can pay
#: for rung by rung: the four branches are woven so that the first four rungs — one
#: of each branch — together open the whole programme, and every later rung waits for
#: the rung below it. The first four nodes are open from the first year; the House of
#: Life needs the deepest rung of all four branches at once.
HEALTH_TREE: tuple[HealthNode, ...] = (
    HealthNode(
        key="wells",
        name="Wells",
        requires=frozenset(),
        effect=f"plague resistance: +{config.HEALTH_RESISTANCE['wells']}",
        delta=HealthDelta(plague_resistance=config.HEALTH_RESISTANCE["wells"]),
    ),
    HealthNode(
        key="herb_gatherers",
        name="Herb gatherers",
        requires=frozenset(),
        effect=(
            f"plague survivors: {config.PLAGUE_SURVIVOR_PERCENT}% -> "
            f"{config.HEALTH_SURVIVOR_PERCENT['herb_gatherers']}%"
        ),
        delta=HealthDelta(
            plague_survivor_percent=config.HEALTH_SURVIVOR_PERCENT["herb_gatherers"]
        ),
    ),
    HealthNode(
        key="midwives",
        name="Midwives",
        requires=frozenset(),
        effect=(
            f"+{config.HEALTH_BIRTHS_PER_THOUSAND['midwives']} births per 1000 people"
        ),
        delta=HealthDelta(
            births_per_thousand=config.HEALTH_BIRTHS_PER_THOUSAND["midwives"]
        ),
    ),
    HealthNode(
        key="milled_grain",
        name="Milled grain",
        requires=frozenset(),
        effect=(
            f"{config.BUSHELS_PER_PERSON} -> "
            f"{config.HEALTH_BUSHELS_PER_PERSON['milled_grain']} bushels per person"
        ),
        delta=HealthDelta(
            bushels_per_person=config.HEALTH_BUSHELS_PER_PERSON["milled_grain"]
        ),
    ),
    HealthNode(
        key="drained_streets",
        name="Drained streets",
        requires=frozenset({"wells"}),
        effect=(
            f"plague resistance: +{config.HEALTH_RESISTANCE['wells']} -> "
            f"+{config.HEALTH_RESISTANCE['drained_streets']}"
        ),
        delta=HealthDelta(
            plague_resistance=config.HEALTH_RESISTANCE["drained_streets"]
        ),
    ),
    HealthNode(
        key="physicians",
        name="Physicians",
        requires=frozenset({"herb_gatherers"}),
        effect=(
            f"plague survivors: "
            f"{config.HEALTH_SURVIVOR_PERCENT['herb_gatherers']}% -> "
            f"{config.HEALTH_SURVIVOR_PERCENT['physicians']}%"
        ),
        delta=HealthDelta(
            plague_survivor_percent=config.HEALTH_SURVIVOR_PERCENT["physicians"]
        ),
    ),
    HealthNode(
        key="wet_nurses",
        name="Wet nurses",
        requires=frozenset({"midwives"}),
        effect=(
            f"+{config.HEALTH_BIRTHS_PER_THOUSAND['wet_nurses']} births per 1000 people"
        ),
        delta=HealthDelta(
            births_per_thousand=config.HEALTH_BIRTHS_PER_THOUSAND["wet_nurses"]
        ),
    ),
    HealthNode(
        key="kitchen_gardens",
        name="Kitchen gardens",
        requires=frozenset({"milled_grain"}),
        effect=(
            f"{config.HEALTH_BUSHELS_PER_PERSON['milled_grain']} -> "
            f"{config.HEALTH_BUSHELS_PER_PERSON['kitchen_gardens']} bushels per person"
        ),
        delta=HealthDelta(
            bushels_per_person=config.HEALTH_BUSHELS_PER_PERSON["kitchen_gardens"]
        ),
    ),
    HealthNode(
        key="brick_drains",
        name="Brick-lined drains",
        requires=frozenset({"drained_streets"}),
        effect=(
            f"plague resistance: +{config.HEALTH_RESISTANCE['drained_streets']} -> "
            f"+{config.HEALTH_RESISTANCE['brick_drains']}"
        ),
        delta=HealthDelta(plague_resistance=config.HEALTH_RESISTANCE["brick_drains"]),
    ),
    HealthNode(
        key="doctors",
        name="Doctors",
        requires=frozenset({"physicians"}),
        effect=(
            f"plague survivors: {config.HEALTH_SURVIVOR_PERCENT['physicians']}% -> "
            f"{config.HEALTH_SURVIVOR_PERCENT['doctors']}%"
        ),
        delta=HealthDelta(
            plague_survivor_percent=config.HEALTH_SURVIVOR_PERCENT["doctors"]
        ),
    ),
    HealthNode(
        key="milk_herds",
        name="Milk herds",
        requires=frozenset({"wet_nurses"}),
        effect=(
            f"+{config.HEALTH_BIRTHS_PER_THOUSAND['milk_herds']} births per 1000 people"
        ),
        delta=HealthDelta(
            births_per_thousand=config.HEALTH_BIRTHS_PER_THOUSAND["milk_herds"]
        ),
    ),
    HealthNode(
        key="oil_presses",
        name="Oil presses",
        requires=frozenset({"kitchen_gardens"}),
        effect=(
            f"{config.HEALTH_BUSHELS_PER_PERSON['kitchen_gardens']} -> "
            f"{config.HEALTH_BUSHELS_PER_PERSON['oil_presses']} bushels per person"
        ),
        delta=HealthDelta(
            bushels_per_person=config.HEALTH_BUSHELS_PER_PERSON["oil_presses"]
        ),
    ),
    HealthNode(
        key="healing_houses",
        name="Healing houses",
        requires=frozenset({"doctors"}),
        effect=(
            f"plague survivors: {config.HEALTH_SURVIVOR_PERCENT['doctors']}% -> "
            f"{config.HEALTH_SURVIVOR_PERCENT['healing_houses']}%"
        ),
        delta=HealthDelta(
            plague_survivor_percent=config.HEALTH_SURVIVOR_PERCENT["healing_houses"]
        ),
    ),
    HealthNode(
        key="birthing_houses",
        name="Birthing houses",
        requires=frozenset({"milk_herds"}),
        effect=(
            f"+{config.HEALTH_BIRTHS_PER_THOUSAND['birthing_houses']} births "
            "per 1000 people"
        ),
        delta=HealthDelta(
            births_per_thousand=config.HEALTH_BIRTHS_PER_THOUSAND["birthing_houses"]
        ),
    ),
    HealthNode(
        key="fish_ponds",
        name="Fish ponds",
        requires=frozenset({"oil_presses"}),
        effect=(
            f"{config.HEALTH_BUSHELS_PER_PERSON['oil_presses']} -> "
            f"{config.HEALTH_BUSHELS_PER_PERSON['fish_ponds']} bushels per person"
        ),
        delta=HealthDelta(
            bushels_per_person=config.HEALTH_BUSHELS_PER_PERSON["fish_ponds"]
        ),
    ),
    HealthNode(
        key="temple_hospital",
        name="Temple hospital",
        requires=frozenset({"healing_houses"}),
        effect=(
            f"plague survivors: "
            f"{config.HEALTH_SURVIVOR_PERCENT['healing_houses']}% -> "
            f"{config.HEALTH_SURVIVOR_PERCENT['temple_hospital']}%"
        ),
        delta=HealthDelta(
            plague_survivor_percent=config.HEALTH_SURVIVOR_PERCENT["temple_hospital"]
        ),
    ),
    HealthNode(
        key="foundling_home",
        name="Foundling home",
        requires=frozenset({"birthing_houses"}),
        effect=(
            f"+{config.HEALTH_BIRTHS_PER_THOUSAND['foundling_home']} births "
            "per 1000 people"
        ),
        delta=HealthDelta(
            births_per_thousand=config.HEALTH_BIRTHS_PER_THOUSAND["foundling_home"]
        ),
    ),
    HealthNode(
        key="palace_nursery",
        name="Palace nursery",
        requires=frozenset({"foundling_home"}),
        effect=(
            f"+{config.HEALTH_BIRTHS_PER_THOUSAND['palace_nursery']} births "
            "per 1000 people"
        ),
        delta=HealthDelta(
            births_per_thousand=config.HEALTH_BIRTHS_PER_THOUSAND["palace_nursery"]
        ),
    ),
    HealthNode(
        key="house_of_life",
        name="House of Life",
        requires=frozenset(
            {"brick_drains", "temple_hospital", "palace_nursery", "fish_ponds"}
        ),
        effect=(
            f"plague survivors: "
            f"{config.HEALTH_SURVIVOR_PERCENT['temple_hospital']}% -> "
            f"{config.HEALTH_SURVIVOR_PERCENT['house_of_life']}%, "
            f"+{config.HEALTH_BIRTHS_PER_THOUSAND['house_of_life']} births "
            "per 1000 people"
        ),
        delta=HealthDelta(
            plague_survivor_percent=config.HEALTH_SURVIVOR_PERCENT["house_of_life"],
            births_per_thousand=config.HEALTH_BIRTHS_PER_THOUSAND["house_of_life"],
        ),
    ),
)

#: The health tree as the engine and the UI see it: the nineteen measures of the
#: ``--health`` rule set, priced by the ladder of :data:`config.HEALTH_COSTS`.
HEALTH: tech.TechTree[HealthNode] = tech.TechTree(
    key="health", label="healers", nodes=HEALTH_TREE
)


def healers(unlocked: frozenset[str]) -> Health:
    """Return the public health the unlocked nodes add up to.

    A classic game passes an empty set and gets the vintage values back: half the
    city lives through a plague, nobody is born and twenty bushels feed a person.
    The survivor share, the resistance and the birth rate are *rates*, so the best
    unlocked value is the one in force and a deeper rung supersedes the one below it
    instead of stacking with it; the bushels that feed a person are the exception,
    because there fewer is better. A key that is not in the tree is ignored, so a
    stale or mistyped key cannot raise here — :meth:`hammurabi.tech.TechTree.node` is
    what reports an unknown key.

    Args:
        unlocked: Keys of the technologies already unlocked.

    Returns:
        The :class:`~hammurabi.models.Health` values for the rules to use.
    """
    survivor_percent = config.PLAGUE_SURVIVOR_PERCENT
    resistance = 0
    births = 0
    bushels_per_person = config.BUSHELS_PER_PERSON
    for item in HEALTH_TREE:
        if item.key not in unlocked:
            continue
        delta = item.delta
        survivor_percent = max(survivor_percent, delta.plague_survivor_percent)
        resistance = max(resistance, delta.plague_resistance)
        births = max(births, delta.births_per_thousand)
        bushels_per_person = min(bushels_per_person, delta.bushels_per_person)
    return Health(
        plague_survivor_percent=survivor_percent,
        plague_resistance=resistance,
        births_per_thousand=births,
        bushels_per_person=bushels_per_person,
    )
