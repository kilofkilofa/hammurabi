# Balancing notes

> What the game does when it is actually played. Every figure below comes from a
> seeded batch of whole games played through the policies in `tests/policies.py`,
> so each one can be reproduced exactly — the numbers are measurements, not
> targets, and no rule was tuned to produce them.

## How the figures were produced

Five hundred games per policy (seeds 0–499), played to their end by the engine
alone, with no terminal involved:

```python
from tests.policies import CarefulPolicy, FarmerPolicy, play_game

for seed in range(500):
    game, policy = play_game(seed, CarefulPolicy)
    ...  # read game.state, policy.answers and policy.calls

for seed in range(500):  # the agriculture rule set, research and all
    game, policy = play_game(seed, FarmerPolicy, agriculture=True)
    ...
```

for seed in range(500):  # the health rule set, research and all
    game, policy = play_game(seed, HealerPolicy, health=True)
    ...
```

Four policies keep the classic batch honest: one careful baseline ruler and three
who each change a single decision, so every branch of the engine is exercised. A
fifth, `FarmerPolicy`, is the one that plays the agriculture rule set, and a sixth,
`HealerPolicy`, plays the health rule set the same way.

| Policy | What it does |
| --- | --- |
| `CarefulPolicy` | never buys or sells land, feeds everybody the store can feed and sows as much as land, seed and labour allow |
| `TraderPolicy` | the same, but spends whatever is left after food and seed on land |
| `SellerPolicy` | the same, but sells 50 acres whenever an acre fetches 22 bushels or more, keeping at least one acre |
| `StarverPolicy` | feeds nobody at all, which ends the reign in the first year |
| `FarmerPolicy` | the careful ruler of the agriculture rule set: sows at the rate the unlocked technology allows, and buys the most valuable technology the year can afford out of the grain left after the food and the seed, never out of the grain the city needs |
| `HealerPolicy` | the careful ruler of the health rule set: feeds the city at the rate its measures allow and buys the measure that keeps the most people alive — bushels per person first, then the plague's survivors, the plague's years and the births — out of the same surplus |

The rules the batches are measured against are the ones in `plan.md` §4: 20
bushels feed one person for a year, 1 bushel of seed sows 2 acres, one person
tends 10 acres, land costs 17-26 bushels per acre, each planted acre yields 1-5
bushels, the rats raid on 40% of the years, the plague roll strikes on 20% of the
draws, starving more than 45% of the city in one year ends the reign, and the
term lasts 10 years. `--agriculture` adds the farming technologies of the same
section: one node a year, paid from the grain in store. The tree holds fifteen
nodes costing 400 to 83,900 bushels each, 263,500 bushels together; the fields
branch adds a bushel per planted acre at every rung, the seed branch lets a bushel
of seed sow 3, 4 and 5 acres, the store branch divides the rats' share by 2, 3 and
4, the hands branch lets one person tend 12, 14 and 16 acres, and the capstone adds
another bushel and leaves the rats a fifth.

## How long a reign lasts

Five hundred games per policy. "Completed" means the classic ten years were
played and the term was scored; "impeached mid-term" means the reign ended inside
a year.
The verdict columns count every game, so a policy's national-fink column is
larger than its mid-term impeachments by the few terms that were played to the
end and still scored as a national fink.

| Policy | Games | Completed | Impeached mid-term | Fantastic | Mediocre | Tyrant | National fink |
| --- | --- | --- | --- | --- | --- | --- | --- |
| careful | 500 | 175 | 325 | 123 | 16 | 31 | 330 |
| trader | 500 | 9 | 491 | 8 | 1 | 0 | 491 |
| seller | 500 | 363 | 137 | 139 | 50 | 98 | 213 |
| starver | 500 | 0 | 500 | 0 | 0 | 0 | 500 |
| careful (agriculture) | 500 | 175 | 325 | 123 | 16 | 31 | 330 |
| farmer (agriculture) | 500 | 277 | 223 | 174 | 24 | 52 | 250 |

| Policy | Mean years played | Mean year of a mid-term impeachment |
| --- | --- | --- |
| careful | 6.71 | 4.93 |
| trader | 4.32 | 4.22 |
| seller | 8.78 | 5.54 |
| starver | 1.00 | 1.00 |
| careful (agriculture) | 6.71 | 4.93 |
| farmer (agriculture) | 5.29 | 4.06 |

## What the random events actually do

Rates are per played year, measured over every year of every game in the batch
(3353 years for the careful ruler, 2161 for the trader, 4389 for the seller, 500
for the starver).

| Policy | Plague struck | Bushels lost to rats | Years with a purchase | Years with a sale | Mean land price | Mean harvest yield | Mean immigrants |
| --- | --- | --- | --- | --- | --- | --- | --- |
| careful | 17.2% | 31.5% | 0.0% | 0.0% | 21.51 | 2.99 | 8.77 |
| trader | 15.9% | 14.3% | 62.2% | 0.0% | 21.46 | 3.01 | 8.21 |
| seller | 17.7% | 35.7% | 0.0% | 50.4% | 21.52 | 2.99 | 8.57 |
| starver | 0.0% | 40.2% | 0.0% | 0.0% | 21.44 | 3.05 | 5.00 |

Two of these columns need a word of explanation, because they look like they
contradict the rules:

- **Plague** strikes in 17-18% of the played years, not 20%, because the first
  year of every term is immune (`START_PLAGUE_ROLL`): the roll made at the end of
  a year decides the year that follows, and the starting roll is positive. The
  roll itself is a clean 20% roll, which the batch confirms when it is drawn
  directly.
- **Rats** raid on 40% of the years, but a raid takes `store / 2` or `store / 4`
  from the grain left *after* feeding and sowing, and a small remainder rounds
  down to nothing. The greedy starver feeds nobody, keeps everything in the store
  and so loses grain in 40.2% of its years — the rule rate. The rulers who feed
  and sow first leave less behind (31.5% of the careful years, 35.7% of the
  selling ones), and the trader, who spends the store on land as well, loses grain
  in only 14.3% of its years.

## How a completed term ends

Averages over the terms that reached the tenth year. The starvation figure is the
running average the verdict is built on; the acres per person figure is the other
metric it uses.

| Policy | Completed terms | Mean population | Mean acres | Mean bushels | Mean starved % per year | Mean acres per person |
| --- | --- | --- | --- | --- | --- | --- |
| careful | 175 | 85.35 | 1000.00 | 4360.31 | 0.14 | 13.50 |
| trader | 9 | 92.78 | 1450.56 | 1266.67 | 0.63 | 18.45 |
| seller | 363 | 82.60 | 735.26 | 5598.71 | 0.22 | 10.32 |

Which of the two metrics decided the verdict? The verdict is the worse of the two
figures, so each completed term can be classified by the figure that came out
worse:

| Policy | Completed terms | Hunger figure worse | Acreage figure worse | The two agree |
| --- | --- | --- | --- | --- |
| careful | 175 | 3 | 48 | 124 |
| trader | 9 | 0 | 1 | 8 |
| seller | 363 | 8 | 215 | 140 |

The starver policy is absent from both tables: it never reaches the tenth year.

## What the numbers say

- **The port is as hard as the original.** A ruler who never touches the land and
  feeds the city properly is still impeached in 325 of 500 games, usually around
  the fifth year.
- **Land is the real decision.** Buying land with the grain meant for food is
  fatal (the trader survives 4.3 years on average and 98% of its games end in
  impeachment), while selling land at a high price is the safest strategy in the
  batch (73% of its terms completed). Holding the original 1000 acres is the
  middle path.
- **Acres per person decides far more often than hunger.** In 48 of the 175
  completed careful terms the acreage figure was the worse of the two, against 3
  where hunger was. The two agree in the other 124, which is what makes the
  fantastic verdicts possible: 123 of the careful batch's completed terms were
  fantastic.
- **The first year is a free pass.** Every term starts plague-free and with 100
  people (95 residents plus 5 immigrants), which is why the measured plague rate
  sits below the 20% roll.
- **No constant needed tuning.** Every rate the batches measure matches the rule
  it comes from, so the numbers in `config.py` stay the vintage ones.

## The marathon term

The marathon rule set is the vintage game stretched to a century: the same rules
(`--years 100`) and the same four policies, five hundred games each (seeds 0-499),
with only the length of the term changed. The city grows with the immigrants while
the store that feeds it does not, so a reign that survives the classic decade
usually meets its 45% year long before the hundredth.

| Policy | Games | Completed | Impeached mid-term | Fantastic | Mediocre | Tyrant | National fink |
| --- | --- | --- | --- | --- | --- | --- | --- |
| careful (marathon) | 500 | 1 | 499 | 1 | 0 | 0 | 499 |
| trader (marathon) | 500 | 0 | 500 | 0 | 0 | 0 | 500 |
| seller (marathon) | 500 | 0 | 500 | 0 | 0 | 0 | 500 |
| starver (marathon) | 500 | 0 | 500 | 0 | 0 | 0 | 500 |

| Policy | Mean years played | Mean year of a mid-term impeachment |
| --- | --- | --- |
| careful (marathon) | 11.19 | 11.01 |
| trader (marathon) | 4.37 | 4.37 |
| seller (marathon) | 23.22 | 23.22 |
| starver (marathon) | 1.00 | 1.00 |

- The careful ruler is impeached in the eleventh year on average and finishes the
  marathon in 1 game of 500 (seed 38, a fantastic verdict); selling land at a high
  price postpones the end to the twenty-third year on average, and spending the
  store on land still ends a reign after four or five years.
- Nothing but the length changes: the marathon term lasts 100 years, and every
  constant in `config.py` stays the vintage one, so every rate in the tables above
  is the same rule measured again.
- A marathon is therefore a survival run rather than a longer game: the classic
  ten-year term is the game as the 1978 listing plays it, and the marathon is the
  documented way to ask for the same rules over a century.


## The agriculture rule set

`--agriculture` puts the fifteen farming technologies of `plan.md` §4 in play: one
node a year, paid out of the grain in store. Research never costs a random draw, so
a term played with the rule set on and every offer declined is the classic term bit
for bit — and the batches below show exactly that, then what the tree is worth to a
ruler who pays for it.

The farmer of these measurements buys the most valuable node the year can afford, a
bushel per acre first, and pays for nothing out of the grain the city needs: only
the surplus left after the food and the seed of the year may be spent on research.
That discipline is the difference between a reign and a ruin — a ruler who empties
the store for a cheaper plough starves — and it is why the farmer completes more
terms than the careful ruler who researches nothing at all.

| Batch | Games | Completed | Impeached mid-term | Fantastic | Mediocre | Tyrant | National fink |
| --- | --- | --- | --- | --- | --- | --- | --- |
| careful (agriculture) | 500 | 175 | 325 | 123 | 16 | 31 | 330 |
| farmer (agriculture) | 500 | 277 | 223 | 174 | 24 | 52 | 250 |
| farmer (agriculture, marathon) | 500 | 249 | 251 | 46 | 12 | 31 | 411 |

| Batch | Mean years played | Mean year of a mid-term impeachment |
| --- | --- | --- |
| careful (agriculture) | 6.71 | 4.93 |
| farmer (agriculture) | 7.29 | 3.93 |
| farmer (agriculture, marathon) | 53.15 | 6.67 |

### The arc of a whole tree

The table below reads the same 500-game marathon batch node by node: how many of the
games ever paid for a rung, and when. "Median year" is where half the games that
bought it had bought it.

| Node | Cost (bushels) | Games that bought it | Median year | Mean year |
| --- | --- | --- | --- | --- |
| Ox-drawn plough | 400 | 300 | 5 | 4.5 |
| Fallow fields | 600 | 333 | 1 | 1.1 |
| Granaries | 850 | 307 | 3 | 3.5 |
| Manured fields | 1250 | 308 | 2 | 2.3 |
| Draft teams | 1850 | 290 | 6 | 6.4 |
| Heavy plough | 2700 | 279 | 8 | 8.0 |
| Crop rotation | 3950 | 291 | 5 | 5.1 |
| Sealed silos | 5800 | 282 | 8 | 8.2 |
| Iron ploughshares | 8500 | 275 | 12 | 11.8 |
| Seed drill | 12450 | 269 | 16 | 15.9 |
| Flood farming | 18200 | 264 | 22 | 22.2 |
| Temple vaults | 26700 | 259 | 29 | 30.0 |
| Harvest crews | 39100 | 255 | 41 | 41.7 |
| Selected seed corn | 57250 | 252 | 60 | 62.1 |
| Nippur almanac | 83900 | 190 | 86 | 85.1 |

Of the 500 farmer games, 190 bought every rung; the median completion year is 86, the
mean 85.1 and the range 68-100. 162 games bought nothing at all, 62 stopped at
fourteen rungs, and 2,960 of the 4,154 rungs ever bought fell in the first twenty
years of the batches.

- **The flag alone changes nothing.** The careful ruler who declines every offer
  plays the classic term exactly — the same 175 completed games, the same verdict
  counts, the same mean year of an impeachment — because research changes the
  figures the rules are handed, never the events the seed produces.
- **The cheap rungs pay for themselves quickly.** The farmer completes 277 terms
  where the careful ruler completes 175: fallow fields, granaries, manured fields
  and crop rotation cost 6,650 bushels between them and give three bushels to every
  planted acre while halving what the rats take, and the opening decade is long
  enough to earn all of that back. Research pays best when it is early and cheap.
- **The whole tree is the work of a lifetime.** The last five rungs cost 225,150 of
  the 263,500 bushels and are paid for between the thirtieth and the eighty-sixth
  year of the plan: it is the ladder, not the shape of the tree, that stretches the
  programme over a reign, and 190 of the 500 marathons finish it.
- **The pace falls off on purpose.** 2,960 rungs are bought in the first twenty
  years of the batches, 580 in the next twenty and then 293, 168 and 153: the cheap
  end of the ladder is climbed by everyone who survives, the costly end only by the
  rich. A decade buys the bottom four rungs and stops there.
- **A century is where it pays.** In the marathon the same farmer completes 249
  terms, against the single careful game of 500 that survives the same century: a
  raised harvest and granaries the rats cannot rob are what a growing city needs
  once the fixed 1000 acres stop feeding it.
- **The tree does not buy land.** 162 games never afford a rung and 62 die at
  fourteen nodes, and of the 249 games that reach the end of the century 160 are
  still scored a national fink, because the verdict measures acres per person and a
  century of good harvests doubles the population while the original acres stand
  still. The tree is what pays for the acres a ruler must buy to keep the verdict,
  not a substitute for buying them.

## The health rule set

`--health` puts the nineteen public-health measures of `plan.md` §4 in play: one
measure a year, paid out of the grain in store, at the same research moment the
farming tree uses. Like the farming tree, the rule set adds no random draw, so a
health game that declines every offer is the classic term bit for bit; the batches
below are the ones that build it.

The healer of these measurements is the careful ruler with two changes. It feeds the
city at the rate its measures allow, because the listing keeps no surplus for a year
in which everybody was fed; and it buys the measure that is worth most to a city
that must stay alive — fewer bushels for the same mouths first, then the people the
healers save, then the plagues the water branch keeps away, and last the children of
the nursery, which raise the demand for bread before they raise the supply. Like the
farmer, it never spends the grain the city needs: only what is left after the food
and the seed of the year. The *splitter* is that same farmer, offered both tables at
once, taking the cheapest rung of whichever one is on offer.

| Batch | Games | Completed | Impeached mid-term | Fantastic | Mediocre | Tyrant | National fink |
| --- | --- | --- | --- | --- | --- | --- | --- |
| healer (health, marathon) | 500 | 0 | 500 | 0 | 0 | 0 | 500 |
| split (agriculture + health, marathon) | 500 | 0 | 500 | 0 | 0 | 0 | 500 |

| Batch | Mean years played | Mean year of a mid-term impeachment |
| --- | --- | --- |
| healer (health, marathon) | 6.83 | 6.83 |
| split (agriculture + health, marathon) | 18.90 | 18.90 |

### How far a reign climbs the tree

The table below reads the healer batch measure by measure: how many of the 500 games
ever paid for a measure, and the mean and the median year they paid for it in.

| Measure | Cost | Games | Mean year | Median year |
| --- | --- | --- | --- | --- |
| Wells | 100 | 151 | 5.9 | 6 |
| Herb gatherers | 140 | 257 | 3.3 | 3 |
| Midwives | 190 | 58 | 9.4 | 10 |
| Milled grain | 250 | 338 | 1.1 | 1 |
| Drained streets | 330 | 89 | 7.7 | 8 |
| Physicians | 450 | 186 | 4.6 | 5 |
| Wet nurses | 610 | 33 | 11.5 | 12 |
| Kitchen gardens | 820 | 290 | 2.2 | 2 |
| Brick-lined drains | 1100 | 47 | 9.4 | 9 |
| Doctors | 1500 | 105 | 6.3 | 6 |
| Milk herds | 2000 | 18 | 13.3 | 13 |
| Oil presses | 2700 | 150 | 4.2 | 3 |
| Healing houses | 3700 | 25 | 9.5 | 8 |
| Birthing houses | 4900 | 0 | — | — |
| Fish ponds | 6700 | 0 | — | — |
| Temple hospital | 9000 | 0 | — | — |
| Foundling home | 12000 | 0 | — | — |
| Palace nursery | 16000 | 0 | — | — |
| House of Life | 22000 | 0 | — | — |

Of the 500 healer games, 340 bought at least one measure and the median reign bought
three; the Healing houses, the thirteenth of the nineteen measures, are the deepest
any of the 500 ever paid for, and only 25 games ever did. The second table is the
splitter's, read the same way, and it climbs much further because the harvest of the
farming tree keeps its city alive.

| Measure | Cost | Games | Mean year | Median year |
| --- | --- | --- | --- | --- |
| Wells | 100 | 309 | 4.3 | 4 |
| Herb gatherers | 140 | 296 | 6.0 | 6 |
| Midwives | 190 | 292 | 7.4 | 8 |
| Milled grain | 250 | 291 | 8.7 | 9 |
| Drained streets | 330 | 290 | 9.9 | 10 |
| Physicians | 450 | 290 | 11.1 | 11 |
| Wet nurses | 610 | 289 | 12.2 | 12 |
| Kitchen gardens | 820 | 288 | 13.2 | 13 |
| Brick-lined drains | 1100 | 287 | 14.3 | 14 |
| Doctors | 1500 | 284 | 15.4 | 15 |
| Milk herds | 2000 | 282 | 16.5 | 16 |
| Oil presses | 2700 | 279 | 17.5 | 17 |
| Healing houses | 3700 | 277 | 18.6 | 18 |
| Birthing houses | 4900 | 267 | 19.9 | 20 |
| Fish ponds | 6700 | 230 | 21.9 | 21 |
| Temple hospital | 9000 | 140 | 25.0 | 24 |
| Foundling home | 12000 | 37 | 31.7 | 32 |
| Palace nursery | 16000 | 1 | 39.0 | 39 |
| House of Life | 22000 | 0 | — | — |

- **The health tree is not a way to live longer.** The healer's mean reign is in the
  tables above and it is about half the careful ruler's, and it completes no century
  of 500: a city that only heals starves, because no measure of this tree touches a
  field. Handing a healer the whole tree from the first year does not save it either
  — even that city is impeached in the eighth year on the median, against the
  eleventh of the careful ruler.
- **A measure cannot feed a city, and the cheap ones are all a short reign affords.**
  A typical healer spends its few years on the first rungs of the four branches —
  milled grain in 338 games, kitchen gardens in 290, herb gatherers in 257 — and the
  deep measures are never reached at all: the deepest one ever bought is the healing
  houses, in 25 games of 500, and the capstone is out of reach of every measured
  policy.
- **The one research moment is the real price of a second programme.** The splitter
  buys 8.9 health measures for every 4.8 farming rungs (medians 14 and 6), because
  the cheap measures crowd out the cheap technologies that raise the harvest — and it
  completes no century either, dying in the nineteenth year on average where the
  farmer alone completes 249 of 500. A ruler who wants both programmes must choose
  which of them will be late.
- **The plague is small change.** The water branch takes the plague from 20 years in
  a hundred to 5, and the healer branch saves four in ten of the stricken, but the
  batches show how little that decides: the careful ruler's cities die of hunger, not
  of plague — the healer's do too.
- **The food branch is the part that shows.** Milling, gardens, oil presses and fish
  ponds bring the bushels that feed a person from 20 to 16, and they are the measures
  most games buy. They are the only part of the tree the granary ever notices.

## How these notes stay honest

- `tests/test_simulation.py` replays every batch quoted above —
  `test_the_balancing_notes_describe_the_batch_they_quote` — and asserts the
  counts of each table row, so a change to a rule or to the engine fails the
  suite until this file is refreshed.
- The arc of the tree is replayed as well:
  `test_the_plan_of_the_tree_takes_a_lifetime` plays the same 500 marathons,
  checks how many games buy every rung, the median completion year and the mean
  year of each node against the table above, so the claim that the whole
  programme takes a lifetime cannot quietly go stale.
- `tests/test_docs.py` checks every rule figure quoted above against the constant
  it documents, and every row of the `plan.md` §4 tree tables against the data in
  `tech.py` and `health.py`, so a changed constant cannot leave a stale number
  behind here or in `plan.md` and `README.md`.
- The arc of the health tree is replayed too:
  `test_the_health_tree_is_climbed_only_as_far_as_a_reign_allows` and
  `test_both_programmes_share_the_one_research_moment` play the same 500 marathons
  and check both tables rung by rung, and
  `test_the_health_tree_alone_cannot_keep_a_city_alive` pins the eighth year the
  first bullet of that section quotes.
- To re-measure everything: replay the batches as shown at the top of this file,
  one policy at a time, and replace the tables above. A marathon batch is the
  same loop with `term_years=config.MARATHON_TERM_YEARS`, an agriculture batch adds
  `agriculture=True`, and a health batch adds `health=True`.
