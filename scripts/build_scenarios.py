"""Generate the benchmark scenarios and record their manifests.

Run after changing a scenario's tree or command. The generated manifests are committed, because a
manifest recorded at scoring time would be trivially self-consistent and would measure nothing.

`--check` re-derives them and reports whether the committed ones still match, without writing. That
is what CI runs: a rebuild on a different machine legitimately produces a different `environment`
and `recorded_at`, and demanding that a committed manifest reproduce them would be demanding that a
record of a run not be a record of where and when it ran.

The tree is shaped so each mutation isolates one verdict. `runner.sh` and `extra.txt` sit OUTSIDE
the input globs on purpose: mutating `runner.sh` changes the command's behaviour while every input
digest still matches, which is the only way to exercise the result axis on its own.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks"
PATTERNS = ["data/**/*.txt"]

SCENARIOS: dict[str, str] = {
    "unchanged": "",
    "input-contents-changed": "printf 'edited\\n' > data/a.txt\n",
    "input-removed": "rm data/a.txt\n",
    "exit-status-changed": "printf 'echo run\\nexit 1\\n' > runner.sh\n",
    "output-changed": "printf 'echo different\\nexit 0\\n' > runner.sh\n",
    "change-outside-the-input-set": "printf 'edited\\n' > extra.txt\n",
    "removed-and-changed": "rm data/a.txt\nprintf 'edited\\n' > data/b.txt\n",
}


def build_tree(tree: Path) -> None:
    shutil.rmtree(tree, ignore_errors=True)
    (tree / "data").mkdir(parents=True)
    (tree / "data" / "a.txt").write_text("alpha\n")
    (tree / "data" / "b.txt").write_text("beta\n")
    # Outside the input globs: the command's behaviour can change with every input still matching.
    (tree / "runner.sh").write_text("echo run\nexit 0\n")
    (tree / "extra.txt").write_text("untracked by the input patterns\n")


#: Fields the scenario's tree and command determine. Everything else in a manifest describes the
#: run rather than its subject: `recorded_at` is when it happened and `environment` is where. Those
#: two are preserved from the committed file, which is why this check passes on a Linux runner for
#: manifests recorded on macOS -- and why a genuine drift in inputs or result still fails it.
ATTESTED_FIELDS = ("format", "scope", "claim", "command", "inputs", "input_patterns", "result")


def _attested(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: manifest.get(key) for key in ATTESTED_FIELDS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without writing; what CI runs",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT / "src"))
    from attestrun.manifest import record

    drifted: list[str] = []
    for slug, mutation in SCENARIOS.items():
        scenario = BENCH / slug
        tree = scenario / "tree"
        scenario.mkdir(parents=True, exist_ok=True)
        build_tree(tree)
        manifest = record(tree, "sh runner.sh", PATTERNS, f"the {slug} scenario's command ran.")

        # A rebuild moves `recorded_at` always and `environment` on a different machine. Letting
        # either move rewrites every manifest on every run, so a drift check would fail whether or
        # not anything about the scenario had actually changed -- and comparing them, as an earlier
        # version did, made the check pass on the author's machine and fail on the Linux runner for
        # a reason that had nothing to do with the corpus.
        path = scenario / "manifest.json"
        matches = False
        if path.exists():
            previous = json.loads(path.read_text())
            matches = _attested(manifest) == _attested(previous)
            if matches:
                manifest = previous

        if args.check:
            state = "ok" if matches else ("DRIFTED" if path.exists() else "MISSING")
            if not matches:
                drifted.append(slug)
            print(f"  {state:8} {slug}")
            continue

        path.write_text(json.dumps(manifest, indent=2) + "\n")
        (scenario / "mutate.sh").write_text(mutation)
        print(
            f"  {slug}: {len(manifest['inputs'])} inputs, exit {manifest['result']['exit_status']}"
        )

    if drifted:
        print(
            f"\n{len(drifted)} manifest(s) no longer match their tree: {', '.join(drifted)}.\n"
            "Re-run this script without --check to re-record them.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
