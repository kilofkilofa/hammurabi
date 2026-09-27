"""Tunable constants for the game rules.

Every value is taken from the 1978 BASIC reference implementation described in
``docs/plan.md`` section 4. Keeping them in one module means the rules can be
inspected and adjusted in a single place, and the tests can assert fidelity to
the documented game.
"""

# --- Initial state -----------------------------------------------------------

# People living in the city before the first immigration.
START_POPULATION = 95

# Bushels of grain in the store at the start of the term.
START_BUSHELS = 2800

# Acres owned at the start of the term.
START_ACRES = 1000

# Number of years the player governs in the classic rule set (the default).
TERM_YEARS = 10

# The marathon rule set: the same rules, played for a whole century of office.
MARATHON_TERM_YEARS = 100

# Immigrants reported in the first year.
START_IMMIGRANTS = 5

# Bushels the rats ate before the first year (shown in the first report).
START_RATS_ATE = 200

# Harvest yield shown in the first report, carried over from the previous year.
START_YIELD_PER_ACRE = 3

# --- Land trading ------------------------------------------------------------

# Land price in bushels per acre, rolled once per year (17-26 inclusive).
LAND_PRICE_MIN = 17
LAND_PRICE_MAX = 26

# --- Food, seed and labour ---------------------------------------------------

# Bushels of grain needed to feed a single person for one year.
BUSHELS_PER_PERSON = 20

# Acres that one bushel of seed can sow.
ACRES_PER_SEED_BUSHEL = 2

# Acres a single person can tend; the true limit is ``10 * population - 1``.
ACRES_PER_WORKER = 10

# --- Harvest and rats --------------------------------------------------------

# Bushels harvested per planted acre (1-5 inclusive).
YIELD_MIN = 1
YIELD_MAX = 5

# Roll that drives the rat event (1-5). An even roll means rats strike, and the
# roll itself is the divisor applied to the grain in store (2 or 4).
RAT_ROLL_MIN = 1
RAT_ROLL_MAX = 5

# --- Random events -----------------------------------------------------------

# Vintage plague roll: ``Q = INT(10 * (2 * RND(1) - PLAGUE_ROLL_OFFSET))``. The
# plague strikes when that roll is not positive, which happens for 20% of the
# draws. The listing's own comment calls it "a 15% chance" (line 541), but the
# expression on the next line is what the game actually does.
PLAGUE_ROLL_OFFSET = 0.3

# Value of the plague roll before the first year. The listing initialises
# ``Q=1`` (line 110), so the first year is always plague-free.
START_PLAGUE_ROLL = 1

# Shift in the roll's offset for each point of public-health resistance: one point
# moves the offset by a tenth, which takes five years in a hundred out of the plague
# band (``PLAGUE_ROLL_OFFSET``), so the water branch walks 20 -> 15 -> 10 -> 5 years
# in a hundred and never abolishes the plague.
PLAGUE_RESISTANCE_OFFSET = 0.1

# Share of the people who live through a plague year, i.e. ``P // 2`` exactly. The
# health rule set raises it through its healer branch; ``rules.plague_survivors``
# reads this value as its default, which keeps the classic rule bit for bit because
# ``P * 50 // 100`` is what the listing computes.
PLAGUE_SURVIVOR_PERCENT = 50

# --- Immigration -------------------------------------------------------------

# Roll (1-5) that scales the number of newcomers.
IMMIGRATION_ROLL_MIN = 1
IMMIGRATION_ROLL_MAX = 5

# Grain value assigned to each acre in the immigration formula.
IMMIGRATION_LAND_WEIGHT = 20

# Divisor in the immigration formula.
IMMIGRATION_DIVISOR = 100

# The "+1" that guarantees at least one newcomer per year.
IMMIGRATION_BASE = 1

# --- Game over ---------------------------------------------------------------

# Starving more than this share of the population in one year ends the game.
IMPEACHMENT_STARVATION_RATIO = 0.45

# --- Final verdict thresholds ------------------------------------------------

# Average percentage of the population starved per year.
VERDICT_STARVATION_CRITICAL = 33
VERDICT_STARVATION_POOR = 10
VERDICT_STARVATION_MEDIOCRE = 3

# Acres per person at the end of the term.
VERDICT_ACRES_CRITICAL = 7
VERDICT_ACRES_POOR = 9
VERDICT_ACRES_MEDIOCRE = 10

