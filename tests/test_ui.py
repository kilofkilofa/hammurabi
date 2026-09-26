"""Tests for the ``rich`` console UI in :mod:`hammurabi.ui`.

The UI is exercised without a terminal: every test draws into a buffer-backed
console and injects a scripted reader, the same seam the entry point uses.
"""

from __future__ import annotations

from io import StringIO

import pytest

from hammurabi import config
from hammurabi.game import Game
from hammurabi.models import GameState, Verdict
from hammurabi.random_source import SeededRandom
from hammurabi.ui import ConsoleUI
from tests.support import careful_console_answers, plain_console, render


def _ui(*answers: str) -> tuple[ConsoleUI, StringIO, list[str]]:
    """Return a UI replaying ``answers`` and recording the questions asked.

    The last answer is repeated like ``support.repeat_last``, so a question the
    engine sends back is answered with the same text.
    """
    console, buffer = plain_console()
    questions: list[str] = []

    def read(question: str) -> str:
        questions.append(question)
        return answers[min(len(questions), len(answers)) - 1]

    return ConsoleUI(console=console, read=read), buffer, questions


# --- Reporting ---------------------------------------------------------------


def test_the_intro_names_the_game_the_term_and_the_starting_position() -> None:
    ui, buffer, _ = _ui("0")

    ui.show_intro(GameState())

    text = render(buffer)
    assert "HAMURABI" in text
    assert "Sumeria" in text
    assert f"{config.TERM_YEARS}-year term of office" in text
    assert "You begin with 95 people, 1000 acres and 2800 bushels of grain." in text


def test_the_intro_credits_the_port_and_its_licence() -> None:
    ui, buffer, _ = _ui("0")

    ui.show_intro(GameState())

    text = render(buffer)
    assert "Python port by kilofkilofa" in text
    assert "non-commercial" in text


def test_the_report_opens_the_year_with_deaths_and_arrivals() -> None:
    ui, buffer, _ = _ui("0")

    ui.show_report(GameState(year=1, starved_this_year=0, immigrants_this_year=5))

    text = render(buffer)
    assert "I beg to report to you," in text
    assert "In year 1, 0 people starved, 5 came to the city." in text


def test_the_status_reports_people_land_harvest_rats_and_grain() -> None:
    ui, buffer, _ = _ui("0")
    state = GameState(
        population=95,
        acres=1000,
        yield_per_acre=3,
        rats_ate_this_year=200,
        bushels=2800,
    )

    ui.show_status(state)

    text = render(buffer)
    assert "Population 95" in text
    assert "Land owned 1000 acres" in text
    assert "Last harvest 3 bushels per acre" in text
    assert "Eaten by rats 200 bushels" in text
    assert "Grain in store 2800 bushels" in text


def test_the_plague_reports_both_populations() -> None:
    ui, buffer, _ = _ui("0")

    ui.show_plague(before=100, after=50)

    text = render(buffer)
    assert "A horrible plague struck! Half the people died." in text
    assert "from 100 to 50" in text


def test_the_land_price_is_announced() -> None:
    ui, buffer, _ = _ui("0")

    ui.show_land_price(23)

    assert "Land is trading at 23 bushels per acre." in render(buffer)


def test_a_rejected_answer_is_explained_with_the_engine_message() -> None:
    ui, buffer, _ = _ui("0")

    ui.show_error("Think again. You have only 800 bushels of grain.")

    assert "Think again. You have only 800 bushels of grain." in render(buffer)


# --- Asking ------------------------------------------------------------------


def test_the_four_questions_return_the_numbers_typed() -> None:
    ui, _, questions = _ui("7", "3", "2000", "12")

    assert ui.ask_acres_to_buy(GameState(), price=20) == 7
    assert ui.ask_acres_to_sell(GameState(), price=20) == 3
    assert ui.ask_bushels_to_feed(GameState()) == 2000
    assert ui.ask_acres_to_plant(GameState()) == 12
    assert len(questions) == 4


def test_every_question_repeats_the_figures_the_player_needs() -> None:
    ui, buffer, questions = _ui("0")
    state = GameState(population=95, acres=1000, bushels=2800)

    ui.ask_acres_to_buy(state, price=23)
    ui.ask_acres_to_sell(state, price=23)
    ui.ask_bushels_to_feed(state)
    ui.ask_acres_to_plant(state)

    assert "wish to buy" in questions[0]
    assert "you have 2800 bushels, land is 23 bushels per acre" in questions[0]
    assert "you own 1000 acres, land is 23 bushels per acre" in questions[1]
    assert "you have 2800 bushels, 95 people live in the city" in questions[2]
    assert "you own 1000 acres, you have 2800 bushels" in questions[3]
    # The question is drawn as well as handed to the reader, so that a player
    # typing on stdin sees it.
    assert "How many acres do you wish to plant with seed?" in render(buffer)


def test_a_line_that_is_not_a_whole_number_is_asked_again() -> None:
    ui, buffer, questions = _ui("twelve", "12")

    assert ui.ask_acres_to_plant(GameState()) == 12
    assert len(questions) == 2
    assert "'twelve' is not a whole number. Try again." in render(buffer)


def test_an_empty_answer_is_asked_again() -> None:
    ui, _, questions = _ui("", "0")

    assert ui.ask_bushels_to_feed(GameState()) == 0
    assert len(questions) == 2


