"""Seeded batches of complete games: the rules working together, not one by one.

The unit tests pin each rule in isolation; these tests play hundreds of whole
terms with the policies from :mod:`tests.policies` and assert the properties that
must hold in *every* game:

* the grain in the store balances to the bushel, from the land trade through the
  food, the seed, the rats and the harvest;
* the population follows from the feeding answer, the immigrants and the plague;
* no resource goes negative, the last acre is never sold, and a term always ends
  with a verdict its own statistics justify.

Everything is seeded, so the batches are reproducible: nothing here depends on
luck. The outcomes of the same batches are written down in ``docs/balancing.md``,
and the ``test_the_balancing_notes_describe_the_batch_they_quote`` test at the end
of this module keeps that document and the engine in step, batch by batch — the
classic ones and the two that play the optional agriculture rule set.
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import pytest

from hammurabi import config, health, rules, tech
from hammurabi.game import Game
from hammurabi.models import GameState, Verdict
from hammurabi.random_source import SeededRandom
from tests.policies import (
    CarefulPolicy,
    FarmerPolicy,
    HealerPolicy,
    Policy,
    SellerPolicy,
    StarverPolicy,
    TraderPolicy,
    play_game,
)

#: Games per policy. A term takes well under a millisecond, so a batch this size
#: costs a fraction of a second while covering far more rule combinations than
#: scripted games ever could.
GAMES = 500

POLICIES = (CarefulPolicy, TraderPolicy, SellerPolicy, StarverPolicy)
IDS = [policy.__name__ for policy in POLICIES]

#: The fold of the health tree, bound once here because the batches pass a ``health``
#: flag around and that name would shadow the module it comes from.
HEALERS = health.healers


@dataclass
class _Year:
    """One played year, rebuilt from the engine's calls and the answers given.

    Attributes:
        state: The game state right after the year was played.
        reported_population: People in the city before the newcomers arrived.
        reported_immigrants: Newcomers this year's report announced.
        plague: Whether the plague struck this year.
        price: Bushels the year's acre fetched.
        store: Bushels in the store before the land trade.
        bought: Acres bought this year.
        sold: Acres sold this year.
        fed_with: Bushels the engine accepted for feeding the city.
        planted: Acres the engine accepted for sowing.
        researched: The technology unlocked this year and what it cost, or
            ``None`` when the year researched nothing.
    """

    state: GameState
    reported_population: int
    reported_immigrants: int
    reported_births: int
    plague: bool
    price: int
    store: int
    bought: int
    sold: int
    fed_with: int
    planted: int
    survivor_percent: int = config.PLAGUE_SURVIVOR_PERCENT
    bushels_per_person: int = config.BUSHELS_PER_PERSON
    births_per_thousand: int = 0
    researched: tuple[str, int] | None = None

    @property
    def people(self) -> int:
        """People alive when this year's decisions were made."""
        opening = (
            self.reported_population + self.reported_immigrants + self.reported_births
        )
        if self.plague:
            return rules.plague_survivors(
                opening, survivor_percent=self.survivor_percent
            )
        return opening

    @property
    def acres(self) -> int:
        """Acres owned before the trade (nothing else changes the acreage)."""
        return self.state.acres - self.bought + self.sold

    @property
    def fed(self) -> int:
        """People the grain the ruler offered could feed."""
        return rules.people_fed(
            self.fed_with, bushels_per_person=self.bushels_per_person
        )

    @property
    def starved(self) -> int:
        """People who went hungry this year."""
        return rules.starvation(self.people, self.fed)

    @property
    def children(self) -> int:
        """Children this year's feeding earns for the next year's report."""
        return rules.births(
            self.people, fed=self.fed, per_thousand=self.births_per_thousand
        )


def _calls(calls: list[tuple[object, ...]], kind: str) -> list[tuple[object, ...]]:
    """Return the recorded calls of one kind."""
    return [call for call in calls if call[0] == kind]


def _only(calls: list[tuple[object, ...]], kind: str) -> tuple[object, ...]:
    """Return the single recorded call of ``kind``."""
    found = _calls(calls, kind)
    assert len(found) == 1, f"expected exactly one {kind!r} call, got {found}"
    return found[0]


