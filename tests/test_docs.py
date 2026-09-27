"""The documents and the constants must not drift apart.

``docs/plan.md`` is the specification, ``README.md`` is what a player reads and
``docs/balancing.md`` records what the seeded batches actually do. Each of them
quotes numbers, and a quoted figure that no longer matches ``config.py`` is worse
than no figure at all, so every rule figure in those three files is compared with
the constant it documents here. Change a constant and this module fails until the
prose follows.

Documented *rates* (the 20% plague roll, the 40% rat roll) are compared with the
rate a seeded draw set actually produces, so the claim is checked against the
engine rather than restated.
"""

from __future__ import annotations

import re
from pathlib import Path

from hammurabi import __version__, config, health, rules, tech
from hammurabi.random_source import SeededRandom

ROOT = Path(__file__).resolve().parent.parent

#: Draws used to measure the documented event rates. Cheap and deterministic.
DRAWS = 10_000


def _document(*parts: str) -> str:
    """Return a document as one line of text, so a missing file fails loudly.

    Runs of whitespace are collapsed to single spaces: the checks below then
    survive re-wrapping a paragraph, which is the most common way these
    documents change.
    """
    text = ROOT.joinpath(*parts).read_text(encoding="utf-8")
    return re.sub(r"\s+", " ", text)


PLAN = _document("docs", "plan.md")
README = _document("README.md")
BALANCING = _document("docs", "balancing.md")

#: The plan as it is written, line by line: the tables are read from this copy, so
#: that a row cannot be assembled out of the cells of two neighbouring tables.
PLAN_SOURCE = ROOT.joinpath("docs", "plan.md").read_text(encoding="utf-8")


def _figures(text: str, pattern: str) -> list[tuple[int, ...]]:
    """Return the numbers captured by every match of ``pattern`` in ``text``.

    A one-group pattern yields one-element tuples, so the same helper serves a
    single figure and a whole table row.
    """
    found = re.findall(pattern, text)
    assert found, f"nothing in the document matches {pattern!r}"
    return [
        tuple(
            int(value) for value in (match if isinstance(match, tuple) else (match,))
        )
        for match in found
    ]


def _text_matches(text: str, pattern: str) -> list[str]:
    """Return what every match of the single-group ``pattern`` captures."""
    found = re.findall(pattern, text)
    assert found, f"nothing in the document matches {pattern!r}"
    return found


def _number(text: str, pattern: str) -> int:
    """Return the one number ``pattern`` captures exactly once in ``text``."""
    found = _figures(text, pattern)
    assert len(found) == 1 and len(found[0]) == 1, (
        f"{pattern!r} matches {found}, expected exactly one number"
    )
    return found[0][0]


def _money(text: str, pattern: str) -> int:
    """Return the thousands-separated figure ``pattern`` captures exactly once."""
    found = _text_matches(text, pattern)
    assert len(found) == 1, f"{pattern!r} matches {found}, expected exactly one"
    return int(found[0].replace(",", ""))


def _tree_rows(section: str) -> list[tuple[str, int, str, str]]:
    """Return the rows of one tree table of ``plan.md`` §4.

    ``section`` names the subsection as it is written in the heading, so the two
    trees of §4 cannot be confused with each other. A tree is the
    ``| Node | Cost (bushels) | Requires | Effect |`` table of that subsection. The
    table is read line by line, before the whitespace of the document is collapsed
    for the prose checks below: that way the cells of the other tables, which have
    two or three of them, cannot be mistaken for a row.
    """
    rows: list[tuple[str, int, str, str]] = []
    inside = False
    for line in PLAN_SOURCE.splitlines():
        if line.startswith("### "):
            inside = section in line
            continue
        if not inside or not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 4 and cells[1].isdigit():
            rows.append((cells[0], int(cells[1]), cells[2], cells[3]))
    assert rows, f"no tree table in the {section} subsection of the plan"
    return rows


