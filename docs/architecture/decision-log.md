# Decision log

**Document version:** 0.1
**Status:** Proposed
**Last updated:** 2026-09-03

Every entry is Accepted or Rejected. Numbering is local to this repository.

---

## DEC-001 — The verdict vocabulary is adopted, not reinvented

**Date:** 2026-09-03
**Status:** Accepted

**Decision.** `verified`, `contradicted`, `unverifiable`, with the same meanings `whence` gives
them. This repository is where the vocabulary is now defined, and `whence` and `tearline` are
intended to adopt it from here rather than keep local copies.

**Why.** It was declared in three places before this one and implemented in code once. That is a
shared vocabulary rather than duplication, and factoring it out earlier would have been abstraction
ahead of use. It is extracted now because there is a third consumer and, more importantly, because
this project's entire output is verdicts about other projects' runs — the definition belongs with
the thing that produces them.

**Tradeoffs.** `whence` and `tearline` acquire a dependency on this package. That is acceptable only
while this package stays small and has no dependencies of its own worth arguing about.

---

## DEC-002 — A manifest binds inputs by content digest, never by name

**Date:** 2026-09-03
**Status:** Accepted

**Decision.** Every input is recorded as a path *and* a SHA-256 of its contents. Verification
recomputes the digests. A path that no longer resolves is `unverifiable`; one whose contents have
moved is `contradicted`.

**Why.** A filename is a claim about the present. This is `whence`'s DEC-002 applied to evaluation
inputs, and for the same reason: a manifest recording that a run used `corpus/scenarios.yaml`
asserts nothing, because the file it names can change underneath the claim without any signal.

**Tradeoffs.** Manifests are verbose and churn whenever an input changes. Correct — an input
changing is exactly the event that should invalidate a claim.

---

## DEC-003 — Replay must not require the network or a credential

**Date:** 2026-09-03
**Status:** Accepted

**Decision.** A manifest is verifiable offline. If a run reached a network service, the recording of
that interaction is an input like any other and is digested with the rest.

**Why.** Re-execution against a live provider is not verification: it costs money, it drifts when a
provider moves a model behind a stable name, and it fails for a reader without credentials — which
is most readers, and all of the independent ones. A claim only a well-funded insider can check is
not a checkable claim.

`whence` is the worked example: its five scenarios replay from recorded registry interactions with
no token, so a manifest over them is verifiable by anyone with the repository.

---

## DEC-004 — An unverifiable input never yields a passing verdict

**Date:** 2026-09-03
**Status:** Accepted

**Decision.** If any input cannot be read, the run's verdict is `unverifiable`. It is never
`verified` on the strength of the inputs that could be read, and never `contradicted` on the
strength of one that could not.

**Why.** Partial verification reported as success is the failure this whole family of projects
exists to prevent, arriving at the layer that is supposed to prevent it. A verifier that degrades
quietly is worse than no verifier, because its output is trusted more.

---

## DEC-005 — The manifest attests one run, not the command's future behaviour

**Date:** 2026-09-03
**Status:** Accepted

**Decision.** A manifest records that *this* command, over *these* inputs, produced *this* result.
It makes no claim that re-running will reproduce it, and the manifest states its own scope in a
field rather than leaving it to be inferred.

**Why.** Non-determinism is real and record-and-replay does not remove it: a model provider, a
scheduler, or a hash seed can change a result without any input changing. Claiming reproducibility
would be claiming something the mechanism does not support, and the gap between the two is exactly
where published evaluation results currently fail.

Stating the narrower claim honestly is more useful than a broader one nobody can rely on.

**Open questions.** Whether repeated recordings should be compared to produce a stability figure.
That is a genuinely stronger claim and it needs its own design.

---

## DEC-006 — Signing is deferred; the digest chain is the contribution

**Date:** 2026-09-03
**Status:** Accepted

**Decision.** Manifests are not cryptographically signed in this version. The format leaves room for
a detached signature and the verification path does not depend on one.

**Why.** Sigstore and the OpenSSF model-signing work already solve signing, and adding a signature
to a manifest whose *contents* are not yet trustworthy attests the wrong thing — it proves who
emitted a claim, not that the claim holds. The digest chain is what makes the claim checkable, and
it is the part nobody ships.

A signature over a verified chain is worth adding later. A signature over an unverified one is
theatre.

---

## DEC-007 — The input set is itself a claim, and an incomplete one verifies a changed run

**Date:** 2026-09-03
**Status:** Accepted

**Decision.** A manifest records the globs its inputs were collected from, alongside the inputs. The
verification output states that coverage is bounded by that declaration. `attestrun` does not claim
to have identified everything that could change a result.

**Why — found by accident, during this project's first real use.** While testing the negative
paths, a stale `__pycache__` entry in the tool under attestation survived a `git checkout`: the
source file was correct, `git status` was clean, every attested digest matched, and the command
produced *different output*. The change was one character, `ok` to `OK`, so the byte length was
identical and the bytecode did not invalidate.

Had re-execution been skipped, the manifest would have reported `verified` for a run whose behaviour
had changed. The digests were all correct. The thing that changed was not an input.

That is not a bug to fix — no input set can be complete, since a result depends on interpreters,
caches, environment, and clocks that no glob enumerates. It is a limit to state, and stating it is
the difference between an honest verification tool and one that inherits the overclaiming it was
built to correct.

**What follows in practice.** Re-execution is the default and `--no-rerun` is opt-in, because digest
checking alone verifies less than it appears to. And the tool reports what it checked rather than
asserting the run is sound.

**Alternatives considered.** Digesting the whole working tree. Rejected: it makes every manifest
churn on unrelated edits, which trains readers to ignore `contradicted` — and it still would not
have caught the case above, since the stale bytecode was inside `.venv`.

**Open questions.** Whether to record an environment fingerprint — interpreter build, installed
package versions — as a separate advisory section. It would have caught this instance. It would also
grow without bound, and most of it does not affect most results.