def _answer(answers: list[tuple[str, int, int, int]], question: str) -> int:
    """Return the accepted answer to ``question``, or ``0`` if never asked.

    Land is either bought or sold, so only one of the two questions is asked in a
    given year.
    """
    found = [answer for what, answer, *_ in answers if what == question]
    assert len(found) <= 1, f"{question!r} was answered more than once: {found}"
    return found[0] if found else 0


def _years(
    seed: int,
    policy: type[Policy],
    *,
    agriculture: bool = False,
    health: bool = False,
):
    """Yield every year of one seeded game as a rebuilt :class:`_Year`."""
    ui = policy()
    game = Game(
        SeededRandom(seed=seed),
        ui,
        state=GameState(agriculture=agriculture, health=health),
    )
    while not game.state.game_over and game.state.year < config.TERM_YEARS:
        # The health in force this year is the one in the state *before* the year
        # is played: research bought during the year only pays off from the next.
        in_force = HEALERS(game.state.unlocked)
        seen_calls = len(ui.calls)
        seen_answers = len(ui.answers)
        game.play_year()
        calls = ui.calls[seen_calls:]
        answers = ui.answers[seen_answers:]
        _, _, _, immigrants, born, population = _only(calls, "report")
        plague = _calls(calls, "plague")
        opening = population + immigrants + born
        if plague:
            assert plague[0] == (
                "plague",
                opening,
                rules.plague_survivors(
                    opening, survivor_percent=in_force.plague_survivor_percent
                ),
            )
            assert game.state.plague_this_year is True
            people = rules.plague_survivors(
                opening, survivor_percent=in_force.plague_survivor_percent
            )
        else:
            assert game.state.plague_this_year is False
            people = opening
        _, status_population, store = _only(calls, "status")
        assert status_population == people, "the status must open the year"
        researched = _calls(calls, "research")
        assert len(researched) <= 1, "at most one research a year"
        yield _Year(
            state=game.state,
            reported_population=population,
            reported_immigrants=immigrants,
            reported_births=born,
            plague=bool(plague),
            price=_only(calls, "price")[1],
            store=store,
            bought=_answer(answers, "buy"),
            sold=_answer(answers, "sell"),
            fed_with=_answer(answers, "feed"),
            planted=_answer(answers, "plant"),
            survivor_percent=in_force.plague_survivor_percent,
            bushels_per_person=in_force.bushels_per_person,
            births_per_thousand=in_force.births_per_thousand,
            researched=(researched[0][1], researched[0][2]) if researched else None,
        )


def _finished(ui: Policy) -> bool:
    """Return whether the end-of-term evaluation ran, ending the game."""
    return "summary" in ui.names()


@pytest.mark.parametrize("policy", POLICIES, ids=IDS)
def test_the_grain_in_the_store_balances_for_every_year(policy: type[Policy]) -> None:
    """The store is a closed ledger: trade, food, seed, rats and harvest."""
    for seed in range(GAMES):
        for year in _years(seed, policy):
            assert config.LAND_PRICE_MIN <= year.price <= config.LAND_PRICE_MAX
            assert not (year.bought > 0 and year.sold > 0), "buy or sell, not both"
            assert rules.can_buy_land(year.bought, year.price, year.store)
            assert rules.can_sell_land(year.sold, year.acres)
            store = year.store + (year.sold - year.bought) * year.price
            assert rules.can_feed_people(year.fed_with, store)
            store -= year.fed_with
            assert rules.can_plant(
                year.planted,
                owned=year.acres + year.bought - year.sold,
                bushels=store,
                population=year.people,
            )
            store -= rules.seed_cost(year.planted)
            state = year.state
            assert 0 <= state.rats_ate_this_year <= store
            expected = (
                store
                - state.rats_ate_this_year
                + rules.harvest(year.planted, state.yield_per_acre)
            )
            assert state.bushels == expected, (
                f"seed {seed}, year {state.year}: {store} bushels at the harvest "
                f"do not lead to a store of {state.bushels}"
            )