def _observed_plague_rate(*, resistance: int = 0) -> float:
    """Share of the draws, in percent, in which the plague roll strikes."""
    rng = SeededRandom(seed=21)
    strikes = sum(
        rules.plague_strikes(rules.plague_roll(rng, resistance=resistance))
        for _ in range(DRAWS)
    )
    return 100 * strikes / DRAWS


def _observed_rat_rate() -> float:
    """Share of the draws, in percent, in which rats eat from a full store."""
    rng = SeededRandom(seed=22)
    raids = sum(rules.rats_eaten(rng, store=1000) > 0 for _ in range(DRAWS))
    return 100 * raids / DRAWS


def test_the_specification_quotes_the_constants_it_defines() -> None:
    """Every rule figure in ``plan.md`` §4 is the constant it describes."""
    assert _number(PLAN, r"\| Population \| (\d+) people") == config.START_POPULATION
    assert _number(PLAN, r"\| Grain in store \| (\d+) bushels") == config.START_BUSHELS
    assert _number(PLAN, r"\| Land owned \| (\d+) acres") == config.START_ACRES
    assert _number(PLAN, r"\| Term \| (\d+) years") == config.TERM_YEARS
    assert (
        _number(PLAN, r"\| Marathon term \| (\d+) years \|")
        == config.MARATHON_TERM_YEARS
    )
    assert (
        _number(PLAN, r"any\s+term from 1 to (\d+) years") == config.MAX_TERM_YEARS
    )
    assert (
        _number(PLAN, r"\| Immigrants in year 1 \| (\d+) \|")
        == config.START_IMMIGRANTS
    )
    assert (
        _number(PLAN, r"\| Rats ate in year 1 \| (\d+) bushels")
        == config.START_RATS_ATE
    )
    assert (
        _number(PLAN, r"\| Harvest yield in year 1 \| (\d+) bushels per acre")
        == config.START_YIELD_PER_ACRE
    )
    assert _number(PLAN, r"the population reaches (\d+)") == (
        config.START_POPULATION + config.START_IMMIGRANTS
    )

    assert _number(PLAN, r"which happens for (\d+)% of the years") == round(
        _observed_plague_rate()
    )
    assert _figures(PLAN, r"a random value of (\d+)[–-](\d+) bushels per acre") == [
        (config.LAND_PRICE_MIN, config.LAND_PRICE_MAX)
    ]
    assert _number(PLAN, r"each person needs (\d+) bushels") == (
        config.BUSHELS_PER_PERSON
    )
    assert _figures(PLAN, r"(\d+) bushel of seed sows (\d+) acres") == [
        (1, config.ACRES_PER_SEED_BUSHEL)
    ]
    assert _number(PLAN, r"1 person can tend (\d+)") == config.ACRES_PER_WORKER
    assert _number(PLAN, r"so at most `(\d+) \* population - 1` acres") == (
        config.ACRES_PER_WORKER
    )
    assert _figures(PLAN, r"each planted acre yields (\d+)[–-](\d+) bushels") == [
        (config.YIELD_MIN, config.YIELD_MAX)
    ]
    assert _number(PLAN, r"(\d+)% chance: rats eat") == round(_observed_rat_rate())
    assert _number(PLAN, r"starving more than (\d+)% of the population") == round(
        config.IMPEACHMENT_STARVATION_RATIO * 100
    )
    assert set(_text_matches(PLAN, r"after (\d+) rejected\s+answers")) == {
        str(config.MAX_ANSWER_ATTEMPTS)
    }
    assert _figures(PLAN, r"\| starved > (\d+)% or acres/person < (\d+) \|") == [
        (config.VERDICT_STARVATION_CRITICAL, config.VERDICT_ACRES_CRITICAL),
        (config.VERDICT_STARVATION_POOR, config.VERDICT_ACRES_POOR),
        (config.VERDICT_STARVATION_MEDIOCRE, config.VERDICT_ACRES_MEDIOCRE),
    ]


def test_the_specification_lists_every_node_of_the_tree() -> None:
    """Every node of :data:`hammurabi.tech.TECH_TREE` is in the ``plan.md`` table.

    The table is what the tree is written from, so the rows are compared with the
    data: the name, the price, the prerequisites and the effect the player reads
    have to match a node exactly, in tree order.
    """
    _assert_tree_table("Agriculture rule set", tech.FARMING)


