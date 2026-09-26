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

# Number of years the player governs.
TERM_YEARS = 10

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

# How many rejected answers in a row the engine tolerates before it gives up.
# A player may always think again, but a UI that can never produce a valid
# answer - a closed stdin or a scripted test double - must not be able to spin
# the engine, and a CPU, forever.
MAX_ANSWER_ATTEMPTS = 100

