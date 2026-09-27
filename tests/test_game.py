"""Tests for the game engine in :mod:`hammurabi.game`.

The engine is driven by the shared test doubles from :mod:`tests.support`: a
scripted random source and a recording UI, so no test needs a terminal or real
randomness.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from itertools import cycle

import pytest

from hammurabi import config, rules, tech
from hammurabi.game import Game
from hammurabi.models import GameState, Verdict
from hammurabi.random_source import SeededRandom
from tests.support import CarefulUI, FakeUI, StubRandom

# Draws of ``RandomSource.random`` whose plague roll is known: the first is far
# above the threshold, the second far below it. See ``rules.plague_roll``.
SAFE_PLAGUE_RANDOM = 0.9  # int(10 * (2 * 0.9 - 0.3)) = 15, so no plague
PLAGUE_RANDOM = 0.05  # int(10 * (2 * 0.05 - 0.3)) = int(-1.99) = -1, so plague


def _year_rng(
    *,
    price: int = 20,
    yield_per_acre: int = 3,
    rats: int = 1,
    migrants: int = 1,
    next_plague: float = SAFE_PLAGUE_RANDOM,
) -> StubRandom:
    """Return a stub covering one year's draws, in the engine's order.

    ``next_plague`` is the draw the engine makes at the end of the year for the
    year that follows, so it never affects the year being played.
    """
    return StubRandom(
        randoms=[next_plague],
        integers=[price, yield_per_acre, rats, migrants],
    )


def _endless_rng(
    *,
    price: int = 20,
    yield_per_acre: int = 3,
    rats: int = 1,
    migrants: int = 1,
    next_plague: float = SAFE_PLAGUE_RANDOM,
) -> StubRandom:
    """Return a stub that repeats one year of draws for as many years as needed.

    The engine draws the year's integers in this order - price, harvest, rats,
    newcomers - so cycling the same block every year keeps every year alike.
    """
    return StubRandom(
        randoms=cycle([next_plague]),
        integers=cycle([price, yield_per_acre, rats, migrants]),
    )


def _spare_state(spare: int, **flags: bool) -> GameState:
    """Return a state whose year leaves ``spare`` bushels for research.

    The food of the city and the seed of its fields are paid before anything is
    offered, so a test that wants the research question put has to start from a
    store that covers both. The newcomers announced in the opening report have
    already joined the city by then, which is why the helper counts them too, and
    it adds the two figures the way the rules do.
    """
    state = GameState(**flags)
    people = state.population + state.immigrants_this_year
    sowable = min(state.acres, rules.max_plantable_acres(people))
    state.bushels = (
        people * config.BUSHELS_PER_PERSON + rules.seed_cost(sowable) + spare
    )
    return state


# --- Opening the year --------------------------------------------------------


def test_the_first_report_announces_the_five_opening_immigrants() -> None:
    ui = FakeUI(feed=(2000,))
    game = Game(_year_rng(), ui)

    game.play_year()

    # The five immigrants are reported before they are added to the city.
    opening = ("report", 1, 0, config.START_IMMIGRANTS, 0, config.START_POPULATION)
    assert opening in ui.calls
    assert game.state.population == 100


def test_a_quiet_year_runs_through_the_documented_steps() -> None:
    ui = FakeUI(feed=(2000,))
    game = Game(_year_rng(), ui)

    game.play_year()

    assert ui.names() == [
        "report",
        "status",
        "price",
        "ask_buy",
        "ask_sell",
        "ask_feed",
        "ask_plant",
    ]


def test_the_first_year_is_always_plague_free() -> None:
    # The listing starts with Q=1 (line 110), a roll that means "safe".
    ui = FakeUI(feed=(2000,))
    game = Game(_year_rng(), ui)

    assert game.state.plague_roll == config.START_PLAGUE_ROLL

    game.play_year()

    assert "plague" not in ui.names()
    assert game.state.population == 100
    assert game.state.plague_this_year is False


def test_the_plague_halves_the_population_when_the_roll_is_not_positive() -> None:
    ui = FakeUI(feed=(2000,))
    game = Game(_year_rng(), ui, state=GameState(plague_roll=-1))

    game.play_year()

    assert ("plague", 100, 50) in ui.calls
    assert game.state.population == 50
    assert game.state.plague_this_year is True


def test_the_roll_made_at_the_end_of_a_year_decides_the_next_one() -> None:
    # A rule-aware player drives this one: the engine plays both years in full,
    # and a scripted feeding answer that outlives the grain would be rejected
    # over and over again.
    ui = CarefulUI()
    game = Game(_endless_rng(next_plague=PLAGUE_RANDOM), ui)

    game.play_year()

    assert game.state.plague_roll == -1
    assert "plague" not in ui.names()  # year 1 used the starting roll

    game.play_year()

    # Year 2 opens with 100 people plus the 3 immigrants announced in year 1.
    assert ("plague", 103, 51) in ui.calls


def test_the_announced_immigrants_join_the_city_in_the_next_report() -> None:
    ui = FakeUI(feed=(2000,))
    rng = StubRandom(randoms=[0.5, 0.5], integers=[20, 3, 1, 5, 20, 3, 1, 1])
    game = Game(rng, ui, state=GameState(bushels=9000))

    game.play_year()
    announced = game.state.immigrants_this_year

    game.play_year()

    # int(5 * (20 * 1000 + 7000) / 100 / 100 + 1) = 14 newcomers.
    assert announced == 14
    assert ("report", 2, 0, 14, 0, 100) in ui.calls
    assert ("status", 114, 7000) in ui.calls


# --- Land trade --------------------------------------------------------------


def test_buying_land_spends_grain_and_skips_the_sale() -> None:
    ui = FakeUI(buy=(10,), feed=(2000,))
    game = Game(_year_rng(price=20), ui)

    game.play_year()

    assert game.state.acres == 1010
    assert "ask_sell" not in ui.names()
    # 2800 - 10 * 20 = 2600 bushels are left when feeding is offered.
    assert ("ask_feed", 100, 2600) in ui.calls


def test_selling_land_is_offered_only_when_nothing_is_bought() -> None:
    ui = FakeUI(buy=(0,), sell=(100,), feed=(2000,))
    game = Game(_year_rng(price=20), ui)

    game.play_year()

    assert ui.names().index("ask_buy") < ui.names().index("ask_sell")
    assert game.state.acres == 900
    assert ("ask_feed", 100, 4800) in ui.calls


def test_an_unaffordable_purchase_is_rejected_and_asked_again() -> None:
    ui = FakeUI(buy=(500, 10), feed=(2000,))
    game = Game(_year_rng(price=20), ui)

    game.play_year()

    assert ui.errors == ["Think again. You have only 2800 bushels of grain."]
    assert game.state.acres == 1010


def test_selling_every_acre_is_rejected() -> None:
    ui = FakeUI(buy=(0,), sell=(1000, 999), feed=(2000,))
    game = Game(_year_rng(), ui)

    game.play_year()

    assert ui.errors == ["Think again. You own only 1000 acres."]
    assert game.state.acres == 1


def test_negative_answers_ask_again_instead_of_ending_the_game() -> None:
    ui = FakeUI(buy=(-5, 0), feed=(2000,))
    game = Game(_year_rng(), ui)

    game.play_year()

    assert len(ui.errors) == 1
    assert game.state.game_over is False


# --- Feeding and starvation --------------------------------------------------


def test_feeding_fewer_than_need_starves_the_rest() -> None:
    ui = FakeUI(feed=(1900,))
    game = Game(_year_rng(), ui)

    game.play_year()

    state = game.state
    assert state.starved_this_year == 5  # 100 people, 95 fed
    assert state.population == 95
    assert state.total_starved == 5
    assert state.starved_percent_avg == pytest.approx(5.0)


def test_feeding_more_than_the_store_is_rejected() -> None:
    ui = FakeUI(feed=(3000, 2000))
    game = Game(_year_rng(), ui)

    game.play_year()

    assert ui.errors == ["Think again. You have only 2800 bushels of grain."]
    assert game.state.starved_this_year == 0


def test_a_ui_that_only_gives_unaffordable_feeding_answers_is_given_up_on() -> None:
    # An unbounded retry loop would spin the CPU forever; the engine caps it.
    ui = FakeUI(feed=(999_999,))
    game = Game(_year_rng(), ui)

    with pytest.raises(RuntimeError):
        game.play_year()

    assert len(ui.errors) == config.MAX_ANSWER_ATTEMPTS


def test_a_ui_that_only_offers_unaffordable_land_is_given_up_on() -> None:
    ui = FakeUI(buy=(10_000,))
    game = Game(_year_rng(price=26), ui)

    with pytest.raises(RuntimeError):
        game.play_year()

    assert len(ui.errors) == config.MAX_ANSWER_ATTEMPTS


def test_the_starvation_average_is_a_running_mean_over_the_starving_years() -> None:
    ui = FakeUI(feed=(1900, 1900), plant=(0,))
    game = Game(_endless_rng(), ui, state=GameState(bushels=8000))

    game.play_year()
    game.play_year()

    # 5 of 100 starved in the first year and 3 of the 98 people (95 survivors
    # plus 3 immigrants) in the second: ((2 - 1) * 5 + 3 * 100 / 98) / 2.
    assert game.state.year == 2
    assert game.state.starved_percent_avg == pytest.approx(4.0306, rel=1e-4)
    assert game.state.total_starved == 8


def test_an_overfed_year_is_left_out_of_the_starvation_figures() -> None:
    # ``550 IF P<C THEN 210``: the listing skips the tally when the grain fed
    # would have been enough for more people than are alive.
    ui = FakeUI(feed=(1900, 2000), plant=(0,))
    game = Game(_endless_rng(), ui, state=GameState(bushels=8000))

    game.play_year()  # 5 of 100 people starve
    average = game.state.starved_percent_avg

    game.play_year()  # 2000 bushels would feed 100, but only 98 people live

    assert average == pytest.approx(5.0)
    assert game.state.starved_this_year == 0
    assert game.state.starved_percent_avg == pytest.approx(5.0)  # not tallied
    assert game.state.total_starved == 5
    assert game.state.population == 98  # the surplus grain was simply wasted


def test_sowing_and_immigration_use_the_population_before_the_deaths() -> None:
    # ``555 P=C`` only shrinks the population at the very end of the year.
    ui = FakeUI(feed=(1200,), plant=(700,))
    game = Game(_year_rng(migrants=5), ui)

    game.play_year()

    # Feeding 1200 bushels leaves 60 people fed of the 100 alive, yet all 100
    # may tend the fields: 10 * 100 - 1 = 999 acres, so 700 are accepted.
    assert ui.errors == []
    # Store after feeding: 1600, minus 350 for the seed, plus 700 * 3 harvested.
    assert game.state.bushels == 1600 - 350 + 700 * 3
    # The immigration formula saw 100 people, not the 60 who live on:
    # int(5 * (20 * 1000 + 3350) / 100 / 100 + 1) = int(12.675) = 12.
    assert game.state.immigrants_this_year == 12
    assert game.state.starved_this_year == 40
    assert game.state.population == 60


# --- Sowing, harvest and rats ------------------------------------------------


def test_planting_more_than_the_land_owned_is_rejected() -> None:
    ui = FakeUI(feed=(2000,), plant=(1001, 500))
    game = Game(_year_rng(), ui)

    game.play_year()

    assert ui.errors == ["Think again. You own only 1000 acres."]
    # 800 bushels after feeding, 250 spent on seed, then 500 * 3 harvested.
    assert game.state.bushels == 800 - 250 + 500 * 3


def test_planting_more_than_the_seed_allows_is_rejected() -> None:
    ui = FakeUI(feed=(2780,), plant=(100, 0))
    game = Game(_year_rng(), ui)

    game.play_year()

    assert ui.errors == ["Think again. You have only 20 bushels of grain."]
    assert game.state.bushels == 20


def test_planting_more_than_the_labour_allows_is_rejected() -> None:
    ui = FakeUI(feed=(2000,), plant=(600, 499))
    game = Game(_year_rng(), ui, state=GameState(plague_roll=-1))

    game.play_year()

    # The plague left 50 people, who can tend at most 499 acres.
    assert ui.errors == [
        "But you have only 50 people to tend the fields. Now then,"
    ]
    assert game.state.bushels == 800 - 249 + 499 * 3


def test_rats_raid_the_store_before_the_harvest() -> None:
    ui = FakeUI(feed=(2000,), plant=(100,))
    game = Game(_year_rng(yield_per_acre=4, rats=2), ui)

    game.play_year()

    # Store after feeding and sowing: 2800 - 2000 - 50 = 750 bushels.
    # The rats take half of it, then the harvest of 100 * 4 arrives.
    assert game.state.rats_ate_this_year == 375
    assert game.state.bushels == 750 - 375 + 400
    assert game.state.yield_per_acre == 4


# --- Impeachment -------------------------------------------------------------


def test_starving_more_than_45_percent_impeaches_the_ruler() -> None:
    ui = FakeUI(feed=(0,))
    game = Game(_year_rng(), ui)

    verdict = game.play()

    assert verdict is Verdict.IMPEACHED
    assert game.state.verdict is Verdict.IMPEACHED
    assert game.state.game_over is True
    assert "impeachment" in ui.names()
    assert "summary" not in ui.names()


def test_exactly_45_percent_starved_does_not_impeach() -> None:
    ui = FakeUI(feed=(1100,))
    game = Game(_year_rng(), ui)

    game.play_year()

    assert game.state.starved_this_year == 45
    assert game.state.verdict is None
    assert game.state.game_over is False


def test_an_impeached_game_cannot_play_another_year() -> None:
    game = Game(_year_rng(), FakeUI(feed=(0,)))
    game.play()

    with pytest.raises(RuntimeError):
        game.play_year()


# --- The closing report ------------------------------------------------------


def test_the_closing_report_adds_the_pending_immigrants() -> None:
    # ``270 IF Z=11 THEN 860``: the listing reports an eleventh year before it
    # scores the ruler, and the immigration queued in year ten joins first.
    ui = FakeUI()
    game = Game(
        StubRandom(),  # no draws left: the closing report must not roll anything
        ui,
        state=GameState(
            year=config.TERM_YEARS,
            population=50,
            acres=500,
            immigrants_this_year=7,
        ),
    )

    verdict = game.play()

    assert ("summary", config.TERM_YEARS, verdict) in ui.calls
    assert game.state.population == 57
    assert game.state.acres_per_person == pytest.approx(500 / 57)


def test_the_closing_report_resolves_the_last_plague_roll() -> None:
    ui = FakeUI()
    game = Game(
        StubRandom(),
        ui,
        state=GameState(
            year=config.TERM_YEARS,
            population=50,
            immigrants_this_year=7,
            plague_roll=-1,
        ),
    )

    game.play()

    assert ("plague", 57, 28) in ui.calls
    assert game.state.population == 28


def test_a_closing_plague_halves_the_population_the_verdict_uses() -> None:
    safe = Game(
        StubRandom(
            randoms=[SAFE_PLAGUE_RANDOM] * config.TERM_YEARS,
            integers=cycle([20, 3, 1, 1]),
        ),
        CarefulUI(),
    )
    struck = Game(
        StubRandom(
            randoms=[SAFE_PLAGUE_RANDOM] * (config.TERM_YEARS - 1)
            + [PLAGUE_RANDOM],
            integers=cycle([20, 3, 1, 1]),
        ),
        CarefulUI(),
    )

    safe.play()
    struck.play()

    # The two games share every draw but the roll made at the end of year ten,
    # which only the closing report resolves.
    assert struck.state.population == safe.state.population // 2


# --- The health rule set -----------------------------------------------------


def test_the_health_flag_adds_no_random_draw() -> None:
    """A health game with every offer declined replays the classic term exactly.

    The same property the farming rule set has: the flag changes the figures the
    rules are handed, never the stream of events, so the two rule sets can be
    measured against each other on the same seeds.
    """
    classic = Game(SeededRandom(seed=11), CarefulUI())
    classic.play()

    ui = CarefulUI()
    kind = Game(SeededRandom(seed=11), ui, state=GameState(health=True))
    kind.play()

    assert "ask_research" in ui.names(), "the research question was never put"
    assert _figures(kind.state) == _figures(classic.state)


def test_a_health_measure_is_paid_for_and_shows_from_the_next_year() -> None:
    """Research costs grain at once and only changes the figures of later years."""
    ui = FakeUI(feed=(1600,), research=["milled_grain", None])
    game = Game(_endless_rng(), ui, state=GameState(health=True, bushels=10_000))

    game.play_year()

    assert game.state.unlocked == frozenset({"milled_grain"})
    assert ("research", "milled_grain", config.HEALTH_COSTS["milled_grain"]) in ui.calls
    # 1600 bushels feed 80 people at the classic twenty, and the mill bought this
    # year does not save them.
    assert game.state.starved_this_year == 20

    game.play_year()

    # The next year the same 1600 bushels feed everybody: the mill shows at last.
    assert game.state.unlocked == frozenset({"milled_grain"})
    assert game.state.starved_this_year == 0


def test_the_research_question_covers_both_programmes() -> None:
    """With both rule sets in play one question a year carries both trees."""
    ui = FakeUI(feed=(2000,), plant=(0,), research=[None])
    game = Game(
        _endless_rng(),
        ui,
        state=GameState(agriculture=True, health=True, bushels=10_000),
    )

    game.play_year()

    asked = [call for call in ui.calls if call[0] == "ask_research"]
    assert len(asked) == 1, "a year holds one research moment"
    _kind, _year, _bushels, offered = asked[0]
    assert offered[:3] == ("plough", "fallow", "granaries"), "the farmers come first"
    assert offered[3:] == ("wells", "herb_gatherers", "midwives", "milled_grain")


def test_the_plague_spares_the_share_the_healers_reach() -> None:
    """The public health in force decides how many the plague takes."""
    ui = FakeUI(feed=(2000,), plant=(499,))
    game = Game(
        _endless_rng(next_plague=PLAGUE_RANDOM),
        ui,
        state=GameState(
            health=True, unlocked=frozenset({"temple_hospital"}), bushels=10_000
        ),
    )

    game.play_year()
    game.play_year()

    plague = [call for call in ui.calls if call[0] == "plague"]
    assert len(plague) == 1, "the roll made at the end of the first year struck"
    _kind, before, after = plague[0]
    assert after == before * config.HEALTH_SURVIVOR_PERCENT["temple_hospital"] // 100


def test_the_drains_make_the_plague_find_fewer_years() -> None:
    """The resistance is in the roll itself, so it changes the year that follows."""

    def roll_for(unlocked: frozenset[str]) -> int:
        game = Game(
            _endless_rng(next_plague=0.17),
            FakeUI(feed=(2000,)),
            state=GameState(health=True, unlocked=unlocked),
        )
        game.play_year()
        return game.state.plague_roll

    assert roll_for(frozenset()) == 0, "the classic roll for that draw, a plague year"
    assert roll_for(frozenset({"brick_drains"})) == 3, "shifted by the deepest drains"


def test_births_join_the_city_when_the_next_report_opens() -> None:
    """The nursery works at the end of a year the city was fed in."""
    ui = FakeUI(feed=(2000,), plant=(999,))
    game = Game(
        _endless_rng(),
        ui,
        state=GameState(health=True, unlocked=frozenset({"palace_nursery"})),
    )

    game.play_year()

    rate = config.HEALTH_BIRTHS_PER_THOUSAND["palace_nursery"]
    assert game.state.born_this_year == rules.births(
        game.state.population, fed=game.state.population, per_thousand=rate
    )

    game.play_year()

    reported = [call for call in ui.calls if call[0] == "report"][-1]
    assert reported[4] == 3, "the second report announces the three children"


def test_a_year_the_city_could_not_feed_brings_no_children() -> None:
    """Hunger is no time for a nursery, whatever the rate in force."""
    ui = FakeUI(feed=(1600,), plant=(999,))
    game = Game(
        _endless_rng(),
        ui,
        state=GameState(health=True, unlocked=frozenset({"palace_nursery"})),
    )

    game.play_year()

    assert game.state.starved_this_year == 20
    assert game.state.born_this_year == 0


def test_a_closing_plague_spares_the_share_the_healers_reach() -> None:
    """The phantom year of the closing report reads the health in force."""
    ui = CarefulUI()
    game = Game(
        StubRandom(
            randoms=[SAFE_PLAGUE_RANDOM] * (config.TERM_YEARS - 1) + [PLAGUE_RANDOM],
            integers=cycle([20, 3, 1, 1]),
        ),
        ui,
        state=GameState(
            health=True,
            unlocked=frozenset({"house_of_life"}),
            bushels=100_000,
        ),
    )

    game.play()

    plague = [call for call in ui.calls if call[0] == "plague"]
    assert len(plague) == 1, "only the closing report resolved a plague"
    _kind, before, after = plague[0]
    assert after == before * config.HEALTH_SURVIVOR_PERCENT["house_of_life"] // 100


def test_the_health_rule_set_asks_nothing_when_no_measure_is_open() -> None:
    """A ruler who cannot afford a measure is never asked a question."""
    ui = FakeUI(feed=(1,))
    game = Game(_endless_rng(), ui, state=GameState(health=True, bushels=1))

    game.play_year()

    assert "ask_research" not in ui.names()
    assert game.state.unlocked == frozenset()


# --- The whole term ----------------------------------------------------------


def test_the_mediocre_verdict_draws_the_would_be_assassins() -> None:
    # ``INT(P * .8 * RND(1))`` with 100 people and a draw of 0.5 (line 965).
    ui = FakeUI()
    game = Game(
        StubRandom(randoms=[0.5]),
        ui,
        state=GameState(
            year=config.TERM_YEARS,
            population=100,
            acres=950,  # 9.5 acres per person: mediocre
            immigrants_this_year=0,
        ),
    )

    verdict = game.play()

    assert verdict is Verdict.MEDIOCRE
    assert game.state.would_be_assassins == 40
    assert ("summary", config.TERM_YEARS, verdict) in ui.calls


def test_the_other_verdicts_do_not_draw_the_assassin_figure() -> None:
    # A stub with no draws left: only the mediocre verdict may roll one.
    game = Game(
        StubRandom(),
        FakeUI(),
        state=GameState(
            year=config.TERM_YEARS,
            population=100,
            acres=1000,  # 10 acres per person: fantastic
            immigrants_this_year=0,
        ),
    )

    verdict = game.play()

    assert verdict is Verdict.FANTASTIC
    assert game.state.would_be_assassins == 0


def test_a_full_term_ends_with_a_verdict() -> None:
    ui = CarefulUI()
    game = Game(_endless_rng(), ui)

    verdict = game.play()

    assert game.state.year == config.TERM_YEARS
    assert game.state.game_over is True
    assert verdict is not None
    assert ui.names()[0] == "intro"
    assert ui.names()[-1] == "summary"
    assert ui.intro_shown == 1


def test_the_summary_receives_the_final_state_and_verdict() -> None:
    ui = CarefulUI()
    game = Game(_endless_rng(), ui)

    verdict = game.play()

    assert ("summary", config.TERM_YEARS, verdict) in ui.calls


def test_the_verdict_matches_the_end_of_term_statistics() -> None:
    game = Game(_endless_rng(), CarefulUI())

    verdict = game.play()

    assert game.state.year == config.TERM_YEARS  # the term ran to its end
    assert verdict is rules.evaluate_verdict(
        game.state.starved_percent_avg, game.state.acres_per_person
    )
    # Well fed but never given more land, the city ends up crowded: only the
    # acres per person separate the verdicts once nobody starves.
    assert verdict is Verdict.TYRANT
    assert game.state.acres_per_person < config.VERDICT_ACRES_POOR


def test_the_same_seed_reproduces_the_same_game() -> None:
    first = Game(SeededRandom(seed=7), CarefulUI())
    second = Game(SeededRandom(seed=7), CarefulUI())

    assert first.play() is second.play()
    assert first.state == second.state


def test_playing_a_finished_game_changes_nothing() -> None:
    ui = CarefulUI()
    game = Game(_endless_rng(), ui)
    verdict = game.play()
    calls = len(ui.calls)

    assert game.play() is verdict
    assert len(ui.calls) == calls
    assert ui.intro_shown == 1


def test_play_year_raises_once_the_ten_year_term_is_over() -> None:
    game = Game(_endless_rng(), CarefulUI())
    game.play()

    with pytest.raises(RuntimeError):
        game.play_year()


# --- The marathon term -------------------------------------------------------


def test_a_marathon_term_is_scored_after_a_century_in_office() -> None:
    # ``270 IF Z=11 THEN 860``: the closing report opens the year after the last
    # one played, whatever length the term has. Seed 38 is the one careful game
    # of the measured 500 that survives all hundred years; see ``balancing.md``.
    ui = CarefulUI()
    game = Game(
        SeededRandom(seed=38),
        ui,
        state=GameState(term_years=config.MARATHON_TERM_YEARS),
    )

    verdict = game.play()

    assert ui.names()[0] == "intro"
    assert ui.names()[-1] == "summary"
    assert game.state.year == config.MARATHON_TERM_YEARS
    assert game.state.game_over is True
    assert verdict is Verdict.FANTASTIC


def test_the_closing_report_waits_for_the_whole_marathon() -> None:
    # A state at the classic tenth year is only a tenth of the marathon, so the
    # engine must not treat the term as over: the length comes from the state.
    game = Game(
        _endless_rng(),
        CarefulUI(),
        state=GameState(term_years=config.MARATHON_TERM_YEARS),
    )

    game.play_year()

    assert game.state.year == 1
    assert game.state.game_over is False


def test_a_marathon_state_is_closed_at_its_hundredth_year() -> None:
    # The closing report runs at the year the state names, not at the tenth.
    ui = FakeUI()
    game = Game(
        StubRandom(),  # no draws left: the closing report must not roll anything
        ui,
        state=GameState(
            year=config.MARATHON_TERM_YEARS,
            term_years=config.MARATHON_TERM_YEARS,
            population=50,
            acres=500,
            immigrants_this_year=7,
        ),
    )

    verdict = game.play()

    assert ui.names()[0] == "intro"  # the term had not been closed before
    assert ("summary", config.MARATHON_TERM_YEARS, verdict) in ui.calls
    assert game.state.population == 57
    assert game.state.year == config.MARATHON_TERM_YEARS


# --- The agriculture rule set ------------------------------------------------


class _FarmerUI(CarefulUI):
    """A careful player who buys the cheapest technology on offer every year."""

    def ask_research(
        self, state: GameState, choices: Sequence[tech.Offer]
    ) -> str | None:
        self.calls.append(
            ("ask_research", state.year, tuple(o.node.key for o in choices))
        )
        return min(choices, key=lambda offer: offer.node.cost).node.key


def test_the_classic_rule_set_never_asks_for_research() -> None:
    """Without the rule set the vintage term has one question less per year."""
    ui = CarefulUI()
    game = Game(_endless_rng(), ui)

    game.play()

    assert "ask_research" not in ui.names()
    assert game.state.unlocked == frozenset()


#: The flags of the optional rule sets, which an A/B comparison drops: a game played
#: with a rule set and a classic game differ only in what those flags add.
RULE_SET_FLAGS = ("agriculture", "health")


def _figures(state: GameState) -> dict[str, object]:
    """Return a state without its rule-set flags, for an A/B comparison."""
    return {
        key: value for key, value in asdict(state).items() if key not in RULE_SET_FLAGS
    }


def test_the_rule_set_adds_no_random_draw() -> None:
    """A term played with the rule set on and research declined replays the classic.

    This is what makes the two rule sets measurable against each other: research
    changes the figures the rules are handed, never the random events themselves.
    """
    classic = Game(SeededRandom(seed=11), CarefulUI())
    classic.play()

    ui = CarefulUI()
    agriculture = Game(
        SeededRandom(seed=11), ui, state=GameState(agriculture=True)
    )
    agriculture.play()

    assert "ask_research" in ui.names(), "the research question was never put"
    assert _figures(agriculture.state) == _figures(classic.state)


def test_research_is_paid_out_of_the_spare_grain_of_the_year() -> None:
    """The cost leaves the store and the node is unlocked for the years to come."""
    ui = FakeUI(plant=(0,), research=["plough"])
    state = _spare_state(config.TECH_COSTS["plough"] + 100, agriculture=True)
    store = state.bushels
    game = Game(_year_rng(), ui, state=state)

    game.play_year()

    assert game.state.unlocked == frozenset({"plough"})
    assert game.state.bushels == store - config.TECH_COSTS["plough"]
    assert game.state.spare_bushels == config.TECH_COSTS["plough"] + 100
    assert ("research", "plough", config.TECH_COSTS["plough"]) in ui.calls


def test_declining_research_keeps_the_grain_and_unlocks_nothing() -> None:
    """Answering ``None`` costs nothing; only what the surplus pays for is offered."""
    ui = FakeUI(plant=(0,))
    state = _spare_state(config.TECH_COSTS["granaries"], agriculture=True)
    store = state.bushels
    game = Game(_year_rng(), ui, state=state)

    game.play_year()

    assert ("ask_research", 1, store, ("plough", "fallow", "granaries")) in ui.calls
    assert game.state.unlocked == frozenset()
    assert game.state.bushels == store
    assert "research" not in ui.names()


def test_a_ruler_without_grain_is_not_asked_to_research() -> None:
    """A question with no affordable answer is never put."""
    ui = FakeUI(plant=(0,))
    game = Game(_year_rng(), ui, state=GameState(agriculture=True, bushels=100))

    game.play_year()

    assert "ask_research" not in ui.names()
    assert game.state.unlocked == frozenset()


def test_a_year_that_leaves_nothing_spare_puts_no_research_question() -> None:
    """The bread of the city is not a budget, however full the granary looks."""
    ui = FakeUI(plant=(0,))
    state = _spare_state(0, agriculture=True)
    store = state.bushels
    game = Game(_year_rng(), ui, state=state)

    game.play_year()

    assert store >= config.TECH_COSTS["plough"], "the store covers the cheapest node"
    assert "ask_research" not in ui.names()
    assert game.state.unlocked == frozenset()
    assert game.state.bushels == store


def test_the_health_s_feeding_rate_widens_the_year_s_budget() -> None:
    """A person fed on thirteen bushels leaves seven more for the programme."""
    ui = FakeUI(plant=(0,))
    state = GameState(health=True, unlocked=frozenset({"date_presses"}))
    people = state.population + state.immigrants_this_year
    sowable = min(state.acres, rules.max_plantable_acres(people))
    seed = rules.seed_cost(sowable)
    cheap_food = people * config.HEALTH_BUSHELS_PER_PERSON["date_presses"]
    state.bushels = cheap_food + seed + 900
    game = Game(_year_rng(), ui, state=state)

    game.play_year()

    assert state.spare_bushels == 900
    assert "ask_research" in ui.names()
    classic_spare = state.bushels - people * config.BUSHELS_PER_PERSON - seed
    assert classic_spare == 200, "the classic rate would leave far less to invest"


def test_only_one_research_starts_in_a_year() -> None:
    """The tree is climbed a node at a time, however much the year leaves spare."""
    ui = FakeUI(plant=(0,), research=["plough", "fallow"])
    state = _spare_state(config.TECH_COSTS["granaries"], agriculture=True)
    store = state.bushels
    game = Game(_year_rng(), ui, state=state)

    game.play_year()

    assert game.state.unlocked == frozenset({"plough"})
    assert [call for call in ui.calls if call[0] == "ask_research"] == [
        ("ask_research", 1, store, ("plough", "fallow", "granaries"))
    ]


def test_an_unknown_technology_is_rejected_and_asked_again() -> None:
    """A key the tree does not know is explained and the question is put again."""
    ui = FakeUI(plant=(0,), research=["taxes", "plough"])
    state = _spare_state(config.TECH_COSTS["granaries"], agriculture=True)
    game = Game(_year_rng(), ui, state=state)

    game.play_year()

    assert ui.errors == [
        "Think again. 'taxes' is not one of the technologies on offer; "
        "answer 0 to research nothing this year."
    ]
    assert game.state.unlocked == frozenset({"plough"})


def test_a_ui_that_only_offers_an_unknown_technology_is_given_up_on() -> None:
    """The give-up bound covers the research question like the other four."""
    ui = FakeUI(plant=(0,), research=["taxes"])
    state = _spare_state(config.TECH_COSTS["granaries"], agriculture=True)
    game = Game(_year_rng(), ui, state=state)

    with pytest.raises(RuntimeError):
        game.play_year()

    assert len(ui.errors) == config.MAX_ANSWER_ATTEMPTS


def test_a_farmer_climbs_the_tree_one_node_a_year() -> None:
    """Each year buys the cheapest node on offer, so the tree only ever grows."""
    ui = _FarmerUI()
    game = Game(_endless_rng(), ui, state=GameState(agriculture=True))

    game.play_year()
    first = game.state.unlocked
    game.play_year()

    assert len(first) == 1
    assert first < game.state.unlocked, "the second year unlocked nothing new"


def test_a_researched_technology_applies_from_the_year_it_is_read() -> None:
    """Fallow fields add their bushels to the harvest of the year that follows."""
    ui = FakeUI(feed=(config.START_BUSHELS,), plant=(0,))
    state = GameState(agriculture=True, unlocked=frozenset({"fallow"}))
    game = Game(_year_rng(yield_per_acre=3), ui, state=state)

    game.play_year()

    assert game.state.yield_per_acre == 3 + config.TECH_YIELD_BONUS_PER_NODE


def test_the_classic_harvest_is_the_roll_alone() -> None:
    """Without the rule set nothing is added to the 1-5 roll."""
    ui = FakeUI(feed=(config.START_BUSHELS,), plant=(0,))
    game = Game(_year_rng(yield_per_acre=3), ui, state=GameState())

    game.play_year()

    assert game.state.yield_per_acre == 3


def test_granaries_shrink_the_rats_share_of_the_store() -> None:
    """The technology divides what an even roll would have left the rats."""
    store = 1000
    ui = FakeUI(feed=(0,), plant=(0,))
    state = GameState(
        agriculture=True, unlocked=frozenset({"granaries"}), bushels=store
    )
    game = Game(_year_rng(rats=4), ui, state=state)

    game.play_year()

    assert game.state.rats_ate_this_year == (
        store // 4 // config.TECH_RAT_DIVISOR["granaries"]
    )


def test_the_plough_sows_more_acres_for_the_same_seed() -> None:
    """A sowing the classic rate could not pay for is accepted with the plough."""
    acres = 999
    ui = FakeUI(plant=(acres,), feed=(0,))
    state = GameState(agriculture=True, unlocked=frozenset({"plough"}), bushels=400)
    game = Game(_year_rng(rats=1), ui, state=state)

    game.play_year()

    assert ui.errors == []
    assert game.state.bushels == (
        400
        - acres // config.TECH_ACRES_PER_SEED["plough"]
        + rules.harvest(acres, 3)
    )


def test_the_classic_rate_refuses_the_sowing_the_plough_allows() -> None:
    """The same answer breaks the classic seed rule, which is the whole point."""
    ui = FakeUI(plant=(999,), feed=(0,))
    game = Game(_year_rng(rats=1), ui, state=GameState(bushels=400))

    with pytest.raises(RuntimeError):
        game.play_year()

    assert ui.errors[0] == "Think again. You have only 400 bushels of grain."


def test_draft_teams_let_one_person_tend_more_acres() -> None:
    """The labour limit follows the tree: twelve acres a person instead of ten."""
    ui = FakeUI(plant=(1000,), feed=(0,))
    state = GameState(
        agriculture=True, unlocked=frozenset({"draft_teams"}), bushels=1000
    )
    game = Game(_year_rng(rats=1), ui, state=state)

    game.play_year()

    assert ui.errors == []


def test_the_classic_labour_limit_refuses_the_same_sowing() -> None:
    """A hundred people tend at most 999 acres, so the thousandth is refused."""
    ui = FakeUI(plant=(1000,), feed=(0,))
    game = Game(_year_rng(rats=1), ui, state=GameState(bushels=1000))

    with pytest.raises(RuntimeError):
        game.play_year()

    assert ui.errors[0] == (
        "But you have only 100 people to tend the fields. Now then,"
    )
