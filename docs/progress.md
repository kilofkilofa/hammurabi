# Progress

> Current level of realisation of [`plan.md`](./plan.md).
> **Keep this file up to date at the end of every task.**

Last updated: 2026-09-27

## Summary

| Milestone | Status | Notes |
| --- | --- | --- |
| M0 — Scaffolding & documentation | **Done** | Skeleton, `docs/`, agent instructions, runnable entry point |
| M1 — Domain model & rules | **Done** | `config.py`, `models.py`, `rules.py`, `random_source.py`; 69 rule tests |
| M2 — Game engine | **Done** | `game.py` with the `UI` protocol; `tests/test_game.py` |
| M3 — Terminal UI | **Done** | `ui.py`: rich intro, yearly report, status table, four bounded questions, verdict panels; 139 tests in total, 19 of them UI tests |
| M4 — CLI options & release packaging | **Done** | `--seed`/`--version`, single-sourced version, non-commercial licence (PolyForm 1.0.0 + `LICENSE`), README (options, how to play, verdicts, development), classifiers and dev extra; `tests/test_packaging.py` |
| M5 — Hardening & polish | **Done** | Bounded input retries and a per-test watchdog; seeded simulation batches (`tests/policies.py`, `tests/test_simulation.py`); a docs cross-check (`tests/test_docs.py`); measured `docs/balancing.md`; every doc claim corrected against the code; released as `1.0.0` |
| M6 — Term as a documented rule | **Done** | The classic ten years stay the default, `--years N` (1-1000) selects the term and `--years 100` plays the documented **marathon** rule set; the term travels in `GameState.term_years`, so the engine and the UI never read a global; marathon tests in `test_game.py`, `test_ui.py`, `test_main.py`, `test_simulation.py`; the measured century in `docs/balancing.md`; released as `1.1.0` |
| M7 — Agriculture rule set | **Done** | `--agriculture` puts the optional farming tech tree of `plan.md` §4 in play: `tech.py` (tree as pure data), `models.Agriculture` + `GameState.agriculture`/`unlocked`, the research step in the engine, the tree table in the UI, `tests/test_tech.py` and agriculture batches in `docs/balancing.md`; released as `1.2.0` |
| M8 — A tree that takes a lifetime | **Done** | The tree grew to fifteen nodes in four branches and a capstone, every rung a figure the ruler sees (acres per bushel of seed, bushels per acre, acres per person, the rats' share); the prices climb by about half again a rung, so the measured plan buys the capstone in year 86 on the median and 190 of 500 marathons buy the whole tree; the arc is tabulated rung by rung in `docs/balancing.md` and pinned by `test_the_plan_of_the_tree_takes_a_lifetime`; released as `1.3.0` |

| M9 — Health rule set | **Done** | `--health` puts the optional public-health tree of `plan.md` §4 in play: `health.py` (nineteen measures, four branches, the House of Life), the `Node`/`TechTree`/`Offer` machinery shared with `tech.py`, one research moment a year covering both trees, `models.Health` + `GameState.health`/`born_this_year`, the four rules with classic defaults (`plague_survivors`, `plague_roll` resistance, `people_fed`, `births`), the children in the report and the programme column in the table; `tests/test_health.py` plus the new cases across the suite, and the measured worth of the tree in `docs/balancing.md`; released as `1.4.0` |

Overall: **M0–M9 complete — `1.4.0`.** The rules layer, the yearly engine, the
`rich` terminal UI, the release metadata, the hardening and the four documented
rule sets are all in place: `hammurabi`, `python -m hammurabi` and
`python main.py` play a real game (add `--years 100` for the marathon,
`--agriculture` for the fifteen-node farming tech tree and `--health` for the
nineteen public-health measures), seeded batches of 500 games per policy guard the
rules in every rule set, and `docs/plan.md`, `README.md` and `docs/balancing.md`
are checked against the code by the suite.

## Done

- `pyproject.toml` with `src/` layout, `rich` dependency, console script
  `hammurabi = hammurabi.main:main` and pytest configuration.
- `.venv` created and the package installed in editable mode.
- `docs/plan.md` — assumptions, canonical rules and target outcome.
- `docs/architecture.md` — directory layout, module responsibilities,
  conventions and development workflow.
- `docs/progress.md` — this file.
- `AGENTS.md` — working rules for AI agents; `.clinerules` points to it.
- `AGENTS.md` §9 — measured machine budget (Apple M1, 8 cores, 16 GB unified
  memory shared with the integrated GPU, ~19 GB free disk) with mandatory
  resource-discipline and token-efficiency rules, enforced by a new Definition
  of Done item.
- Runnable skeleton: `hammurabi/__init__.py`, `hammurabi/__main__.py`, the root
  `main.py` launcher and a smoke test.
- **M1** — `config.py` with every rule constant from `plan.md` §4.
- **M1** — `models.py` with the `Verdict` enum and the `GameState` dataclass.
- **M1** — `random_source.py` with the injectable `RandomSource` protocol and
  `SeededRandom`.
- **M1** — `rules.py` with the pure rules: land price, harvest yield, plague,
  rats, immigration, food, seed, labour, validation helpers and the verdict.
- **M1** — `tests/test_rules.py` covering every rule, its boundaries, the
  documented constants and RNG reproducibility.
- **M2** — `game.py` with the `Game` engine: the yearly loop over the rules
  layer, the injected `RandomSource`, the `UI` protocol it defines and the
  buy-or-sell land trade of the original.
- **M2** — `tests/support.py` with the shared test doubles (`StubRandom`,
  `repeat_last`, `FakeUI`, `CarefulUI`); `tests/test_rules.py` now uses the
  shared `StubRandom`.
- **M2** — `tests/test_game.py` covering the opening report and immigrants, the
  plague, land trading and its rejections, feeding and starvation, the running
  average, sowing limits, rats before the harvest, impeachment and full seeded
  terms.
- **M3** — `ui.py` with `ConsoleUI`: the `rich` intro panel, the yearly report,
  the status table, the land price, the four questions (each repeating the figures
  the player needs), the engine's rejection messages and the panels for the
  impeachment and the four verdicts, closing with the listing's farewell.
- **M3** — the answer reader is injected (`ConsoleUI(read=...)`, `input` by
  default) and its parsing loop is bounded by `config.MAX_ANSWER_ATTEMPTS`;
  `tests/test_ui.py` covers every rendering, the re-ask and give-up behaviour, an
  ended input, a rejected answer that comes back through the console and a whole
  seeded game played through the real UI.
- **M3** — the mediocre verdict's would-be assassins are drawn by the engine
  (`rules.would_be_assassins`, previously unused, now fills the new
  `GameState.would_be_assassins`), so all randomness stays behind the injected RNG
  and the UI only renders the figure.
- **M4** — `main.py` really plays the game: `--seed N` replays a game, `--version`
  reports the release, an ended input stops cleanly with exit code 0 and Ctrl-C
  returns 130. The tests replay a full ten-year term through `main()` and run
  `python -m hammurabi` with a closed stdin.
- **M4** — release metadata in `pyproject.toml`: description, `readme`, keywords,
  classifiers, a `dev` extra providing `pytest`, and a **single-sourced version** —
  `dynamic = ["version"]` read from `hammurabi.__version__`, so the distribution,
  `hammurabi --version` and the package cannot drift.
- **M4** — `tests/test_packaging.py`: the installed distribution reports
  `__version__`, the console script points at `hammurabi.main:main`, and
  `pyproject.toml` declares the metadata without a literal version of its own.
  The tests skip when the package is not installed, so a plain `pythonpath` run
  still passes.
- **M4** — `README.md` gained the options, a "How to play" summary, the verdict
  table with its thresholds, the development recipe (`pip install -e ".[dev]"`)
  and a refreshed status note; `.gitignore` now also covers `dist/` and `build/`.
- **M4** — licence: **PolyForm Noncommercial 1.0.0**, free for non-commercial use
  and deliberately *not* open source. `LICENSE` carries the verbatim text with the
  `Required Notice:` line, `README.md` explains what it allows, and
  `pyproject.toml` declares it as the SPDX reference
  `LicenseRef-PolyForm-Noncommercial-1.0.0` with `license-files = ["LICENSE"]`.
  That moved the build backend to `setuptools>=77`, the first release that
  implements the PEP 639 licence fields.
- **M5 (partial)** — test-run resource safety: the engine's four input loops now
  run through the shared `Game._ask_until_accepted` helper, which is bounded by
  `config.MAX_ANSWER_ATTEMPTS`, so a UI that can never produce an accepted
  answer raises `RuntimeError` instead of spinning a CPU core forever.
- **M5 (partial)** — `pyproject.toml` sets `faulthandler_timeout = 20` with
  `faulthandler_exit_on_timeout`, so a test that outlives the bound dumps its
  traceback and aborts the run rather than leaving a stray process behind; the
  entry-point smoke test also got an explicit `subprocess` `timeout`.
- **M5 (partial)** — the previously hanging
  `test_the_roll_made_at_the_end_of_a_year_decides_the_next_one` now plays its
  two years with the rule-aware `CarefulUI`, and two new tests cover the give-up
  behaviour for unaffordable feeding and land.
- **M5 (partial)** — documented the low-priority, single-process test recipe
  (`nice -n 19`, `taskpolicy -b`) and the "one session at a time / no stray
  processes" rules in `AGENTS.md` §7 and §9.1 and `docs/architecture.md` §8.
- **M5** — seeded simulation batches: `tests/policies.py` (four rule-aware
  policies — careful, land trader, land seller and starver — plus `play_game`)
  and `tests/test_simulation.py`, which plays 500 games per policy and asserts
  the grain balance, the population arithmetic, the resource invariants, the
  verdict of every term, the documented event rates, reproducibility, and that a
  batch of this size reaches all four verdicts.
- **M5** — `tests/test_docs.py`: every rule figure quoted in `docs/plan.md`,
  `README.md` and `docs/balancing.md` is compared with the constant or the
  measured event rate it documents, so a changed constant fails the suite until
  the prose follows.
- **M5** — `docs/balancing.md`: what the seeded batches actually do — reign
  length, verdict distribution, per-year event rates and final state for each
  policy, plus which of the two verdict metrics decided every completed term. The
  careful row is asserted by `tests/test_simulation.py`, so the document cannot
  drift from the engine.
- **M5** — every documentation claim corrected against the code: the plague step
  now records the real 20% roll with a plague-free first year, the starvation
  step documents the `P < C` tally skip, a new step 11 documents the undrawn
  closing report, the "known differences" table keeps only the negative-input
  difference, the year-1 figures are in the initial-state table, and
  `architecture.md` lists the new modules and the closing report in its turn
  sequence.
- **M5** — release: `hammurabi.__version__` is `1.0.0`, the target outcome in
  `plan.md` §6 is met, and `README.md` reports the release.
- **Working rules** — `AGENTS.md` §2, §6, §7 and §8 now state that the agent
  never stages, commits, tags or pushes: every change is left in the working
  tree for the maintainer to review, commit and push by hand.
- **Attribution** — `NOTICE` names the authors of the original game (Dyment's
  1968 FOCAL original, Ahl's 1978 BASIC listing) and states that the PolyForm
  licence covers this repository's code, documentation and tests only; the
  `README.md` gained a *Credits and provenance* section, the licence section
  repeats the scope, and the intro banner now credits kilofkilofa.
- **Run instructions** — the README's *Quick start* became *Run the game*: three
  numbered steps (clone, install in a virtual environment, run `hammurabi`), the
  two alternative entry points, the options and what the first screen asks for.
- **M6** — the term became a documented rule instead of a constant: `config.py`
  holds the classic `TERM_YEARS` (10, the default) and the marathon
  `MARATHON_TERM_YEARS` (100), `GameState.term_years` carries whichever is being
  played, and `game.py`/`ui.py` read it from the state, so the engine and the
  console UI never consult a global — the banner and the closing report of a
  marathon both say "100-year".
- **M6** — `main.py` gained `--years N` (default 10, bounds 1-`MAX_TERM_YEARS`
  checked before the engine is built, exit code 2 with a message that names both
  rule sets), so `hammurabi --years 100` plays the marathon.
- **M6** — tests for both terms: the marathon played end to end with a seeded
  policy and through the real console UI (seed 38, the one careful game of the
  measured 500 that survives the century), the closing report at the state's last
  year, the CLI option, its bounds, and a marathon batch that keeps
  `docs/balancing.md` honest.
- **M6** — `docs/balancing.md` records what the marathon measures: the same
  vintage rules over a century leave the careful ruler impeached in the eleventh
  year on average and only 1 term of 500 completed, which is why the ten-year term
  stays the default and the marathon is documented as a survival run.
- **M6** — release: `hammurabi.__version__` is `1.1.0`; `plan.md` §4 documents the
  second rule set, §6 its target outcome, `architecture.md` the state field and
  the CLI option, and `README.md` both terms.
- **M7** — a third rule set, opt-in behind `--agriculture`: the farming tech tree
  of `plan.md` §4, six nodes in two branches (plough → granaries → draft teams,
  fallow → irrigation) that meet in the Nippur almanac capstone. The tree lives in
  the new `tech.py` as pure data with pure helpers (`node`, `available`,
  `can_research`, `offers`, `settings`), so the engine decides what may be
  researched without knowing a single rule number.
- **M7** — the technology travels in the state: `GameState.agriculture` turns the
  rule set on, `GameState.unlocked` is the frozen set of researched keys, and
  `models.Agriculture` holds the effective settings (harvest bonus, acres per seed,
  acres per worker, rat divisor) that the engine derives once a year with
  `tech.settings()`.
- **M7** — `rules.py` takes the technology as keyword arguments that default to
  the vintage values (`harvest_yield(bonus=)`, `rats_eaten(divisor=)`,
  `seed_cost(acres_per_seed=)`, `max_plantable_acres(acres_per_worker=)`,
  `can_plant(...)`), so a classic caller keeps the 1978 numbers and the rules
  never learn which rule set is being played.
- **M7** — the engine gained one step: after the harvest the ruler may pay for a
  single node (research costs no random draw, is asked only when the store can
  afford one, and takes effect in the following years, because the settings are
  read at the top of a year). The `_ask_until_accepted` helper became generic so
  the research answer — a node key or nothing — gets the same bounded retry loop
  and the same engine-side rejection as the four numbers.
- **M7** — the UI draws the tree as a numbered table with costs and effects, asks
  for a technology (`0` for none), reports what was researched, announces the rule
  set in the banner and lists the mastered technologies in the closing report.
- **M7** — tests: `tests/test_tech.py` for the tree (branches, prerequisites,
  capstone, costs, settings, the almanac superseding the granaries), the research
  step in `tests/test_game.py` (cost, unlocking, effect from the next year, the
  plough's seed rate, the draft teams' labour, rejection and give-up, and a term
  with the rule set on replayed against the classic one to prove no extra draw),
  the UI and the CLI, plus a new `FarmerPolicy` and the agriculture ledger,
  invariants and measured rows in `tests/test_simulation.py`.
- **M7** — `docs/balancing.md` measures the rule set against the classic game:
  declining every offer plays the classic term bit for bit (175 of 500 careful
  games complete), while the farmer who buys the harvest nodes completes 103 in
  the decade and 103 in the century, against the single classic careful game of
  500 that survives a hundred years. The tree is documented as a long game: it
  costs more than it returns within a decade.
- **M7** — release: `hammurabi.__version__` is `1.2.0`; `plan.md` §4 documents the
  rule set, §5 records M7, §6 its target outcome, `architecture.md` the new module,
  the state fields, the turn step and the flag, and `README.md` the option and what
  the tree costs.
- **M8** — the tree deepened from six nodes to fifteen, in four branches (fields,
  seed, store and hands) that meet in the Nippur almanac; every rung is a figure the
  ruler sees: 2→3→4→5 acres per bushel of seed, +1 bushel per acre five times, the
  rats' share from a half to a fifth, 10→12→14→16 acres per person.
- **M8** — `config.TECH_COSTS` became the price ladder (400 to 83,900 bushels,
  263,500 together, about half again at every rung), `config.TECH_ACRES_PER_SEED`,
  `TECH_ACRES_PER_WORKER` and `TECH_RAT_DIVISOR` hold the rate each rung reaches,
  `Tech.cost` reads the ladder, and `tech.settings` adds the harvest bonuses up while
  the best unlocked rate wins.
- **M8** — `FarmerPolicy` now researches only out of the surplus left after the food
  and the seed of the year and records every purchase (`bought`), which is what
  makes the re-measured batches reproducible; `tests/test_tech.py` was rewritten for
  the deeper tree (branches, ladder, reachability, rate semantics).
- **M8** — the UI reports how far the programme has come with the research question
  ("Your farmers have mastered 1 of 15 technologies.") and the banner names the size
  of the tree; `tests/test_ui.py` and `tests/test_docs.py` follow. `test_docs.py` now
  also compares the `plan.md` §4 tree table row by row with `tech.TECH_TREE`.
- **M8** — `docs/balancing.md` was re-measured. The farmer completes 277 decades
  where the careful ruler completes 175, and 249 centuries where the careful ruler
  completes one; 190 of the 500 marathons buy all fifteen rungs, with a median
  completion year of 86 (mean 85.1, range 68-100), and the whole arc of the tree is
  tabulated rung by rung. `test_the_plan_of_the_tree_takes_a_lifetime` replays that
  batch and pins the counts and the years.
- **M8** — release: `hammurabi.__version__` is `1.3.0`; `plan.md` §4 carries the
  fifteen-node table and the lifetime rationale, §5 records M8, §6 its target outcome,
  `README.md` the deeper tree and `architecture.md` the ladder semantics.
- **M9** — `health.py`: the optional public-health tree as pure data — nineteen
  measures in four branches (water 3, healers 5, nursery 6, food 4) that meet in the
  **House of Life**, each with its price, prerequisites and effect — and `healers`,
  which folds the unlocked measures into `models.Health`. The prices climb by about a
  third a rung from 100 to 22,000 bushels, 84,490 together: the modest programme of
  the two, because it buys people rather than grain.
- **M9** — `tech.py` refactored around the machinery both rule sets share: the
  `Node` protocol, `TechTree` (with `node`, `available`, `can_research`, `offers`,
  `mastered` and `size`), the `Offer` that carries the programme a node comes from,
  `enabled_trees` (the one place that maps a rule-set flag to its tree) and `offers`,
  which gathers the union. `TECH_TREE` is now `FARMING.nodes`; the helpers that
  served only the farming tree are gone, and `tests/test_tech.py` reads the tree it
  tests.
- **M9** — the four rules, each with the classic value as its default:
  `plague_survivors(P, survivor_percent=50)` (bit for bit the listing's `P // 2`),
  `plague_roll(rng, resistance=0)` (one point shifts the offset by a tenth, which
  really does take five years in a hundred out of the plague: the roll is whole, so
  shifting the offset rather than the roll itself is the only way to get that step
  and still leave the plague possible), `people_fed(bushels, bushels_per_person=20)`
  and the new `births(P, fed=..., per_thousand=0)` (nobody is born in a year the city
  could not feed itself).
- **M9** — the engine: `_bear_children` works out the children the next report
  announces, `_open_year` and the closing report add them with the immigrants, the
  plague takes the share the public health reaches, `_feed_people` feeds at the rate
  in force, and `_research` asks one question a year over the union of the trees in
  play; the UI reports the children, names the dead of a milder plague, prints a
  programme column when both trees offer something, and lists each programme's
  mastery in the closing report.
- **M9** — the suite: `tests/test_health.py` (24 tests: branches, chains, the
  capstone, the ladder, offers, the fold and its rate semantics), the four rules in
  `tests/test_rules.py`, the engine and the UI cases, the flag and the marathon in
  `tests/test_main.py`, the health tables and figures in `tests/test_docs.py`, and the
  batches in `tests/test_simulation.py` (`HealerPolicy`, `rate`, `_years(health=)`
  and the two arcs).
- **M9** — `docs/balancing.md` was measured rather than promised. The healer is
  impeached in the seventh year on average and completes no century of 500; the
  median reign buys three of the nineteen measures and the deepest one any game ever
  reaches is the thirteenth; the splitter — the farmer offered both tables — buys
  8.9 measures for every 4.8 rungs and finishes neither. The two arcs, the batch rows
  and the eighth-year ceiling of a fully built tree are all replayed by
  `tests/test_simulation.py`. This is the honest outcome of M9: the health tree does
  not spread a programme over a lifetime, because a health-only reign does not last
  one.
- **M9** — release: `hammurabi.__version__` is `1.4.0`; `plan.md` §4 carries the
  health table and its four rules, §5 records M9, §6 its target outcome,
  `README.md` the new flag and `architecture.md` the shared machinery, the `Health`
  value and the union research.

## In progress

- **M4** — `[project.urls]` is still open: the project has no public repository
  yet, and a placeholder URL belongs in no release. For the same reason the
  copyright holder in `LICENSE` is the neutral "Hammurabi contributors" until the
  maintainer puts their own name there.

## Next steps

1. **M4** — add `[project.urls]` once the project has a public repository, and
   name the copyright holder in `LICENSE`.
2. Keep the documents and the engine in step: `tests/test_docs.py` and
   `tests/test_simulation.py` fail whenever a constant moves and the prose, the
   `plan.md` §4 tree tables or the arcs in `docs/balancing.md` do not follow, so a
   rule change is a documentation change by construction. Retuning either price
   ladder means re-running that rule set's marathon batch and replacing its arc table
   with the new one.
3. **Known issue found during M7** — the bracketed hint of a question is dropped
   from the *drawn* question: `rich` reads `[you have 2800 bushels, land is 23
   bushels per acre]` as markup, so the console shows only "How many acres do you
   wish to buy?" while the reader of the answer still receives the hint (which is
   what the scripted players use). Escaping the bracket or moving the figures into
   the question text would fix it, and it changes every rendered transcript, so it
   deserves its own task.

## Decision log

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-09-26 | Use the 1978 BASIC listing as the reference ruleset | It is the widely known "old 80s" version the project targets |
| 2026-09-26 | Engine takes an injected RNG and UI | Makes the game deterministic and testable without a terminal |
| 2026-09-26 | Keep game logic out of the UI module | Separation of concerns; rules remain unit-testable |
| 2026-09-26 | `AGENTS.md` is the single source of agent instructions | Avoids drift between tools; `.clinerules` only points to it |
| 2026-09-26 | RNG seam is a thin `RandomSource` protocol (`random`, `randint`) | Keeps all rule knowledge in `rules.py`; tests can inject any scripted stub |
| 2026-09-26 | Rules return values and never mutate `GameState` | The engine owns transitions, which keeps the rules trivially testable |
| 2026-09-26 | The `UI` protocol lives in `game.py`, not in `ui.py` | The engine owns the interface it consumes, so `rich` never enters the domain layer and `ui.py` merely implements it |
| 2026-09-26 | Land is bought or sold in a year, never both | Matches the listing (`330 IF Q=0 THEN 340`); the price is fixed for the year, so trading twice would be pointless |
| 2026-09-26 | An invalid answer is rejected and asked again | The listing quits on a negative answer; re-asking is friendlier and keeps every rule check in the engine |
| 2026-09-26 | Copy the listing's behaviour rather than its comments: the plague roll is the 20% expression `Q = INT(10*(2*RND(1)-0.3))` with a plague-free year 1, and the starvation average skips the `P < C` years | The comment above listing line 541 says "15%" while the expression beside it strikes on 20% of the draws, and the replay of a term follows the code that runs; `plan.md` §4 records each quirk instead of hiding it |
| 2026-09-26 | Record the development machine's resources in `AGENTS.md` §9 and cap CPU, GPU, memory, disk and token usage | Development runs on a laptop, not a build farm: full saturation would make it unusable, and heavy runs cost time and tokens without improving this small game |
| 2026-09-26 | Bound every input-retry loop with `config.MAX_ANSWER_ATTEMPTS` | A UI that can never return a valid answer (a closed stdin or a scripted test double) made the engine loop forever, pegging a CPU core and freezing the development laptop |
| 2026-09-26 | Abort a test that outlives `faulthandler_timeout` (20 s) | A hang must never leave a stray process burning CPU; the whole suite runs in about 0.2 s, so the bound only ever catches a genuine hang |
| 2026-09-26 | Run the suite single-process, one session at a time, at low priority | Parallel test sessions were what saturated the 8-core laptop during development |
| 2026-09-26 | `ConsoleUI` draws the question and reads the answer through an injected `read` callable (`input` by default) | Keeps the rendering in `rich` while letting a test play a whole game without a terminal |
| 2026-09-26 | The engine draws the mediocre verdict's would-be assassins into `GameState.would_be_assassins` | Every random draw stays behind the injected RNG, the UI stays deterministic, and the previously unused `rules.would_be_assassins` now has its caller |
| 2026-09-26 | The console UI bounds its number-parsing loop with `config.MAX_ANSWER_ATTEMPTS` | The same reason as the engine's loop: text that can never be read as a number must not spin a CPU core |
| 2026-09-26 | Each question repeats the figures it needs in brackets, and the status is a `rich` table rather than the listing's plain lines | Cosmetic; `plan.md` §3 allows the tone and the numbers without the original layout, and the repeated figures are what a scripted test player reads |
| 2026-09-26 | Single-source the version: `hammurabi.__version__` plus `dynamic = ["version"]` in `pyproject.toml` | The distribution, `hammurabi --version` and the package can never report different versions; `tests/test_packaging.py` guards the seam |
| 2026-09-26 | Ship the test dependency as a `dev` extra (`pip install -e ".[dev]"`) | The documented workflow already promised "editable install with dev tools"; the extra turns that into one command |
| 2026-09-26 | Stay at `0.1.0` until `plan.md` §6 is met, then release `1.0.0` | M5 hardening is still outstanding, and the plan defines `1.0.0` as the complete target outcome |
| 2026-09-26 | Packaging assertions live in `tests/test_packaging.py` and skip when nothing is installed | They verify release metadata rather than gameplay, and a checkout that relies on `pythonpath` alone must still pass |
| 2026-09-26 | Licence: PolyForm Noncommercial 1.0.0 — free for non-commercial use | The maintainer asked for a licence that is free but not for commercial use; PolyForm's non-commercial licence is written for software and needs no custom wording, while Creative Commons itself advises against using its licences for code. It is source-available rather than open source, and `README.md` says so plainly |
| 2026-09-26 | Declare the licence as `LicenseRef-PolyForm-Noncommercial-1.0.0` and ship the text through `license-files` (`setuptools>=77`) | PolyForm publishes no SPDX identifier, and PEP 639 wants an SPDX expression instead of free text; `setuptools>=77` is the first release implementing those fields |
| 2026-09-26 | No `[project.urls]` yet | The project has no public repository, and a placeholder URL would be a false statement in the released metadata |
| 2026-09-26 | Release `1.0.0` once `plan.md` §6 is met | The plan defines 1.0.0 as the complete target outcome, the milestone list ends with the M5 hardening, and the version is single-sourced, so one edit keeps the package, the distribution and `--version` together |
| 2026-09-26 | Record balancing as *measured* figures in `docs/balancing.md` instead of tuning the constants | The port reproduces the vintage rules rather than re-balancing them, so the document says what the rules do; the careful batch is asserted by `tests/test_simulation.py`, which keeps the notes honest without a second implementation |
| 2026-09-26 | Correct every document claim that described the listing's intent rather than its behaviour | `plan.md`, `README.md` and `architecture.md` had claimed a 15% plague, no `P < C` tally skip and no eleventh report; a specification that disagrees with the code misleads more than it helps |
| 2026-09-26 | Cross-check the documents from the test suite (`tests/test_docs.py`) | Documentation drift is silent otherwise; comparing the quoted figures with the constants and the measured event rates turns "remember to update the docs" into a failing test |
| 2026-09-26 | The agent never stages, commits, tags or pushes; version control is manual (`AGENTS.md` §2, §6, §7, §8) | The maintainer reviews and commits every change by hand: an automated commit or push publishes unreviewed work, and a push to a shared remote cannot be taken back the way a local edit can |
| 2026-09-26 | Credit the original authors and the port author in `NOTICE`, `README.md` and the intro banner | The port follows a game from 1968/1978, so its provenance belongs where the game is played and in the release metadata; saying that the licence covers this repository only keeps the credit honest about what is *not* licensed, and PEP 639 lets `NOTICE` travel with the release through `license-files` |
| 2026-09-26 | Make the term a documented rule with two rule sets: the classic ten years by default and the 100-year **marathon** behind `--years` | Asked for a hundred-year game; measuring it first showed the vintage starvation rule ends a careful reign around the eleventh year, so a hundred-year term is a survival run rather than a longer game. Keeping ten years as the default preserves the faithful port and its balance figures, while the marathon is one flag away and measured in `docs/balancing.md` |
| 2026-09-26 | Carry the term in `GameState.term_years` and validate `--years` in `main.py` | The engine and the UI must not read a global: the state already travels through both, so the banner, the closing report and the loop bound all follow the game being played, and the CLI keeps the badly typed numbers (0, negatives, absurdly long terms) out of the engine |
| 2026-09-27 | Add the farming rule set as opt-in behind `--agriculture`, and keep the classic game the default | The port's contract is the 1978 game: a rule set that changed the default would falsify every measured figure and every classic transcript, so the tree sits one flag away instead |
| 2026-09-27 | Research costs no random draw: it changes the figures the rules are handed, never the stream of events | The two rule sets can then be measured against each other on the same seeds, and a term played with the rule set on and every offer declined is the classic term bit for bit — `tests/test_game.py` proves it and `docs/balancing.md` shows the identical rows |
| 2026-09-27 | Keep the tree in a new `tech.py` and hand the technology to `rules.py` as keyword arguments that default to the classic values | `rules.py` stays a pure, rule-set-free layer, the tree is data the tests can read directly, and a classic caller cannot accidentally get a bonus |
| 2026-09-27 | The rats' divisor takes the strongest value instead of stacking | Granaries halving the loss and the almanac quartering it are alternatives for the same problem; stacking them would leave an eighth and make the rats irrelevant |
| 2026-09-27 | Ask for research only when the store can afford a node, and pay for it before the immigration formula runs | A question with no acceptable answer would spin the bounded retry loop, and paying before the newcomers keeps the ledger single-entry while making the price of the school visible that year |
| 2026-09-27 | Record the measured trade-off instead of tuning the tree to beat the classic decade | The notes measure what the rules do; the batches showed the tree is a long game (it costs more than it returns in ten years and turns a 1-in-500 marathon into 103 survivors), and making the vintage decade easier would have been a balance change to the original game in disguise |
| 2026-09-27 | Release `1.2.0` | M7 adds behaviour, a flag and a module, so the minor version moves; the version stays single-sourced in `hammurabi.__version__` |
| 2026-09-27 | Deepen the tree to fifteen nodes and make every rung a figure the ruler sees | The six-node tree was bought within twenty years of a marathon, so the development ended long before the reign did and the later rungs were invisible in the numbers; the deeper tree gives the programme a whole reign and a felt effect at every rung (M8) |
| 2026-09-27 | Price the tree as a ladder that grows by about half again at every rung | The pacing of the programme is money, not the number of nodes: the ladder puts the first rungs within reach of the opening years and the capstone at 83,900 bushels, and the measured completion median lands at 86 years. The top stays below the 130,000 bushels the store settles at while the rats raid it, so the last rung is reachable — but only after decades of surplus |
| 2026-09-27 | Rates are absolute and the best unlocked rung wins, while the harvest bonuses add up | "3→4 acres per bushel" is a rate, not a bonus: taking the maximum replaces the difference arithmetic of the old deltas, so no two rungs can stack by accident and a retuned ladder cannot silently change what a deeper node means |
| 2026-09-27 | The measuring farmer keeps a food reserve and researches only out of the surplus of the year | A ruler who empties the store for a cheaper plough starves, and that made the earlier batches chaotic — a hundred bushels of difference in a price moved the century survival rate fourfold; the reserve rule is what a competent player does and it makes the batches a smooth function of the ladder, which is what tuning needs |
| 2026-09-27 | Release `1.3.0` | M8 changes the tree, its prices and the measured balance, so the minor version moves; the version stays single-sourced in `hammurabi.__version__` |
| 2026-09-27 | Put the health tree in its own `health.py` and share the research machinery in `tech.py` | The two rule sets are played the same way — a ladder of nodes, one question a year, the store pays — so the machinery is one implementation (`Node`, `TechTree`, `Offer`, `enabled_trees`, `offers`), while the data, the rates and the fold stay with the rule set they belong to |
| 2026-09-27 | One research moment a year for both programmes, not one each | A year holds one decision point, so `--agriculture --health` asks once and the offer covers both trees, every node labelled with the programme that made it. Two questions a year would double the pace of development and make each flag change the other's arithmetic |
| 2026-09-27 | Give the water branch its resistance through the plague roll's *offset*, not through the roll | The roll is whole, so shifting it can only take the plague from 20 to 10, 5 and then 0 years in a hundred — the last of which would abolish a rule of the game. Shifting the offset before the roll is drawn gives the documented 20 -> 15 -> 10 -> 5, leaves the plague possible, and still costs no extra random draw |
| 2026-09-27 | The births rule grants no children in a year the city could not feed itself | A nursery is not what a famine needs, and without the condition the rule would deepen exactly the famine the ruler is being judged for; it also keeps the nursery branch out of the years that are already lost |
| 2026-09-27 | Price the health tree as the modest programme — 84,490 bushels against the farming tree's 263,500 | The ladder is what a short reign can actually climb: the first rungs must fit the opening years, and the healer batch shows the cheap measures bought while the deep ones stay out of reach. A ladder priced like the farming one would be unbuyable content rather than a hard programme |
| 2026-09-27 | Record that the health tree cannot carry a reign instead of adding a harvest rule to make it carry one | Measured: a health-only ruler is impeached for famine after about seven years, and even a city handed the whole tree on the first day dies in the eighth year on the median — the harvest, not medicine, is what keeps a city alive. A fifth rule raising the harvest would have blurred the two rule sets into one bonus, so the tree stands with its four rules and `docs/balancing.md` states what it is worth |
| 2026-09-27 | Release `1.4.0` | M9 adds a rule set, a module, a flag and engine behaviour, so the minor version moves; the version stays single-sourced in `hammurabi.__version__` |

## How to update this file

1. Move finished items from "Next steps" to "Done".
2. Update the summary table and the "Overall" line.
3. Refresh the "Last updated" date.
4. Record any notable decision with its rationale.
