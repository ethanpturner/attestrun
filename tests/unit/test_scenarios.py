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


def test_coverage_is_scored_from_observed_verdicts() -> None:
    """The registry's `expects` is a declared string; scoring coverage from it would check a YAML
    file against itself, which the evaluation plan names as the likeliest way this ships broken."""
    for entry in ENTRIES:
        result = score_scenario(ROOT / entry["path"], entry["slug"])
        assert result.observed_overall == entry["expects"], (
            f"{entry['slug']}: registry says {entry['expects']}, tool produced "
            f"{result.observed_overall}"
        )


def test_a_failing_mutation_is_a_scenario_failure_not_a_crash(tmp_path: Path) -> None:
    """check=True raised past the per-scenario reporting, so one bad mutation killed the run and
    the operator saw a traceback instead of which scenario failed."""
    import shutil

    source = ROOT / str(ENTRIES[0]["path"])
    scenario = tmp_path / "s"
    shutil.copytree(source, scenario)
    (scenario / "mutate.sh").write_text("exit 3\n")
    result = score_scenario(scenario, "broken")
    assert not result.passed
    assert any("mutation failed" in p for p in result.problems)
