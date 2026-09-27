"""Command-line entry point for the Hammurabi game.

This module is the only place where the concrete dependencies meet: it parses the
command line, builds the seeded random source and the terminal UI, and hands both
to the engine. The yearly loop itself lives in ``game.py``.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence

from rich.console import Console

from hammurabi import __version__, config
from hammurabi.game import Game
from hammurabi.models import GameState
from hammurabi.random_source import SeededRandom
from hammurabi.ui import ConsoleUI

#: Exit code of a term that finished, or that stopped because input ran out.
EXIT_OK = 0

#: Exit code of a command line ``argparse`` cannot accept.
EXIT_USAGE = 2

#: Exit code after Ctrl-C: the shell convention of 128 plus ``SIGINT``.
EXIT_INTERRUPTED = 130


def build_parser() -> argparse.ArgumentParser:
    """Return the parser behind the ``hammurabi`` command."""
    parser = argparse.ArgumentParser(
        prog="hammurabi",
        description=(
            "Govern ancient Sumeria for a term of office: ten years, or a "
            "hundred in the marathon."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="N",
        help="seed the random events; the same seed replays the same game",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=config.TERM_YEARS,
        metavar="N",
        help=(
            f"length of the term in years (1-{config.MAX_TERM_YEARS}): "
            f"{config.TERM_YEARS} is the classic game and "
            f"{config.MARATHON_TERM_YEARS} the marathon"
        ),
    )
    parser.add_argument(
        "--agriculture",
        action="store_true",
        help=(
            "play the optional agriculture rule set: research farming "
            "technologies out of the year's spare grain"
        ),
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help=(
            "play the optional health rule set: research public-health measures "
            "out of the year's spare grain"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Return the parsed command line, rejecting a term outside its bounds.

    Args:
        argv: Command-line arguments without the program name; ``sys.argv[1:]``
            is read when it is omitted.

    Returns:
        The parsed arguments, with ``years`` a whole number of years inside
        ``1..`` :data:`~hammurabi.config.MAX_TERM_YEARS`.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if not 1 <= args.years <= config.MAX_TERM_YEARS:
        # A term of zero years could never be played and an unbounded one would
        # ask for a game nobody can finish, so both are refused before the
        # engine is built.
        parser.error(
            f"--years must be between 1 and {config.MAX_TERM_YEARS}"
            f" (the classic game is {config.TERM_YEARS} years,"
            f" the marathon {config.MARATHON_TERM_YEARS})"
        )
    return args


def main(
    argv: Sequence[str] | None = None,
    *,
    console: Console | None = None,
    read: Callable[[str], str] | None = None,
) -> int:
    """Play one term of Hammurabi.

    Args:
        argv: Command-line arguments without the program name; ``sys.argv[1:]``
            is parsed when it is omitted.
        console: Optional ``rich`` console used for output, which keeps the entry
            point testable without a terminal.
        read: Optional callable asked for the player's answers; tests script a
            whole game with it, and the default reads ``stdin``.

    Returns:
        ``EXIT_OK`` when the term ended or the input ran out, and
        ``EXIT_INTERRUPTED`` when the player gave up the throne with Ctrl-C.
    """
    args = parse_args(argv)
    console = console or Console()
    game = Game(
        SeededRandom(args.seed),
        ConsoleUI(console=console, read=read),
        GameState(
            term_years=args.years,
            agriculture=args.agriculture,
            health=args.health,
        ),
    )

    try:
        game.play()
    except EOFError:
        # A closed stdin or the end of a pipe: the steward stops instead of
        # asking a question nobody can answer.
        console.print("\nNo more answers are coming. So long for now.")
        return EXIT_OK
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]The throne is abdicated. So long for now.[/yellow]")
        return EXIT_INTERRUPTED
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())

