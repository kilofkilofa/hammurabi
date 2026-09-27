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
| M10 — Twenty-five-node rule sets | **Done** | Both optional rule sets of `plan.md` §4 grew to twenty-five nodes each: the farming tree (`tech.py`) now carries nine field rungs, five seed rungs, five store rungs, five hands rungs and the almanac, and the health tree (`health.py`) four water rungs, six healers, seven nursery rungs, seven of food and the House of Life; the price ladders climb by about a quarter a rung (farming 263,450 bushels from 250 to 52,890; health 86,070 from 100 to 16,590); the survivor share climbs every five from the classic half to nineteen in twenty and the feeding rate falls to thirteen bushels; every arc in `docs/balancing.md` was re-measured rung by rung, and the measured plan buys the farming tree out in year 49 on the median (45 as M10 itself measured it, before the `1.5.2` reorder moved the figure); released as `1.5.0` |
| M11 — The year's budget pays for research | **Done** | Research of either rule set may only be paid out of the year's **spare grain**: `rules.spare_grain` sets the food the people need (at the health in force) and the seed the land needs aside, `GameState.spare_bushels` carries the figure, the engine offers nothing above it and the UI quotes it with the question; measured over 500 marathons with a ruler who buys the costliest node first, the old gate let 326 years end below the food line, and the measured arcs of both rule sets are unchanged because their policies already spent only the surplus; ships with `1.5.0`, and the `--all` master toggle over `config.RULE_SETS` follows in the `1.5.1` patch |
| `1.5.2` — The research question opens the year | **Done** | The research question is now put at the top of the year, straight after the report and the plague (`plan.md` §4 step 3) and from the second year of a term on (`config.FIRST_RESEARCH_YEAR`), so the budget is the store the report has just shown — grain the granary really holds — and never the surplus the trade and the harvest of that year are about to earn; the crop of the year is reported where it lands instead (`ui.show_harvest`, between the sowing and the newcomers, whenever a tree is in play), so the grain the next question is paid from is printed by the year that earned it; a year whose spare grain pays for no node reports that empty budget in one line (`ui.show_no_research`) instead of falling silent, and the banner says the question opens from the second year on, so a rule set is never invisible and no first-year question is promised; the classic game has no research, no crop and no empty-budget line, and keeps the vintage transcript bit for bit, and `test_the_store_the_research_question_quotes_adds_up` pins the arithmetic of an opening year (8000 store with 112 people and 1000 acres: 8000 − 2240 food − 333 seed = 5427 may be invested, and that same year ends at 11960), while the arcs of both rule sets were re-measured for the moved budget (the farming tree is bought out in year 49 on the median, by 282 of 500 marathons, in `docs/balancing.md`) |

Overall: **M0–M11 complete — `1.5.2`, with the moved research question of the patch on
top of the `--all` toggle.** The rules layer, the yearly engine, the `rich` terminal UI,
the release metadata, the hardening and the four documented rule sets are all in place:
`hammurabi`, `python -m hammurabi` and
`python main.py` play a real game (add `--years 100` for the marathon,
`--agriculture` for the twenty-five-node farming tech tree, `--health` for the
twenty-five public-health measures and `--all` for every optional rule set at once),
research is paid out of the year's spare grain rather than out of the bread of the
city, the research question opens the year — never the first year of a term, so the
vintage opening is untouched — and never falls silent: a rule-set year shows the
table of what its budget can pay for, or the line that says the store leaves nothing
over — and the crop the next budget comes from is reported
where it lands, seeded batches of 500 games per policy guard the rules in every rule
set, and `docs/plan.md`, `README.md` and `docs/balancing.md` are checked against the
code by the suite.

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
- **M10** — both optional rule sets of `plan.md` §4 grew to twenty-five nodes each.
  The farming tree now runs **fields 9** (fallow fields, green manuring, manured
  fields, irrigated terraces, crop rotation, royal gardens, flood farming,
  irrigation canals, selected seed corn) for +9 bushels an acre, the almanac a
  tenth; **seed 5** (3→4→5→6→7 acres a bushel); **store 5** (the rats' share from a
  half to a sixth, the almanac a seventh); and **hands 5** (10→12→14→16→18→20 acres
  a person). The public-health tree now runs **water 4** (the three resistance rungs
  and the aqueducts), **healers 6** (adding the apothecaries), **nursery 7** (adding
  the children's gardens) and **food 7** (adding the smokehouses, the breweries and
  the date presses), so the survivor share climbs 60→65→70→75→80→85→90→95 and the
  bushels that feed a person fall 19→13.
