# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

`attestrun` binds an evaluation run's inputs and results into a manifest and re-derives the claim
offline. The minimal implementation runs: `record` and `verify`, with a three-valued verdict.
Cryptographic signing is deferred (DEC-006).

Keep tense discipline: present indicative for what runs, "is designed to" for anything unbuilt.

## Binding constraints

- **The verdict vocabulary is defined here** (DEC-001) — `verified`, `contradicted`,
  `unverifiable` — and `whence` and `tearline` are intended to adopt it from this package rather
  than keep local copies.
- **Inputs bind by content digest, never by name** (DEC-002).
- **Verification works offline, with no credential** (DEC-003). A network interaction a run made is
  a recorded input like any other.
- **An unverifiable input never yields a passing verdict, and outranks `contradicted`** (DEC-004).
  Partial verification reported as success is the failure this project exists to prevent, arriving
  at the layer meant to prevent it.
- **A manifest attests one run, not the command's future behaviour** (DEC-005). Its scope is a
  field in the document, not something a reader must infer.
- **The input set is itself a claim** (DEC-007). Coverage is bounded by the declared globs, and the
  tool says so. Re-execution is the default; `--no-rerun` verifies less than it appears to.

## Working norms

- **mypy is strict.** The quality gate is `uv run ruff check . && uv run mypy && uv run pytest`.
- **No runtime dependencies.** A verification tool that drags in a dependency tree is a verification
  tool nobody can audit. Keep it that way, or argue for the exception in the decision log.
- **Test the negative paths before trusting a check.** Every guard here has a test that makes it
  fire; a checker that has only ever passed has not been tested.
- **Match the prose register**: flat declarative, no marketing language, no emoji, no second person.

## Relationship to sibling projects

One of four sharing a thesis: a security claim should be a checkable artifact rather than an
assertion. [`trace`](https://github.com/ethanpturner/trace) is where the distinction originates
(its DEC-009), [`whence`](https://github.com/ethanpturner/whence) applies it to model provenance,
[`tearline`](https://github.com/ethanpturner/tearline) to retrieval entitlements, and this to the
evaluation results the others produce.
