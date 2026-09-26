# Hammurabi

A faithful Python re-implementation of the classic text-based **Hammurabi**
game (also known as *Sumeria*) — the resource-management game originally written
in 1968 and popularised by David H. Ahl's *101 BASIC Computer Games* (1978).

Govern the city-state of Sumeria for ten years: buy and sell land, feed your
people and plant grain while harvests, rats, immigration and plague decide your
fate.

> **Project status:** v1.0.0 — the full target outcome of
> [`docs/plan.md`](docs/plan.md) §6 is met. The rules layer, the ten-year engine,
> the `rich` terminal UI, the release metadata and the M5 hardening (seeded
> simulation tests, a docs cross-check and balancing notes) are all in place. See
> [`docs/progress.md`](docs/progress.md).

## Requirements

- Python 3.10 or newer
- `rich` at runtime, `pytest` for the tests (installed by the project metadata;
  see [Development](#development))

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
hammurabi
```

Alternative entry points:

```bash
python -m hammurabi   # run as a module
python main.py        # convenience launcher from the repository root
```

Options:

```bash
hammurabi --help      # usage and options
hammurabi --seed 42   # replay a game: the same seed brings the same events
hammurabi --version   # print the version
```

## How to play

You govern Sumeria for ten years. Every year the game reports what happened and
then asks four questions: how many acres to buy (or, if you buy none, to sell),
how many bushels to feed the people and how many acres to sow with seed. Answer
with whole numbers.

- 20 bushels feed one person for a year; anyone unfed starves.
- 1 bushel of seed sows 2 acres, and one person can tend 10 acres.
- Land costs 17–26 bushels per acre, and the price is fixed for the whole year.
- Harvests, rats, immigrants and plague are random — and starving more than 45%
  of the city in one year ends your reign at once.

A line that is not a whole number, or an amount the rules cannot accept, is
explained and asked for again. After ten years the game judges you on the average
starvation rate and the acres per person you leave behind: an outstanding ruler
earns a fantastic verdict, a careless one is impeached as a national fink.

## Verdicts

The bands are checked from the best one downwards, so the first row whose figures
you meet is the verdict you get:

| Verdict | Figures at the end of the term |
| --- | --- |
| **Fantastic** | at most 3% starved per year on average, at least 10 acres per person |
| **Mediocre** | at most 10% starved, at least 9 acres per person |
| **Tyrant** | at most 33% starved, at least 7 acres per person |
| **National fink** | anything worse — or more than 45% starved in a single year, which ends the reign at once |

## Development

```bash
pip install -e ".[dev]"   # the package plus its test dependency
nice -n 19 pytest -q      # single process, low priority, one run at a time
```

The layout is described in [`docs/architecture.md`](docs/architecture.md): the
rules are pure functions in `rules.py`, `game.py` runs the ten-year loop behind an
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

