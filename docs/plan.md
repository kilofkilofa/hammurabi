# Hammurabi — Project Plan

> Living document. Update it whenever scope, rules or goals change.
> For "what is actually implemented today" see [`progress.md`](./progress.md).

## 1. Overview

`hammurabi` is a Python re-implementation of the classic text-based resource
management game **Hammurabi** (also known as **Sumeria**). The original was
written by Doug Dyment in 1968 in FOCAL and popularised through David H. Ahl's
*101 BASIC Computer Games* (1978).

The player rules the ancient city-state of Sumeria for a **ten-year term**, or
for a whole century in the **marathon** rule set, deciding each year how much
land to buy or sell, how much grain to feed the people and how many acres to
plant, while random events (harvests, rats, immigration and plague) shape the
outcome.

The target is a faithful, cleanly structured and fully tested Python
implementation that is still fun to play in a terminal.

## 2. Goals

- Reproduce the classic rules and the ten-year term with high fidelity, and keep
  the length of the term a documented choice rather than a hard-coded one.
- Keep the game engine free of terminal I/O so it can be unit tested and
  simulated headlessly.
- Make runs deterministic and reproducible by injecting a seedable RNG.
- Provide a pleasant terminal UI built on `rich`.
- Ship clear documentation (`docs/`) and an automated test suite (`tests/`).

## 3. Non-goals (v1.0)

- Graphics, web UI, networking, persistent save files.
- Multiplayer or AI opponents.
- Byte-for-byte reproduction of the original BASIC strings — we keep the tone
  and meaning, not the original punctuation and typos.

## 4. Canonical game rules

Derived from the 1978 BASIC listing
(`vintage-basic.net/bcg/hammurabi.bas`), which is the reference behaviour.

### Initial state

| Resource | Value |
| --- | --- |
| Population | 95 people |
| Grain in store | 2800 bushels |
| Land owned | 1000 acres |
| Term | 10 years |
| Marathon term | 100 years |
| Immigrants in year 1 | 5 |
| Rats ate in year 1 | 200 bushels |
| Harvest yield in year 1 | 3 bushels per acre |

After the first immigration the population reaches 100, which is why many
descriptions simply quote "100 people".

The classic rule set is the ten-year term. The **marathon** plays exactly the
same rules over 100 years: nothing but the length of the term changes, so a
marathon run is the vintage game stretched to a century, and
[`balancing.md`](./balancing.md) records what that measures — the city grows
faster than the store can feed it, so the vast majority of marathon reigns end in
an impeachment long before the hundredth year. `hammurabi --years N` plays any
term from 1 to 1000 years; the classic ten is the default and 100 the marathon.

### Turn sequence

1. **Report** — year, people starved last year, immigrants, plague, population,
   acres owned, harvest yield per acre, grain eaten by rats, grain in store. The
   immigrants announced in the report join the city as part of this step.
2. **Plague** — the plague roll `INT(10 * (2 * RND(1) - 0.3))`, drawn at the end
   of the previous year, decides the plague: it strikes when the roll is not
   positive, which happens for 20% of the years. Half the population then dies
   (rounded down). Year 1 uses the listing's initial roll (`Q = 1`), so the
   first year is always plague-free.
3. **Land price** — a random value of 17–26 bushels per acre, rolled once per
   year and fixed for both buying and selling that year.
4. **Buy or sell land** — buy with grain, sell for grain. The price is fixed for
   the whole year, so as in the original the ruler does one of the two, never
   both. At least one acre must remain (selling every acre is forbidden).
5. **Feed the people** — each person needs 20 bushels. Unfed people starve.
6. **Plant grain** — 1 bushel of seed sows 2 acres and 1 person can tend 10
   acres, so at most `10 * population - 1` acres. Planting 0 acres is allowed.
7. **Harvest** — each planted acre yields 1–5 bushels.
8. **Rats** — 40% chance: rats eat `store / 2` or `store / 4` bushels, where
   `store` is the grain left after feeding and seeding (before harvest).
9. **Immigration** — the number of new citizens is worked out from land, grain
   and population. They are announced in the next year's report, which is when
   they join the city.
10. **Starvation check** — starving more than 45% of the population in a single
    year means immediate impeachment and the end of the game. A year in which
    the ruler fed more grain than the people needed (`P < C`, listing line 550)
    adds nothing to the running average, to the total of people starved or to
    the population, and does not even count as a year without starvation.
11. **Scoring** — the listing opens one further (undrawn) report before it judges
    the ruler, so that report's immigration joins the city and the plague roll
    made at the end of the tenth year is resolved before the verdict is derived
    from the starvation average and the acres per person.

