# Progress

> Current level of realisation of [`plan.md`](./plan.md).
> **Keep this file up to date at the end of every task.**

Last updated: 2026-09-26

## Summary

| Milestone | Status | Notes |
| --- | --- | --- |
| M0 — Scaffolding & documentation | **Done** | Skeleton, `docs/`, agent instructions, runnable entry point |
| M1 — Domain model & rules | **Done** | `config.py`, `models.py`, `rules.py`, `random_source.py`; 69 rule tests |
| M2 — Game engine | **Done** | `game.py` with the `UI` protocol; `tests/test_game.py` |
| M3 — Terminal UI | **Done** | `ui.py`: rich intro, yearly report, status table, four bounded questions, verdict panels; 139 tests in total, 19 of them UI tests |
| M4 — CLI options & release packaging | **Done** | `--seed`/`--version`, single-sourced version, non-commercial licence (PolyForm 1.0.0 + `LICENSE`), README (options, how to play, verdicts, development), classifiers and dev extra; `tests/test_packaging.py` |
| M5 — Hardening & polish | In progress | Test-run resource safety done (bounded retries, per-test watchdog); simulation/property tests outstanding |

Overall: **M0–M4 complete — the rules layer, the ten-year engine, the `rich`
terminal UI and the release metadata are implemented and tested, and `hammurabi`,
`python -m hammurabi` and `python main.py` all play a real game. M5 is partly
done: the test suite can no longer hang or saturate the development laptop, while
the simulation tests and the docs cross-check are still to come.**

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

## In progress

- **M4** — `[project.urls]` is still open: the project has no public repository
  yet, and a placeholder URL belongs in no release. For the same reason the
  copyright holder in `LICENSE` is the neutral "Hammurabi contributors" until the
  maintainer puts their own name there.
- **M5** — test-run resource safety is complete; property and simulation tests,
  the docs cross-check and the balancing notes are still to come.

## Next steps

1. **M4** — add `[project.urls]` once the project has a public repository, and
   name the copyright holder in `LICENSE`.
2. **M5** — property and simulation tests (for example seeded batches of games
   asserting the rule invariants: grain never negative, population never rising
   without immigrants, verdict always one of the four).
3. **M5** — cross-check `docs/` against the code and record the balancing notes.
4. **M5** — when the target outcome in `plan.md` §6 is met, bump `__version__` to
   `1.0.0` and report the release complete.

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
| 2026-09-26 | Keep the documented 15% plague chance and the per-year starvation average | The listing's expression is nearer 20%, skips year 1 and skips years without starvation; those quirks are recorded in `plan.md` §4 instead of being copied |
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

## How to update this file

1. Move finished items from "Next steps" to "Done".
2. Update the summary table and the "Overall" line.
3. Refresh the "Last updated" date.
4. Record any notable decision with its rationale.
