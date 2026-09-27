# Architecture

> This document describes the **target** architecture of the project.
> For the current implementation status see [`progress.md`](./progress.md).

## 1. Design principles

1. **Separate rules from orchestration from I/O.**
   Game rules are pure functions, the engine is a plain object that owns the
   game loop, and all terminal input/output lives in one UI module.
2. **Dependency injection for the two side-effect sources.**
   The engine receives an RNG and a UI object. This makes the game fully
   deterministic in tests (seed the RNG, use a fake UI) and keeps `rich` out of
   the domain layer.
3. **Data, not dictionaries.**
   The mutable state of a game is a single `GameState` dataclass; rules are
   functions that take state and inputs and return values — no hidden globals.
4. **Everything testable without a terminal.**
   No module except `ui.py` / `main.py` may read from `stdin` or write to
   `stdout`.
5. **English, typed, documented.** All identifiers, docstrings, comments, docs
   and user-facing messages are in English and annotated with type hints.

## 2. Directory layout

```
hammurabi/
├── AGENTS.md               # instructions for AI agents (single source of truth)
├── .clinerules             # thin Cline entry point pointing at AGENTS.md + docs/
├── README.md               # short user-facing intro and how to run the game
├── LICENSE                 # PolyForm Noncommercial 1.0.0 (non-commercial use)
├── NOTICE                  # credits, provenance and the scope of the licence
├── pyproject.toml          # project metadata, deps, entry point, pytest config
├── requirements.txt        # pinned/installed dependency snapshot
├── main.py                 # thin dev launcher -> hammurabi.main:main
├── docs/
│   ├── architecture.md     # this file: structure and how to work on the project
│   ├── plan.md             # assumptions, rules and target outcome
│   ├── balancing.md        # measured behaviour of seeded batches of games
│   └── progress.md         # current level of plan realisation
├── src/
│   └── hammurabi/
│       ├── __init__.py     # package metadata (__version__)
│       ├── __main__.py     # enables `python -m hammurabi`
│       ├── main.py         # CLI entry point: builds RNG + UI, starts a game
│       ├── config.py       # all rule constants in one place
│       ├── models.py       # Verdict enum, Agriculture, Health and GameState
│       ├── tech.py         # the research machinery and the farming tree
│       ├── health.py       # the optional public-health tree (pure data)
│       ├── rules.py        # pure rule functions (no I/O)
│       ├── random_source.py# the RNG seam: RandomSource protocol + SeededRandom
│       ├── game.py         # Game engine, yearly loop and the UI protocol
│       └── ui.py           # rich-based console UI
└── tests/
    ├── __init__.py
    ├── support.py          # shared doubles: scripted RNG, recording UI,
    │                       # buffer-backed console and scripted player
    ├── policies.py         # player policies for the simulation tests
    ├── test_rules.py       # unit tests for every rule
    ├── test_tech.py        # unit tests for the agriculture tech tree
    ├── test_health.py      # unit tests for the public-health tree
    ├── test_game.py        # unit and integration tests for the engine
    ├── test_ui.py          # rendering, prompts and stop behaviour of the UI
    ├── test_simulation.py  # seeded batches: invariants and the balance figures
    ├── test_docs.py        # every figure quoted in docs/ matches config.py
    ├── test_packaging.py   # release metadata and the single-sourced version
    └── test_main.py        # smoke tests for the entry point
```

## 3. Module responsibilities

