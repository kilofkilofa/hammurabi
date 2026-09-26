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
from hammurabi.main import EXIT_OK, main
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
