# 2026-09-03 — attestrun, and a limitation it found in itself on first use

Last of the four. Scaffolded and implemented in one session, because the design questions had
already been answered by the three projects that needed it.

## Why now and not earlier

I argued twice against building this: an attestation layer with nothing to attest is a schema. That
held until `whence` phase one landed. `whence evaluate` now produces a real result — five scenarios
scored against authored truth sets, offline, no credential — which is exactly the kind of claim that
currently gets published as a number in a README and cannot be re-derived by a reader.

So the first thing this tool ever attested was a real run of a sibling project, not a fixture.

## The extraction, done properly this time

DEC-001 moves the verdict vocabulary here. I had earlier claimed it was hand-implemented three times
and that extraction was overdue; checking found it was *declared* three times and implemented once,
and I corrected that rather than let the overstatement justify the work.

It is extracted now for a better reason than duplication: this project's entire output is verdicts
about other projects' runs, so the definition belongs with the thing that produces them.

## What the first real use found

The negative tests were meant to confirm three guards. They confirmed those, and then produced
something I did not plan.

While reverting a deliberate change to `whence`, a stale `__pycache__` entry survived `git
checkout`. The source file was correct. `git status` was clean. `git diff` was empty. Every attested
digest matched. **And the command produced different output.** The edit was one character — `ok` to
`OK` — so the byte length was identical and the bytecode never invalidated.

Had verification skipped re-execution, the manifest would have reported `verified` for a run whose
behaviour had changed, with every digest correct. The thing that changed was not an input.

That is not a bug. No input set can be complete: a result depends on interpreters, caches,
environment and clocks that no glob enumerates. It is a limit, and DEC-007 states it — the input set
is itself a claim, coverage is bounded by the declared globs, and the tool says so rather than
implying it identified everything that matters.

It also settled a default. Re-execution is on unless `--no-rerun` is passed, because digest checking
alone verifies considerably less than it appears to. A tool built to correct overclaiming is the
last place that should inherit it.

## The verdict precedence is the load-bearing detail

`unverifiable` outranks `contradicted`. An input that could not be read means the run was not fully
checked, so reporting `contradicted` on the strength of the parts that *were* read asserts more than
was established — and reporting `verified` asserts very much more.

Tested directly: one missing input plus one moved input yields `unverifiable`, not `contradicted`.
Both facts appear in the per-input lines; only the weaker one propagates.

## Deliberately not built

Signing (DEC-006). Sigstore and the OpenSSF model-signing work already solve it, and a signature
over a manifest whose contents are not yet trustworthy attests the wrong thing — it proves who
emitted a claim, not that the claim holds. The digest chain is the part nobody ships. A signature
over a verified chain is worth adding; over an unverified one it is theatre.

## Open next

- Have `whence` and `tearline` adopt `Verdict` from this package rather than keeping local copies.
- An environment fingerprint as an advisory section. It would have caught the bytecode case, and it
  grows without bound, and most of it does not affect most results — which is why it is an open
  question rather than a decision.
- Repeated recordings compared to produce a stability figure. That is a genuinely stronger claim
  than DEC-005 supports and needs its own design.