- **M10** — `config.TECH_COSTS` and `config.HEALTH_COSTS` are the new quarter-step
  ladders (farming 250→52,890, 263,450 bushels together; health 100→16,590, 86,070
  together); `TECH_MAX_YIELD_BONUS` rose to 10, `TECH_ACRES_PER_SEED` to seven,
  `TECH_ACRES_PER_WORKER` to twenty and `TECH_RAT_DIVISOR` to seven. The rate
  dictionaries carry one entry per rung, and the `plan.md` §4 tables, `README.md`,
  `test_tech.py`, `test_health.py`, `test_rules.py` and `test_docs.py` all follow
  them; the two tables are still compared row by row with the trees by
  `tests/test_docs.py`.
- **M10** — `docs/balancing.md` was re-measured rung by rung for both trees. The
  farmer completes 282 decades and 282 centuries, buys all twenty-five rungs in 282
  games of 500 with a median completion year of 49 (mean 49.2, range 43-61), and
  5,199 of the 7,131 rungs ever bought fall in the first twenty years. The healer's
  arc reaches the smokehouses — the nineteenth of the twenty-five, in 25 games — and
  a fully built health tree is impeached in the twelfth year on the median. The
  splitter buys 12.7 measures for every 8.7 rungs, and for the first time one of
  these policies reaches the House of Life (37 games of 500). These are the counts of
  the re-measurement the `1.5.2` reorder carried out (the question opens the year, so
  the budget is drawn before the trade and the harvest of that year); as M10 itself
  first measured them they read 296 decades, 262 centuries in year 45 on the median,
  5,726 of 7,296 rungs in the first twenty years, the smokehouses in 24 games and the
  House of Life in 80.
- **M10** — the arc tests were renamed and re-stated to that measured reality:
  `test_the_plan_of_the_tree_is_the_work_of_a_reign` replaces
  `test_the_plan_of_the_tree_takes_a_lifetime`, the capstone is now bought by more
  than half the games instead of fewer, and the splitter's deepest measure is the
  capstone rather than a rung short of it. The classic game is untouched: the
  careful, trader, seller and starver batches report exactly the counts they did
  before, because nothing but the two trees changed.
- **M10** — release: `hammurabi.__version__` is `1.5.0`; `plan.md` §4 carries both
  new tables, §5 records M10, §6 its target outcome, `README.md` the deeper trees,
  and `architecture.md` their new sizes and the version policy.
