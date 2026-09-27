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
| `FarmerPolicy` | the careful ruler of the agriculture rule set: sows at the rate the unlocked technology allows, and buys the most valuable of the technologies the year's spare grain can pay for — the engine offers nothing above that, so the food of the city and the seed of its fields are never on the table for anyone |
| `HealerPolicy` | the careful ruler of the health rule set: feeds the city at the rate its measures allow and buys the measure that keeps the most people alive — bushels per person first, then the plague's survivors, the plague's years and the births — out of the same surplus |

The rules the batches are measured against are the ones in `plan.md` §4: 20
bushels feed one person for a year, 1 bushel of seed sows 2 acres, one person
tends 10 acres, land costs 17-26 bushels per acre, each planted acre yields 1-5
bushels, the rats raid on 40% of the years, the plague roll strikes on 20% of the
draws, starving more than 45% of the city in one year ends the reign, and the
term lasts 10 years. `--agriculture` adds the farming technologies of the same
section: one node a year, paid out of the year's spare grain — what the store holds
once the food of the city and the seed of its fields are set aside. The tree holds
twenty-five nodes costing 250 to 52,890 bushels each, 263,450 bushels together; the
fields branch adds a bushel per planted acre at every rung, the seed branch lets a
bushel of seed sow 3, 4, 5, 6 and 7 acres, the store branch divides the rats' share
by 2, 3, 4, 5 and 6, the hands branch lets one person tend 12, 14, 16, 18 and 20
acres, and the capstone adds another bushel and leaves the rats a seventh.

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
| farmer (agriculture) | 500 | 282 | 218 | 165 | 30 | 53 | 252 |

| Policy | Mean years played | Mean year of a mid-term impeachment |
| --- | --- | --- |
| careful | 6.71 | 4.93 |
| trader | 4.32 | 4.22 |
| seller | 8.78 | 5.54 |
| starver | 1.00 | 1.00 |
| careful (agriculture) | 6.71 | 4.93 |
| farmer (agriculture) | 7.17 | 3.52 |

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

`--agriculture` puts the twenty-five farming technologies of `plan.md` §4 in play: one
node a year, paid out of the year's spare grain — what the store holds once the food
the people need and the seed the land needs have been set aside. The question opens
the year, so the budget is the store the opening report has just shown, and the crop
of the year is reported where it lands, so the grain a question quotes is grain the
granary has really held. Research never costs a random draw, so a term played with the
rule set on and every offer declined is the classic term bit for bit — and the batches
below show exactly that, then what the tree is worth to a ruler who pays for it.

The farmer of these measurements buys the most valuable node the year can afford, a
bushel per acre first, and spends nothing on research that the year does not leave
over. That discipline is now the rule of the game rather than a habit of the policy:
the engine prices the food of the city and the seed of its fields into the budget, so
no ruler — scripted or at the keyboard — can empty the granary for a cheaper plough.
Where the farmer still differs from a careless ruler is the ranking of what is on
offer, and that is why the farmer completes more terms than the careful ruler who
researches nothing at all.

| Batch | Games | Completed | Impeached mid-term | Fantastic | Mediocre | Tyrant | National fink |
| --- | --- | --- | --- | --- | --- | --- | --- |
| careful (agriculture) | 500 | 175 | 325 | 123 | 16 | 31 | 330 |
| farmer (agriculture) | 500 | 282 | 218 | 165 | 30 | 53 | 252 |
| farmer (agriculture, marathon) | 500 | 282 | 218 | 9 | 3 | 16 | 472 |

| Batch | Mean years played | Mean year of a mid-term impeachment |
| --- | --- | --- |
| careful (agriculture) | 6.71 | 4.93 |
| farmer (agriculture) | 7.17 | 3.52 |
| farmer (agriculture, marathon) | 57.93 | 3.52 |

### The arc of a whole tree

The table below reads the same 500-game marathon batch node by node: how many of the
games ever paid for a rung, and when. "Median year" is where half the games that
bought it had bought it.

