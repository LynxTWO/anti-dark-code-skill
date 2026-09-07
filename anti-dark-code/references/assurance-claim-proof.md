# Assurance claim proof

Record:

1. the exact claimed object and scope, such as frame, stream, finalized file, staged output set, or published result
2. the producer path and an independent oracle that can falsify the claim
3. every finalization boundary, including finish, flush, close, child exit, final length, and manifest completion
4. whole-output proof when the claim covers a whole artifact; partial checks do not prove final blocks, metadata, length, or truncation safety
5. positive, mismatch, truncation, finalization-failure, cancellation, and unavailable-capability outcomes when applicable
6. the exact runtime, toolchain, target tuple, observed counts, and skipped boundary
7. every UI, tooltip, log, document, receipt, or downstream copy that repeats or carries the claim

Reopen or independently decode finalized assurance-bearing output. Compare format, expected length or sample count, and all payload bytes or a collision-resistant digest over those exact bytes. A successful write or per-unit check does not cover an ignored final flush.

Treat disagreement between the product verifier and a credible independent oracle as a verifier finding. Preserve the rejected artifact, locate the first failing object and boundary, and test both implementations before changing the producer or suppressing the check.

Trace classifier ancestry. When several parents can reach one recovery child, test every reachable parent/child route. One covered route does not validate siblings.

Treat retry, reset, and fallback scope as operation identity. State whether the budget is global, per job, per address, per payload shape, or per exact command. Test exhaustion and reset at that boundary so one sibling cannot consume another's recovery.

Separate outcome proof from branch-activation proof. A green end-to-end result does not exercise an intermittent recovery branch unless a counter, trace, injected fault, or retained event proves activation. Keep branch coverage `unknown` when activation evidence is zero.

When proof moves across a copy, metadata rewrite, rename, upload, or publication boundary, carry an immutable receipt that binds the exact output set and semantic oracle. Revalidate it at the new boundary or explicitly clear the claim. Prevent time-of-check/time-of-use gaps with an appropriate lease over the bytes being hashed, copied, or reopened.

Verify an isolation property, never the request that asked for it. The probe must observe the property in context: attempt exactly what the boundary must prevent and require an observed denial, in every environment the claim covers. Reading back the configuration that requested the isolation is not evidence, because it reproduces the original error. Where the probe cannot run, a gate asserting the property fails rather than passes, and the claim stays `inferred` with the gap named. A probe that tests nothing is indistinguishable from a passing probe, so silence must not be scored as success. Where a property has no cheap in-context probe at all, record it as unverified rather than asserting it.

A checker satisfied by editing the artifact it checks is a ritual, not evidence; a review-closure signal pinned to a literal the author can update in the same edit certifies nothing. Bind closure signals to something outside the artifact under review: a second artifact, a recorded run, or a reviewer identity. Substitute a check that would fail if the claimed review had not actually happened.

Prefer substantive properties over a single declarative line: no finding left in an open state, no unresolved verdict language in the document, and a hash binding so any edit is visible. Scope the scan to the whole document, because a live verdict often lives in a different section than the one a first attempt checks, and a check that passes over the section holding the rejection is no better than the literal it replaced. And distinguish a live claim from an accurate historical record: tense is a reliable discriminator, and closing a check must never require deleting true history.


Trigger: accepting a `guarantee` about output, isolation, recovery, or review closure. Apply [core evidence and authority](../SKILL.md#evidence); this recipe grants no execution or mutation permission.

Result: a scoped claim with an independent falsifier, observed activation and finalization evidence, or a named unmet obligation. For transactions use [preservation](assurance-preservation.md); for publication use [publication integrity](assurance-publication-integrity.md).
