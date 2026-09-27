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
7. **Harvest** — each planted acre yields 1–5 bushels, plus the bushels the
   agriculture rule set's husbandry technologies add when it is in play.
8. **Rats** — 40% chance: rats eat `store / 2` or `store / 4` bushels, where
   `store` is the grain left after feeding and seeding (before harvest). The
   granaries and the Nippur almanac divide that share further.
9. **Research** — *(agriculture rule set only)* the ruler may pay for one node of
   the farming tech tree below, but only out of the **spare grain of the year**:
   what the store holds once the food the people need (at the public health in
   force) and the seed the land needs for the next sowing have been set aside. A
   node costing more than that is not offered, so the bread of the city and the
   seed of its fields can never be invested. Asked only when at least one node fits
   in that spare grain; a node takes effect in the years that follow, because the
   farming technology is read at the start of a year.
10. **Immigration** — the number of new citizens is worked out from land, grain
    and population. They are announced in the next year's report, which is when
    they join the city.
11. **Starvation check** — starving more than 45% of the population in a single
    year means immediate impeachment and the end of the game. A year in which
    the ruler fed more grain than the people needed (`P < C`, listing line 550)
    adds nothing to the running average, to the total of people starved or to
    the population, and does not even count as a year without starvation.
12. **Scoring** — the listing opens one further (undrawn) report before it judges
    the ruler, so that report's immigration joins the city and the plague roll
    made at the end of the tenth year is resolved before the verdict is derived
    from the starvation average and the acres per person.

An answer that breaks a rule is rejected and asked for again; after 100 rejected
answers in a row the engine stops with an error instead of looping forever
(`config.MAX_ANSWER_ATTEMPTS`).

### Agriculture rule set (`--agriculture`)

The rules above are what `hammurabi` plays by default, in the classic decade and
in the marathon alike. `hammurabi --agriculture` adds an optional farming rule set
on top of them: the farming technologies of Sumeria. Once a year, after the harvest
and before the newcomers are counted, the ruler may pay for **one** node of the tree
out of the year's spare grain: the food the people need and the seed the land needs
for the next sowing are set aside first, so the bread of the city can never be
invested. The node takes effect in the years that follow, costs no random draw of its
own, and changes nothing else about the game.

The tree holds 25 nodes; all of them together cost 263,450 bushels. They stand in
four branches — the fields, the seed, the store and the hands — and meet in the
capstone. The **Nippur almanac**, which reads the flood from the stars, needs the
deepest yield and the best storage at once. The table is printed in the order a
city that means to last buys it.

| Node | Cost (bushels) | Requires | Effect |
| --- | --- | --- | --- |
| Ox-drawn plough | 250 | — | 2 -> 3 acres per bushel of seed |
| Fallow fields | 310 | — | +1 bushel per acre |
| Granaries | 390 | — | the rats eat 1/2 of their share |
| Heavy plough | 490 | Ox-drawn plough | 3 -> 4 acres per bushel of seed |
| Green manuring | 610 | Fallow fields | +1 bushel per acre |
| Draft teams | 760 | Ox-drawn plough | 10 -> 12 acres per person |
| Sealed silos | 950 | Granaries | the rats eat 1/3 of their share |
| Manured fields | 1190 | Green manuring | +1 bushel per acre |
| Row sowing | 1490 | Heavy plough | 4 -> 5 acres per bushel of seed |
| Iron ploughshares | 1860 | Draft teams | 12 -> 14 acres per person |
| Underground cellars | 2330 | Sealed silos | the rats eat 1/4 of their share |
| Irrigated terraces | 2910 | Manured fields | +1 bushel per acre |
| Seed drill | 3640 | Row sowing | 5 -> 6 acres per bushel of seed |
| Harvest crews | 4540 | Iron ploughshares | 14 -> 16 acres per person |
| Temple vaults | 5680 | Underground cellars | the rats eat 1/5 of their share |
| Crop rotation | 7100 | Irrigated terraces | +1 bushel per acre |
| Garden seed | 8870 | Seed drill | 6 -> 7 acres per bushel of seed |
| Ox-driven threshers | 11090 | Harvest crews | 16 -> 18 acres per person |
| Undercrofts | 13870 | Temple vaults | the rats eat 1/6 of their share |
| Royal gardens | 17330 | Crop rotation | +1 bushel per acre |
| Water lifts | 21660 | Ox-driven threshers | 18 -> 20 acres per person |
| Flood farming | 27080 | Royal gardens | +1 bushel per acre |
| Irrigation canals | 33850 | Flood farming | +1 bushel per acre |
| Selected seed corn | 42310 | Irrigation canals | +1 bushel per acre |
| Nippur almanac | 52890 | Selected seed corn, Undercrofts | +1 bushel per acre, the rats eat 1/7 of their share |