- **M11** — research is paid out of the year's **spare grain**, not out of the store:
  `rules.spare_grain` sets the food the people need (at the feeding rate in force, so
  the health's measures widen the budget) and the seed the land needs aside,
  `GameState.spare_bushels` carries the figure, `Game._research` offers nothing above
  it, and `ConsoleUI.ask_research` prints it above the table ("You may spend 301 of
  your 2800 bushels on research; the food of your people and the seed of your fields
  are already set aside") as well as in the question's hint — the drawn question drops
  the bracketed hint, which is the known issue listed below. `TechTree.can_research`
  and `tech.Offer` say the same thing in their docstrings, and the intro banner now
  says the programme is paid "out of the grain left over once the people are fed and
  the fields are sown".
- **M11** — the rule was measured before it was written. The old gate compared the
  price with the store alone: over 500 marathons of 100 years played by a ruler who
  buys the costliest node on offer, 326 years ended with the store below the food the
  city needs *because of the purchase*, and 1,261 years ended below it. With the
  spare-grain rule no purchase can cross that line. The measured policies of
  `docs/balancing.md` are bit for bit unchanged — they already spent only the surplus
  — so no arc, no figure and no row of the balancing notes moved. The opening year
  still offers the ox-drawn plough: 2,800 − 2,000 (food for a hundred people) − 499
  (seed for the 999 acres they can tend) = 301 bushels spare.
- **M11** — tests and documents: `tests/test_rules.py` covers the rule itself (food
  and seed set aside, never negative, the rates and the labour limit it is given),
  `tests/test_game.py` proves a node above the surplus is never offered while the
  store could pay for it, that the health's feeding rate widens the budget and that
  `spare_bushels` carries the figure, and `tests/test_ui.py` pins the hint and the
  banner. `plan.md` §4 (the research rule and the consequence lists of both rule
  sets), §5 (M11) and §6 (the v1.5 outcome), `architecture.md`, `balancing.md`,
  `README.md` and this file follow.
- **M11 / `1.5.1`** — `hammurabi --all` turns on every optional rule set at once, the
  master toggle `plan.md` §4 and §6 (the v1.5.1 outcome) document. The list lives in
  `config.RULE_SETS` (today `("agriculture", "health")`) instead of being spelled out
  in `main.py`, so the toggle covers the farming tree and the public-health measures
  today and any set added to that tuple later without a new branch; each name is both
  the flag and the `GameState` field, and `tests/test_docs.py` fails if a rule set of
  the tuple is missing from §4 or if `--all` leaves the README. The classic game is
  untouched — the toggle only sets flags — and `tests/test_main.py` proves it: a bare
  command turns every set off, `--all` turns every name of the tuple on, the names are
  checked against the `GameState` fields, and `--all` plays exactly the term of
  `--agriculture --health`, event for event. The version moves to `1.5.1`: `1.5.0` is
  released, and the policy in `architecture.md` forbids editing a release.
- **`1.5.2`** — the research question opens the year, and the crop is reported where
  it lands. A ruler was asked what to research against a budget drawn from a store
  the granary would only hold at the end of the year: the harvest landed silently
  between the sowing and the question, so the figure on offer could not be checked
  against anything the report had shown, and the grain it quoted was already spent on
  the trade, the bread and the seed of the same year. The engine now puts the question
  in step 3 of `plan.md` §4 — straight after the report and the plague, before the
  land price is rolled and before the trade, the feeding and the sowing — and only
  from the second year of a term on (`config.FIRST_RESEARCH_YEAR`), so the vintage
  opening year is untouched and the classic game, which has no research, is never
  asked at all; the budget is `rules.spare_grain` at that moment, so the figure on
  offer is grain the granary really holds. The crop of the year is reported where it
  lands instead: `ui.show_harvest`, called between the sowing and the newcomers and
  only when a tree is in play, prints the harvest, the rats and the store the crop
  leaves, so the grain the following year's question is paid from is printed by the
  year that earned it, while a game without a rule set reports no crop and keeps the
  vintage transcript (asserted from both sides in `test_game.py`, with the lines
  pinned by `tests/test_ui.py`). A year whose spare grain pays for no node is no longer
  silent: the engine calls `ui.show_no_research`, which prints the store it measured
  the budget from and says the food of the people and the seed of the fields are set
  aside first, so a rule-set year always shows the research moment — as the table of
  what the budget can pay for, or as the line that says there is nothing to pay with —
  and a ruler can tell a programme they switched on from one that is not being played
  (the maintainer reported exactly that confusion after `1.5.2` came out). The banner
  says the question opens from the second year on, because the vintage opening year
  puts none; `--all` turns on the sets of `config.RULE_SETS`, today the farming and the
  health tree, while the army of the conquest rule set is M12 and still ahead.
  `test_the_store_the_research_question_quotes_adds_up`
  pins the arithmetic from both sides: the granary opens at 8000 bushels with 112
  people, who need 2240 bushels of bread, and the 1000 acres need 333 bushels of seed,
  so the year may invest `8000 - 2240 - 333 = 5427` and the question quotes the 8000
  the report showed — never the 11960 the same year ends at. The measured arcs of both
  rule sets moved with the budget, since a budget drawn at the top of the year is
  drawn before the trade and the harvest of that year: the classic batches of
  `docs/balancing.md` are exactly the ones they were, and the agriculture, health and
  split batches were re-run and re-stated (the farming tree is bought out in year 49 on
  the median, by 282 of 500 marathons). `plan.md` §4 (the turn sequence), §5 and §6 (the
  v1.5.2 outcome), `architecture.md` (the yearly skeleton, the engine's module row and
  the version policy), `README.md` and this file follow. The version moves to `1.5.2`:
  `1.5.1` is released, and the policy in `architecture.md` forbids editing a release.

## In progress

- **M4** — `[project.urls]` is still open: the project has no public repository
  yet, and a placeholder URL belongs in no release. For the same reason the
  copyright holder in `LICENSE` is the neutral "Hammurabi contributors" until the
  maintainer puts their own name there.

## Next steps

1. **M12 — conquest rule set** (next, planned as `1.6.0`): the army, one to twelve
   AI neighbours, battles, margin-scaled spoils and five-year peace treaties, behind
   `--war` / `--opponents N` — adding `"war"` to `config.RULE_SETS` is all the
   `--all` toggle of M11 needs to cover the new set as well. `Neighbour` in
   `models.py`, the battles as pure functions in a new `war.py`, the muster and the
   neighbour turn in the yearly loop, the soldiers as an argument of the planting
   rules, and the measured worth of conquest in `docs/balancing.md`. The
   research-budget rule of M11 shipped with `1.5.0` and the crop report with
   `1.5.2`, so the war rule set is the next minor version; `plan.md` §3's non-goal on
   AI opponents is relaxed for it first.
2. **M4** — add `[project.urls]` once the project has a public repository, and
   name the copyright holder in `LICENSE`.
3. Keep the documents and the engine in step: `tests/test_docs.py` and
   `tests/test_simulation.py` fail whenever a constant moves and the prose, the
   `plan.md` §4 tree tables or the arcs in `docs/balancing.md` do not follow, so a
   rule change is a documentation change by construction. Retuning either price
   ladder means re-running that rule set's marathon batch and replacing its arc table
   with the new one.
4. **Known issue found during M7** — the bracketed hint of a question is dropped
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
| 2026-09-27 | Ask for research only when the store can afford a node, and pay for it before the immigration formula runs — *superseded in M11, where the budget became the year's spare grain rather than the whole store* | A question with no acceptable answer would spin the bounded retry loop, and paying before the newcomers keeps the ledger single-entry while making the price of the school visible that year |
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
| 2026-09-27 | Grow both optional trees to twenty-five nodes and re-space the ladder to about a quarter a rung | Twenty-five rungs on the old third/half-again ladder would put the capstone past a million bushels, out of reach of any reign; re-spacing keeps the whole farming programme at 263,450 bushels and the health programme at 86,070, and the measured arc buys the farming tree out in year 45 instead of 86 — the work of a reign rather than of a lifetime (M10) |
| 2026-09-27 | Add the deeper branches as further rungs of the four existing branches, not as new branches | The four branches already name every lever the rules expose (acres a bushel of seed, bushels an acre, the rats' share, acres a person); a fifth branch would have had to invent a fifth lever or duplicate one of the four, so the deeper tree is the same four levers, more finely priced |
| 2026-09-27 | Keep the health ceilings hard: a survivor share below 100%, resistance at +3 and a feeding rate above zero | A plague that takes nobody and a year that costs no grain would abolish the two rules the health tree modifies; the water branch stops at +3, so the plague still comes five years in a hundred, and the food branch stops at thirteen bushels a person (M10) |
| 2026-09-27 | Restate the arc tests to the measured outcome instead of tuning the ladders to the old claims | The measured tree is bought out in year 45, not 86, and its capstone is now bought by more than half the games: the claims were re-measured and the tests renamed (`test_the_plan_of_the_tree_is_the_work_of_a_reign`) rather than bending the prices to keep an obsolete figure (M10) |
| 2026-09-27 | Release `1.5.0` | M10 changes both trees, their ladders and the measured balance, so the minor version moves; the version stays single-sourced in `hammurabi.__version__` |
| 2026-09-27 | Research may only be paid out of the year's **spare grain** — the store less the food the people need and the seed the land needs (M11) | The old gate compared the price with the store alone, so a ruler could pay with the bread of the city: measured over 500 marathons with a costliest-node-first ruler, 326 years ended below the food line because of the purchase. Pricing the food and the seed into the budget turns the discipline `docs/balancing.md` measures into the rule of the game, and because the measured policies already spent only the surplus, both arcs stay bit for bit the same — the change needs no new constant, no extra random draw and no re-measured table |
| 2026-09-27 | Add `--all` as the master toggle over the optional rule sets, reading `config.RULE_SETS` instead of naming the flags one by one | One flag for the whole set, so a player does not have to remember each programme, and the `--all` toggle was already planned for the conquest rule set; keeping the list in `config.RULE_SETS` means a rule set added there is covered by the same loop, with no second place in `main.py` that could fall out of step. It is released as `1.5.1` rather than edited into `1.5.0`, which is already out |

| 2026-09-27 | Put the research question at the **top** of the year (`1.5.2`), and report the crop of the year where it lands | The question quoted a store the granary would only hold at the end of the year — the harvest landed silently between the report and the question — so the figure on offer could not be reconciled with any line on screen. Opening the year with the question makes the budget the store the report has just printed, less the food the people need and the seed the land needs (the spare grain of M11), and the crop then belongs where it lands: reported after the sowing, with the rats and the grain left behind, so the next year's budget can be checked against the granary. This supersedes the same day's decision to report the crop *before* the question, which put a correct figure next to a question that then spent a different one. The question is skipped in the first year of a term, which leaves the vintage opening year and the whole classic game untouched |
| 2026-09-27 | Re-measure the arcs of both rule sets for the moved budget instead of re-tuning the ladders | No price, no rate and no random draw changed, so the tables moved because the year is spent in a different order: the classic batches are bit for bit the ones they were, while the agriculture, health and split batches were re-run and re-stated in `docs/balancing.md` (the farming tree is bought out in year 49 on the median, by 282 of 500 marathons) |
| 2026-09-27 | Release the moved question and the crop report as `1.5.2` rather than editing them into `1.5.1` | `1.5.1` is already released and the policy in `architecture.md` forbids editing a release; the change moves an existing question and adds a report line without touching a rule, so the patch version moves |
| 2026-09-27 | Report an empty research budget in one line (`ui.show_no_research`) and say in the banner that the question opens the second year on, rather than leaving the rule sets silent | Reported by the maintainer playing `--all` on `1.5.2`: "I do not see the option to develop agriculture or health." The engine was right — the vintage opening year asks nothing (`config.FIRST_RESEARCH_YEAR`) and the question is put only when the year's spare grain can afford a node, which 158 of 500 careful ten-year games never reach — but the player could not tell a programme they had switched on from one that was not being played at all. The two gaps were that a year with an empty budget printed nothing, and that the banner promised a question "each year" while the first year never puts one. Neither change touches a rule, a rate, a random draw or a measured figure: the question is still put only when the surplus covers a rung, and the classic transcript gains neither a line nor a paragraph. The army the report also expected is **not** in this version — conquest is M12 and planned as `1.6.0`, and `--all` turns on every set named in `config.RULE_SETS`, which today holds the farming and the health tree only |

## How to update this file

1. Move finished items from "Next steps" to "Done".
2. Update the summary table and the "Overall" line.
3. Refresh the "Last updated" date.
4. Record any notable decision with its rationale.
