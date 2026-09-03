# 2026-09-03 — The check that was checking the machine

CI regenerated every scenario manifest and diffed the result against the committed one. It went red,
and the reason is worth writing down because the check was wrong in a way that reads as right.

A manifest records `environment` — `{python: 3.14.6, platform: Darwin}` — and `recorded_at`. Those
describe **where and when the run happened**. Everything else describes its subject: the command,
the input patterns, each input's digest, the result. Regenerating on a Linux runner and demanding a
byte-identical file was demanding that a record of a run not record where it ran.

The immediate cause was a fix I made earlier the same day. `recorded_at` moves on every rebuild, so
I preserved it — but only when everything else matched, `environment` included. On my machine
everything else did match, so the check passed. On the runner it did not, so the whole manifest was
re-recorded with the runner's environment and a fresh timestamp, and the diff was non-empty. The
failure mode is the one worth avoiding: a guard that is satisfied where it is written and fails
where it runs.

`--check` now compares the fields the tree and the command determine and leaves the other two alone.
Verified both directions: a moved input digest fails it, a manifest carrying `platform: Linux` does
not.

There is a small point of principle underneath. This project exists to say that an evaluation claim
should be re-derivable, and the temptation in a moment like this is to make the manifest reproducible
by stripping what varies. That would be the wrong repair — the environment is part of what the
manifest attests, and DEC-002's coverage bound already says that no input set is complete. The check
should ask whether the attested facts still hold, not whether two machines are the same machine.

## Open

Nothing new. The coverage bound is still what it was: `verify` states that its coverage is bounded by
what it was told to digest, and re-executes by default, because a stale bytecode cache once produced
different output from a clean tree with every digest matching.