The **fields** branch adds a bushel per planted acre at every rung, so the harvest
roll of 1–5 can reach 11–15 bushels an acre once the whole branch and the almanac
are unlocked: it adds at most +10 bushels per planted acre. The **seed** branch lets
one bushel of seed sow 3, 4, 5, 6 and then 7 acres, the **store** branch makes the
rats take a half, a third, a quarter, a fifth and then a sixth of their share, and
the **hands** branch lets one person tend 12, 14, 16, 18 and then 20 acres. Every one
of those is a *rate*: the best rung unlocked is the one in force, and no two of them
add up. The rats' share is divided by 2 with the granaries, by 3 with the sealed
silos, by 4 with the underground cellars, by 5 with the temple vaults, by 6 with the
undercrofts and by 7 with the almanac, and each of the nine field rungs adds its
bushel to the same roll.

The prices climb by about a quarter at every rung, and that is what turns the
programme into the work of a reign: the first rungs fit into the opening years, the
middle ones need the surplus of a good decade, and the last ones cost what many
harvests leave over. Measured over five hundred marathons, a ruler who spends the
spare grain of each year on the tree buys the last node in year 45 on the median and
finishes the whole tree in 262 of the 500 games; the arc of that plan, rung by rung,
is in [`balancing.md`](./balancing.md).

Five consequences are worth stating plainly:

- the price must fit in the year's **spare grain**, not in the store: the food the
  people need and the seed the land needs are set aside first, so a ruler can invest
  the surplus of a good year but never the bread of the city or the seed of its
  fields — the discipline [`balancing.md`](./balancing.md) measures is the rule, not
  a habit of the policy;
- the question is put only when that spare grain can afford at least one node, so a
  ruler without a surplus is never asked a question they cannot answer, and the
  classic game (where the rule set is off) is never asked at all;
- the research is paid **before** the immigration formula runs, so a city that
  bought technology that year receives slightly fewer newcomers — the price of the
  school is paid by the city that would have grown;
- no draw is added, so the same seed produces exactly the same events with and
  without the rule set: [`balancing.md`](./balancing.md) measures the two against
  each other, and a ruler who declines every offer plays the classic term
  unchanged;
- the farming technology of a year is read at the start of it, so a node paid for
  in December shows in the fields of the following year.

The mature tree feeds a city the classic rules cannot feed — in the measured
marathon the same farmer survives 262 centuries of 500 where the careful ruler
survives one — but it does not give that city land. A century of good harvests
doubles the population, so a ruler who wants the acres per person of the verdict
to hold must buy acres as well; the tree is what pays for them.

### Health rule set (`--health`)

`hammurabi --health` adds the other optional rule set: the public-health measures of
Sumeria, bought with the same yearly research as the farming tree. Once a year, in
the same moment the agriculture rule set uses, the ruler may pay for **one** measure
out of the spare grain of the year. The measure takes effect in the years that
follow, costs no random draw of its own, and changes nothing else about the game.
With both rule sets in play the offer covers both trees — a year holds one research
moment however many programmes it serves — and the table says which programme offers
each node.