| Module | Responsibility | Depends on |
| --- | --- | --- |
| `config.py` | Named constants for every tunable rule (start values, prices, thresholds, rates, and the two research price ladders with their rates and bonuses). No logic. | — |
| `models.py` | `GameState` dataclass holding the term length, the rule-set flags, the unlocked technologies, the year, population, acres, bushels and the running statistics; the `Agriculture` and `Health` settings the rules are handed; small enums such as `Verdict`. | `config` |
| `tech.py` | The research machinery the optional rule sets share (`Node`, `TechTree`, `Offer`, `enabled_trees`, `offers`) plus the agriculture tree as pure data: the twenty-five nodes in four branches and a capstone, each with its price, prerequisites and effect, and `settings`, which folds the unlocked nodes into `Agriculture` — the harvest bonuses add up and the best rate unlocked wins. No I/O, no state, no RNG. | `config`, `models` |
| `health.py` | The optional health rule set as pure data: the twenty-five measures in four branches and the House of Life, each with its price, prerequisites and effect, and `healers`, which folds the unlocked measures into `Health` — the survivor share, the plague resistance and the birth rate take the best value unlocked and the bushels that feed a person the smallest. No I/O, no state, no RNG. | `config`, `models`, `tech` |
| `rules.py` | Pure functions: land price, harvest yield, rat loss, immigration, plague, people fed, births, starvation, impeachment, input validation, the year's spare grain for research and the final verdict. Both rule sets enter as keyword arguments that default to the classic values. | `config`, `models`, `random_source` |
| `random_source.py` | The RNG seam: a `RandomSource` protocol (`random`, `randint`) plus the `SeededRandom` implementation backed by `random.Random`. Tests inject a scripted stub. | — |
| `game.py` | `Game` engine: owns a `GameState`, runs the yearly loop, applies rules, asks for one research at the top of a year when a rule set is on and the year is not the first (the offer covering every tree in play, paid out of the year's spare grain — the store the report has just shown, less the food of the city and the seed of its fields), reports the year's crop where it lands, reports a research budget that can pay for nothing in one line instead of asking, updates statistics, decides game over. Also defines the `UI` protocol that the engine consumes. | `config`, `models`, `rules`, `tech`, `health` |
| `ui.py` | `ConsoleUI`: renders reports via `rich`, asks the player for the yearly numbers and for a node when the trees offer one, reports the year's crop where it lands, prints error, impeachment and end-of-term messages. Implements the `UI` protocol from `game.py`; the engine validates every answer, so no rule knowledge ends up here. | `rich`, `game`, `models`, `tech` |
| `main.py` | Entry point: parse args (`--seed`, `--years`, `--agriculture`, `--health`, `--all`), construct the starting state, RNG and UI, run `Game`. | `game`, `models`, `ui`, `random_source` |
| `__main__.py` | Allows `python -m hammurabi`. | `main` |

The `UI` protocol lives in `game.py` rather than `ui.py` because the engine owns
the interface it consumes: `ui.py` only has to satisfy it. That keeps `rich` out
of the domain layer and lets the tests drive the engine with a plain recording
double. `ConsoleUI` reads the keyboard through an injectable `read` callable
(``input`` by default), which is the seam the UI tests use to play whole games
without a terminal.

## 4. Data model

```python
@dataclass(frozen=True)
class Agriculture:
    yield_bonus: int = 0                            # bushels added to a harvest
    acres_per_seed: int = 2                         # acres one seed bushel sows
    acres_per_worker: int = 10                      # acres one person can tend
    rat_divisor: int = 1                            # extra divisor on the rats

@dataclass(frozen=True)
class Health:
    plague_survivor_percent: int = 50               # share who live through a plague
    plague_resistance: int = 0                      # points shifting the plague roll
    births_per_thousand: int = 0                    # children per 1000 in a fed year
    bushels_per_person: int = 20                    # bushels that feed one person

@dataclass
class GameState:
    year: int = 0                 # years elapsed (0 before the first report)
    term_years: int = 10          # length of the term: the classic ten years
    agriculture: bool = False     # the optional farming rule set is in play
    health: bool = False          # the optional public-health rule set is in play
    unlocked: frozenset[str] = frozenset()  # technologies bought, either tree
    population: int = 95
    acres: int = 1000
    bushels: int = 2800
    starved_this_year: int = 0    # people starved in the last year
    immigrants_this_year: int = 5 # people who arrived in the last year
    born_this_year: int = 0       # children born in the last year
    rats_ate_this_year: int = 200 # bushels lost to rats in the last year
    yield_per_acre: int = 3       # harvest of the last year
    plague_this_year: bool = False
    plague_roll: int = 1          # roll carried over from the last year
    total_starved: int = 0        # people lost across the whole term
    starved_percent_avg: float = 0.0  # running average starvation percentage
    would_be_assassins: int = 0   # named only by the mediocre verdict
    game_over: bool = False
    verdict: Verdict | None = None
```

`GameState` is the single source of truth for a game. `rules.py` never mutates
it; `game.py` owns the transitions. `Agriculture` and `Health` are the derived
values: the engine reads them once a year with `tech.settings(state.unlocked)` and
`health.healers(state.unlocked)` and hands their fields to the rules, which is why
`rules.py` needs no rule-set knowledge and a classic game simply passes the
defaults. `unlocked` holds the keys of both trees; each fold ignores the keys that
belong to the other, so one state can carry two programmes.

## 5. Turn lifecycle

Every call to `Game.play_year()` runs the steps below; they mirror the original
listing, including the fact that the report opens the year and that the land
trade is either a purchase or a sale.

```
year += 1
report (starved, immigrants, children) -> the announced arrivals join the city
plague? (the public health decides the share) -> status (population, acres, yield, rats, store)
research? (a rule set is on and the year is not the first: one node of the trees in
           play, paid out of the year's spare grain — the store the status has just
           shown, less the food the people need and the seed the land needs — and a
           year the surplus cannot cover reports that empty budget in one line)
land price -> buy land --(nothing bought)--> sell land
feed -> starvation and the running average -> the population shrinks
plant seed (land, seed and labour checked against the farming technology)
harvest yield -> rats raid the pre-harvest store -> store += harvest - rats
harvest report (with a rule set on: the crop, the rats and the store the crop leaves)
immigrants for the next report
children for the next report (health rule set; none in a year the city could not feed)
plague roll for the next year (the water branch shifts the offset)
impeachment? (more than 45% starved) -> game over
term over? -> the undrawn closing report adds the last immigrants and plague,
then the term is scored
```

The research step is one question opening the year, whatever the flags, from the
second year of a term on (`config.FIRST_RESEARCH_YEAR`), so a rule set never touches
the vintage opening year: `tech.enabled_trees` maps `state.agriculture` and
`state.health` to the trees they play, `tech.offers` gathers what each of them can
sell, and every offer carries the label of the programme that made it, which is how
the UI can tell the two tables apart. The price must fit in the year's spare grain,
which `rules.spare_grain` works out from the store, the people to be fed and the acres
to be sown; the engine writes that figure to `state.spare_bushels`, offers nothing
above it and the UI quotes it with the question, so the bread of the city and the seed
of its fields are never on the table. A year whose surplus cannot cover a rung is not
asked about one — no question with no acceptable answer is ever put — but it is not
passed over in silence either: `ui.show_no_research` prints the store the budget was
measured from and says the food of the people and the seed of the fields are set aside
first, so a rule-set year always shows its research moment. Because the question is put
just after the status
and before the land trade, the feeding and the sowing, the store it quotes is the one
the report has just shown — grain the granary really holds at that moment, never the
surplus the year might still earn. The crop of the year is reported where it lands
instead: with a rule set in play `ui.show_harvest` carries the harvest, the rats and
the store the crop leaves, between the sowing and the newcomers, so the grain the
following year's question is paid from can be checked against the granary; a game
without a rule set reports no crop and keeps the vintage transcript. Both folds are
read at the top of the year, so a node bought now shows in the figures of the following
year — the plague roll included, which is drawn later in the year it was bought.

`Game.play()` repeats this until the term named by `state.term_years` has been
played or the ruler is impeached, then stores the outcome in `state.verdict` and
hands it to the UI.

Answers that break a rule are rejected through `UI.show_error` and asked for
again: `can_buy_land`, `can_sell_land`, `can_feed_people` and `can_plant` decide,
so the UI never needs to know a rule. The retries are bounded by
`config.MAX_ANSWER_ATTEMPTS` inside `Game._ask_until_accepted`: after that many
rejected answers in a row the engine raises `RuntimeError`. A UI that can never
produce a valid number — a closed stdin or a scripted test double — therefore
stops the game instead of spinning a core forever. `ConsoleUI` bounds its own
number parsing the same way: a line that is not a whole number is complained
about and the question is put again, and after `config.MAX_ANSWER_ATTEMPTS` such
lines the UI raises `RuntimeError` too.

## 6. Testing strategy

| Level | What it covers | Location |
| --- | --- | --- |
| Unit — rules | Every pure function in `rules.py` with fixed RNG stubs and boundary values | `tests/test_rules.py` |
| Unit — tree | The agriculture tech tree: its branches, prerequisites, price ladder and the settings it folds into `Agriculture` | `tests/test_tech.py` |
| Unit — health tree | The public-health tree: its four branches, the House of Life, the price ladder and the rates it folds into `Health`, including the rule that a lower feeding rate wins | `tests/test_health.py` |
| Unit — engine | Year transitions with a fake RNG and a scripted UI; impeachment path | `tests/test_game.py` |
| Unit — UI | Every report, table, prompt and closing panel rendered into a buffer; the answer loop that re-asks and gives up | `tests/test_ui.py` |
| Integration | A seeded game played to completion produces a stable verdict; a whole term played through the real console UI with a scripted player | `tests/test_game.py`, `tests/test_ui.py` |
| Simulation | Seeded batches of whole games per policy, playing the classic rule set, the agriculture one and the health one: the cross-game invariants (grain never negative, the store balances with the research included, population only rises through immigrants and the births of a fed year, a verdict is always reached, years never exceed the term), the arcs of both trees over a marathon batch (the year each node is bought, the median completion year of the farming tree, the deepest measure a healer ever reaches) and the figures recorded in `docs/balancing.md` | `tests/test_simulation.py`, `tests/policies.py` |
| Documentation | Every figure quoted in `docs/plan.md`, `README.md` and `docs/balancing.md` is compared with the constant it documents, so a rule change fails the build | `tests/test_docs.py` |
| Smoke | `main()` plays a scripted game, stops cleanly when the input ends, forwards `--seed` and `--years`, turns every rule set of `config.RULE_SETS` on with `--all`, refuses a term it cannot play; `python -m hammurabi` runs with a closed stdin | `tests/test_main.py` |
| Packaging | The installed distribution matches `__version__`, the console script points at `hammurabi.main:main`, and `pyproject.toml` declares the release metadata with no literal version of its own | `tests/test_packaging.py` |

Guidelines:

- Never rely on real time or unseeded randomness — always inject a seeded
  `random.Random` or a stub.
- Test boundaries, not only the happy path (0 acres planted, exactly 45%
  starved, exactly 20 bushels per person, etc.).
- Keep the UI out of tests by using a fake `UI` implementation, and never let a
  test read the real terminal: `ConsoleUI` takes an injected `read` callable.
- Share the doubles: `tests/support.py` provides `StubRandom` (a scripted random
  source), `FakeUI` (records every call and replays scripted answers, research
  nodes included),
  `CarefulUI` (plays whole games as a rule-aware player) and, for the UI tests,
  `plain_console` (a buffer-backed console), `render` (collapses the wrapping a
  `rich` console adds) and `careful_console_answers` (a player that answers from
  the figures each question repeats).
- Simulation tests live in `tests/test_simulation.py` and play seeded batches of
  whole games through the policies in `tests/policies.py` (careful ruler, land
  trader, land seller, serial starver). They assert the invariants that must hold
  in every game and pin the batch figures recorded in `docs/balancing.md`. Keep
  each batch in the low hundreds of games so the suite stays cheap, and never
  assert on a single seed's outcome.

## 7. Coding conventions

- **Language:** all names, docstrings, comments, messages and docs in English.
- **Typing:** type hints on every public function; `from __future__ import
  annotations` is not required for 3.10+ but prefer modern syntax (`X | None`).
- **Docstrings:** module-level docstring on every module; docstring on every
  public class and function describing purpose and key rules.
- **Functions:** small and single-purpose; pure functions in `rules.py` have no
  I/O and no globals.
- **Constants:** every magic number lives in `config.py` with a comment tying it
  to the original rule.
- **Randomness:** only via the injected RNG wrapper in `random_source.py`.
- **Imports:** standard library, then third-party, then local; absolute imports
  inside the package (`from hammurabi import rules`).
- **Line length:** about 88 characters; keep functions readable over clever.

## 8. Development workflow

Prerequisites: the virtual environment at `.venv` with the package installed in
editable mode.

```bash
# activate the environment
source .venv/bin/activate

# (re)install the package in editable mode with dev tools
pip install -e ".[dev]"

# run the game
hammurabi                 # console script
python -m hammurabi       # module form
python main.py            # thin root launcher

# run the tests (single process, low priority, one session at a time)
nice -n 19 pytest -q                  # keep the desktop responsive
taskpolicy -b nice -n 19 pytest -q    # macOS background QoS, efficiency cores
pytest tests/test_game.py -q          # a single file while iterating
```

`pyproject.toml` already configures `pytest` with `testpaths = ["tests"]` and
`pythonpath = ["src"]`, so tests import `hammurabi` without extra setup. It also
sets `faulthandler_timeout` and `faulthandler_exit_on_timeout`, so a test that
runs longer than 20 seconds dumps its traceback and aborts the whole run instead
of leaving a stray process spinning a core.

### Packaging and release

- Licence: **PolyForm Noncommercial 1.0.0** — free for non-commercial use, and
  deliberately not an OSI open-source licence. PolyForm publishes no SPDX
  identifier, so `pyproject.toml` refers to it as
  `LicenseRef-PolyForm-Noncommercial-1.0.0` and ships the text through
  `license-files = ["LICENSE"]`. The build backend therefore has to be
  `setuptools>=77`, the first release that understands the PEP 639 licence fields.
- `pyproject.toml` carries the release metadata: name and description, `readme`,
  the maintainer in `authors`, keywords, classifiers, `[project.urls]` pointing at
  the GitHub repository, the `rich` runtime dependency and a `dev` extra that
  provides `pytest`. `requirements.txt` is the pinned snapshot of the installed
  environment and is not used by the build.
- The version has **one** source: `hammurabi.__version__` in
  `src/hammurabi/__init__.py`. `pyproject.toml` declares `dynamic = ["version"]`
  and reads that attribute, so the installed distribution, `hammurabi --version`
  and the package can never disagree; `tests/test_packaging.py` guards it.
- Version policy: `0.x` while the target outcome in `plan.md` §6 was incomplete;
  `1.0.0` marks that outcome being met (the end of M5), `1.1.0` adds the
  documented term choice (M6), `1.2.0` the optional agriculture rule set (M7),
  `1.3.0` the fifteen-node tree whose price ladder spreads the programme over a
  lifetime (M8), `1.4.0` the optional public-health rule set (M9), `1.5.0` the
  twenty-five-node trees whose quarter-step ladders spread the programme over a
  reign (M10), `1.5.1` the `--all` master toggle over the optional rule sets (a
  patch: it adds a flag, not a rule) and `1.5.2` the research question opening the
  year, its budget drawn from the store the report has just shown, with the year's
  crop reported where it lands (a patch: it moves one step of the optional rule sets
  and the line that reports the crop, and leaves the classic game, the spare-grain
  rule and both trees untouched). Any later change needs a new patch or minor
  version, never an edit of an existing release.
- Nothing built is committed: `.venv/`, `*.egg-info/`, `dist/` and `build/` are
  ignored and recreated by `pip install -e ".[dev]"`.

## 9. Extension points

- **Add or tweak a rule:** put the number in `config.py`, implement the pure
  logic in `rules.py`, wire it in `game.py`, add a unit test.
- **New input/output:** extend the `UI` protocol and `ConsoleUI`, never the
  engine.
- **New verdict or message:** add it to the verdict mapping in `rules.py` and
  render it in `ui.py`.
- **Alternate rule sets:** the term lengths are the first documented case — the
  classic ten years and the marathon century live in `config.py` and travel in
  `GameState.term_years`, so `Game` and `ConsoleUI` never read a global. The
  agriculture rule set is the second: `GameState.agriculture` turns it on, the
  tree lives in `tech.py`, the engine derives an `Agriculture` value from
  `GameState.unlocked` once a year and passes its fields to the rules as
  keyword arguments that default to the classic numbers. A wider rule set would
  go the same way: data plus defaults in `config.py`, with the derived settings
  passed into the rules rather than read from a global.

## 10. Glossary

| Term | Meaning |
| --- | --- |
| acre | unit of land; buying/selling changes it |
| bushel | unit of grain; used for food, seed, land and taxes to the rats |
| plague | 20% yearly event killing half the population; the first year is always safe |
| impeachment | instant game over when more than 45% starve in one year |
| verdict | final evaluation after the term |