def test_the_specification_lists_every_measure_of_the_health_tree() -> None:
    """Every measure of :data:`hammurabi.health.HEALTH_TREE` is in its own table."""
    _assert_tree_table("Health rule set", health.HEALTH)


def _assert_tree_table(section: str, tree: tech.TechTree) -> None:
    """Compare one ``plan.md`` tree table with the tree it documents."""
    rows = _tree_rows(section)
    assert [name for name, *_rest in rows] == [item.name for item in tree.nodes]
    by_name = {item.name: item for item in tree.nodes}
    for name, cost, requires, effect in rows:
        item = by_name[name]
        assert cost == item.cost, f"{name} costs {cost} in the table"
        assert effect == item.effect, f"{name} reads differently in the table"
        named = () if requires == "—" else tuple(requires.split(", "))
        missing = [need for need in named if need not in by_name]
        assert not missing, f"{missing} are not names of the {section} tree"
        assert {by_name[need].key for need in named} == set(item.requires), (
            f"{name} needs {requires} in the table"
        )


def test_the_specification_quotes_the_health_figures() -> None:
    """The prose of ``plan.md`` §4 names the constants the health tree is built on."""
    assert _number(PLAN, r"tree holds (\d+) measures") == health.HEALTH.size
    assert _money(PLAN, r"cost ([\d,]+) bushels between them") == sum(
        config.HEALTH_COSTS.values()
    )
    assert _number(PLAN, r"leave the plague (\d+) years in a hundred") == round(
        _observed_plague_rate(resistance=max(config.HEALTH_RESISTANCE.values()))
    )
    assert _number(PLAN, r"up to (\d+) children for every 1000 people") == max(
        config.HEALTH_BIRTHS_PER_THOUSAND.values()
    )
    assert _figures(PLAN, r"person for a year from (\d+) down to (\d+)") == [
        (
            config.BUSHELS_PER_PERSON,
            min(config.HEALTH_BUSHELS_PER_PERSON.values()),
        )
    ]
    # The survivor share is one ladder: every value from the classic half to the
    # House of Life's nineteen in twenty is reached by exactly one measure, and the
    # plan quotes each step of it.
    reached = {
        config.PLAGUE_SURVIVOR_PERCENT,
        *config.HEALTH_SURVIVOR_PERCENT.values(),
    }
    assert sorted(reached) == [config.PLAGUE_SURVIVOR_PERCENT, *range(60, 100, 5)], (
        "the ladder is the classic half and then every five"
    )
    quoted = {
        pair
        for item in health.HEALTH_TREE
        for pair in re.findall(r"plague survivors: (\d+)% -> (\d+)%", item.effect)
    }
    assert set(_text_matches(PLAN, r"plague survivors: (\d+)% -> (\d+)%")) == quoted


def test_the_specification_quotes_the_agriculture_figures() -> None:
    """The prose of ``plan.md`` §4 names the constants the tree is built from."""
    assert _number(PLAN, r"tree holds (\d+) nodes") == len(tech.TECH_TREE)
    assert _money(PLAN, r"together cost ([\d,]+) bushels") == sum(
        item.cost for item in tech.TECH_TREE
    )
    assert _number(PLAN, r"adds at most \+(\d+) bushels per planted acre") == (
        config.TECH_MAX_YIELD_BONUS
    )
    assert _figures(PLAN, r"by (\d+) with the") == [
        (divisor,) for divisor in config.TECH_RAT_DIVISOR.values()
    ]


def test_the_specification_documents_every_rule_set_flag() -> None:
    """§4 names a flag for every optional rule set, plus the master toggle."""
    for rule_set in config.RULE_SETS:
        assert f"--{rule_set}" in PLAN, rule_set
    assert "--all" in PLAN


