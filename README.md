# attestrun

**Status: minimal implementation runs.** `attestrun` binds an evaluation run's inputs and results
into a signed-shaped manifest and re-derives the claim from it offline. Cryptographic signing is
deferred (DEC-006).

```
uv run attestrun evaluate                       # every benchmark scenario, offline
uv run attestrun record --command "uv run pytest -q" --out run.json
uv run attestrun verify run.json
```

The record example deliberately uses a command that exists in this repository. An earlier version
attested `whence evaluate` against a sibling checkout, which reports `exit status : 127` when the
sibling is absent or not on `PATH` — success-shaped output for a command that never ran. Attesting
a sibling is a real use (this project's CI does it), and it needs the sibling present and the
command runnable there.

## The problem

Published AI-security results are not checkable. A paper or a README says a defense blocks 91% of
some attack set, and a reader has no way to re-derive that number: the corpus is unversioned, the
scaffolding is undescribed, the model is named but not pinned, and re-running costs money and drifts
when a provider moves a model behind a name.

The consequences are measured. Across forty agent-safety benchmarks there is **no ranking
concordance** — they reach contradictory conclusions about the same systems. The Foundation Model
Transparency Index puts sector-average disclosure at 40/100, with no major developer adequately
disclosing train-test overlap. And the most consequential claims are the least reproducible, which
is the wrong way round.

UK AISI's Inspect is the closest thing to a reproducibility layer that exists, and by its own
documentation it captures configuration for **re-execution**, not attestation: no content hashes, no
signing, and no provider-free replay.

## What it does

Takes a command that produces an evaluation result, and emits a **run manifest** binding:

- every input file's content digest, resolved from a declared input set
- the exact command, its exit status, and its output
- the interpreter version and platform, recorded as advisory context and never compared
- a claim — what the run is asserted to show

`attestrun verify` re-executes against the same digests and reports `verified`, `contradicted`, or
`unverifiable`. An input that has moved is `contradicted`. An input that cannot be read is
`unverifiable` — never a pass.

## Recording a command that has a first run

Record against a **warm** environment. Many commands print setup output the first time and nothing
afterwards — `uv run` announces "Installed N packages" on its first invocation in a project — so a
manifest recorded on the first run captures noise the verifying run cannot reproduce, and the result
axis comes back `unverifiable` for a command that is perfectly deterministic once warm.

The tool is right to report that: the outputs genuinely differ. The recording was of the wrong
thing. Run the command once, then record.

## What it does not do

It does not make a non-deterministic run deterministic. It attests **this run**, with these inputs,
producing this result. A claim that the same command will produce the same result tomorrow is a
different and much stronger claim, and the manifest says which one it is making (DEC-005).

## How it is evaluated

Seven scenarios — five mutation classes plus an unmutated baseline and the bound below — and a
coverage rule: **every verdict must be produced by
at least one of them**. A verification tool that has only ever returned `verified` has not been
tested, and that is the most likely way this project ships broken and looks fine.

The scenario worth reading is `change-outside-the-input-set`, which asserts a **pass** for a run
whose behaviour changed — because the change fell outside the declared input globs. That is not a
defect. It is the bound DEC-007 states, pinned so it cannot be quietly forgotten.

## Lineage

The three-valued verdict is defined here for this project's own output; `whence` and [`tearline`](https://github.com/ethanpturner/tearline) are its
first intended consumers. All three descend from
[`trace`](https://github.com/ethanpturner/trace)'s DEC-009: a finding means evidence supports a
weakness, a documentation gap means it could not be determined whether a control exists, and
collapsing the two is the failure the work exists to avoid.
