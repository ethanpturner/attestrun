"""attestrun — bind an evaluation run's inputs and results, and re-derive the claim offline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from attestrun.evaluate import coverage, score_scenario
from attestrun.manifest import load, record, verify
from attestrun.verdict import Verdict

ROOT = Path(__file__).resolve().parent.parent.parent

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
    entries = _registry()
    failed = 0
    for entry in entries:
        result = score_scenario(ROOT / entry["path"], entry["slug"])
        if result.passed:
            print(f"ok    {entry['slug']}  ({entry['expects']})")
        else:
            failed += 1
            print(f"FAIL  {entry['slug']}")
            for problem in result.problems:
                print(f"        {problem}")

    # A verification tool that has only ever returned `verified` has not been tested.
    missing = coverage([e["expects"] for e in entries])
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