The tree holds 25 measures; all of them cost 86,070 bushels between them, a third of
the farming ladder, because what it buys is people rather than grain. They stand in
four branches — the water, the healers, the nursery and the food — and meet in the
capstone. The **House of Life**, which needs the deepest measure of every branch at
once, is the last word in medicine. The table is printed in the order a city can pay
for it, and its first four rungs are one of each branch, so even a young treasury can
choose where to begin.

| Measure | Cost (bushels) | Requires | Effect |
| --- | --- | --- | --- |
| Wells | 100 | — | plague resistance: +1 |
| Herb gatherers | 124 | — | plague survivors: 50% -> 60% |
| Midwives | 153 | — | +4 births per 1000 people |
| Milled grain | 190 | — | 20 -> 19 bushels per person |
| Drained streets | 235 | Wells | plague resistance: +1 -> +2 |
| Physicians | 290 | Herb gatherers | plague survivors: 60% -> 70% |
| Wet nurses | 359 | Midwives | +8 births per 1000 people |
| Kitchen gardens | 444 | Milled grain | 19 -> 18 bushels per person |
| Brick-lined drains | 550 | Drained streets | plague resistance: +2 -> +3 |
| Apothecaries | 680 | Physicians | plague survivors: 70% -> 75% |
| Milk herds | 842 | Wet nurses | +12 births per 1000 people |
| Oil presses | 1041 | Kitchen gardens | 18 -> 17 bushels per person |
| Aqueducts | 1288 | Brick-lined drains | plague survivors: 50% -> 65% |
| Doctors | 1594 | Apothecaries | plague survivors: 75% -> 80% |
| Birthing houses | 1972 | Milk herds | +18 births per 1000 people |
| Fish ponds | 2440 | Oil presses | 17 -> 16 bushels per person |
| Healing houses | 3019 | Doctors | plague survivors: 80% -> 85% |
| Foundling home | 3736 | Birthing houses | +25 births per 1000 people |
| Smokehouses | 4623 | Fish ponds | 16 -> 15 bushels per person |
| Temple hospital | 5720 | Healing houses | plague survivors: 85% -> 90% |
| Palace nursery | 7078 | Foundling home | +34 births per 1000 people |
| Breweries | 8758 | Smokehouses | 15 -> 14 bushels per person |
| Children's gardens | 10836 | Palace nursery | +40 births per 1000 people |
| Date presses | 13408 | Breweries | 14 -> 13 bushels per person |
| House of Life | 16590 | Brick-lined drains, Temple hospital, Children's gardens, Date presses | plague survivors: 90% -> 95%, +45 births per 1000 people |

Four rules change, each of them with the classic value as its default, so a game
without the flag is bit for bit the 1978 game:

| Rule | Classic | With the health rule set |
| --- | --- | --- |
| the plague's survivors | `P // 2` | the share the healer branch reaches, `P * survivor_percent // 100` |
| the plague roll | the vintage `INT(10 * (2 * RND(1) - .3))` | the offset shifts by a tenth per point of resistance, which takes five years in a hundred out of the plague |
| the people one bushel feeds | `bushels // 20` | `bushels // bushels_per_person`, down to thirteen |
| the births of a year | none at all | `P * per_thousand // 1000`, and only in a year the city fed itself |

The **water** branch takes five years in a hundred out of the plague at every rung,
so the deepest drains leave the plague 5 years in a hundred and no measure can
abolish it. The **healers** branch decides how many of the stricken live: six in ten
with the herb gatherers, nine in ten with the temple hospital and nineteen in twenty
with the House of Life. The **nursery** branch is the only one of the four that adds
people to the city, up to 45 children for every 1000 people in a year the city fed
itself. The **food** branch brings the bushels that feed one person for a year from 20 down
to 13: it is the cheapest way to keep a growing city alive and the only one of the
four that the granary notices.

