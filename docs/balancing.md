# Balancing notes

> What the game does when it is actually played. Every figure below comes from a
> seeded batch of whole games played through the policies in `tests/policies.py`,
> so each one can be reproduced exactly — the numbers are measurements, not
> targets, and no rule was tuned to produce them.

## How the figures were produced

Five hundred games per policy (seeds 0–499), played to their end by the engine
alone, with no terminal involved:

```python
from tests.policies import CarefulPolicy, play_game

for seed in range(500):
    game, policy = play_game(seed, CarefulPolicy)
    ...  # read game.state, policy.answers and policy.calls
```

Four policies keep the batch honest: one careful baseline ruler and three who
each change a single decision, so every branch of the engine is exercised.

| Policy | What it does |
| --- | --- |
| `CarefulPolicy` | never buys or sells land, feeds everybody the store can feed and sows as much as land, seed and labour allow |
| `TraderPolicy` | the same, but spends whatever is left after food and seed on land |
| `SellerPolicy` | the same, but sells 50 acres whenever an acre fetches 22 bushels or more, keeping at least one acre |
| `StarverPolicy` | feeds nobody at all, which ends the reign in the first year |

The rules the batches are measured against are the ones in `plan.md` §4: 20
bushels feed one person for a year, 1 bushel of seed sows 2 acres, one person
tends 10 acres, land costs 17-26 bushels per acre, each planted acre yields 1-5
bushels, the rats raid on 40% of the years, the plague roll strikes on 20% of the
draws, starving more than 45% of the city in one year ends the reign, and the
term lasts 10 years.

## How long a reign lasts

Five hundred games per policy. "Completed" means the ten years were played and
the term was scored; "impeached mid-term" means the reign ended inside a year.
The verdict columns count every game, so a policy's national-fink column is
larger than its mid-term impeachments by the few terms that were played to the
end and still scored as a national fink.

| Policy | Games | Completed | Impeached mid-term | Fantastic | Mediocre | Tyrant | National fink |
| --- | --- | --- | --- | --- | --- | --- | --- |
| careful | 500 | 175 | 325 | 123 | 16 | 31 | 330 |
| trader | 500 | 9 | 491 | 8 | 1 | 0 | 491 |
| seller | 500 | 363 | 137 | 139 | 50 | 98 | 213 |
| starver | 500 | 0 | 500 | 0 | 0 | 0 | 500 |

| Policy | Mean years played | Mean year of a mid-term impeachment |
| --- | --- | --- |
| careful | 6.71 | 4.93 |
| trader | 4.32 | 4.22 |
| seller | 8.78 | 5.54 |
| starver | 1.00 | 1.00 |

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

## How these notes stay honest

- `tests/test_simulation.py` replays the careful batch and asserts the counts in
  the first table, so a change to a rule or to the engine fails the suite until
  this file is refreshed.
- `tests/test_docs.py` checks every rule figure quoted above against the constant
  it documents, so a changed constant cannot leave a stale number behind here or
  in `plan.md` and `README.md`.
- To re-measure everything: replay the batch as shown at the top of this file,
  one policy at a time, and replace the tables above.
