"""attestrun — bind an evaluation run's inputs and results, and re-derive the claim offline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from attestrun.evaluate import coverage, score_scenario
from attestrun.manifest import load, record, verify
from attestrun.verdict import Verdict


def _repo_root() -> Path:
    """The checkout this package runs from.

    `parent.parent.parent` is the repository only for a source checkout; from a wheel in
    site-packages it points into the virtualenv, and `evaluate` -- a command the README documents --
    raised FileNotFoundError. Walk up for the marker instead.
    """
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "benchmarks" / "scenarios.yaml").exists():
            return candidate
    return Path.cwd()


ROOT = _repo_root()

DEFAULT_PATTERNS = ["benchmarks/**/*.yaml", "benchmarks/**/*.json", "src/**/*.py"]


def _cmd_record(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    manifest = record(
        workdir, args.command, args.input or DEFAULT_PATTERNS, args.claim or args.command
    )
    Path(args.out).write_text(json.dumps(manifest, indent=2) + "\n")
    unreadable = [i["path"] for i in manifest["inputs"] if i["sha256"] is None]
    print(f"recorded {len(manifest['inputs'])} inputs -> {args.out}")
    print(f"  exit status : {manifest['result']['exit_status']}")
    print(f"  output sha  : {manifest['result']['output_sha256'][:16]}")
    for path in unreadable:
        print(f"  unreadable  : {path}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    manifest = load(Path(args.manifest))
    result = verify(manifest, Path(args.workdir).resolve(), rerun=not args.no_rerun)
    counts = {v: 0 for v in Verdict}
    for check in result.inputs:
        counts[check.verdict] += 1
        if check.verdict is not Verdict.VERIFIED:
            print(f"  {check.verdict.value:13} {check.path}: {check.detail}")
    print(
        f"  inputs: {counts[Verdict.VERIFIED]} verified, "
        f"{counts[Verdict.CONTRADICTED]} contradicted, {counts[Verdict.UNVERIFIABLE]} unverifiable"
    )
    print(f"  result: {result.result_verdict.value} — {result.result_detail}")

    # DEC-007: coverage is bounded by the declared globs and the tool says so. The patterns were
    # recorded and never shown, leaving the most-argued decision in the log with no output surface:
    # a reader had to infer completeness rather than read the bound.
    patterns = manifest.get("input_patterns") or []
    shown = ", ".join(str(p) for p in patterns) if patterns else "(no patterns recorded)"
    print(f"\n  coverage is bounded by: {shown}")
    print("  anything outside those patterns was not examined")
    if scope := manifest.get("scope"):
        print(f"  scope: {scope}")

    print(f"\n{manifest.get('claim', '(no claim recorded)')}")
    print(f"  -> {result.overall.value}")
    return 0 if result.overall is Verdict.VERIFIED else 1


def _registry() -> list[dict[str, str]]:
    """The scenario registry, read without a YAML dependency (project-scope.md §3)."""
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in (ROOT / "benchmarks" / "scenarios.yaml").read_text().splitlines():
        stripped = raw.strip()
        if stripped.startswith("- slug:"):
            if current:
                entries.append(current)
            current = {"slug": stripped.split(":", 1)[1].strip()}
        elif current and stripped.startswith(("path:", "expects:")):
            key, _, value = stripped.partition(":")
            current[key] = value.strip()
    if current:
        entries.append(current)
    return entries


def _cmd_evaluate(args: argparse.Namespace) -> int:
    registry = ROOT / "benchmarks" / "scenarios.yaml"
    if not registry.exists():
        print(
            f"no scenario registry at {registry}. `attestrun evaluate` scores this project's own "
            f"corpus and needs a source checkout; it is not available from an installed package.",
            file=sys.stderr,
        )
        return 2

    entries = _registry()
    failed = 0
    observed: list[str] = []
    for entry in entries:
        result = score_scenario(ROOT / entry["path"], entry["slug"])
        observed.append(result.observed_overall)
        if not result.passed:
            # Report the scenario's own problems first. Otherwise a scenario that failed before
            # producing a verdict -- a failed mutation, say -- is reported as a registry
            # disagreement with an empty verdict, which names the wrong thing.
            failed += 1
            print(f"FAIL  {entry['slug']}")
            for problem in result.problems:
                print(f"        {problem}")
        elif result.observed_overall != entry.get("expects"):
            failed += 1
            print(
                f"FAIL  {entry['slug']}: the registry declares `expects: {entry.get('expects')}` "
                f"and the scenario produced `{result.observed_overall}`"
            )
        else:
            print(f"ok    {entry['slug']}  ({result.observed_overall})")

    # A verification tool that has only ever returned `verified` has not been tested. Scored from
    # the verdicts the tool ACTUALLY produced: scoring the registry's declared strings would check a
    # list of words in a YAML file against itself, which is the failure the evaluation plan names as
    # the most likely way this ships broken.
    missing = coverage(observed)
    if missing:
        failed += 1
        print(f"FAIL  coverage: no scenario produces {', '.join(missing)}")
    else:
        print(f"\n{len(entries)} scenarios; every verdict is produced by at least one.")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="attestrun", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", help="run a command and bind its inputs and result")
    rec.add_argument("--command", required=True)
    rec.add_argument("--workdir", default=".")
    rec.add_argument("--input", action="append", help="glob of inputs to digest (repeatable)")
    rec.add_argument("--claim", help="what this run is asserted to show")
    rec.add_argument("--out", default="run.json")
    rec.set_defaults(func=_cmd_record)

    ver = sub.add_parser("verify", help="re-derive a manifest's claim")
    ver.add_argument("manifest")
    ver.add_argument("--workdir", default=".")
    ver.add_argument("--no-rerun", action="store_true", help="check input digests only")
    ver.set_defaults(func=_cmd_verify)

    ev = sub.add_parser("evaluate", help="score every registered benchmark scenario")
    ev.set_defaults(func=_cmd_evaluate)

    args = parser.parse_args()
    return int(args.func(args))