What the tree is worth is a measurement rather than a promise, and it is a modest
one: a reign that only heals is impeached for famine within about a dozen years,
because what a growing city needs is a harvest, not medicine, and no measure of the
tree touches the
fields. The measured arc of a healer's plan — how far the twenty-five measures are
actually bought — is in [`balancing.md`](./balancing.md), next to the row that prices
the one research moment: a ruler who splits it between both programmes buys part of
each and finishes neither.

Five consequences are worth stating plainly:

- the price must fit in the year's **spare grain**, exactly as with the farming
  tree, and the food set aside is the food of the health in force — so the measures
  bring their own margin, because feeding a person out of fewer bushels leaves more
  to invest;
- the question is put only when that spare grain can afford at least one measure, so
  a ruler without a surplus is never asked a question they cannot answer, and a
  classic game is never asked at all;
- the research is paid **before** the immigration formula runs, so a city that built
  a measure that year receives slightly fewer newcomers, exactly as with the farming
  tree;
- no draw is added, so the same seed produces exactly the same events with and
  without the flag: a ruler who declines every offer plays the classic term unchanged;
- the public health of a year is read at the start of it, so a measure paid for in
  December shows in the following year, the roll of that year included.

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
| M7 | Agriculture rule set | The optional `--agriculture` tech tree of §4: `tech.py`, the research step in the engine, the tree in the UI, and the measured trade-off in the balancing notes |
| M8 | A tree that takes a lifetime | The fifteen-node tree of §4, its price ladder and the measured eighty-five-year plan: the deeper `tech.py`, the progress line in the UI, and the balancing notes re-measured rung by rung |
| M9 | Health rule set | The optional `--health` tree of §4: `health.py`, the `TechTree` machinery shared with `tech.py`, the union of both programmes in the one research moment of a year, and the measured worth of the tree in the balancing notes |
| M10 | Twenty-five-node rule sets | Both optional rule sets of §4 grow to twenty-five nodes each: the quarter-step price ladders, the deeper branches of the farming tree (fields 9, seed 5, store 5, hands 5 and the almanac) and the wider public health (water 4, healers 6, nursery 7, food 7 and the House of Life), with every arc in the balancing notes re-measured rung by rung |
| M11 | The year's budget pays for research | Research of either rule set may only be paid out of the spare grain of the year — the store less the food the people need at the health in force and the seed the land needs for the next sowing — so no node is offered that the surplus cannot pay for, the figure travels with the question, and the discipline the balancing notes measure becomes the rule of the game rather than a habit of the policy |

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

### Target outcome for v1.2 (the agriculture rule set)

`1.2.0` keeps both earlier games as they are — the classic decade stays the
default and `--years` still chooses the term — and adds the opt-in rule set of §4:

- `hammurabi --agriculture` plays the game with the farming tech tree; without
  the flag nothing at all changes, not even a random draw;
- the tree lives in `tech.py` as pure data, the effective farming technology
  travels in `GameState` (`agriculture`, `unlocked`), and the rules take it as
  plain arguments that default to the vintage values, so `rules.py` stays free of
  rule-set knowledge and a classic caller keeps the 1978 numbers;
- the engine asks for one research a year, only when the rule set is on and the
  grain on offer can pay for a node, and pays for it before the newcomers are
  counted — since `1.5.0` that grain is the year's spare grain rather than the whole
  store, as the target outcome below records;
- the suite covers the tree, the research step, the UI's table and the entry
  point's flag, and `docs/balancing.md` measures the rule set against the classic
  game: the flag alone is inert, and the tree costs more than it returns in a
  decade while transforming the marathon;
- `plan.md`, `README.md` and `docs/architecture.md` document the rule set, the
  tree and the opt-in flag.

### Target outcome for v1.3 (a tree that takes a lifetime)

`1.3.0` keeps the classic game and the v1.2 rule set as they are — the flag still
gates every change — and deepens the tree of §4, so that development is a whole
reign's work rather than a decade's trick:

