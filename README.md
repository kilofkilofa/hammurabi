# Hammurabi

A faithful Python re-implementation of the classic text-based **Hammurabi**
game (also known as *Sumeria*) — the resource-management game originally written
in 1968 and popularised by David H. Ahl's *101 BASIC Computer Games* (1978).

Govern the city-state of Sumeria for the classic 10-year term — or ask for a
100-year marathon — buying and selling land, feeding your people and planting
grain while harvests, rats, immigration and plague decide your fate. Add
`--agriculture` and you may also pay for the farming technologies of Sumeria;
add `--health` and you may pay for its public-health measures instead.

> **Project status:** v1.4.0 — the full target outcome of
> [`docs/plan.md`](docs/plan.md) §6 is met. M9 put the public-health rule set of §4
> behind `--health`, sharing the one research moment of a year with the farming
> tree; M8 deepened the optional agriculture rule set into a fifteen-node tree
> whose price ladder spreads the whole programme over eighty to ninety years; M7
> put that rule set behind `--agriculture`, and M6 added the second documented rule
> set — the classic ten years stay the default while `--years 100` plays the
> marathon. The measured outcome of all of them is in
> [`docs/balancing.md`](docs/balancing.md). See
> [`docs/progress.md`](docs/progress.md).

## Requirements