def test_the_readme_quotes_the_same_rules() -> None:
    """The player-facing summary and the released version cannot disagree."""
    assert _text_matches(README, r"Project status:\*\* v(\d+\.\d+\.\d+)") == [
        __version__
    ]
    assert _number(README, r"the classic\s+(\d+)-year term") == config.TERM_YEARS
    assert (
        _number(README, r"a\s+(\d+)-year marathon") == config.MARATHON_TERM_YEARS
    )
    assert _number(README, r"(\d+) bushels feed one person") == (
        config.BUSHELS_PER_PERSON
    )
    assert _figures(README, r"(\d+) bushel of seed sows (\d+) acres") == [
        (1, config.ACRES_PER_SEED_BUSHEL)
    ]
    assert _number(README, r"one person can tend (\d+) acres") == (
        config.ACRES_PER_WORKER
    )
    assert _figures(README, r"Land costs (\d+)[–-](\d+) bushels per acre") == [
        (config.LAND_PRICE_MIN, config.LAND_PRICE_MAX)
    ]
    assert _number(README, r"starving more than (\d+)%") == round(
        config.IMPEACHMENT_STARVATION_RATIO * 100
    )
    assert _figures(
        README, r"at most (\d+)% starved per year on average, at least (\d+) acres"
    ) == [(config.VERDICT_STARVATION_MEDIOCRE, config.VERDICT_ACRES_MEDIOCRE)]
    assert _figures(README, r"at most (\d+)% starved, at least (\d+) acres") == [
        (config.VERDICT_STARVATION_POOR, config.VERDICT_ACRES_POOR),
        (config.VERDICT_STARVATION_CRITICAL, config.VERDICT_ACRES_CRITICAL),
    ]
    assert _number(README, r"[Tt]he (\d+) nodes of the tree") == len(tech.TECH_TREE)
    assert _number(README, r"cost from (\d+) bushels up") == (
        min(item.cost for item in tech.TECH_TREE)
    )
    assert _number(README, r"[Tt]he (\d+) measures of the health tree") == (
        health.HEALTH.size
    )
    assert "--agriculture" in README
    assert "--health" in README
    assert "--all" in README


def test_the_balancing_notes_quote_the_same_rules() -> None:
    """The measured notes restate the rules, so they must not fall behind them."""
    assert _number(BALANCING, r"(\d+)\s+bushels feed one person") == (
        config.BUSHELS_PER_PERSON
    )
    assert _figures(BALANCING, r"(\d+)\s+bushel of seed sows (\d+)\s+acres") == [
        (1, config.ACRES_PER_SEED_BUSHEL)
    ]
    assert _number(BALANCING, r"one person\s+tends (\d+) acres") == (
        config.ACRES_PER_WORKER
    )
    assert _figures(BALANCING, r"costs (\d+)[–-](\d+) bushels per acre") == [
        (config.LAND_PRICE_MIN, config.LAND_PRICE_MAX)
    ]
    assert _figures(BALANCING, r"yields (\d+)[–-](\d+)\s+bushels") == [
        (config.YIELD_MIN, config.YIELD_MAX)
    ]
    assert _number(BALANCING, r"the\s+term lasts (\d+) years") == config.TERM_YEARS
    assert (
        _number(BALANCING, r"the marathon term lasts (\d+) years")
        == config.MARATHON_TERM_YEARS
    )
    assert set(_text_matches(BALANCING, r"strikes on (\d+)% of the\s+draws")) == {
        str(round(_observed_plague_rate()))
    }
    assert set(_text_matches(BALANCING, r"raid on (\d+)% of the years")) == {
        str(round(_observed_rat_rate()))
    }
    assert _number(BALANCING, r"starving more than (\d+)% of the city") == round(
        config.IMPEACHMENT_STARVATION_RATIO * 100
    )
    assert _figures(
        BALANCING, r"with (\d+)\s+people \((\d+) residents plus (\d+) immigrants\)"
    ) == [
        (
            config.START_POPULATION + config.START_IMMIGRANTS,
            config.START_POPULATION,
            config.START_IMMIGRANTS,
        )
    ]
    assert _number(BALANCING, r"original (\d+) acres") == config.START_ACRES

