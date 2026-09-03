# Evaluation plan

**Document version:** 0.1
**Status:** Proposed
**Last updated:** 2026-09-03

## 1. What is being measured

A verification tool's failure modes are asymmetric, and only one of them is visible in normal use.

**Missed detection** — reporting `verified` for a run whose inputs or result have changed. Invisible
to the person relying on it, which is what makes it the serious one.

**False alarm** — reporting `contradicted` for a run that is fine. Visible immediately, and the
reason a tool stops being run. DEC-008 exists because this project shipped one.

**False abstention** — reporting `unverifiable` where the evidence in fact settles the question.
Not harmful, and still a defect: it makes the tool useless without being wrong.

So the measurement is not accuracy. It is **that each of the three verdicts is produced exactly when
it should be**, which means every scenario names the verdict it expects and every verdict has at
least one scenario producing it.

## 2. Scenario layout

```
benchmarks/<slug>/
  tree/            the working directory the manifest was recorded against
  manifest.json    the recorded manifest
  mutate.sh        what to do to the tree before verifying; absent means verify as-is
  expected.yaml    the expected verdict, per input and overall
  scenario.md      what it measures and why the near-misses are near
```

`expected.yaml` is never read by the tool, only by the scorer.

## 3. Coverage requirement

**Every verdict must be produced by at least one scenario, and every mutation class by at least
one.** A verification tool that has only ever returned `verified` has not been tested; that is the
single most likely way this project could ship broken and look fine.

| Mutation | Expected |
|---|---|
| nothing | `verified` |
| an input's contents change | `contradicted` |
| an input is removed | `unverifiable` (DEC-004) |
| the command's exit status changes | `contradicted` |
| the command's output changes, exit status unchanged | `unverifiable` (DEC-008) |
| something changes that no input glob covers | `verified` — **the tool's own limit** (DEC-007) |
| one input removed and another changed | `unverifiable` — precedence (DEC-004) |

The sixth row is the important one. It asserts that the tool reports a **pass** for a run whose
behaviour changed, because the change was outside the declared input set. That is not a defect to be
fixed; it is the bound DEC-007 states, and a scenario that pins it stops the bound from being
quietly forgotten.

## 4. What is not measured

- Whether a claim is *true*. The tool checks that a result is the recorded one, not that the result
  means what its author says.
- Performance.
- Whether the input set is *well chosen*. No tool can decide that (DEC-007); the scenarios can only
  demonstrate what follows when it is not.

## 5. Divergence handling

When a run disagrees with a scenario, classify before editing:

1. **Tool defect** — fix the tool.
2. **Scenario defect** — fix the expectation, and record why.
3. **The bound moved** — a decision changed what the correct verdict is. Requires a decision-log
   entry, not an edit. DEC-008 is the worked example: a scenario asserting `contradicted` for
   changed output became wrong when the decision changed, and the test was updated *with a note*
   rather than silently.

**A run's output is never an argument for changing an expectation.**