| Node | Cost (bushels) | Games that bought it | Median year | Mean year |
| --- | --- | --- | --- | --- |
| Ox-drawn plough | 250 | 288 | 10 | 9.4 |
| Fallow fields | 310 | 342 | 2 | 2.1 |
| Granaries | 390 | 288 | 5 | 5.3 |
| Heavy plough | 490 | 282 | 12 | 11.6 |
| Green manuring | 610 | 291 | 3 | 3.2 |
| Draft teams | 760 | 282 | 13 | 13.1 |
| Sealed silos | 950 | 282 | 7 | 7.2 |
| Manured fields | 1190 | 282 | 4 | 4.4 |
| Row sowing | 1490 | 282 | 15 | 14.6 |
| Iron ploughshares | 1860 | 282 | 16 | 15.9 |
| Underground cellars | 2330 | 282 | 9 | 8.7 |
| Irrigated terraces | 2910 | 282 | 6 | 6.1 |
| Seed drill | 3640 | 282 | 17 | 17.1 |
| Harvest crews | 4540 | 282 | 18 | 18.3 |
| Temple vaults | 5680 | 282 | 11 | 10.9 |
| Crop rotation | 7100 | 282 | 9 | 9.9 |
| Garden seed | 8870 | 282 | 20 | 19.8 |
| Ox-driven threshers | 11090 | 282 | 22 | 21.8 |
| Undercrofts | 13870 | 282 | 15 | 16.3 |
| Royal gardens | 17330 | 282 | 24 | 21.8 |
| Water lifts | 21660 | 282 | 28 | 28.4 |
| Flood farming | 27080 | 282 | 31 | 31.6 |
| Irrigation canals | 33850 | 282 | 37 | 37.2 |
| Selected seed corn | 42310 | 282 | 43 | 42.8 |
| Nippur almanac | 52890 | 282 | 49 | 49.2 |

Of the 500 farmer games, 282 bought every rung; the median completion year is 49, the
mean 49.2 and the range 43-61. 158 games bought nothing at all, and 5,199 of the
7,131 rungs ever bought fell in the first twenty years of the batches.

- **The flag alone changes nothing.** The careful ruler who declines every offer
  plays the classic term exactly — the same 175 completed games, the same verdict
  counts, the same mean year of an impeachment — because research changes the
  figures the rules are handed, never the events the seed produces.
- **The cheap rungs pay for themselves quickly.** The farmer completes 282 terms
  where the careful ruler completes 175: the six opening rungs cost 2,810 bushels
  between them and give two bushels to every planted acre, half the rats' share and
  two more acres a person can tend, and the opening decade is long enough to earn all
  of that back. Research pays best when it is early and cheap.
- **The whole tree is the work of a reign.** The last five rungs cost 177,790 of the
  263,450 bushels and are paid for between the twenty-third and the sixty-first year
  of the plan: it is the ladder, not the shape of the tree, that sets the pace, and
  282 of the 500 marathons finish it.
- **The pace falls off on purpose.** 5,199 rungs are bought in the first twenty years
  of the batches, 1,400 in the next twenty and 531 in the third, and a single one
  after the sixtieth year: the cheap end of the ladder is climbed by everyone who
  survives, the costly end only by the rich.
- **A century is where it pays.** In the marathon the same farmer completes 282
  terms, against the single careful game of 500 that survives the same century: a
  raised harvest and granaries the rats cannot rob are what a growing city needs
  once the fixed 1000 acres stop feeding it.
- **The tree does not buy land.** 158 games never afford a rung, and of the 282 games
  that reach the end of the century 254 are still scored a national fink, because the
  verdict measures acres per person and a century of good harvests doubles the
  population while the original acres stand still. The tree is what pays for the
  acres a ruler must buy to keep the verdict, not a substitute for buying them.

## The health rule set

`--health` puts the twenty-five public-health measures of `plan.md` §4 in play: one
measure a year, paid out of the year's spare grain, at the same research moment the
farming tree uses. Like the farming tree, the rule set adds no random draw, so a
health game that declines every offer is the classic term bit for bit; the batches
below are the ones that build it.