def test_the_grain_in_the_store_balances_when_the_ruler_researches() -> None:
    """The rule set adds one line to the ledger: research is paid from the store.

    The seed, the labour and the harvest all follow the technology unlocked at
    the *start* of the year, because a node bought in December only shows in the
    following year's fields.
    """
    for seed in range(GAMES):
        for year in _years(seed, FarmerPolicy, agriculture=True):
            state = year.state
            researched = year.researched
            bought_now = {researched[0]} if researched else set()
            settings = tech.settings(state.unlocked - bought_now)
            store = year.store + (year.sold - year.bought) * year.price
            store -= year.fed_with
            assert rules.can_plant(
                year.planted,
                owned=year.acres + year.bought - year.sold,
                bushels=store,
                population=year.people,
                acres_per_seed=settings.acres_per_seed,
                acres_per_worker=settings.acres_per_worker,
            )
            store -= rules.seed_cost(
                year.planted, acres_per_seed=settings.acres_per_seed
            )
            assert 0 <= state.rats_ate_this_year <= store
            expected = (
                store
                - state.rats_ate_this_year
                + rules.harvest(year.planted, state.yield_per_acre)
            )
            if researched is not None:
                key, cost = researched
                assert cost == tech.FARMING.node(key).cost
                assert key in state.unlocked, "the store paid for nothing"
                expected -= cost
            assert state.bushels == expected, (
                f"seed {seed}, year {state.year}: the harvest, the rats and the "
                f"research do not lead to a store of {state.bushels}"
            )


@pytest.mark.parametrize("policy", POLICIES, ids=IDS)
def test_the_population_follows_the_feeding_answer_every_year(
    policy: type[Policy],
) -> None:
    """Hunger is settled at the end of the year, unless it ends the reign."""
    for seed in range(GAMES):
        starved_so_far = 0
        for year in _years(seed, policy):
            state = year.state
            assert 0 <= state.starved_this_year <= year.people
            if state.game_over:
                assert state.verdict is Verdict.IMPEACHED
                assert state.starved_this_year == year.starved
                assert rules.is_impeached(year.people, year.starved)
                assert state.population == year.people, "the city shrinks too late"
                assert state.total_starved == starved_so_far
            elif year.fed > year.people:
                # The listing jumps to the next year here: nobody starves, the
                # city does not grow and the year is not tallied.
                assert state.starved_this_year == 0
                assert state.population == year.people
                assert state.total_starved == starved_so_far
            else:
                assert state.starved_this_year == year.starved
                assert state.population == year.fed
                starved_so_far += year.starved
                assert state.total_starved == starved_so_far


@pytest.mark.parametrize("policy", POLICIES, ids=IDS)
def test_no_game_ever_breaks_a_resource_invariant(policy: type[Policy]) -> None:
    """Nothing goes negative and no city is left without land or a year."""
    for seed in range(GAMES):
        for year in _years(seed, policy):
            state = year.state
            assert 1 <= state.year <= config.TERM_YEARS
            assert state.acres >= 1, "the last acre may not be sold"
            assert state.bushels >= 0, "the store may not go negative"
            assert state.population >= 0
            assert state.starved_this_year >= 0
            assert config.YIELD_MIN <= state.yield_per_acre <= config.YIELD_MAX
            assert state.rats_ate_this_year >= 0


def test_no_health_game_ever_breaks_a_resource_invariant() -> None:
    """The health rule set keeps the store, the land, the births and the tree sound."""
    for seed in range(GAMES):
        for year in _years(seed, HealerPolicy, health=True):
            state = year.state
            assert state.acres >= 1, "the last acre may not be sold"
            assert state.bushels >= 0, "the store may not go negative"
            assert state.health is True
            assert all(health.HEALTH.node(key).key == key for key in state.unlocked)
            assert len(state.unlocked) <= health.HEALTH.size
            # The births of a year follow from its feeding, and a year the city
            # could not feed itself brings none at all.
            assert state.born_this_year == year.children
            assert state.born_this_year >= 0
            if year.fed < year.people:
                assert state.born_this_year == 0, "hunger is no time for a nursery"
            # The public health in force sits inside the bounds the tree documents.
            assert config.PLAGUE_SURVIVOR_PERCENT <= year.survivor_percent <= (
                max(config.HEALTH_SURVIVOR_PERCENT.values())
            )
            assert year.bushels_per_person <= config.BUSHELS_PER_PERSON
            assert 0 <= year.births_per_thousand <= (
                max(config.HEALTH_BIRTHS_PER_THOUSAND.values())
            )


