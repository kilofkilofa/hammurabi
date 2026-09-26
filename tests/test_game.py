"""Tests for the ten-year engine in :mod:`hammurabi.game`.

The engine is driven by the shared test doubles from :mod:`tests.support`: a
scripted random source and a recording UI, so no test needs a terminal or real
randomness.
"""

from __future__ import annotations

from itertools import cycle

import pytest

from hammurabi import config, rules
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


# --- Opening the year --------------------------------------------------------


def test_the_first_report_announces_the_five_opening_immigrants() -> None:
    ui = FakeUI(feed=(2000,))
    game = Game(_year_rng(), ui)

    game.play_year()

    # The five immigrants are reported before they are added to the city.
    opening = ("report", 1, 0, config.START_IMMIGRANTS, config.START_POPULATION)
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
    assert ("report", 2, 0, 14, 100) in ui.calls
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
