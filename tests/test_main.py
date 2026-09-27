"""Smoke tests for the command-line entry point.

The tests pin the two ways a run can end without a traceback - a finished term
and an input that dries up - and check that ``--seed`` reaches the engine. They
also run ``python -m hammurabi`` in a subprocess with its input closed, which is
how the entry points are verified without an interactive session.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from hammurabi import __version__, config
from hammurabi.main import EXIT_OK, EXIT_USAGE, main, parse_args
from tests.support import careful_console_answers, plain_console, render


def _play(*arguments: str) -> str:
    """Run a whole game with the scripted player and return its output."""
    console, buffer = plain_console()

    exit_code = main(list(arguments), read=careful_console_answers, console=console)

    assert exit_code == EXIT_OK
    return render(buffer)


def test_main_plays_the_game_and_reports_the_impeachment() -> None:
    # Answering zero to everything starves the whole city in the first year, so
    # the game ends immediately and the test stays cheap.
    console, buffer = plain_console()

    exit_code = main([], read=lambda _question: "0", console=console)

    text = render(buffer)
    assert exit_code == EXIT_OK
    assert "HAMURABI" in text
    assert "declared national fink!!!!" in text
    assert "So long for now." in text


def test_main_stops_cleanly_when_the_input_ends() -> None:
    def read(_question: str) -> str:
        raise EOFError

    console, buffer = plain_console()

    exit_code = main([], read=read, console=console)

    assert exit_code == EXIT_OK
    assert "No more answers are coming." in render(buffer)


def test_main_plays_a_whole_ten_year_term() -> None:
    # Seed 1 is one the scripted player governs for the full term; see the
    # matching console UI test.
    text = _play("--seed", "1")

    assert f"In your {config.TERM_YEARS}-year term of office" in text
    assert text.count("I beg to report to you,") == config.TERM_YEARS


def test_the_same_seed_replays_the_same_game() -> None:
    assert _play("--seed", "1") == _play("--seed", "1")


def test_a_different_seed_plays_a_different_game() -> None:
    assert _play("--seed", "1") != _play("--seed", "2")


def test_main_reports_its_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == EXIT_OK
    assert __version__ in capsys.readouterr().out


def test_python_dash_m_hammurabi_runs_with_a_closed_stdin() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "hammurabi"],
        capture_output=True,
        text=True,
        check=False,
        # A smoke test must never hang: the entry point waits for input, so give
        # it an empty stdin and a timeout rather than a terminal. An unbounded
        # wait would leave a stray process behind.
        stdin=subprocess.DEVNULL,
        timeout=30,
    )

    assert result.returncode == EXIT_OK
    assert "HAMURABI" in result.stdout
    assert "So long for now." in result.stdout


def test_the_classic_term_is_the_default() -> None:
    """Without ``--years`` the command plays the documented ten-year game."""
    assert parse_args([]).years == config.TERM_YEARS


def test_main_plays_a_term_of_the_requested_length() -> None:
    # One year is cheap to play and shows the option reaching the engine.
    text = _play("--seed", "1", "--years", "1")

    assert "In your 1-year term of office" in text
    assert text.count("I beg to report to you,") == 1


def test_main_plays_the_marathon_term() -> None:
    # Seed 38 is the one careful game of the measured 500 that survives the
    # whole marathon and is still scored; see ``docs/balancing.md``.
    text = _play("--seed", "38", "--years", str(config.MARATHON_TERM_YEARS))

    assert f"In your {config.MARATHON_TERM_YEARS}-year term of office" in text
    assert text.count("I beg to report to you,") == config.MARATHON_TERM_YEARS


@pytest.mark.parametrize("years", ["0", "-1", str(config.MAX_TERM_YEARS + 1)])
def test_main_refuses_a_term_it_cannot_play(
    years: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--years", years])

    assert exit_info.value.code == EXIT_USAGE
    assert "--years must be between 1 and" in capsys.readouterr().err


# --- The agriculture rule set ------------------------------------------------


def test_the_agriculture_rule_set_is_off_by_default() -> None:
    """Without the flag the command plays the classic game, as it always did."""
    assert parse_args([]).agriculture is False
    assert parse_args(["--agriculture"]).agriculture is True


def test_main_plays_the_agriculture_rule_set() -> None:
    """The flag reaches the engine and the banner announces the rule set."""
    text = _play("--seed", "1", "--agriculture")

    assert "This is the agriculture rule set" in text
    assert "Which technology do you wish to research?" in text


def test_main_founds_a_school_when_the_player_asks_for_one() -> None:
    """A player who answers the first number buys technology; the summary lists it."""

    def read(question: str) -> str:
        if "wish to research" in question:
            return "1"
        return careful_console_answers(question)

    console, buffer = plain_console()
    exit_code = main(["--seed", "1", "--agriculture"], read=read, console=console)

    text = render(buffer)
    assert exit_code == EXIT_OK
    assert "Your scholars start work on the Ox-drawn plough" in text
    assert text.count("Your scholars start work on") >= 1


def test_main_plays_a_marathon_of_the_agriculture_rule_set() -> None:
    """The rule set composes with ``--years``: a century, research declined.

    Seed 38 is the one careful game of the measured 500 that survives the whole
    marathon, and the scripted player researches nothing, so the term is the
    classic century plus the extra question.
    """
    text = _play(
        "--seed", "38", "--years", str(config.MARATHON_TERM_YEARS), "--agriculture"
    )

    assert f"In your {config.MARATHON_TERM_YEARS}-year term of office" in text
    assert text.count("I beg to report to you,") == config.MARATHON_TERM_YEARS


# --- The health rule set -----------------------------------------------------


def test_the_health_rule_set_is_off_by_default() -> None:
    """Without the flag the command plays the classic game, as it always did."""
    assert parse_args([]).health is False
    assert parse_args(["--health"]).health is True


def test_main_plays_the_health_rule_set() -> None:
    """The flag reaches the engine and the banner announces the rule set."""
    text = _play("--seed", "1", "--health")

    assert "This is the health rule set" in text
    assert "Which technology do you wish to research?" in text


def test_main_builds_the_first_measure_when_the_player_asks_for_one() -> None:
    """A player who answers the first number builds a measure; the report names it."""

    def read(question: str) -> str:
        if "wish to research" in question:
            return "1"
        return careful_console_answers(question)

    console, buffer = plain_console()
    exit_code = main(["--seed", "1", "--health"], read=read, console=console)

    text = render(buffer)
    assert exit_code == EXIT_OK
    assert "Your scholars start work on the Wells" in text


def test_main_plays_both_rule_sets_at_once() -> None:
    """Both flags compose: one question a year, both programmes on the table."""
    text = _play("--seed", "1", "--agriculture", "--health")

    assert "This is the agriculture and health rule set" in text
    assert "Programme" in text, "the table must say which programme offers what"
    assert text.count("Which technology do you wish to research?") >= 1


def test_main_plays_a_marathon_of_the_health_rule_set() -> None:
    """The rule set composes with ``--years``: a century of public health."""
    text = _play(
        "--seed", "38", "--years", str(config.MARATHON_TERM_YEARS), "--health"
    )

    assert f"In your {config.MARATHON_TERM_YEARS}-year term of office" in text
    assert "Which technology do you wish to research?" in text
