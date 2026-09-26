# AGENTS.md — Working rules for AI agents

This file is the **single source of truth** for how an AI agent (Cline, or any
other assistant) must work in this repository. `.clinerules` is only a pointer
to this file, so update the rules here and nowhere else.

## 1. Mandatory first step for every new task

Before planning, editing or running anything, read these files **in this order**:

1. `docs/plan.md` — assumptions, canonical game rules, milestones, target outcome.
2. `docs/architecture.md` — directory layout, module responsibilities,
   conventions, development workflow.
3. `docs/progress.md` — what is already implemented and what comes next.
4. This `AGENTS.md` — the working rules below.

Do not start work until you have read them. If a task conflicts with the docs,
say so explicitly and propose a documentation update instead of silently
deviating.

## 2. Scope and posture

- The game is a faithful Python port of the classic 1978 BASIC **Hammurabi**
  (a.k.a. *Sumeria*). Match the rules in `docs/plan.md` §4 exactly.
- Prefer small, reviewable changes over large rewrites.
- Ask before introducing a new third-party dependency; the only runtime
  dependency is `rich` and the only dev dependency is `pytest` unless the plan
  changes.
- Never leave the repository in a broken state: run the checks in §6 before
  considering a task finished.

## 3. Architecture rules (do not violate)

- Game rules go in `rules.py` as **pure functions**; no I/O, no globals.
- All terminal input/output lives in `ui.py` / `main.py`. Never print from the
  engine or from `rules.py`.
- Randomness must come from the **injected, seedable RNG** wrapper — never call
  `random` directly from `rules.py` or `game.py`.
- Every tunable number belongs in `config.py`, with a comment naming the rule it
  comes from. No magic numbers elsewhere.
- The mutable game state lives in the `GameState` dataclass in `models.py`.

## 4. Coding conventions

- Write **all** code, docstrings, comments, commit-style messages, docs and
  user-facing text in **English**.
- Add type hints to public functions and a module docstring to every module.
- Keep functions small and single-purpose; prefer clarity over cleverness.
- Use absolute intra-package imports (`from hammurabi import rules`).
- Follow the surrounding style; keep lines around 88 characters.

## 5. Documentation duties

- New rule or behaviour → update `docs/plan.md` §4 and `docs/architecture.md`
  if structure changed.
- Any completed work → update `docs/progress.md` (summary table, "Done",
  "Next steps", "Last updated", and the decision log when relevant).
- Do not create parallel instructions; keep `AGENTS.md` authoritative.

## 6. Definition of done (checklist)

- [ ] Rules implemented exactly as specified in `docs/plan.md` §4.
- [ ] Unit tests added or updated for the change.
- [ ] `pytest` passes.
- [ ] `hammurabi`, `python -m hammurabi` and `python main.py` still start.
- [ ] `docs/progress.md` updated, plus `docs/plan.md` / `docs/architecture.md`
      when needed.
- [ ] No new undocumented dependency, no unused code, no TODOs left behind.
- [ ] Commands stayed inside the machine budget in §9 (single-process tests, no
      background processes, no large artefacts left behind).

## 7. Commands

```bash
source .venv/bin/activate   # use the project virtual environment
pip install -e .            # (re)install editable, if needed
nice -n 19 pytest -q        # run the test suite: single process, low priority
taskpolicy -b nice -n 19 pytest -q   # macOS: background QoS, efficiency cores
pytest tests/test_rules.py -q        # a single file while iterating
hammurabi                   # run the game (console script)
python -m hammurabi         # run the game (module form)
python main.py              # run the game (root launcher)
```

## 8. Don'ts

- Don't put gameplay logic in `ui.py` or `main.py`.
- Don't read keyboard input or draw the screen outside `ui.py`.
- Don't use unseeded randomness in tests or in the engine.
- Don't hard-code rule numbers outside `config.py`.
- Don't change the documented rules without updating `docs/plan.md` first.
- Don't write non-English text in files or in the UI.
- Don't saturate the machine and don't burn tokens — see §9 for the measured
  budget and the rules that follow from it.

## 9. Machine budget & resource discipline

Development happens on a **laptop**, not on a build farm. Every task must stay
light enough that the OS, the editor and the game keep responding, must not
compete for the user's machine, and must stay cheap in tokens so work finishes
quickly. The measured profile of the development machine is:

| Resource | Measured value |
| --- | --- |
| Machine | MacBook Pro (`MacBookPro17,1`), macOS 27.0, Apple M1 SoC |
| CPU | Apple M1, 8 cores (4 performance + 4 efficiency) |
| GPU | integrated 8-core Apple GPU (Metal) — **no CUDA** |
| Memory | 16 GB unified memory, shared by CPU and GPU, no swap |
| Disk | 228 GB volume, only ~19 GB free |
| Interpreter | Python 3.14.6 in `.venv` (package targets Python 3.10+) |

The unified memory is shared with the integrated GPU, so there is no spare
accelerator to offload work to: every task has to stay within the laptop.

### 9.1 Resource rules (mandatory)

- Never saturate the machine: leave at least half of the cores free. This game
  is tiny and needs a fraction of one core; a heavy command is a red flag.
- Do not add or use parallel or forked test/build runners (`pytest-xdist`,
  `-n auto`, `multiprocessing`, `concurrent.futures`). Run `pytest`
  single-process, **one session at a time** — never two test runs, and never a
  test run plus a build, in parallel. Lower its priority so the desktop stays
  responsive: `nice -n 19` (`taskpolicy -b` on macOS also moves it to the
  efficiency cores).
- Never leave a stray test process behind. After a killed or timed-out run check
  with `ps -Ao pid,pcpu,command | grep pytest` and kill anything left. A loop
  that rejects an answer forever is a bug, not a load to tolerate: bound it in
  the engine (`config.MAX_ANSWER_ATTEMPTS`) instead of waiting it out.
- Run at most two resource-heavy commands at a time; batch the cheap ones
  instead of fanning out unrelated builds.
- Never leave a long-running process behind: no daemons, servers, file watchers,
  polling loops or `while True`. Every command an agent starts must terminate.
- Bound anything that could run away with a timeout, and prefer `-x`,
  `--maxfail` or a targeted test selection while iterating; run the full suite
  once at the end (see §6).
- Cap simulations and benchmarks: keep seed-driven runs small (a few thousand
  games at most) and never train or run machine-learning or GPU workloads —
  there is no CUDA device and the integrated GPU shares memory with the CPU.
- Keep process memory small: no datasets, model weights or caches of more than
  a few hundred MB. Check with `top -o mem` or `vm_stat` if unsure.
- Free disk space is scarce: do not download large artefacts, and do not leave
  build output, coverage data or logs behind. Write temporary output to `/tmp`
  and delete it when the task is done; keep at least 5 GB free
  (`df -h /`).
- Do not launch the game in an interactive session from an agent command; the
  entry points are verified by the smoke tests or by piping input.

### 9.2 Token efficiency (mandatory)

- Read only what is needed: use line ranges or `search_codebase` instead of
  dumping whole files, and never paste large files back into the reply.
- Batch independent reads, searches and commands into a single tool call.
- Filter command output (`head`, `tail`, `grep`, `wc -l`) so that logs stay
  short, and quote only the relevant lines in the answer.
- Do not re-read or re-print a file merely to confirm an edit; state the change
  and its path instead.
- Prefer several small, precise replacements over rewriting a whole file.

### 9.3 When a task really needs more

If a task cannot be done inside this budget — for example a large simulation to
tune a balance number — stop, explain what is required and why, and ask the user
before running it. Scaling up is a decision for the user, not a default.