def test_no_agriculture_game_ever_breaks_a_resource_invariant() -> None:
    """The rule set keeps the store, the land and the tree inside their bounds."""
    for seed in range(GAMES):
        for year in _years(seed, FarmerPolicy, agriculture=True):
            state = year.state
            assert state.acres >= 1, "the last acre may not be sold"
            assert state.bushels >= 0, "the store may not go negative"
            assert state.agriculture is True
            assert all(tech.FARMING.node(key).key == key for key in state.unlocked)
            assert len(state.unlocked) <= len(tech.TECH_TREE)
            assert config.YIELD_MIN <= state.yield_per_acre <= (
                config.YIELD_MAX + config.TECH_MAX_YIELD_BONUS
            )


@pytest.mark.parametrize("policy", POLICIES, ids=IDS)
def test_the_plague_roll_carries_into_the_next_year(policy: type[Policy]) -> None:
    """The roll made at the end of a year decides the year that follows."""
    for seed in range(GAMES):
        carried: int | None = None
        for year in _years(seed, policy):
            if carried is None:
                assert year.plague is False, "the starting roll keeps year 1 safe"
            else:
                assert year.plague is rules.plague_strikes(carried)
            carried = year.state.plague_roll


@pytest.mark.parametrize("policy", POLICIES, ids=IDS)
def test_a_term_always_ends_with_a_verdict_its_statistics_justify(
    policy: type[Policy],
) -> None:
    """Either the statistics or the impeachment decides, never anything else."""
    for seed in range(GAMES):
        game, ui = play_game(seed, policy)
        state = game.state
        assert state.game_over is True
        assert state.verdict is not None
        assert state.acres_per_person == rules.acreage_per_person(
            state.acres, state.population
        )
        if _finished(ui):
            assert state.verdict is rules.evaluate_verdict(
                state.starved_percent_avg, state.acres_per_person
            )
        else:
            # A ruler who starves more than 45% in a single year is deposed on
            # the spot: the statistics of the whole term are never consulted.
            assert state.verdict is Verdict.IMPEACHED
            assert rules.is_impeached(state.population, state.starved_this_year)
        if state.verdict is Verdict.MEDIOCRE:
            most = int(config.VERDICT_ASSASSIN_SHARE * state.population)
            assert 0 <= state.would_be_assassins <= most
        else:
            assert state.would_be_assassins == 0


def test_a_batch_of_games_reaches_every_verdict() -> None:
    """Five hundred careful games are enough to meet all four verdicts.

    The careful ruler never trades land and is still impeached in two games out
    of three (see ``docs/balancing.md``): the port keeps the difficulty of the
    original, so a seeded batch of this size cannot accidentally look easy.
    """
    verdicts = Counter(
        play_game(seed, CarefulPolicy)[0].state.verdict for seed in range(GAMES)
    )
    assert set(verdicts) == set(Verdict), f"verdicts seen: {dict(verdicts)}"


def test_a_ruler_who_feeds_nobody_is_impeached_at_once() -> None:
    """Starving everybody is far over 45%, so year 1 ends the reign."""
    game, ui = play_game(seed=0, policy=StarverPolicy)
    state = game.state
    assert state.year == 1
    assert state.game_over is True
    assert state.verdict is Verdict.IMPEACHED
    assert state.population == config.START_POPULATION + config.START_IMMIGRANTS
    assert state.starved_this_year == state.population
    assert ui.errors == []


def test_the_policies_never_answer_with_something_the_engine_rejects() -> None:
    """Every policy plays inside the rules, so no answer is ever refused."""
    for policy in POLICIES:
        for seed in range(25):
            _game, ui = play_game(seed, policy)
            assert ui.errors == []


def test_the_same_seed_replays_the_same_game() -> None:
    """Replaying a seed is exact: the state, the calls and the answers."""
    for policy in POLICIES:
        for seed in range(25):
            first, first_ui = play_game(seed, policy)
            second, second_ui = play_game(seed, policy)
            assert asdict(first.state) == asdict(second.state)
            assert first_ui.calls == second_ui.calls
            assert first_ui.answers == second_ui.answers