- the tree grows from six nodes to fifteen, in four branches that meet in the
  Nippur almanac, and every node changes a figure the ruler sees year after year:
  acres per bushel of seed, bushels per acre, acres per person or the bushels the
  rats eat;
- the prices climb by about half again at every rung, so the first nodes fit into
  the opening years and the capstone costs 83,900 bushels;
- the rates do not stack — the best rung unlocked is the one in force — while the
  harvest bonus of every field rung adds to the same roll;
- the tree can be finished inside a marathon and not inside a decade: the measured
  plan buys the capstone in year 86 on the median, and 190 of the 500 marathons buy
  the whole tree before the term ends;
- the UI reports how far the programme has come with the research question, and
  `docs/balancing.md` records the arc of the plan rung by rung.

### Target outcome for v1.4 (the health rule set)

`1.4.0` keeps the classic game and the farming rule set as they are — every change
stays behind its own flag — and adds the second opt-in rule set of §4:

- `hammurabi --health` plays the game with the public-health tree; without the flag
  nothing at all changes, not even a random draw, and a health game that declines
  every offer is the classic term bit for bit;
- the tree lives in `health.py` as pure data and shares the research machinery of
  `tech.py` (`Node`, `TechTree`, `Offer`), so `tech.enabled_trees` is the single
  place that maps a rule-set flag to the tree it plays;
- the two rule sets share the one research moment of a year: with both flags the
  offer covers both trees, the table names the programme of every node, and one
  question a year is asked;
- the public health travels in `GameState` (`health`, and the `born_this_year` the
  report names) and in a `Health` value the engine folds once a year, so `rules.py`
  keeps its classic defaults while the survivor share, the plague resistance, the
  births and the bushels that feed a person all enter as plain arguments;
- the suite covers the tree, the four rules, the births in the report, the plague
  message, the programme column and both entry-point flags; `docs/balancing.md`
  records what the tree is worth — how far a health-only reign actually climbs it,
  and what splitting the research moment between the two programmes costs — instead
  of claiming a lifetime this rule set cannot fill.

### Target outcome for v1.5 (twenty-five-node rule sets)

`1.5.0` keeps every game exactly as it was — the classic decade, the marathon and
both opt-in rule sets behind their own flags — and deepens the two trees of §4 to
twenty-five nodes each:

- the farming tree grows from fifteen nodes to twenty-five in the same four
  branches plus the Nippur almanac: nine field rungs and the almanac add a bushel to
  every planted acre, five seed rungs sow up to seven acres a bushel, five store
  rungs take the rats' share down to a sixth (and the almanac to a seventh) and five
  hands rungs let one person tend twenty acres;
- the public-health tree grows from nineteen measures to twenty-five: the water
  branch adds the aqueducts, the healers the apothecaries, the nursery the
  children's gardens and the food branch the smokehouses, the breweries and the date
  presses, so the survivor share climbs the fives from the classic half to nineteen
  in twenty and the bushels that feed a person fall to thirteen;
- the price ladders climb by about a quarter a rung instead of a third or a half:
  the farming tree costs 263,450 bushels from 250 to 52,890, the health tree 86,070
  from 100 to 16,590, and the measured plan buys the whole farming tree in year 45 on
  the median;
- the ceilings stay ceilings: no survivor share reaches 100%, no water rung adds
  more than +3 to the plague roll, and the feeding rate stays above zero, so the
  plague can always come and feeding always costs something;
- the research of both rule sets is paid out of the year's **spare grain** — the
  store less the food the people need at the health in force and the seed the land
  needs — so a node whose price does not fit is never offered and the bread of the
  city can never be invested;
- `docs/balancing.md` is re-measured rung by rung for both trees, and
  `tests/test_docs.py` still compares every row of the two §4 tables with the data
  in `tech.py` and `health.py`.

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