An answer that breaks a rule is rejected and asked for again; after 100 rejected
answers in a row the engine stops with an error instead of looping forever
(`config.MAX_ANSWER_ATTEMPTS`).

### End of game (after the tenth year)

Two metrics drive the final evaluation:

- the **average percentage of the population that starved per year**, and
- the **acres per person** at the end of the term.

| Condition | Verdict |
| --- | --- |
| starved > 33% or acres/person < 7 | impeached — "declared national fink" |
| starved > 10% or acres/person < 9 | compared to Nero and Ivan the Terrible |
| starved > 3% or acres/person < 10 | "could have been better" |
| otherwise | "a fantastic performance" |

The closing report also quotes the average starvation percentage, the total
number of people who died and the acres per person at the start and the end of
the term. The mediocre verdict names how many people would like to see the ruler
assassinated (``INT(P * .8 * RND(1))``, listing line 965); the engine draws that
figure, and the UI only renders it.

### Known differences from the 1978 listing

The listing is the reference for behaviour, and its quirks are part of the game:
the 20% plague roll, the plague-free first year, the skipped tally after
overfeeding and the undrawn final report are all reproduced and written down in
the turn sequence above. What differs is only the handling of input the listing
cannot cope with. Each difference is a decision, not an oversight.

| Listing behaviour | This implementation | Why |
| --- | --- | --- |
| a negative answer ends the game with "I cannot do what you wish" | the engine rejects it and asks again | the documented `can_*` helpers treat negatives as invalid |
| the listing loops forever on an answer it cannot accept | after 100 rejected answers in a row the engine stops with an error | an unbounded loop spins a CPU core forever when no valid answer can ever be given |

## 5. Milestones

Each milestone is independently testable and ends with `progress.md` updated.

| ID | Milestone | Deliverable |
| --- | --- | --- |
| M0 | Scaffolding & documentation | Project skeleton, `docs/`, agent instructions, runnable entry point |
| M1 | Domain model & rules | `config.py`, `models.py`, `rules.py` — pure, fully unit tested |
| M2 | Game engine | `game.py` — the yearly loop, wired to injected RNG and UI |
| M3 | Terminal UI | `ui.py` — `rich` based report, prompts and validation messages |
| M4 | CLI options & release packaging | `--seed`/`--version` options, `README.md` polish, release metadata in `pyproject.toml` (non-commercial licence, single-sourced version) |
| M5 | Hardening & polish | Property/simulation tests, docs cross-check, balancing notes |
| M6 | Term as a documented rule | The marathon rule set and `--years`; the term travels in `GameState`; balancing notes for the century |

### Stretch ideas (after v1.0)

- Difficulty presets (harsher plague / different land prices).
- Save and resume a game (JSON) and a local high-score table.
- Alternate rule set that mirrors a second historical BASIC variant.

## 6. Target outcome (definition of "done" for v1.0)

A player can install the package and run `hammurabi` (or `python -m hammurabi`)
to play a complete, faithful ten-year game in the terminal:

- the rules in section 4 are implemented exactly;
- all game logic is importable and simulatable without a terminal;
- the test suite passes and covers every rule and the end-of-game verdicts;
- `docs/` describes the project accurately and `progress.md` reports v1.0
  complete.

### Target outcome for v1.1 (the marathon)

`1.1.0` keeps the v1.0 game as its default and adds the second rule set of §4:

- `hammurabi --years N` selects the length of the term; `10` (the classic game)
  is the default and `100` is the marathon;
- the term lives in `GameState.term_years`, so the engine and the UI never read
  a global and a marathon transcript reports its own length;
- the suite covers the marathon (a hundred-year term played end to end, the
  closing report at the last year, the option's bounds) and keeps
  `docs/balancing.md` honest with a measured marathon batch;
- `docs/` and `README.md` document both terms and what the marathon measures.

## 7. Tech stack

| Concern | Choice |
| --- | --- |
| Language | Python 3.10+ (development uses 3.14) |
| Package layout | `src/` layout, single package `hammurabi` |
| Terminal UI | `rich` |
| Testing | `pytest` |
| Build backend | `setuptools` (`pyproject.toml`) |

## 8. Success criteria

- `pytest` is green, including tests for rules, engine and entry point.
- `hammurabi` and `python -m hammurabi` both start the game.
- Random behaviour is fully controlled by an injected, seedable RNG, so a seed
  reproduces a game exactly.
- Code is typed, documented with docstrings, and written in English.

## 9. References

- Original BASIC listing: <http://vintage-basic.net/bcg/hammurabi.bas>
- Background: David H. Ahl, *101 BASIC Computer Games* (1978), and Doug
  Dyment's 1968 FOCAL original *The Sumer Game*.