def test_the_random_events_keep_the_documented_rates() -> None:
    """Seeded tables reproduce the rates ``plan.md`` §4 documents."""
    draws = 2000

    plague = SeededRandom(seed=7)
    strikes = sum(
        rules.plague_strikes(rules.plague_roll(plague)) for _ in range(draws)
    )
    assert abs(strikes / draws - 0.20) < 0.03, "the plague roll is a 20% roll"

    rats = SeededRandom(seed=8)
    raids = sum(rules.rats_eaten(rats, store=1000) > 0 for _ in range(draws))
    assert abs(raids / draws - 0.40) < 0.03, "rats raid on an even roll of 1-5"

    prices = SeededRandom(seed=9)
    average_price = sum(rules.land_price(prices) for _ in range(draws)) / draws
    assert abs(average_price - 21.5) < 0.3, "the price band is 17-26"

    harvests = SeededRandom(seed=10)
    average_yield = sum(rules.harvest_yield(harvests) for _ in range(draws)) / draws
    assert abs(average_yield - 3.0) < 0.2, "the harvest band is 1-5"


#: The balancing notes quote the counts below, and this test keeps the two in
#: step: a rule or engine change has to update ``docs/balancing.md`` with it.
BALANCING_NOTES = Path(__file__).resolve().parent.parent / "docs" / "balancing.md"


def _documented_row(label: str) -> list[int]:
    """Return the figures in the ``| label |`` row of the balancing notes."""
    for line in BALANCING_NOTES.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {label} |"):
            return [int(cell) for cell in line.strip("|").split("|")[1:]]
    raise AssertionError(f"no '| {label} |' row in {BALANCING_NOTES}")


#: The batches ``docs/balancing.md`` quotes and this module replays: the label of
#: the row, the policy, the rule sets and the length of the term. The agriculture and
#: health rows are what the optional rule sets are measured by, so the notes cannot
#: claim anything about them that the engine does not do.
BATCHES = [
    ("careful", CarefulPolicy, False, False, config.TERM_YEARS),
    ("careful (marathon)", CarefulPolicy, False, False, config.MARATHON_TERM_YEARS),
    ("careful (agriculture)", CarefulPolicy, True, False, config.TERM_YEARS),
    ("farmer (agriculture)", FarmerPolicy, True, False, config.TERM_YEARS),
    (
        "farmer (agriculture, marathon)",
        FarmerPolicy,
        True,
        False,
        config.MARATHON_TERM_YEARS,
    ),
    (
        "healer (health, marathon)",
        HealerPolicy,
        False,
        True,
        config.MARATHON_TERM_YEARS,
    ),
    (
        "split (agriculture + health, marathon)",
        FarmerPolicy,
        True,
        True,
        config.MARATHON_TERM_YEARS,
    ),
]
BATCH_IDS = [label for label, *_ in BATCHES]

#: The verdicts in the order the balancing tables list them.
ORDER = (Verdict.FANTASTIC, Verdict.MEDIOCRE, Verdict.TYRANT, Verdict.IMPEACHED)


@pytest.mark.parametrize(
    ("label", "policy", "agriculture", "health", "term_years"),
    BATCHES,
    ids=BATCH_IDS,
)
def test_the_balancing_notes_describe_the_batch_they_quote(
    label: str,
    policy: type[Policy],
    agriculture: bool,
    health: bool,
    term_years: int,
) -> None:
    """``docs/balancing.md`` quotes the batches this engine really plays."""
    verdicts: Counter[Verdict] = Counter()
    completed = 0
    for seed in range(GAMES):
        game, ui = play_game(
            seed,
            policy,
            term_years=term_years,
            agriculture=agriculture,
            health=health,
        )
        verdicts[game.state.verdict] += 1
        completed += _finished(ui)

    games, documented_completed, documented_impeached, *documented_verdicts = (
        _documented_row(label)
    )
    assert games == GAMES, f"{BALANCING_NOTES} quotes {games} games, not {GAMES}"
    assert documented_completed == completed
    assert documented_impeached == GAMES - completed
    documented = dict(zip(ORDER, documented_verdicts, strict=True))
    expected = {verdict: verdicts[verdict] for verdict in ORDER}
    assert documented == expected, (
        f"{BALANCING_NOTES} quotes other verdict counts: {documented} != {expected}"
    )


