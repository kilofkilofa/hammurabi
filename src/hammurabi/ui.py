"""The ``rich`` terminal UI.

:class:`ConsoleUI` is the only component that reads the keyboard or draws on the
terminal, and it implements the :class:`~hammurabi.game.UI` protocol the engine
consumes: it renders the yearly reports of the 1978 listing and collects the
ruler's four decisions.

No rule lives here. The engine validates every answer and explains a rejection
through :meth:`ConsoleUI.show_error`, so this module only has to turn the game
state into readable output and the typed line into a whole number. The wording
follows the listing closely, with its obvious typos corrected ("Charlemagne",
"remaining").
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hammurabi import config, tech
from hammurabi.models import GameState, Verdict

#: Drawn while the player types; the question itself is printed above it.
ANSWER_PROMPT = "> "

#: Title of the listing, which spells the king's name "HAMURABI".
TITLE = "HAMURABI"

#: Subtitle printed under the title in the listing.
SUBTITLE = "CREATIVE COMPUTING  MORRISTOWN, NEW JERSEY"

#: Credit shown in the banner: the port's author and the scope of its licence.
CREDIT = "Python port by kilofkilofa — free for non-commercial use"

#: Panel title used for each verdict.
VERDICT_TITLES: dict[Verdict, str] = {
    Verdict.IMPEACHED: "National fink",
    Verdict.TYRANT: "Tyrant",
    Verdict.MEDIOCRE: "Mediocre",
    Verdict.FANTASTIC: "Fantastic",
}

#: Border colour used for each verdict.
VERDICT_STYLES: dict[Verdict, str] = {
    Verdict.IMPEACHED: "red",
    Verdict.TYRANT: "red",
    Verdict.MEDIOCRE: "yellow",
    Verdict.FANTASTIC: "green",
}


def read_from_stdin(_question: str) -> str:
    """Read one line from the terminal; the question has already been drawn.

    This is the default reader of :class:`ConsoleUI`. A closed ``stdin`` makes
    :func:`input` raise :class:`EOFError`, which the entry point turns into a
    clean stop instead of a traceback.
    """
    return input(ANSWER_PROMPT)


def _fink_lines(state: GameState) -> list[str]:
    """Return the impeachment text of the listing (lines 560-567)."""
    return [
        f"You starved {state.starved_this_year} people in one year!!!",
        "Due to this extreme mismanagement you have not only been impeached and "
        "thrown out of office but you have also been declared national fink!!!!",
    ]


def _verdict_lines(state: GameState, verdict: Verdict) -> list[str]:
    """Return the closing lines the listing prints for ``verdict``."""
    if verdict is Verdict.FANTASTIC:
        return [
            "A fantastic performance!!! Charlemagne, Disraeli and Jefferson "
            "combined could not have done better!",
        ]
    if verdict is Verdict.MEDIOCRE:
        return [
            "Your performance could have been somewhat better, but really "
            "wasn't too bad at all.",
            f"{state.would_be_assassins} people would dearly like to see you "
            "assassinated but we all have our trivial problems.",
        ]
    return [
        "Your heavy-handed performance smacks of Nero and Ivan IV.",
        "The people (remaining) find you an unpleasant ruler and, frankly, "
        "hate your guts!!",
    ]


def _researched_line(state: GameState) -> str | None:
    """Return the line naming the researched technologies, when there are any.

    The classic game researches nothing, so its closing report gains no line; the
    agriculture rule set lists what the ruler's farmers mastered, in tree order.
    """
    if not state.unlocked:
        return None
    names = [item.name for item in tech.TECH_TREE if item.key in state.unlocked]
    return f"Your farmers mastered: {', '.join(names)}."


def _ruleset_note(state: GameState) -> str:
    """Return the sentence announcing the rule set, for the intro panel.

    The classic game needs no note, because it asks the four vintage questions;
    the agriculture rule set adds a fifth and says so before the first year. The
    size of the tree is read from :mod:`hammurabi.tech`, so the banner cannot fall
    behind a deeper tree.
    """
    if not state.agriculture:
        return ""
    return (
        "\n\nThis is the agriculture rule set: each year you may also pay for "
        f"one of the {len(tech.TECH_TREE)} farming technologies out of the grain "
        "in store. The later ones cost what many harvests leave over, so the "
        "whole programme is the work of a lifetime."
    )


def _term_statistics(state: GameState) -> str:
    """Return the term statistics that open the closing report (860-875)."""
    started = config.START_ACRES / config.START_POPULATION
    statistics = (
        f"In your {state.term_years}-year term of office, "
        f"{state.starved_percent_avg:.1f} percent of the population starved per "
        f"year on the average, i.e. a total of {state.total_starved} people "
        f"died!!\nYou started with {started:.1f} acres per person and ended with "
        f"{state.acres_per_person:.1f} acres per person."
    )
    researched = _researched_line(state)
    return statistics if researched is None else f"{statistics}\n{researched}"


class ConsoleUI:
    """Draw the game in a terminal and collect the ruler's answers.

    Implements the :class:`~hammurabi.game.UI` protocol. Every rule is enforced
    by the engine, so an answer that breaks one comes back through
    :meth:`show_error`; this class never decides what is legal.

    Args:
        console: ``rich`` console to draw on. A fresh one is created when it is
            omitted, which lets the tests capture the output in a buffer.
        read: Callable asked for one raw answer at a time, receiving the question
            text. It defaults to :func:`read_from_stdin`; tests inject a scripted
            player so a whole game can be played without a terminal.
    """

    def __init__(
        self,
        *,
        console: Console | None = None,
        read: Callable[[str], str] | None = None,
    ) -> None:
        self.console = console or Console()
        self._read = read if read is not None else read_from_stdin

    # --- Reporting -----------------------------------------------------------

    def show_intro(self, state: GameState) -> None:
        """Announce the game and the ruler's starting position."""
        self.console.print(
            Panel(
                f"[bold]{TITLE}[/bold]\n[dim]{SUBTITLE}[/dim]\n\n"
                "Try your hand at governing ancient Sumeria successfully for a "
                f"{state.term_years}-year term of office.{_ruleset_note(state)}"
                f"\n\n[dim]{CREDIT}[/dim]",
                border_style="green",
                title="Hammurabi",
                title_align="left",
            )
        )
        self.console.print(
            f"You begin with {state.population} people, {state.acres} acres and "
            f"{state.bushels} bushels of grain."
        )
        self.console.print(
            "[dim]Answer with whole numbers; interrupt with Ctrl-C to abdicate."
            "[/dim]"
        )

    def show_report(self, state: GameState) -> None:
        """Open the year: its number, last year's deaths and arrivals."""
        self.console.print()
        self.console.print("[bold]HAMURABI:  I beg to report to you,[/bold]")
        self.console.print(
            f"In year {state.year}, {state.starved_this_year} people starved, "
            f"{state.immigrants_this_year} came to the city."
        )

    def show_plague(self, *, before: int, after: int) -> None:
        """Report that the plague halved the population."""
        self.console.print(
            f"[red]A horrible plague struck! Half the people died.[/red] "
            f"The population fell from {before} to {after}."
        )

    def show_status(self, state: GameState) -> None:
        """Report the city's people, land, last harvest, rats and grain."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold")
        table.add_column(justify="right")
        table.add_row("Population", str(state.population))
        table.add_row("Land owned", f"{state.acres} acres")
        table.add_row("Last harvest", f"{state.yield_per_acre} bushels per acre")
        table.add_row("Eaten by rats", f"{state.rats_ate_this_year} bushels")
        table.add_row("Grain in store", f"{state.bushels} bushels")
        self.console.print(table)

    def show_land_price(self, price: int) -> None:
        """Report the price fixed for this year's land trade."""
        self.console.print(f"Land is trading at {price} bushels per acre.")

    def show_research(self, researched: tech.Tech) -> None:
        """Report the farming technology the ruler has just paid for."""
        self.console.print(
            f"Your scholars start work on the {researched.name} "
            f"({researched.effect}); it shows in the years to come."
        )

    def show_error(self, message: str) -> None:
        """Explain why the engine rejected the last answer."""
        self.console.print(f"[bold yellow]{message}[/bold yellow]")

    def show_impeachment(self, state: GameState) -> None:
        """Report the impeachment that ended the term early."""
        self._show_closing_panel(_fink_lines(state), Verdict.IMPEACHED)
        self._show_farewell()

    def show_summary(self, state: GameState, verdict: Verdict) -> None:
        """Report the term statistics and the final verdict."""
        self.console.print()
        self.console.print(_term_statistics(state))
        # ``880 IF P1>33 THEN 565``: the end-of-term impeachment reuses the text
        # of the mid-term one, and both close with the same farewell.
        lines = (
            _fink_lines(state)
            if verdict is Verdict.IMPEACHED
            else _verdict_lines(state, verdict)
        )
        self._show_closing_panel(lines, verdict)
        self._show_farewell()


    # --- Asking --------------------------------------------------------------

    def ask_acres_to_buy(self, state: GameState, *, price: int) -> int:
        """Ask how many acres to buy this year."""
        return self._ask_int(
            "How many acres do you wish to buy? "
            f"[you have {state.bushels} bushels, land is {price} bushels per acre]"
        )

    def ask_acres_to_sell(self, state: GameState, *, price: int) -> int:
        """Ask how many acres to sell this year."""
        return self._ask_int(
            "How many acres do you wish to sell? "
            f"[you own {state.acres} acres, land is {price} bushels per acre]"
        )

    def ask_bushels_to_feed(self, state: GameState) -> int:
        """Ask how many bushels to feed the people with."""
        return self._ask_int(
            "How many bushels do you wish to feed your people? "
            f"[you have {state.bushels} bushels, {state.population} people live "
            "in the city]"
        )

    def ask_acres_to_plant(self, state: GameState) -> int:
        """Ask how many acres to sow with seed."""
        return self._ask_int(
            "How many acres do you wish to plant with seed? "
            f"[you own {state.acres} acres, you have {state.bushels} bushels, "
            f"{state.population} people live in the city]"
        )

    def ask_research(
        self, state: GameState, choices: Sequence[tech.Tech]
    ) -> str | None:
        """Ask which farming technology to research this year.

        The nodes on offer are drawn as a numbered table, because their names
        alone would hide what they cost and what they do. Answering ``0`` starts
        no research and leaves the grain in store. A number outside the table is
        handed back as text, so the engine rejects it and asks again, exactly as it
        does for a sowing that breaks a rule.

        Args:
            state: State the question is asked in; only its grain is quoted.
            choices: Nodes the store can pay for, in tree order.

        Returns:
            The key of the chosen node, ``None`` for no research this year, or the
            typed digits when they name no node on the list.
        """
        table = Table(show_header=True, box=None, padding=(0, 2))
        table.add_column("#", justify="right", style="bold")
        table.add_column("Technology")
        table.add_column("Cost", justify="right")
        table.add_column("Effect")
        for number, item in enumerate(choices, start=1):
            table.add_row(str(number), item.name, f"{item.cost} bushels", item.effect)
        self.console.print(
            f"Your farmers have mastered {len(state.unlocked)} of "
            f"{len(tech.TECH_TREE)} technologies."
        )
        self.console.print(table)
        answer = self._ask_int(
            "Which technology do you wish to research? "
            f"[you have {state.bushels} bushels, answer 0 to research nothing]"
        )
        if answer == 0:
            return None
        if 1 <= answer <= len(choices):
            return choices[answer - 1].key
        return str(answer)

    # --- Internals -----------------------------------------------------------

    def _ask_int(self, question: str) -> int:
        """Print ``question`` and return the whole number the player answers.

        A line that is not a whole number is complained about and the question is
        put again, exactly as the engine re-asks a number that breaks a rule.

        Args:
            question: The question to show, hints included.

        Returns:
            The first answer that reads as a whole number.

        Raises:
            RuntimeError: If ``config.MAX_ANSWER_ATTEMPTS`` answers in a row
                cannot be read as whole numbers, so that no input can spin this
                loop forever.
            EOFError: If the input ends; the entry point treats that as the end
                of the game.
        """
        for _ in range(config.MAX_ANSWER_ATTEMPTS):
            self.console.print(f"[bold cyan]{question}[/bold cyan]")
            answer = self._read(question)
            try:
                return int(answer.strip())
            except ValueError:
                self.show_error(
                    f"'{answer.strip()}' is not a whole number. Try again."
                )
        raise RuntimeError(
            f"gave up after {config.MAX_ANSWER_ATTEMPTS} unreadable answers in a row"
        )

    def _show_closing_panel(self, lines: list[str], verdict: Verdict) -> None:
        """Draw ``lines`` inside a panel titled after ``verdict``."""
        self.console.print(
            Panel(
                "\n".join(lines),
                title=VERDICT_TITLES[verdict],
                title_align="left",
                border_style=VERDICT_STYLES[verdict],
            )
        )

    def _show_farewell(self) -> None:
        """Close the game with the listing's parting words (line 995)."""
        self.console.print("\nSo long for now.")