The healer of these measurements is the careful ruler with two changes. It feeds the
city at the rate its measures allow, because the listing keeps no surplus for a year
in which everybody was fed; and it buys the measure that is worth most to a city
that must stay alive — fewer bushels for the same mouths first, then the people the
healers save, then the plagues the water branch keeps away, and last the children of
the nursery, which raise the demand for bread before they raise the supply. Like the
farmer, it never spends the grain the city needs — the engine sets the food aside for
both tables — and the food it sets aside is the food of the health in force, so every
measure that feeds a person out of fewer bushels widens the budget for the next one.
The *splitter* is that same farmer, offered both tables at once, taking the cheapest
rung of whichever one is on offer.

| Batch | Games | Completed | Impeached mid-term | Fantastic | Mediocre | Tyrant | National fink |
| --- | --- | --- | --- | --- | --- | --- | --- |
| healer (health, marathon) | 500 | 0 | 500 | 0 | 0 | 0 | 500 |
| split (agriculture + health, marathon) | 500 | 0 | 500 | 0 | 0 | 0 | 500 |

| Batch | Mean years played | Mean year of a mid-term impeachment |
| --- | --- | --- |
| healer (health, marathon) | 7.71 | 7.71 |
| split (agriculture + health, marathon) | 24.18 | 24.18 |

### How far a reign climbs the tree

The table below reads the healer batch measure by measure: how many of the 500 games
ever paid for a measure, and the mean and the median year they paid for it in.

| Measure | Cost | Games | Mean year | Median year |
| --- | --- | --- | --- | --- |
| Wells | 100 | 130 | 8.7 | 9 |
| Herb gatherers | 124 | 245 | 5.1 | 5 |
| Midwives | 153 | 48 | 13.4 | 14 |
| Milled grain | 190 | 342 | 2.1 | 2 |
| Drained streets | 235 | 87 | 10.8 | 11 |
| Physicians | 290 | 177 | 6.5 | 7 |
| Wet nurses | 359 | 23 | 16.1 | 16 |
| Kitchen gardens | 444 | 301 | 3.1 | 3 |
| Brick-lined drains | 550 | 56 | 12.8 | 13 |
| Apothecaries | 680 | 138 | 7.9 | 8 |
| Milk herds | 842 | 19 | 17.7 | 18 |
| Oil presses | 1041 | 250 | 4.3 | 4 |
| Aqueducts | 1288 | 37 | 14.6 | 14 |
| Doctors | 1594 | 90 | 9.9 | 10 |
| Birthing houses | 1972 | 10 | 19.1 | 19 |
| Fish ponds | 2440 | 135 | 6.3 | 5 |
| Healing houses | 3019 | 40 | 13.4 | 12 |
| Foundling home | 3736 | 4 | 24.2 | 23.5 |
| Smokehouses | 4623 | 25 | 12.6 | 9 |
| Temple hospital | 5720 | 0 | — | — |
| Palace nursery | 7078 | 0 | — | — |
| Breweries | 8758 | 0 | — | — |
| Children's gardens | 10836 | 0 | — | — |
| Date presses | 13408 | 0 | — | — |
| House of Life | 16590 | 0 | — | — |

Of the 500 healer games, 340 bought at least one measure and the median reign bought
three; the smokehouses, the nineteenth of the twenty-five measures, are the deepest
any of the 500 ever paid for, and only 24 games ever did. The second table is the
splitter's, read the same way, and it climbs much further because the harvest of the
farming tree keeps its city alive.

