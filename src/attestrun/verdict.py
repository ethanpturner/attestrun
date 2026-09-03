"""The verdict vocabulary, defined here and adopted by consumers (DEC-001).

Three values, never a boolean, and never a score. A score collapses "not determined" onto the same
axis as "not true", and a consumer reading 0.0 cannot tell them apart.
"""

from __future__ import annotations

from enum import StrEnum


class Verdict(StrEnum):
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    UNVERIFIABLE = "unverifiable"

    @classmethod
    def combine(cls, verdicts: list[Verdict]) -> Verdict:
        """The weakest wins, and `unverifiable` outranks `contradicted` (DEC-004).

        An input that could not be read means the run was not fully checked, and reporting
        `contradicted` on the strength of the parts that were read asserts more than was
        established. Reporting `verified` asserts very much more.
        """
        if not verdicts:
            return cls.UNVERIFIABLE
        if cls.UNVERIFIABLE in verdicts:
            return cls.UNVERIFIABLE
        if cls.CONTRADICTED in verdicts:
            return cls.CONTRADICTED
        return cls.VERIFIED