# Share of the population that the mediocre verdict claims would like to see the
# ruler assassinated: ``INT(P * .8 * RND(1))`` in the listing (line 965).
VERDICT_ASSASSIN_SHARE = 0.8

# --- Input validation --------------------------------------------------------

# Longest term ``--years`` accepts. The marathon is the intended large value;
# the cap only stops a mistyped number from asking for an endless game.
MAX_TERM_YEARS = 1000

# How many rejected answers in a row the engine tolerates before it gives up.
# A player may always think again, but a UI that can never produce a valid
# answer - a closed stdin or a scripted test double - must not be able to spin
# the engine, and a CPU, forever.
MAX_ANSWER_ATTEMPTS = 100

# --- Optional rule sets (``--all``) ------------------------------------------

#: The optional rule sets of ``plan.md`` section 4, in the order they are turned on:
#: the farming technologies of ``--agriculture`` and the public health of ``--health``.
#: ``hammurabi --all`` turns on every set named here, and each name is both the
#: command-line flag and the ``GameState`` field that plays it, so a rule set added
#: to this tuple is covered by the master toggle without a branch of its own.
RULE_SETS: tuple[str, ...] = ("agriculture", "health")


# --- Agriculture rule set (``--agriculture``) --------------------------------

# The optional rule set of ``plan.md`` section 4: the farming technologies of
# Sumeria, twenty-five nodes the ruler pays for out of the year's spare grain. Its
# nodes are described in :mod:`hammurabi.tech`; the classic game researches nothing
# and every value below is reachable only through that flag.
#
# The prices form a ladder that grows by about a quarter at every step, so the first
# nodes are affordable in the opening years while the last ones cost what many
# harvests leave over — the grain in store settles below 130,000 bushels while the
# rats raid it, so the top of the ladder stays within reach. That is what spreads the
# whole programme over a reign rather than over a decade: the measured plan of
# ``docs/balancing.md`` needs most of a century to buy the tree to its capstone, the
# twenty-five nodes together costing 263,450 bushels.

# Bushels of grain each node of the tree costs to research, keyed by the node key
# of :data:`hammurabi.tech.TECH_TREE`.
TECH_COSTS: dict[str, int] = {
    "plough": 250,
    "fallow": 310,
    "granaries": 390,
    "heavy_plough": 490,
    "green_manuring": 610,
    "draft_teams": 760,
    "silos": 950,
    "manuring": 1190,
    "row_sowing": 1490,
    "iron_ploughshares": 1860,
    "cellars": 2330,
    "irrigated_terraces": 2910,
    "seed_drill": 3640,
    "harvest_crews": 4540,
    "vaults": 5680,
    "rotation": 7100,
    "garden_seed": 8870,
    "ox_threshers": 11090,
    "undercrofts": 13870,
    "royal_gardens": 17330,
    "water_lifts": 21660,
    "flood_farming": 27080,
    "irrigation_canals": 33850,
    "seed_corn": 42310,
    "almanac": 52890,
}

# Bushels per acre each field node adds to the harvest roll: the nine rungs of the
# fields branch plus the Nippur almanac. The ten together are the most the tree can
# give, which the tests pin to TECH_MAX_YIELD_BONUS.
TECH_YIELD_BONUS_PER_NODE = 1
TECH_YIELD_BONUS_ALMANAC = 1
TECH_MAX_YIELD_BONUS = 9 * TECH_YIELD_BONUS_PER_NODE + TECH_YIELD_BONUS_ALMANAC

# Acres one bushel of seed sows once the seed-rate nodes are unlocked; the classic
# rule sows ACRES_PER_SEED_BUSHEL acres. The most advanced node the ruler owns is
# the rate in force, because these are rates rather than bonuses.
TECH_ACRES_PER_SEED: dict[str, int] = {
    "plough": 3,
    "heavy_plough": 4,
    "row_sowing": 5,
    "seed_drill": 6,
    "garden_seed": 7,
}

# Acres one person can tend once the labour nodes are unlocked; the classic rule
# is ACRES_PER_WORKER acres.
TECH_ACRES_PER_WORKER: dict[str, int] = {
    "draft_teams": 12,
    "iron_ploughshares": 14,
    "harvest_crews": 16,
    "ox_threshers": 18,
    "water_lifts": 20,
}

