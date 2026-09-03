"""Every registered scenario, scored against its committed expectation."""

from __future__ import annotations

from pathlib import Path

import pytest

from attestrun import _registry
from attestrun.evaluate import coverage, score_scenario
from attestrun.verdict import Verdict

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = _registry()


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["slug"] for e in ENTRIES])
def test_scenario(entry: dict[str, str]) -> None:
    result = score_scenario(ROOT / entry["path"], entry["slug"])
    assert result.passed, result.problems


def test_every_verdict_is_produced_by_some_scenario() -> None:
    """A verification tool that has only ever returned `verified` has not been tested. This is the
    single most likely way this project ships broken and looks fine (evaluation-plan.md §3)."""
    assert not coverage([e["expects"] for e in ENTRIES])
    assert {v.value for v in Verdict} <= {e["expects"] for e in ENTRIES}


def test_scoring_does_not_modify_the_corpus() -> None:
    """Mutations are applied to a copy. A scoring run that edited the committed trees would make
    the second run measure something different from the first."""
    before = {
        p: p.read_bytes()
        for entry in ENTRIES
        for p in (ROOT / entry["path"] / "tree").rglob("*")
        if p.is_file()
    }
    for entry in ENTRIES:
        score_scenario(ROOT / entry["path"], entry["slug"])
    assert {p: p.read_bytes() for p in before} == before
