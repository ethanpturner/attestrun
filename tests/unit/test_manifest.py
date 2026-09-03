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


def test_changed_output_with_the_same_exit_status_is_unverifiable(tmp_path: Path) -> None:
    """Superseded by DEC-008. This test previously asserted `contradicted`, encoding the semantics
    that CI found to be wrong: an identical exit status with differing output does not establish
    the claim is false, and treating it as though it does reports every nondeterministic command
    -- which is most of them -- as a failed verification."""
    work = _project(tmp_path)
    manifest = record(work, "echo hello", ["benchmarks/**/*.yaml"], "c")
    manifest["command"] = "echo goodbye"
    assert verify(manifest, work).result_verdict is Verdict.UNVERIFIABLE


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


def test_nondeterministic_output_is_unverifiable_not_contradicted(tmp_path: Path) -> None:
    """DEC-008. Most real commands embed a duration, a temporary path, or an iteration order.
    Reporting a differing output as `contradicted` tells an operator that an unchanged, passing
    command failed verification -- which is how this decision was found, from this project's own CI
    recording `pytest` and then contradicting itself."""
    work = _project(tmp_path)
    manifest = record(work, "echo hello", ["benchmarks/**/*.yaml"], "c")
    manifest["result"]["output_sha256"] = "0" * 64  # same exit status, different output
    result = verify(manifest, work)
    assert result.result_verdict is Verdict.UNVERIFIABLE
    assert "not byte-reproducible" in result.result_detail


def test_a_changed_exit_status_still_contradicts(tmp_path: Path) -> None:
    """The exit status is the determinative signal: a command that succeeded and now fails is a
    changed result whatever its output says."""
    work = _project(tmp_path)
    manifest = record(work, "true", ["benchmarks/**/*.yaml"], "c")
    manifest["command"] = "false"
    assert verify(manifest, work).result_verdict is Verdict.CONTRADICTED