| Measure | Cost | Games | Mean year | Median year |
| --- | --- | --- | --- | --- |
| Wells | 100 | 289 | 9.0 | 10 |
| Herb gatherers | 124 | 284 | 11.4 | 12 |
| Midwives | 153 | 282 | 13.0 | 13 |
| Milled grain | 190 | 282 | 14.5 | 15 |
| Drained streets | 235 | 282 | 15.8 | 16 |
| Physicians | 290 | 282 | 17.2 | 17 |
| Wet nurses | 359 | 282 | 18.5 | 19 |
| Kitchen gardens | 444 | 282 | 19.7 | 20 |
| Brick-lined drains | 550 | 282 | 20.9 | 21 |
| Apothecaries | 680 | 281 | 22.1 | 22 |
| Milk herds | 842 | 280 | 23.3 | 23 |
| Oil presses | 1041 | 280 | 24.5 | 25 |
| Aqueducts | 1288 | 280 | 25.7 | 26 |
| Doctors | 1594 | 275 | 26.8 | 27 |
| Birthing houses | 1972 | 271 | 27.9 | 28 |
| Fish ponds | 2440 | 266 | 29.0 | 29 |
| Healing houses | 3019 | 261 | 30.1 | 30 |
| Foundling home | 3736 | 257 | 31.1 | 31 |
| Smokehouses | 4623 | 248 | 32.2 | 32 |
| Temple hospital | 5720 | 244 | 33.2 | 33 |
| Palace nursery | 7078 | 243 | 34.2 | 34 |
| Breweries | 8758 | 233 | 35.4 | 35 |
| Children's gardens | 10836 | 199 | 36.9 | 37 |
| Date presses | 13408 | 124 | 38.9 | 39 |
| House of Life | 16590 | 37 | 41.5 | 42 |

- **The health tree is not a way to live longer.** The healer's mean reign is 7.71
  years and it completes no century of 500: a city that only heals starves, because
  no measure of this tree touches a field. Handing a healer the whole tree from the
  first year does not save it either — even that city is impeached in the twelfth
  year on the median, against the eleventh of the careful ruler.
- **A measure cannot feed a city, and the cheap ones are all a short reign affords.**
  A typical healer spends its few years on the first rungs of the four branches —
  milled grain in 342 games, kitchen gardens in 301, herb gatherers in 245 — and the
  deep measures are never reached at all: the deepest one ever bought is the
  smokehouses, in 25 games of 500, and the capstone is out of reach of every healer.
- **The one research moment is the real price of a second programme.** The splitter
  buys 12.7 health measures for every 8.7 farming rungs (medians 18 and 12), because
  the cheap measures crowd out the cheap technologies that raise the harvest — and it
  completes no century either, dying in the twenty-fourth year on average where the
  farmer alone completes 282 of 500. It does reach the capstone now and then — 37 of
  the 500 games buy the House of Life — but a ruler who wants both programmes must
  still choose which of them will be late.
- **The plague is small change.** The water branch takes the plague from 20 years in
  a hundred to 5, and the healer branch saves four in ten of the stricken, but the
  batches show how little that decides: the careful ruler's cities die of hunger, not
  of plague — the healer's do too.
- **The food branch is the part that shows.** Milling, gardens, oil presses, fish
  ponds, smokehouses, breweries and date presses bring the bushels that feed a person
  from 20 to 13, and they are the measures most games buy. They are the only part of
  the tree the granary ever notices.

## How these notes stay honest

- `tests/test_simulation.py` replays every batch quoted above —
  `test_the_balancing_notes_describe_the_batch_they_quote` — and asserts the
  counts of each table row, so a change to a rule or to the engine fails the
  suite until this file is refreshed.
- The arc of the tree is replayed as well:
  `test_the_plan_of_the_tree_is_the_work_of_a_reign` plays the same 500 marathons,
  checks how many games buy every rung, the median completion year and the mean
  year of each node against the table above, so the claim that the whole
  programme is the work of a reign cannot quietly go stale.
- `tests/test_docs.py` checks every rule figure quoted above against the constant
  it documents, and every row of the `plan.md` §4 tree tables against the data in
  `tech.py` and `health.py`, so a changed constant cannot leave a stale number
  behind here or in `plan.md` and `README.md`.
- The arc of the health tree is replayed too:
  `test_the_health_tree_is_climbed_only_as_far_as_a_reign_allows` and
  `test_both_programmes_share_the_one_research_moment` play the same 500 marathons
  and check both tables rung by rung, and
  `test_the_health_tree_alone_cannot_keep_a_city_alive` pins the twelfth year the
  first bullet of that section quotes.
- To re-measure everything: replay the batches as shown at the top of this file,
  one policy at a time, and replace the tables above. A marathon batch is the
  same loop with `term_years=config.MARATHON_TERM_YEARS`, an agriculture batch adds
  `agriculture=True`, and a health batch adds `health=True`.
