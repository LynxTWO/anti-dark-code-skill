# Coverage and slicing

Compatibility reference `05`. Use with [Understand](tasks/understand.md), [Investigate](tasks/investigate.md), or [Verify](tasks/verify.md) when a large, mixed, old or interruption-prone scope cannot be represented honestly in one result. Apply the [core contract](../SKILL.md); application code stays read-only.

## Build obligations from actual shape

Capture runtime units, apps/packages/services/tools, languages/frameworks, ownership evidence and generated/vendored/mirrored/minified/serialized/binary trees. Include quiet scripts, notebooks, editor/import/bootstrap hooks, CI/CD, release and migration runners, language surfaces and external control planes when source shows them. Use [hidden control planes](specialist-hidden-control-planes.md) for specialty branches.

Rank consequential areas by severity (`low`, `medium`, `high`, `critical`) and explain impact: trust/access, money/entitlements, secrets, deletion, regulated/user content, corruption, irreversible operations, callbacks, live economy, native/secure storage, infrastructure state, model/data lineage, and prose involved in IDs/hashes/replay/policy. Severity is separate from confidence, coverage disposition and logging exposure.

Define each slice by runtime unit, subsystem, trust edge, critical flow, directory, environment/control-plane route or language boundary. Make it large enough to matter and small enough to verify. Risk changes the order; it never silently reduces the user's comprehensive scope or caps review at a fixed number of paths.

## Ledger contract

For each obligation record: name/paths, runtime/flow, reason and severity, owner if known, evidence/source identity, classification, examined/deferred/excluded/blocked disposition, blockers, testable exit criterion, next task/check and invalidation dependencies. Keep confidence attached to claims rather than using it as a coverage status.

Reuse `docs/architecture/coverage-ledger.md`, `repo-slices.md`, nested domain ledgers and `docs/unknowns/coverage-pass.md` when useful and authorized. Existing templates, calibration fields and stored status vocabularies retain their current meaning; report the new engagement disposition alongside them without silent enum/schema migration.

Record exclusions explicitly and explain how each is represented: adjacent docs/manifests/runbooks for generated/engine/binary material; separate owner/access obligations for sibling repos, submodules and remote systems. Excluding inline edits does not exclude their operational effects from a requested audit.

For verification ownership, record relevant IDs from the existing [capability catalog](../assets/verification-capabilities.json), ladder level, exact gate/next check, replay/corpus location and runner/hardware constraint. Do not drop V21 or V22 because an old ledger example ended at V20. A narrow assessment is labeled scoped; a comprehensive plan screens every catalog entry under [verification planning](14-deterministic-verification.md).

## Freshness and finish

Reuse evidence only while its source identity and relevant invalidation dependencies remain valid. A recent timestamp is insufficient. Reopen changed, contradictory or incomplete dependency sets conservatively; refresh affected obligations rather than restarting unrelated work.

Finish when every declared obligation has evidence or a named disposition, reason and next action. One helper cannot cover an entire flow, one service cannot cover a monorepo, and one checkout cannot cover its remote release plane. A checkpoint records remaining work without claiming completion.
