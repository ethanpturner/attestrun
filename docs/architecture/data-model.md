# Data model

**Document version:** 0.1
**Status:** Proposed
**Last updated:** 2026-09-03

Authoritative for the manifest format. The format is versioned by its `format` field; a document
carrying an unknown value is refused rather than parsed optimistically.

## 1. Manifest

`format: attestrun/1`

| Field | Type | Required | Notes |
|---|---|---|---|
| `format` | str | yes | `attestrun/1`. A foreign value is refused at load; no other field is validated there, so a manifest missing `command` or `result` raises rather than being refused cleanly. |
| `recorded_at` | str | yes | UTC, second precision. |
| `scope` | str | yes | What the manifest claims, in prose (DEC-005). Present so a reader need not infer the strength of the claim. |
| `claim` | str | yes | What the run is asserted to show. Author-supplied. |
| `command` | str | yes | Executed verbatim on verification. |
| `environment` | object | yes | `python`, `platform`. Advisory: recorded for a reader, never compared (DEC-007). |
| `input_patterns` | list[str] | yes | The globs inputs were collected from. **Coverage is bounded by this** and the verifier says so. |
| `inputs` | list[`Input`] | yes | |
| `result` | `Result` | yes | |

## 2. `Input`

| Field | Type | Required | Notes |
|---|---|---|---|
| `path` | str | yes | Relative to the working directory. |
| `sha256` | str \| null | yes | `null` when the file could not be read at record time — never a placeholder digest. |
| `size` | int | yes | Recorded for a reader. Not used as a pre-check and not compared. |

## 3. `Result`

| Field | Type | Required | Notes |
|---|---|---|---|
| `exit_status` | int | yes | **The determinative signal** on re-execution (DEC-008). |
| `output_sha256` | str | yes | Advisory on re-execution: a difference with an identical exit status is `unverifiable`, not `contradicted`. |
| `output` | str | yes | Retained so a reader can see what was recorded. |

## 4. Verdicts

`verified`, `contradicted`, `unverifiable` (DEC-001). Combination follows one rule: **the weakest
wins, and `unverifiable` outranks `contradicted`** (DEC-004).

| Situation | Verdict |
|---|---|
| Input digest matches | `verified` |
| Input digest differs | `contradicted` |
| Input unreadable | `unverifiable` |
| Re-execution: exit status differs | `contradicted` |
| Re-execution: same status, output differs | `unverifiable` (DEC-008) |
| Re-execution skipped (`--no-rerun`) | `unverifiable` |

## 5. Rules that are not fields

- **An absent digest is `null`, never a placeholder.** A synthetic value would compare unequal and
  report `contradicted` for a file that was simply unreadable.
- **`environment` is recorded and never compared.** It is advisory context; comparing it would make
  every manifest fail on a different interpreter patch release, and DEC-007 states the limit rather
  than pretending to close it.
- **The verifier reports what it checked**, including the input patterns and the scope, so a reader
  can see the bound on coverage rather than inferring completeness.
- **Verification re-globs `input_patterns`.** A file added after recording that the declared globs
  cover is `contradicted`. Iterating only the recorded list would bound coverage by the files that
  existed at record time, which is narrower than the bound DEC-007 states.
- **A manifest with no inputs is `unverifiable`.** An empty digest chain is not a pass, and an
  unmatched glob — what a typo in `--input` produces — must not verify.
- **A `null` digest is `unverifiable`, never `contradicted`.** Nothing was digested, so nothing can
  disagree.