# Divisors applied to the bushels the rats eat. Granaries halve the loss, sealed
# silos take a third, the cellars a fourth, the temple vaults a fifth, the
# undercrofts a sixth and the Nippur almanac leaves the rats a seventh of it. The
# strongest unlocked divisor wins rather than stacking, so the almanac supersedes
# the undercrofts once both are unlocked.
TECH_RAT_DIVISOR: dict[str, int] = {
    "granaries": 2,
    "silos": 3,
    "cellars": 4,
    "vaults": 5,
    "undercrofts": 6,
    "almanac": 7,
}

# --- Health rule set (``--health``) ------------------------------------------

# The second optional rule set of ``plan.md`` section 4: the public-health measures
# of Sumeria, twenty-five nodes the ruler pays for out of the year's spare grain and
# researches with the same yearly question as the farming tree. Its nodes are
# described in :mod:`hammurabi.health`; the classic game has no public health at all
# and every value below is reachable only through that flag.
#
# The rates below follow the rule set's own arithmetic: the plague survivor share,
# the plague resistance and the birth rate are *rates*, so the best unlocked value is
# the one in force and no two rungs ever stack; the bushels that feed a person are
# the one place where the smallest value wins, because there less is better.

# Bushels of grain each node of the health tree costs to research, keyed by the node
# key of :data:`hammurabi.health.HEALTH_TREE`. The ladder climbs by about a quarter a
# step, like the farming one, but it is the modest programme of the two: the
# twenty-five measures cost 86,070 bushels together, where the twenty-five farming
# technologies cost 263,450, because what the health tree buys is people rather than
# grain. The measured plan of ``docs/balancing.md`` therefore climbs most of it in a
# decade and reaches the deepest rungs only in a century that farms as well.
HEALTH_COSTS: dict[str, int] = {
    "wells": 100,
    "herb_gatherers": 124,
    "midwives": 153,
    "milled_grain": 190,
    "drained_streets": 235,
    "physicians": 290,
    "wet_nurses": 359,
    "kitchen_gardens": 444,
    "brick_drains": 550,
    "apothecaries": 680,
    "milk_herds": 842,
    "oil_presses": 1041,
    "aqueducts": 1288,
    "doctors": 1594,
    "birthing_houses": 1972,
    "fish_ponds": 2440,
    "healing_houses": 3019,
    "foundling_home": 3736,
    "smokehouses": 4623,
    "temple_hospital": 5720,
    "palace_nursery": 7078,
    "breweries": 8758,
    "childrens_gardens": 10836,
    "date_presses": 13408,
    "house_of_life": 16590,
}

# Share of the population that lives through a plague year, keyed by the node that
# reaches it. The classic game buries half the city; the deepest healer rung and the
# House of Life save all but one in twenty, and no node goes further, because a
# plague that never took anybody would not be a rule any more.
HEALTH_SURVIVOR_PERCENT: dict[str, int] = {
    "herb_gatherers": 60,
    "aqueducts": 65,
    "physicians": 70,
    "apothecaries": 75,
    "doctors": 80,
    "healing_houses": 85,
    "temple_hospital": 90,
    "house_of_life": 95,
}

# Added to the plague roll, keyed by the node that reaches it: the classic plague
# strikes in twenty years of a hundred, and each rung of the water branch takes five
# of those years away — 20 -> 15 -> 10 -> 5. The deepest drains leave five years in a
# hundred and no node reaches +4, because the plague must always be able to come.
HEALTH_RESISTANCE: dict[str, int] = {
    "wells": 1,
    "drained_streets": 2,
    "brick_drains": 3,
}

# Children born per thousand people in a year the city fed itself, keyed by the node
# that reaches it. The classic game has no births at all, and the House of Life
# outdoes every single rung of the nursery branch that leads to it.
HEALTH_BIRTHS_PER_THOUSAND: dict[str, int] = {
    "midwives": 4,
    "wet_nurses": 8,
    "milk_herds": 12,
    "birthing_houses": 18,
    "foundling_home": 25,
    "palace_nursery": 34,
    "childrens_gardens": 40,
    "house_of_life": 45,
}

# Bushels that feed one person for one year, keyed by the node that reaches it. The
# classic twenty becomes thirteen once the date presses are built; this is the one
# rate where the smallest unlocked value is the one in force.
HEALTH_BUSHELS_PER_PERSON: dict[str, int] = {
    "milled_grain": 19,
    "kitchen_gardens": 18,
    "oil_presses": 17,
    "fish_ponds": 16,
    "smokehouses": 15,
    "breweries": 14,
    "date_presses": 13,
}

