"""The combination rule, which is where a verification tool quietly overclaims."""

from __future__ import annotations

from attestrun.verdict import Verdict


def test_all_verified_is_verified() -> None:
    assert Verdict.combine([Verdict.VERIFIED, Verdict.VERIFIED]) is Verdict.VERIFIED


def test_unverifiable_outranks_contradicted() -> None:
    """DEC-004. An input that could not be read means the run was not fully checked, so reporting
    `contradicted` on the strength of the parts that were read asserts more than was established."""
    assert Verdict.combine([Verdict.CONTRADICTED, Verdict.UNVERIFIABLE]) is Verdict.UNVERIFIABLE


def test_one_contradiction_defeats_many_verifications() -> None:
    assert Verdict.combine([Verdict.VERIFIED] * 99 + [Verdict.CONTRADICTED]) is Verdict.CONTRADICTED


def test_nothing_checked_is_not_a_pass() -> None:
    assert Verdict.combine([]) is Verdict.UNVERIFIABLE
