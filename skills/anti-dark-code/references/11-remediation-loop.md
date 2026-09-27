# Bounded remediation

Compatibility reference `11`. Use [Remediate](tasks/remediate.md) for supported findings, including an existing audit backlog. Apply [core authority, evidence and recovery](../SKILL.md). Existing session authorization carries forward; this reference neither mandates a fresh whole-repo audit nor grants protected-action permission.

## Recheck the affected obligation

Read the finding, current source identity, relevant contracts/map/ledger fragments and verification evidence. Refresh only invalidated dependencies. A new runtime/control plane, unreviewed telemetry, protected change, saved-text identity change or stale comment scope reopens its affected obligation before dependent work continues. Missing unrelated rollout documents do not block a well-supported narrow fix.

Prefer a failing invariant, exact diff, minimized replay, property counterexample, architecture rule or measured budget before behavior changes. Use [adversarial review](07-adversarial-review.md) to select an independent falsifier appropriate to the stakes. For a broader guarantee, load the matching [assurance recipe](assurance-contracts.md) before implementation/acceptance; static file facts do not require blanket loading.

## Make the batch reviewable

A backlog item records title, exact area/paths, severity, impact, evidence/confidence, approval state, smallest next action, verification, owner if known and current status. Preserve the existing backlog vocabulary (`open`, `ready`, `in progress`, `blocked`, `deferred`, `fixed`) and stored schemas. Separate ready authorized fixes, protected actions needing a packet, and evidence gaps.

For each selected fix record exact files, expected behavior/preservation boundary, checks, necessary docs, rollback and relevant observability note. Keep batches small and single-purpose. Repair exactly the artifacts a gate/finding names. A broader cleanup must use the gate's actual classifier and exclusions; do not approximate a text classifier across binaries.

Stop the dependent edit if evidence becomes insufficient or a new protected side effect falls outside authorization. Continue independent authorized work. Prepare a concrete approval packet with target, protected category, current evidence, reviewed change, possible breakage, verification, rollback and remaining decision. Do not repeatedly ask for permission already granted within the same source/scope binding.

## Verify the fix and its guard

Test changes name the behavior contract and why an old expectation was wrong/incomplete. Reject deleting assertions, skipping cases, widening mocks/timeouts, re-recording snapshots or relaxing policy solely to get green. A verifier reviews consequential test changes separately from implementation; retain useful pre-fix reproducers.

A widened detector/matcher ships a regression guard for the newly caught form with a recorded pre-fix red and post-fix green result. A one-off probe is not a recurring guard. If proving the guard by reverting/mutating the fix, use [mutation restoration](specialist-mutation-restoration.md): durably preserve all files, restore unconditionally, verify bytes and run the final exact-tree green check. Diagnose survivors and hangs rather than hiding them in scores.

For external component probes, moves/extractions or TODO lifecycle use [remediation edges](specialist-remediation-edges.md). For text-only fixes use [critical comments](03-critical-path-comments.md) and [hygiene](06-writing-hygiene.md); authored/persisted prose uses [language boundaries](12-transcreation-boundary.md).

## Checkpoint and stop

After each meaningful batch, verify affected behavior, docs, logging/privacy, hidden entrypoints and authorization. Route checks conservatively when impact dependencies are incomplete. Record actual executed results, residual risks and next obligation; update only authorized affected artifacts.

A user-requested multi-commit campaign checkpoints at least every 10 commits and stops for review at 20 unless the user supplied another bound or already authorized continuation. These are bounds on an authorized campaign, not instructions to create commits. Stop earlier when the requested slice is complete or a concrete blocker prevents its dependent work.

Finish when the claimed fix is reproduced and verified in scope, or report the precise incomplete/approval-blocked state. Maintenance harness installation and the [combined comment loop](combined-03-06-loop.md) are separate optional outcomes, not required closing passes.
