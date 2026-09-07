# Deterministic verification planning

Compatibility reference `14`. Use with [Verify](tasks/verify.md) to select defensible checks for the declared repository or change. Apply [core execution and evidence](../SKILL.md). Planning does not install tools or authorize gate execution; session authority already granted remains valid within its scope.

## Profile the actual scope

Read current relevant calibration, invariants/map, package scripts, CI/test/architecture configuration and changed paths. When a trusted shared ADC tool, supported runtime and authorized read access are available, use its `probe --repo <path>` and `plan --repo <path>` if their outputs answer the task. Omit `--write` unless durable artifact creation is authorized. Resolve the actual tool path rather than assuming a host installation directory.

The probe reads names, manifests, selected bounded config/code indicators without executing application code. Its profile records evidence paths, scan limits, exclusions, `evidence_classes` and `documentation_only`. It excludes host skill trees, agent worktrees and nested repositories with their own `.git`; reviewed `--exclude` entries propagate to planning. Inspect reported dominant unrecognized source extensions, which can make classification incomplete.

Prose about billing, simulation or security does not prove implementation. Documentation-only non-core matches remain candidates pending source evidence. Missing scanner signals are unknown where the scan cannot prove absence. If tool/runtime/permission is unavailable, name the blocker, perform a bounded manual inventory, and identify lost machine checks. If output is large, inspect its summary and named evidence fields, expanding for specific unresolved questions.

## Select capabilities without blanket prose loads

Use the existing [machine catalog](../assets/verification-capabilities.json) for capability IDs, statuses, selection rules and default levels. A comprehensive plan screens **every catalog entry**, retaining a recoverable status, reason, evidence, level, deterministic work and remaining judgment per entry. Review selected/candidate entries and every exclusion/default materially affecting risk or coverage.

A narrow task may assess an explicit subset; label it scoped and do not call it a complete repository plan. [Capability index](verification-capabilities.md) and [repo profiles](repo-verification-profiles.md) are optional interpretation aids. Open specialist detail only for selected risks or unresolved dispositions. Suggestions do not authorize dependency installation.

Statuses remain `selected`, `candidate`, `deferred`, `not_applicable`. Keep planned/selected/configured/executed/passed separate in reports; no executed tests means no tested result.

## Configure and verify the selected work

Use the existing four-level ladder: L0 cheap static/schema/type/lint/architecture checks; L1 affected unit/contract/integration/replay; L2 selected property/fuzz/model/mutation/performance/fault checks; L3 full-suite/soak/migration/platform/broad campaigns. Change levels only with a measured cost/risk rationale. Run cheap blockers first; batch independent checks only when side effects permit.

For actual gate definitions, source rebinding and execution load [exact gate contract](specialist-exact-gate-contract.md). For configured-runner/frozen-lock/count obligations use [gate environment](specialist-gate-environment.md). For changed-path selection include semantic edges through contracts, configuration, content, generated outputs, deployment and control planes. Unknown impact requires conservative selection; intent routing does not alter the existing `route` command or enable new selective execution.

Choose triggered recipes for [audited producers](specialist-audited-producers.md), [restricted builds](specialist-restricted-builds.md), [falsifiable detectors](specialist-verifier-falsifiability.md), [mutation restoration](specialist-mutation-restoration.md), or [strong assurance](assurance-contracts.md). Deterministic gates settle facts before additional model opinions; use [adversarial review](07-adversarial-review.md) for judgment-heavy findings.

## Result and stop

Return the scoped plan, exact proposed/configured commands, approval/prerequisite state and actual results. Preserve bounded redacted failure packets with first bad event, invariant, expected/actual, source/environment identity, seed/start state/trace, producer exit code, replay command and retained-log path. Keep green output compact and minimize reproduced regressions into fixtures/corpus where practical.

Finish when selected obligations have results or named blockers and all requested coverage is dispositioned. No dependency, permission, source binding or stored enum changes merely to make the plan look complete.
