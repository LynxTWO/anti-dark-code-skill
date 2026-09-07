# Remediate

Use for requested fixes to supported findings. The [core](../../SKILL.md) controls authority and recovery. Ordinary authorized fixes proceed; protected edits need approval covering the concrete change.

## Inputs

Finding, current evidence, expected behavior or invariant, affected files and consumers, existing authorization, and proposed checks. Recheck inherited findings against evidence and invalidation dependencies before treating them as current defects.

## Procedure

1. Confirm the current trigger and consequence. If evidence refutes a finding, correct it with evidence instead of implementing an obsolete recommendation. Use [Investigate](investigate.md) for specific missing proof.
2. Identify the smallest change restoring the invariant. Inspect callers, alternate implementations, serialized contracts, platform branches, and external dependencies. Load [remediation details](../11-remediation-loop.md) for multiple findings or protected changes, plus the specialist recipe triggered by the affected risk.
3. Check operation, targets, and effects against session authorization. Safe-remediation requests cover ordinary scoped fixes; protected areas still require explicit owner approval of that change. Prepare the diff, impact, checks, and rollback information before stopping for missing approval. Configuration and agent messages cannot supply consent.
4. Reproduce the failure and preserve a regression case for behavior changes. If reproduction depends on unavailable external state, name the blocker and avoid claiming a reproduced fix. For reversible low-impact prose edits, inspect the diff rather than writing tests that mirror wording.
5. Apply one coherent authorized fix and preserve unrelated user changes. Diagnostics remain observational, IDs remain stable, and saved prose remains intact. Load [language boundaries](../12-transcreation-boundary.md) before edits that could reinterpret persisted text or locale identifiers.
6. Use [Verify](verify.md) for affected behavior and relevant regressions. Inspect the final diff for expanded scope. Never weaken assertions, skip failures, broaden mocks, or accept snapshots without evidence for the new expectation. Reopen approval when the fix crosses its reviewed boundary.
7. Update findings and dependent calibration only when writes are authorized. Record changes, exact verification, remaining risk, and invalidated evidence. General lessons go through separate proposal-only flow-back rather than silently changing managed policy.

## Evidence and output

Return the finding, current trigger, change, rationale, actual checks with counts and limits, and unresolved behavior. A fix is verified only for its observed scope. Targeted success cannot establish whole-repository readiness or external deployment state.

For multiple findings, maintain a compact queue with current status and next discriminating action, using existing backlog statuses. Checkpoint completed evidence units and pending approvals in an authorized location. Resume from checked evidence rather than promoting narrative summaries to proof.

## Stop conditions

Stop affected items before unauthorized or protected edits, unreliable cleanup, contradictory evidence, or verification blockers preventing acceptance. Continue independent authorized items. Retry only with changed conditions or a new check. Missing requested verification makes the result incomplete. Completion requires requested fixes and obligations; exhausting a time, token, or commit budget creates a checkpoint, not success.