@pytest.mark.parametrize("policy", POLICIES, ids=IDS)
def test_a_marathon_term_never_runs_past_its_last_year(policy: type[Policy]) -> None:
    """The term in the state bounds the loop, whatever its length."""
    for seed in range(25):
        game, ui = play_game(seed, policy, term_years=config.MARATHON_TERM_YEARS)

        assert 1 <= game.state.year <= config.MARATHON_TERM_YEARS
        if _finished(ui):
            assert game.state.year == config.MARATHON_TERM_YEARS
            assert game.state.verdict is rules.evaluate_verdict(
                game.state.starved_percent_avg, game.state.acres_per_person
            )
        else:
            # A ruler who starves more than 45% in a single year is deposed on
            # the spot: the statistics of the whole term are never consulted.
            assert game.state.verdict is Verdict.IMPEACHED
            assert rules.is_impeached(
                game.state.population, game.state.starved_this_year
            )


# --- The arc of the whole tree -----------------------------------------------

#: What ``docs/balancing.md`` records of the tree, node by node, over the 500-game
#: marathon batch: the keys in tree order, the games that ever bought the node, and
#: the mean and the median year they bought it in.
TREE_ARC = (
    ("plough", 300, 4.5, 5),
    ("fallow", 333, 1.1, 1),
    ("granaries", 307, 3.5, 3),
    ("manuring", 308, 2.3, 2),
    ("draft_teams", 290, 6.4, 6),
    ("heavy_plough", 279, 8.0, 8),
    ("rotation", 291, 5.1, 5),
    ("silos", 282, 8.2, 8),
    ("iron_ploughshares", 275, 11.8, 12),
    ("seed_drill", 269, 15.9, 16),
    ("flood_farming", 264, 22.2, 22),
    ("vaults", 259, 30.0, 29),
    ("harvest_crews", 255, 41.7, 41),
    ("seed_corn", 252, 62.1, 60),
    ("almanac", 190, 85.1, 86),
)

#: Games that bought every node before the century ended, and the median year the
#: last one was paid for — the figure ``plan.md`` §4 calls eighty to ninety years.
TREE_FINISHED = 190
TREE_COMPLETION_MEDIAN = 86


