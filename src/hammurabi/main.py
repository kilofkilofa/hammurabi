"""Command-line entry point for the Hammurabi game.

This module is the only place where the concrete dependencies meet: it parses the
command line, builds the seeded random source and the terminal UI, and hands both
to the engine. The ten-year loop itself lives in ``game.py``.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence

from rich.console import Console

from hammurabi import __version__
from hammurabi.game import Game
from hammurabi.random_source import SeededRandom
from hammurabi.ui import ConsoleUI

#: Exit code of a term that finished, or that stopped because input ran out.
EXIT_OK = 0

#: Exit code after Ctrl-C: the shell convention of 128 plus ``SIGINT``.
EXIT_INTERRUPTED = 130


def build_parser() -> argparse.ArgumentParser:
    """Return the parser behind the ``hammurabi`` command."""
    parser = argparse.ArgumentParser(
        prog="hammurabi",
        description="Govern ancient Sumeria for a ten-year term of office.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="N",
        help="seed the random events; the same seed replays the same game",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    console: Console | None = None,
    read: Callable[[str], str] | None = None,
) -> int:
    """Play one ten-year term of Hammurabi.

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
    args = build_parser().parse_args(argv)
    console = console or Console()
    game = Game(SeededRandom(args.seed), ConsoleUI(console=console, read=read))

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