- Python 3.10 or newer
- `rich` at runtime, `pytest` for the tests (installed by the project metadata;
  see [Development](#development))

## Run the game

Python 3.10 or newer is all you need; `pip` installs `rich` for you.

**1. Get the project and enter its directory** — skip this if you already have a
checkout:

```bash
git clone https://github.com/kilofkilofa/hammurabi.git
cd hammurabi
```

**2. Create a virtual environment and install the game** — once per checkout:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
```

**3. Start playing:**

```bash
hammurabi
```

That is the whole recipe: type `hammurabi` and the game starts. Any of these two
commands runs the same game if you prefer:

```bash
python -m hammurabi   # run as a module, works without the console script
python main.py        # launcher from the repository root
```

Options:

```bash
hammurabi --help      # usage and options
hammurabi --seed 42   # replay a game: the same seed brings the same events
hammurabi --years 100 # the marathon: the same rules for a century
hammurabi --agriculture # the farming tech tree: research out of the grain in store
hammurabi --health    # the public-health tree: the same research, medicine instead
hammurabi --version   # print the version
```

The game opens with a banner, reports each year and asks you for three whole
numbers; type a number and press Enter. An answer the rules cannot accept is
explained and asked for again, Ctrl-C abdicates at any time, and when the input
runs out the game says goodbye and stops.

## How to play

You govern Sumeria for the term you asked for: the classic ten years by default,
or a hundred in the marathon (`--years 100`). Every year the game reports what
happened and then asks four questions: how many acres to buy (or, if you buy
none, to sell), how many bushels to feed the people and how many acres to sow
with seed. Answer with whole numbers.

- 20 bushels feed one person for a year; anyone unfed starves.
- 1 bushel of seed sows 2 acres, and one person can tend 10 acres.
- Land costs 17–26 bushels per acre, and the price is fixed for the whole year.
- Harvests, rats, immigrants and plague are random — and starving more than 45%
  of the city in one year ends your reign at once.

Add `--agriculture` and each year also asks which farming technology to research,
or `0` for none. The 15 nodes of the tree cost from 400 bushels up, paid out of
the grain in store: the ox-drawn plough, the heavy plough and the seed drill let a
bushel of seed sow 3, 4 and then 5 acres; fallow fields, manuring, crop rotation,
flood farming and the selected seed corn add a bushel per acre each; the granaries,
the sealed silos, the temple vaults and the Nippur almanac cut what the rats eat;
and the draft teams, the iron ploughshares and the harvest crews let one person
tend 12, 14 and then 16 acres. The price climbs by about half again at every rung,
so the whole programme is the work of a lifetime: measured over five hundred
marathons, the last node is bought in year 86 on the median, and the classic decade
is only the first few rungs — [`docs/balancing.md`](docs/balancing.md) has the
figures.

Add `--health` instead and the yearly question offers the 19 measures of the health
tree, which start at 100 bushels: the wells, the drained streets and the
brick-lined drains keep the plague away, so it comes 20, then 15, 10 and finally 5
years in a hundred; the herb gatherers, the physicians, the doctors, the healing
houses and the temple hospital save the sick, until nineteen in twenty live through
a plague year; the midwives, the wet nurses, the milk herds, the birthing houses,
the foundling home and the palace nursery bring children into the city; and the
milled grain, the kitchen gardens, the oil presses and the fish ponds bring the
bushels that feed one person for a year from 20 down to 16. The **House of Life**
needs the deepest measure of every branch at once. This tree buys people, not
grain, so it will not save a city from famine on its own — the measured arc of a
healer's plan is in [`docs/balancing.md`](docs/balancing.md). Ask for both rule
sets and the one research moment a year serves both trees, as long as you can
choose.

A line that is not a whole number, or an amount the rules cannot accept, is
explained and asked for again. When the term ends the game judges you on the
average starvation rate and the acres per person you leave behind: an outstanding
ruler earns a fantastic verdict, a careless one is impeached as a national fink.

## Verdicts

The bands are checked from the best one downwards, so the first row whose figures
you meet is the verdict you get:

| Verdict | Figures at the end of the term |
| --- | --- |
| **Fantastic** | at most 3% starved per year on average, at least 10 acres per person |
| **Mediocre** | at most 10% starved, at least 9 acres per person |
| **Tyrant** | at most 33% starved, at least 7 acres per person |
| **National fink** | anything worse — or more than 45% starved in a single year, which ends the reign at once |

## Credits and provenance

*The Sumer Game* was written by **Doug Dyment** in 1968 in FOCAL; **David H. Ahl**
turned it into BASIC as **HAMURABI** for *101 BASIC Computer Games* (Creative
Computing, Morristown, New Jersey, 1978). That listing is the reference for the
rules implemented here.

This repository is an independent Python re-implementation by **kilofkilofa**.
The rules are re-implemented from the documented behaviour of the original
rather than translated from its code, and the reports are this port's own
wording; the title and the "Creative Computing" subtitle kept in the banner are
a nod to the original. No copyright is claimed over the original game or its
listings, which remain with their authors and carry no known free licence — see
[`NOTICE`](NOTICE).

## Development

```bash
pip install -e ".[dev]"   # the package plus its test dependency
nice -n 19 pytest -q      # single process, low priority, one run at a time
```

The layout is described in [`docs/architecture.md`](docs/architecture.md): the
rules are pure functions in `rules.py`, `game.py` runs the yearly loop behind an
injected RNG and UI object, and only `ui.py` / `main.py` touch the terminal.

## Documentation

| Document | Contents |
| --- | --- |
| [docs/plan.md](docs/plan.md) | Assumptions, canonical rules and target outcome |
| [docs/architecture.md](docs/architecture.md) | Structure, modules, conventions and workflow |
| [docs/progress.md](docs/progress.md) | Current level of plan realisation |
| [docs/balancing.md](docs/balancing.md) | What seeded batches of games actually do (rates, verdicts, balance figures) |
| [AGENTS.md](AGENTS.md) | Working rules for AI agents contributing to the project |

## Licence

Hammurabi is **free for non-commercial use** under the
[PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/):
you may use, study, change and share it for any non-commercial purpose, but you
may not sell it or build a commercial product on it. Commercial use needs a
separate licence from the copyright holder. The full text is in
[`LICENSE`](LICENSE).

This is deliberately **not** an open-source licence: it restricts commercial use.
The licence covers the code, documentation and tests of this repository only; it
says nothing about the 1968 original or the 1978 BASIC listing, which have their
own authors and no known free licence ([`NOTICE`](NOTICE)).

