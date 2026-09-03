# Project scope

**Document version:** 0.1
**Status:** Proposed
**Last updated:** 2026-09-03

## 1. Problem

Published AI-security results are not checkable. A paper or a README states that a defence blocks
some percentage of an attack set, and a reader has no way to re-derive the number: the corpus is
unversioned, the scaffolding is undescribed, the model is named but not pinned, and re-running costs
money and drifts when a provider moves a model behind a stable name.

The consequences are measured rather than asserted. Across forty agent-safety benchmarks there is no
ranking concordance — they reach contradictory conclusions about the same systems. Sector-average
disclosure sits around 40/100 on the Foundation Model Transparency Index, with no major developer
adequately disclosing train-test overlap. And the most consequential claims are the least
reproducible, which is the wrong way round.

UK AISI's Inspect is the closest thing to a reproducibility layer that exists. By its own
documentation it captures configuration for **re-execution**, not attestation: no content hashes, no
signing, and no provider-free replay.

## 2. What `attestrun` does

Takes a command that produces a result, and emits a manifest binding:

- every input file's content digest, resolved from a declared input set
- the exact command, its exit status, and its output digest
- the scope of the claim, as a field rather than an inference

`attestrun verify` recomputes the digests, optionally re-executes, and reports `verified`,
`contradicted`, or `unverifiable`.

## 3. Non-goals

Out of scope by decision, not by deferral.

- **It does not make a nondeterministic run deterministic.** It attests one run (DEC-005). A claim
  that re-running reproduces the result is stronger and different, and the manifest says which one
  it is making.
- **It does not sign** (DEC-006). Sigstore and the OpenSSF model-signing work solve signing, and a
  signature over contents that are not yet trustworthy attests the wrong thing.
- **It does not identify everything that could change a result** (DEC-007). Coverage is bounded by
  the declared input globs, and the tool says so.
- **It does not interpret the command's output.** Whether a result is *good* is the caller's
  question; whether it is *the recorded one* is this tool's.
- **It has no runtime dependencies**, and adding one requires an argument in the decision log. A
  verification tool that drags in a dependency tree is one nobody can audit.

## 4. Intended users

Someone publishing an evaluation result who wants a reader to be able to re-derive it, and the
reader on the other end.

## 5. Success condition

A reader with the repository and the manifest, and no credentials, can re-derive the claim or learn
precisely why they cannot. A run that reports `unverifiable` with its reason is a successful run.
