"""Score the benchmark scenarios.

Each scenario is a recorded manifest plus a mutation. The mutation is applied to a **copy** of the
committed tree, so a scoring run never modifies the corpus and a failed run leaves nothing behind.

The manifests are committed rather than recorded at scoring time: a manifest recorded against the
tree it is about to be checked against is trivially self-consistent and measures nothing.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from attestrun.manifest import load, verify
from attestrun.verdict import Verdict


@dataclass
class ScenarioScore:
    slug: str
    problems: list[str] = field(default_factory=list)
    #: The verdict the tool actually produced. Coverage is scored from this rather than from the
    #: registry's declared string, which would check a YAML file against itself.
    observed_overall: str = ""

    @property
    def passed(self) -> bool:
        return not self.problems


def _expected(path: Path) -> dict[str, Any]:
    """A three-line reader for the subset of YAML these files use.

    Deliberately not a dependency: `project-scope.md` §3 says this tool has no runtime dependencies,
    and pulling in a parser so the test corpus can be read would trade that for very little.
    """
    out: dict[str, Any] = {"inputs": {}}
    section = None
    for raw in path.read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  ") and section == "inputs":
            key, _, value = raw.strip().partition(":")
            out["inputs"][key] = [
                v.strip() for v in value.strip().strip("[]").split(",") if v.strip()
            ]
            continue
        key, _, value = raw.partition(":")
        section = key.strip()
        if section in {"overall", "result"}:
            out[section] = value.strip()
        elif section != "inputs":
            section = None
    return out


def score_scenario(scenario: Path, slug: str) -> ScenarioScore:
    result = ScenarioScore(slug=slug)
    expected = _expected(scenario / "expected.yaml")
    manifest = load(scenario / "manifest.json")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "tree"
        shutil.copytree(scenario / "tree", work)
        mutation_file = scenario / "mutate.sh"
        # evaluation-plan.md documents an absent mutate.sh as "verify as-is"; an unconditional
        # read_text raised FileNotFoundError instead, so the documented affordance never worked.
        mutation = mutation_file.read_text().strip() if mutation_file.exists() else ""
        if mutation:
            completed = subprocess.run(
                mutation, cwd=work, shell=True, check=False, capture_output=True, text=True
            )
            if completed.returncode != 0:
                # check=True raised straight out of score_scenario, past the per-scenario
                # reporting, so one bad mutation killed the whole run and the operator saw a
                # traceback rather than which scenario failed and why.
                result.problems.append(
                    f"mutation failed (exit {completed.returncode}): "
                    f"{(completed.stderr or completed.stdout).strip()[:200]}"
                )
                return result
        actual = verify(manifest, work)

    result.observed_overall = actual.overall.value
    if actual.overall.value != expected.get("overall"):
        result.problems.append(f"overall {actual.overall.value} != {expected.get('overall')}")
    if "result" in expected and actual.result_verdict.value != expected["result"]:
        result.problems.append(f"result axis {actual.result_verdict.value} != {expected['result']}")
    by_verdict: dict[str, list[str]] = {}
    for check in actual.inputs:
        by_verdict.setdefault(check.verdict.value, []).append(check.path)
    for verdict, paths in expected["inputs"].items():
        if sorted(by_verdict.get(verdict, [])) != sorted(paths):
            result.problems.append(
                f"inputs {verdict}: {sorted(by_verdict.get(verdict, []))} != {sorted(paths)}"
            )
    return result


def coverage(expectations: list[str]) -> list[str]:
    """Every verdict must be produced by at least one scenario (evaluation-plan.md §3)."""
    missing = {v.value for v in Verdict} - set(expectations)
    return sorted(missing)
