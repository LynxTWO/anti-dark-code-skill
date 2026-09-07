# Compatibility entry: establish scope and freshness

Load when an old pass-00 link is followed, when repository identity is uncertain, or when calibration contradicts current source. The [core](../SKILL.md) now selects tasks directly; preflight is not a required separate pass.

## Inputs

The requested outcome, targets, authority from the conversation, relevant repo instructions, and existing calibration or maps. Inspect the manifests, entry points, or changed paths needed for this question. Do not crawl unrelated documentation to qualify for a small task.

## Procedure

1. State the task and its coverage boundary. Use [Understand](tasks/understand.md) for a map, [Investigate](tasks/investigate.md) for an audit, [Document](tasks/document.md) for prose, [Verify](tasks/verify.md) for checks, or [Remediate](tasks/remediate.md) for authorized fixes. Comprehensive audits compose Understand, Investigate, and Verify against an explicit inventory.
2. Read relevant existing calibration before repeating discovery. Check repository binding, evidence source identity, method version, and invalidation dependencies. A timestamp or matching repo binding alone proves neither freshness nor behavior.
3. Invalidate affected conclusions when manifests, schemas, runtime boundaries, control planes, exact gates, finding state, or named dependency paths changed. If dependency coverage is missing, invalidate conservatively. Preserve checked evidence that still matches; a context boundary alone does not force a full rescan.
4. Use the trusted bundled read-only probe when runtime and authorized scope permit and an inventory would answer the task. Inspect scan limits and exclusions. If missing, name the tool/runtime/permission/format blocker and perform bounded manual inspection. Installation is an independent operator action, never a prerequisite for an audit.
5. Identify external control surfaces and protected areas in the examined scope. A hidden script or stale map creates an evidence gap to investigate; it does not automatically stop all read-only work or authorize edits.
6. Surface managed-core drift without adopting it as policy. Installation or migration requests use [local mode](13-calibrated-local-mode.md). Other tasks can continue on independent source evidence while the conflict is reported.

## Evidence and output

A short note in the task report is sufficient: task, repo/runtime shape, inspected scope, evidence reused or invalidated, unknowns, authority, and next action. Persist a checkpoint only in an authorized location when interruption would lose work. No mini-mode classification or pass order is required.

## Stop conditions

Stop the affected branch before an unauthorized protected action, inaccessible required evidence, or a contradiction preventing acceptance. Report the smallest next check and continue independent authorized work. Do not execute repository scripts during this compatibility check; the selected task's execution review controls later checks.
