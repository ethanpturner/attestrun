# 2026-09-03 — An evaluation plan for the tool that checks evaluations

`attestrun` had a decision log and nothing else: no project scope, no data model, and no statement
of how anyone would know it worked. For a project in a portfolio arguing that claims should be
checkable, that was the gap that undercut it most.

## What the plan measures

Not accuracy. A verification tool's failure modes are asymmetric and only one is visible in use:

- **Missed detection** — `verified` for a run that changed. Invisible to whoever relies on it, which
  is what makes it the serious one.
- **False alarm** — `contradicted` for a run that is fine. Visible immediately, and the reason a
  tool stops being run. DEC-008 exists because this project shipped one.
- **False abstention** — `unverifiable` where the evidence settles it. Harmless, still a defect.

So the requirement is that each verdict is produced exactly when it should be, and the coverage
rule follows: **every verdict must be produced by at least one scenario.** A tool that has only ever
returned `verified` has not been tested.

## The tree shape did the work

`runner.sh` and `extra.txt` sit outside the `data/**/*.txt` input globs on purpose. Mutating
`runner.sh` changes what the command does while every input digest still matches, which is the only
way to exercise the result axis alone — without it, `exit-status-changed` and `output-changed` would
also trip an input contradiction and measure two things at once.

That took a couple of attempts to see. The first sketch put the runner inside the globs and every
result-axis scenario came back `contradicted` for the wrong reason.

## The scenario worth having

`change-outside-the-input-set` asserts a **pass** for a run whose behaviour changed, because the
change fell outside the declared globs. Every instinct says a benchmark should not enshrine a miss.

But it is not a miss. It is DEC-007's bound, which exists because no input set can be complete, and
writing it down as an expected `verified` is what stops it being quietly forgotten by someone later
"fixing" the tool to catch it. A bound nobody has pinned is a bound that erodes.

## Two things done deliberately

**Manifests are committed, not recorded at scoring time.** A manifest recorded against the tree it
is about to be checked against is trivially self-consistent and measures nothing.

**Mutations apply to a copy.** A scoring run that edited the committed trees would make the second
run measure something different from the first, and the failure would look like flakiness rather
than corpus damage. Pinned by a test that hashes every tree file before and after a full scoring
pass.

**No YAML dependency.** The scope document says this tool has no runtime dependencies, and pulling
in a parser so the corpus could be read would trade that for very little. The registry and expected
files use a subset a dozen lines can read, and the reader is documented as deliberate rather than
lazy.

## Open next

- The environment fingerprint remains an open question rather than a decision, for the reason
  recorded in DEC-007: it would have caught the stale-bytecode case, it grows without bound, and
  most of it does not affect most results.
