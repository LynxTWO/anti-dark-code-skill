# Critical-path comments

Compatibility reference `03`. Use with [Document](tasks/document.md) for authorized explanatory comments. Apply the [core contract](../SKILL.md). Mode: comment-only application changes; no logic, control flow, imports, signatures, dependency/configuration changes or formatting outside touched comment lines.

## Select the bounded path

Reuse a current map or inspect the relevant code directly. Select paths from evidenced risk: trust and access checks, money/entitlements, state machines, deletion/retention, migrations, webhooks, concurrency, replay/idempotency, irreversible background work, privileged scripts, release/control-plane hooks, or language/persisted-text boundaries. Record selected paths, why now, what remains uncovered and the next useful slice. A scaffold needs a short proposed critical-path plan, not invented comments.

## Explain the load-bearing rule

Place comments beside the enforcement or dependency. Explain why the subsystem exists, trusted/untrusted inputs, invariant, side effect, ordering, failure consequence, privacy/security assumption and repair/rollback hazard that future edits could miss. Useful locations include seed/time/hash identity construction, duplicate suppression, event tails, serialized queues, migration/reset compatibility, authorization/release gates, authoritative receipts/history and schema/renderer boundaries.

Keep comments short and evidence-backed. Do not state historical incidents, provider timing or guarantees that the source cannot support. For example:

```ts
// The summary participates in persisted receipt identity. Changing its wording
// needs an identity/migration decision before existing receipts are rewritten.
const id = hashRecord({ tick, sequence, kind, summary });
```

This is appropriate only after tracing the actual identity contract. A comment such as "This makes localization safe" supplies no falsifiable boundary.

## Preserve the allowed-text boundary

Exclude generated, vendored, mirrored third-party, minified and binary files, plus engine-owned serialized assets and metadata. Use adjacent docs/runbooks/manifests for those surfaces. Do not alter pragmas, linter directives, type-affecting docblocks, SQL hints, framework magic comments or other toolchain-sensitive text. Hand-maintained assets still require evidence that the proposed text is behavior-neutral.

When behavior is unclear, record the exact function/line, uncertainty, impact and next check using [core evidence](../SKILL.md#evidence); do not embed a guess. For authored content, locale overlays or saved prose, use [language boundaries](12-transcreation-boundary.md). A comment request does not authorize rewriting that content.

## Verify and finish

Review the exact diff for the allowed-text boundary, then apply [writing hygiene](06-writing-hygiene.md) to touched prose. If a comment-only change cannot be proved behavior-neutral because text affects tooling, stop that edit and document it. Use relevant existing checks where they can falsify the preservation claim.

Return files/paths clarified, invariants and risks explained, verification actually performed, unknowns and remaining scope. Reuse `docs/unknowns/critical-paths.md` or a current ledger when authorized and useful. Finish at the requested slice; [combined commenting](combined-03-06-loop.md) is an optional bounded campaign, not an automatic continuation.
