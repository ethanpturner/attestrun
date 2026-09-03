"""Record and verify, including the paths where a tool is tempted to report success."""

from __future__ import annotations

import json
from pathlib import Path

from attestrun.manifest import digest_file, load, record, verify
from attestrun.verdict import Verdict


def _project(tmp_path: Path) -> Path:
    (tmp_path / "benchmarks").mkdir()
    (tmp_path / "benchmarks" / "corpus.yaml").write_text("a: 1\n")
    return tmp_path


def test_record_then_verify_round_trips(tmp_path: Path) -> None:
    work = _project(tmp_path)
    manifest = record(work, "echo hello", ["benchmarks/**/*.yaml"], "it says hello")
    assert verify(manifest, work).overall is Verdict.VERIFIED


def test_moved_input_is_contradicted(tmp_path: Path) -> None:
    work = _project(tmp_path)
    manifest = record(work, "echo hello", ["benchmarks/**/*.yaml"], "c")
    (work / "benchmarks" / "corpus.yaml").write_text("a: 2\n")
    result = verify(manifest, work)
    assert result.overall is Verdict.CONTRADICTED
    assert any(c.verdict is Verdict.CONTRADICTED for c in result.inputs)


def test_missing_input_is_unverifiable_not_contradicted(tmp_path: Path) -> None:
    """Absence of the artifact is not evidence the recorded digest was wrong (DEC-004)."""
    work = _project(tmp_path)
    manifest = record(work, "echo hello", ["benchmarks/**/*.yaml"], "c")
    (work / "benchmarks" / "corpus.yaml").unlink()
    result = verify(manifest, work)
    assert result.overall is Verdict.UNVERIFIABLE
    assert all(c.verdict is not Verdict.CONTRADICTED for c in result.inputs)


def test_changed_output_is_contradicted_though_inputs_hold(tmp_path: Path) -> None:
    work = _project(tmp_path)
    manifest = record(work, "echo hello", ["benchmarks/**/*.yaml"], "c")
    manifest["command"] = "echo goodbye"
    assert verify(manifest, work).result_verdict is Verdict.CONTRADICTED


def test_no_rerun_never_reports_verified(tmp_path: Path) -> None:
    """Digest checking alone verifies less than it appears to (DEC-007)."""
    work = _project(tmp_path)
    manifest = record(work, "echo hello", ["benchmarks/**/*.yaml"], "c")
    assert verify(manifest, work, rerun=False).overall is Verdict.UNVERIFIABLE


def test_unreadable_file_digests_to_none_rather_than_a_placeholder(tmp_path: Path) -> None:
    assert digest_file(tmp_path / "absent") is None


def test_load_rejects_a_foreign_document(tmp_path: Path) -> None:
    path = tmp_path / "x.json"
    path.write_text(json.dumps({"format": "something-else"}))
    try:
        load(path)
    except ValueError as exc:
        assert "manifest" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("a foreign document was accepted")