def test_the_plan_of_the_tree_takes_a_lifetime() -> None:
    """The whole programme is a lifetime's work, and ``balancing.md`` has the arc.

    This is the measurement behind the claim of ``plan.md`` §4 that the tree takes
    eighty to ninety years to buy: the same 500-game marathon batch as the tables
    of ``docs/balancing.md``, read node by node. Retuning the price ladder fails
    here until the notes are re-measured as well.
    """
    bought: dict[str, list[int]] = {item.key: [] for item in tech.TECH_TREE}
    completion: list[int] = []
    for seed in range(GAMES):
        _game, ui = play_game(
            seed,
            FarmerPolicy,
            term_years=config.MARATHON_TERM_YEARS,
            agriculture=True,
        )
        for year, key in ui.bought:
            bought[key].append(year)
        if len(ui.bought) == len(tech.TECH_TREE):
            completion.append(max(year for year, _key in ui.bought))

    assert 80 <= TREE_COMPLETION_MEDIAN <= 90, "the window the plan is documented in"
    assert len(completion) == TREE_FINISHED
    assert statistics.median(completion) == TREE_COMPLETION_MEDIAN

    for key, games, mean_year, median_year in TREE_ARC:
        years = bought[key]
        assert len(years) == games, f"{key} was bought by {len(years)} games"
        assert round(statistics.mean(years), 1) == mean_year, f"{key} mean year"
        assert statistics.median(years) == median_year, f"{key} median year"

    # Every rung but the capstone is bought by at least half the games, and the
    # capstone by far fewer: the last stretch of the ladder is what a reign runs
    # out of time for.
    assert all(games >= GAMES // 2 for _key, games, *_rest in TREE_ARC[:-1])
    assert TREE_ARC[-1][1] < GAMES // 2


# --- The arc of the health tree ----------------------------------------------

#: What ``docs/balancing.md`` records of the health tree, measure by measure, over the
#: 500-game healer marathon batch: the keys in tree order, the games that ever bought
#: the measure, and the mean and the median year they bought it in. No measure above
#: the healing houses is ever bought: a reign that only heals does not last long
#: enough to climb further, which is the measured truth the notes state.
HEALTH_ARC = (
    ("wells", 151, 5.9, 6),
    ("herb_gatherers", 257, 3.3, 3),
    ("midwives", 58, 9.4, 10),
    ("milled_grain", 338, 1.1, 1),
    ("drained_streets", 89, 7.7, 8),
    ("physicians", 186, 4.6, 5),
    ("wet_nurses", 33, 11.5, 12),
    ("kitchen_gardens", 290, 2.2, 2),
    ("brick_drains", 47, 9.4, 9),
    ("doctors", 105, 6.3, 6),
    ("milk_herds", 18, 13.3, 13),
    ("oil_presses", 150, 4.2, 3),
    ("healing_houses", 25, 9.5, 8),
    ("birthing_houses", 0, 0.0, 0),
    ("fish_ponds", 0, 0.0, 0),
    ("temple_hospital", 0, 0.0, 0),
    ("foundling_home", 0, 0.0, 0),
    ("palace_nursery", 0, 0.0, 0),
    ("house_of_life", 0, 0.0, 0),
)

#: The summary the notes quote of the healer batch: the mean and the median measures a
#: reign ever pays for, the games that bought at least one, and the deepest measure of
#: the whole tree that any of the 500 games reached.
HEALER_RUNGS_MEAN = 3.5
HEALER_RUNGS_MEDIAN = 3
HEALER_GAMES_WITH_A_MEASURE = 340
HEALTH_DEEPEST = ("healing_houses", 25)

#: The same arc for the batch that plays both rule sets at once: the farmer of
#: ``--agriculture``, offered the health measures as well, buys the cheapest rung of
#: whichever table is on offer. Splitting the one research moment between two
#: programmes is what this row measures.
SPLIT_ARC = (
    ("wells", 309, 4.3, 4),
    ("herb_gatherers", 296, 6.0, 6),
    ("midwives", 292, 7.4, 8),
    ("milled_grain", 291, 8.7, 9),
    ("drained_streets", 290, 9.9, 10),
    ("physicians", 290, 11.1, 11),
    ("wet_nurses", 289, 12.2, 12),
    ("kitchen_gardens", 288, 13.2, 13),
    ("brick_drains", 287, 14.3, 14),
    ("doctors", 284, 15.4, 15),
    ("milk_herds", 282, 16.5, 16),
    ("oil_presses", 279, 17.5, 17),
    ("healing_houses", 277, 18.6, 18),
    ("birthing_houses", 267, 19.9, 20),
    ("fish_ponds", 230, 21.9, 21),
    ("temple_hospital", 140, 25.0, 24),
    ("foundling_home", 37, 31.7, 32),
    ("palace_nursery", 1, 39.0, 39),
    ("house_of_life", 0, 0.0, 0),
)

#: The splitter's summary: it buys more measures than farming technologies, and the
#: deepest measure of the health tree is reached once in 500 games.
SPLIT_HEALTH_RUNGS_MEAN = 8.9
SPLIT_HEALTH_RUNGS_MEDIAN = 14
SPLIT_FARMING_RUNGS_MEAN = 4.8
SPLIT_FARMING_RUNGS_MEDIAN = 6
SPLIT_GAMES_WITH_A_MEASURE = 309
SPLIT_DEEPEST = ("palace_nursery", 1)


#: The median year a healer survives when the whole tree is handed to it before the
#: first year: the figure ``docs/balancing.md`` quotes against the careful ruler's
#: eleventh.
HEALTH_ONLY_MEDIAN_YEARS = 8


def _plays(
    policy: type[Policy], **flags: bool
) -> tuple[dict[str, list[int]], list[int], list[int]]:
    """Replay a marathon batch and return its health arc and its rung counts.

    Returns:
        The year each measure was bought in, keyed by the measure; the number of
        measures each game bought; and the number of farming nodes each bought.
    """
    years: dict[str, list[int]] = {}
    health_rungs: list[int] = []
    farming_rungs: list[int] = []
    for seed in range(GAMES):
        _game, ui = play_game(
            seed, policy, term_years=config.MARATHON_TERM_YEARS, **flags
        )
        bought_health = [
            (year, key) for year, key in ui.bought if key in config.HEALTH_COSTS
        ]
        for year, key in bought_health:
            years.setdefault(key, []).append(year)
        health_rungs.append(len(bought_health))
        farming_rungs.append(
            sum(1 for _year, key in ui.bought if key in config.TECH_COSTS)
        )
    return years, health_rungs, farming_rungs


def _assert_arc(
    arc: tuple[tuple[str, int, float, int], ...], years: dict[str, list[int]]
) -> None:
    """Assert one arc table against the batch that was played."""
    for key, games, mean_year, median_year in arc:
        found = years.get(key, [])
        assert len(found) == games, f"{key} was bought by {len(found)} games"
        if not games:
            assert mean_year == 0.0 and median_year == 0
            continue
        assert round(statistics.mean(found), 1) == mean_year, f"{key} mean year"
        assert statistics.median(found) == median_year, f"{key} median year"


def test_the_health_tree_is_climbed_only_as_far_as_a_reign_allows() -> None:
    """``docs/balancing.md`` records what a health-only reign can actually buy.

    The health programme is priced like the farming one and a health-only reign is
    short — the harvest, not the plague, decides how long a city lasts — so the arc
    of the healer batch stops at the healing houses, the thirteenth of the nineteen
    measures. This test is what makes that claim checkable rather than a remark.
    """
    years, rungs, _farming = _plays(HealerPolicy, health=True)

    assert round(statistics.mean(rungs), 1) == HEALER_RUNGS_MEAN
    assert statistics.median(rungs) == HEALER_RUNGS_MEDIAN
    assert sum(1 for value in rungs if value) == HEALER_GAMES_WITH_A_MEASURE
    _assert_arc(HEALTH_ARC, years)

    keys = [key for key, *_rest in HEALTH_ARC]
    deepest, games = HEALTH_DEEPEST
    reached = [key for key in keys if years.get(key)]
    assert HEALTH_ARC[keys.index(deepest)][1] == games
    assert keys.index(deepest) == len(reached) - 1, "a deeper measure was bought"
    assert all(
        not years.get(key) for key in keys if keys.index(key) > keys.index(deepest)
    ), "a measure the notes call unreachable was bought"


def test_the_health_tree_alone_cannot_keep_a_city_alive() -> None:
    """``docs/balancing.md`` says a whole tree built on day one still starves.

    The claim is the point of the health rule set: medicine is not a harvest, so even
    a city handed every measure before the first year is impeached for famine in the
    eighth year on the median, against the eleventh of the careful ruler.
    """
    years: list[int] = []
    completed = 0
    for seed in range(GAMES):
        ui = HealerPolicy()
        game = Game(
            SeededRandom(seed=seed),
            ui,
            state=GameState(
                term_years=config.MARATHON_TERM_YEARS,
                health=True,
                unlocked=frozenset(item.key for item in health.HEALTH_TREE),
            ),
        )
        game.play()
        years.append(game.state.year)
        completed += _finished(ui)

    assert completed == 0, "a health-only city must not survive a century"
    assert statistics.median(years) == HEALTH_ONLY_MEDIAN_YEARS


def test_both_programmes_share_the_one_research_moment() -> None:
    """``docs/balancing.md`` quotes the splitter's arc as well as the healer's.

    The farmer who is offered both tables buys the cheapest rung of either, so the
    cheap measures arrive long before the deep farming rungs: the one research moment
    a year is the real price of a second programme.
    """
    years, health_rungs, farming_rungs = _plays(
        FarmerPolicy, agriculture=True, health=True
    )

    assert round(statistics.mean(health_rungs), 1) == SPLIT_HEALTH_RUNGS_MEAN
    assert statistics.median(health_rungs) == SPLIT_HEALTH_RUNGS_MEDIAN
    assert round(statistics.mean(farming_rungs), 1) == SPLIT_FARMING_RUNGS_MEAN
    assert statistics.median(farming_rungs) == SPLIT_FARMING_RUNGS_MEDIAN
    assert sum(1 for value in health_rungs if value) == SPLIT_GAMES_WITH_A_MEASURE
    _assert_arc(SPLIT_ARC, years)

    deepest, games = SPLIT_DEEPEST
    assert len(years.get(deepest, [])) == games
    assert "house_of_life" not in years, "the notes call the capstone unreachable"


