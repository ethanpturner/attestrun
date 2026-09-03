"""Generate the benchmark scenarios and record their manifests.

Run after changing a scenario's tree or command. The generated manifests are committed, because a
manifest recorded at scoring time would be trivially self-consistent and would measure nothing.

The tree is shaped so each mutation isolates one verdict. `runner.sh` and `extra.txt` sit OUTSIDE
the input globs on purpose: mutating `runner.sh` changes the command's behaviour while every input
digest still matches, which is the only way to exercise the result axis on its own.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

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


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from attestrun.manifest import record

    for slug, mutation in SCENARIOS.items():
        scenario = BENCH / slug
        tree = scenario / "tree"
        scenario.mkdir(parents=True, exist_ok=True)
        build_tree(tree)
        manifest = record(tree, "sh runner.sh", PATTERNS, f"the {slug} scenario's command ran.")
        (scenario / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (scenario / "mutate.sh").write_text(mutation)
        print(
            f"  {slug}: {len(manifest['inputs'])} inputs, exit {manifest['result']['exit_status']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
