# Benchmarks

Layout and the coverage requirement are in `docs/architecture/evaluation-plan.md`.

The rule that matters: **every verdict must be produced by at least one scenario.** A verification
tool that has only ever returned `verified` has not been tested, and that is the most likely way
this project ships broken and looks fine.

`scenarios.yaml` is the authoritative list. A directory not registered there is not part of the set.
