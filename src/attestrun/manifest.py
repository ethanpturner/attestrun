"""Building and verifying run manifests."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from attestrun.verdict import Verdict

FORMAT = "attestrun/1"


def digest_file(path: Path) -> str | None:
    """SHA-256 of a file's bytes. `None` when it cannot be read -- never a placeholder."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def collect_inputs(workdir: Path, patterns: list[str]) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for pattern in patterns:
        for path in sorted(workdir.glob(pattern)):
            if not path.is_file():
                continue
            inputs.append(
                {
                    "path": str(path.relative_to(workdir)),
                    "sha256": digest_file(path),
                    "size": path.stat().st_size,
                }
            )
    return inputs


@dataclass
class InputCheck:
    path: str
    verdict: Verdict
    detail: str


@dataclass
class Verification:
    manifest_path: str
    inputs: list[InputCheck] = field(default_factory=list)
    result_verdict: Verdict = Verdict.UNVERIFIABLE
    result_detail: str = ""

    @property
    def overall(self) -> Verdict:
        return Verdict.combine([c.verdict for c in self.inputs] + [self.result_verdict])


def record(workdir: Path, command: str, patterns: list[str], claim: str) -> dict[str, Any]:
    # check=False: a non-zero exit is part of what the manifest records, not an error to raise on.
    completed = subprocess.run(
        command, cwd=workdir, shell=True, capture_output=True, text=True, check=False
    )
    output = completed.stdout + completed.stderr
    return {
        "format": FORMAT,
        "recorded_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # DEC-005: the scope of the claim is a field, not something a reader must infer.
        "scope": (
            "This manifest attests that the recorded command, over inputs with the recorded "
            "digests, produced the recorded result. It does not claim that re-running will "
            "reproduce it."
        ),
        "claim": claim,
        "command": command,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.system(),
        },
        "inputs": collect_inputs(workdir, patterns),
        "input_patterns": patterns,
        "result": {
            "exit_status": completed.returncode,
            "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
            "output": output,
        },
    }


def verify(manifest: dict[str, Any], workdir: Path, *, rerun: bool = True) -> Verification:
    result = Verification(manifest_path=str(workdir))

    for entry in manifest.get("inputs") or []:
        path = workdir / str(entry["path"])
        actual = digest_file(path)
        if actual is None:
            # DEC-004: unreadable is not evidence the claim is false.
            result.inputs.append(
                InputCheck(entry["path"], Verdict.UNVERIFIABLE, "input could not be read")
            )
        elif actual != entry["sha256"]:
            result.inputs.append(
                InputCheck(
                    entry["path"],
                    Verdict.CONTRADICTED,
                    f"contents moved: {actual[:12]} != {str(entry['sha256'])[:12]}",
                )
            )
        else:
            result.inputs.append(InputCheck(entry["path"], Verdict.VERIFIED, "digest matches"))

    if not rerun:
        result.result_verdict = Verdict.UNVERIFIABLE
        result.result_detail = "re-execution skipped; inputs checked only"
        return result

    completed = subprocess.run(
        manifest["command"], cwd=workdir, shell=True, capture_output=True, text=True, check=False
    )
    output = completed.stdout + completed.stderr
    actual = hashlib.sha256(output.encode()).hexdigest()
    expected = manifest["result"]["output_sha256"]
    if completed.returncode != manifest["result"]["exit_status"]:
        result.result_verdict = Verdict.CONTRADICTED
        result.result_detail = (
            f"exit status {completed.returncode} != {manifest['result']['exit_status']}"
        )
    elif actual != expected:
        result.result_verdict = Verdict.CONTRADICTED
        result.result_detail = f"output digest {actual[:12]} != {str(expected)[:12]}"
    else:
        result.result_verdict = Verdict.VERIFIED
        result.result_detail = "command re-executed and produced identical output"
    return result


def load(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text())
    if data.get("format") != FORMAT:
        raise ValueError(f"{path} is not an {FORMAT} manifest")
    return data