def test_a_reader_that_never_answers_readably_is_given_up_on() -> None:
    ui, _, questions = _ui("not a number")

    with pytest.raises(RuntimeError, match="gave up after"):
        ui.ask_bushels_to_feed(GameState())

    # The retry loop is bounded, exactly like the engine's own one, so that no
    # input can spin a core forever.
    assert len(questions) == config.MAX_ANSWER_ATTEMPTS


def test_an_ended_input_stops_the_question() -> None:
    console, _ = plain_console()

    def read(_question: str) -> str:
        raise EOFError

    ui = ConsoleUI(console=console, read=read)

    with pytest.raises(EOFError):
        ui.ask_acres_to_buy(GameState(), price=20)


# --- Closing the game --------------------------------------------------------


def test_the_impeachment_declares_the_ruler_a_national_fink() -> None:
    ui, buffer, _ = _ui("0")

    ui.show_impeachment(GameState(year=3, starved_this_year=80))

    text = render(buffer)
    assert "You starved 80 people in one year!!!" in text
    assert "impeached and thrown out of office" in text
    assert "declared national fink!!!!" in text
    assert "So long for now." in text


def test_the_summary_reports_the_term_statistics() -> None:
    ui, buffer, _ = _ui("0")
    state = GameState(
        population=57,
        acres=500,
        total_starved=130,
        starved_percent_avg=12.5,
    )

    ui.show_summary(state, Verdict.TYRANT)

    text = render(buffer)
    assert f"In your {config.TERM_YEARS}-year term of office, 12.5 percent" in text
    assert "a total of 130 people died!!" in text
    assert "You started with 10.5 acres per person" in text
    assert "ended with 8.8 acres per person" in text
    assert "Nero and Ivan IV" in text
    assert "So long for now." in text


def test_the_mediocre_summary_names_the_would_be_assassins() -> None:
    ui, buffer, _ = _ui("0")
    state = GameState(population=100, acres=950, would_be_assassins=42)

    ui.show_summary(state, Verdict.MEDIOCRE)

    text = render(buffer)
    assert "Mediocre" in text
    assert "42 people would dearly like to see you assassinated" in text


def test_the_fantastic_summary_compares_the_ruler_to_jefferson() -> None:
    ui, buffer, _ = _ui("0")

    ui.show_summary(GameState(), Verdict.FANTASTIC)

    text = render(buffer)
    assert "Fantastic" in text
    assert "Charlemagne, Disraeli and Jefferson" in text


def test_an_end_of_term_impeachment_uses_the_fink_text() -> None:
    ui, buffer, _ = _ui("0")
    state = GameState(
        year=config.TERM_YEARS,
        starved_this_year=40,
        starved_percent_avg=35.0,
    )

    ui.show_summary(state, Verdict.IMPEACHED)

    text = render(buffer)
    assert f"In your {config.TERM_YEARS}-year term of office" in text
    assert "declared national fink!!!!" in text
    assert "Nero and Ivan IV" not in text


# --- The engine and the UI together ------------------------------------------


def test_the_engine_complains_through_the_console_and_asks_again() -> None:
    console, buffer = plain_console()
    answers = iter(["100000", "0"])  # more grain than the store holds, then none

    def read(question: str) -> str:
        return next(answers) if "wish to feed" in question else "0"

    game = Game(SeededRandom(seed=1), ConsoleUI(console=console, read=read))

    game.play_year()

    assert "Think again. You have only 2800 bushels of grain." in render(buffer)


def test_a_whole_game_can_be_played_through_the_console_ui() -> None:
    # Seed 1 is one the scripted player governs for the full classic term, ending
    # on a fantastic verdict; the same game is replayed through ``main`` in
    # ``test_main``.
    console, buffer = plain_console()
    game = Game(
        SeededRandom(seed=1),
        ConsoleUI(console=console, read=careful_console_answers),
    )

    verdict = game.play()

    text = render(buffer)
    assert verdict is not None
    assert game.state.game_over is True
    assert game.state.year == config.TERM_YEARS
    assert text.count("I beg to report to you,") == config.TERM_YEARS
    assert f"In your {config.TERM_YEARS}-year term of office" in text
    assert "So long for now." in text


# --- The marathon term -------------------------------------------------------


def test_the_intro_announces_the_term_the_state_asks_for() -> None:
    """The banner repeats the term being played, not the classic constant."""
    ui, buffer, _ = _ui("0")

    ui.show_intro(GameState(term_years=config.MARATHON_TERM_YEARS))

    assert f"{config.MARATHON_TERM_YEARS}-year term of office" in render(buffer)


def test_a_marathon_term_can_be_played_through_the_console_ui() -> None:
    # Seed 38 is the one careful game of the measured 500 that survives the whole
    # marathon; the classic whole-game test above plays seed 1 instead.
    console, buffer = plain_console()
    game = Game(
        SeededRandom(seed=38),
        ConsoleUI(console=console, read=careful_console_answers),
        GameState(term_years=config.MARATHON_TERM_YEARS),
    )

    verdict = game.play()

    text = render(buffer)
    assert verdict is not None
    assert game.state.game_over is True
    assert game.state.year == config.MARATHON_TERM_YEARS
    assert text.count("I beg to report to you,") == config.MARATHON_TERM_YEARS
    assert f"In your {config.MARATHON_TERM_YEARS}-year term of office" in text
    assert "So long for now." in text
