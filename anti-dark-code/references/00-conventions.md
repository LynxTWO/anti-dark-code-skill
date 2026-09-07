# Stored vocabulary and artifact compatibility

Load when reading or updating an existing ledger, calibration record, or unknowns artifact. The [core](../SKILL.md#evidence) is canonical for evidence and authorization; this reference preserves stored shapes. It is not a mandatory startup read.

## Confidence and severity

Confidence remains `verified`, `inferred`, or `unknown` as defined in the core. Claim kind is a separate report field: `source_fact`, `configured_behavior`, `observed_behavior`, or `guarantee`. Do not add unsupported keys to validated JSON; retain these distinctions in the accompanying report or existing evidence fields.

Severity expresses plausible consequence:

- `low`: annoyance or local cleanup, recoverable in minutes.
- `medium`: meaningful regression, slow recovery, scoped impact.
- `high`: user-visible incident, corruption risk, or exposure within one trust zone.
- `critical`: money movement, takeover, data loss, privacy breach, irreversible change, or cross-trust-zone exposure.

Logging exposure categories describe observed or possible reach; they do not replace severity.

## Status vocabulary

### Coverage ledger status

- `unscanned` - not yet touched by any pass
- `mapped` - architecture inventory complete for the area
- `commented` - critical-path comments added
- `audited` - logging or telemetry audit complete
- `reviewed` - adversarial or scenario pass ran
- `tested` - bounded automated or runtime evidence ran; record the exact scope, counts, skips, and untested boundary
- `deferred` - skipped on purpose; reason recorded
- `excluded` - will not get code-level passes (generated, vendored, mirrored, binary, engine-owned serialized)
- `approval-gated` - needs explicit human approval before any further edit
- `blocked` - cannot progress; reason and next check recorded

### Item status (backlog, unknowns, slices)

- `open` - recorded, not yet started
- `ready` - evidence and approval state are sufficient to act
- `in progress` - actively being worked
- `blocked` - cannot progress; reason and next check recorded
- `deferred` - intentionally postponed; reason recorded
- `resolved` / `fixed` / `done` - closed; pick the verb that fits the artifact (unknowns close as `resolved`, backlog items close as `fixed`, slices close as `done`)

## Classification labels (areas and slices)

Use alongside status. A single area can carry more than one label.

- `owned-clear`
- `owned-risky`
- `legacy-unclear`
- `generated`
- `vendored`
- `third-party mirror`
- `binary or asset-heavy`
- `external-control-plane`
- `cross-repo-boundary`
- `approval-gated`

## Diagnostic outcome labels

Keep validation blockers separate from source findings:

- `source defect` - the supported target reached the relevant behavior and produced a reproducible source-level failure
- `unexercised path` - the check did not discover, enable, invoke, or observe the target behavior
- `toolchain blocker` - a required SDK, compiler, workload, reference assembly, or build tool was unavailable
- `native dependency blocker` - a required native library, SDK, driver, executable, or architecture-specific artifact was unavailable
- `capability unavailable` - the environment lacks the optional runtime, service, hardware, permission, or format needed for the check
- `external-state blocker` - proof depends on a vendor console, sibling repo, credential, network service, or other state outside the checked repo

Record the command, target tuple, observed failure, and next best check. A missing prerequisite is not evidence that source is defective, and an unexercised path is not a passing path.

## Unknowns entry shape

Reuse the existing artifact first. One-off unknowns may remain in the report. When creating a persistent unknowns file, preserve the existing template shape below; the fallback path is `docs/unknowns/<task>.md`. Never create it without write authorization.

```markdown
### <short title of the unknown>

- **Area or file:** <path or subsystem>
- **Concern:** <what is unclear in one sentence>
- **Why it matters:** <what could go wrong if this resolves badly>
- **Evidence found so far:** <files, lines, commands, doc references>
- **Confidence:** <verified | inferred | unknown>
- **Likely owner:** <person, team, or "unknown">
- **Next best check:** <specific, runnable, repo-local when possible>
- **Risk level:** <low | medium | high | critical>
- **Status:** <open | in progress | resolved | blocked | deferred>
- **Notes:** <optional; dated updates>
```

Pass-specific unknowns files (`docs/unknowns/<pass-name>.md`) follow `assets/templates/unknowns-file.md`, which uses this same shape.

## Verification capability status

`calibration/verification-plan.json` keeps the catalog's `selected`, `candidate`, `deferred`, and `not_applicable` values. Selection is not execution, coverage, or permission. Derive IDs and the capability count from [the catalog](../assets/verification-capabilities.json), not a copied range.

## Reporting coverage without changing schemas

In prose, distinguish examined, deferred, excluded, and blocked surfaces. For existing ledgers, keep their stored status and describe what was actually examined: `mapped` means architecture inventory, `commented` means comments added, `tested` requires bounded execution evidence. Do not translate `mapped` into tested or reinterpret old records during a text-only upgrade.

## Calibrated local paths

When the repo carries a local anti-dark-code skill, use:

| Purpose | Default path |
|---|---|
| Canonical repo-local skill | `.agents/skills/anti-dark-code/` |
| Repo profile | `.agents/skills/anti-dark-code/calibration/repo-profile.json` |
| Invariants | `.agents/skills/anti-dark-code/calibration/invariants.md` |
| Accumulated system map | `.agents/skills/anti-dark-code/calibration/system-map.md` |
| Exact deterministic gates | `.agents/skills/anti-dark-code/calibration/gates.json` |
| Verification capability plan | `.agents/skills/anti-dark-code/calibration/verification-plan.json` |
| Coverage ledger | `.agents/skills/anti-dark-code/calibration/coverage-ledger.md` |
| Findings ledger | `.agents/skills/anti-dark-code/calibration/findings-ledger.md` |
| Upstream lesson queue | `.agents/skills/anti-dark-code/calibration/upstream-candidates.md` |
| Local run artifacts | `.anti-dark-code/runs/` |

The shared updater owns the local skill core. The repo owns `calibration/`.

## Artifact and writing defaults

Prefer existing repo documents. Templates under [assets/templates](../assets/templates/) define fallback shapes; load only the one being created. [Writing hygiene](06-writing-hygiene.md) applies to changed text, not an automatic repository-wide rewrite.

If commits are authorized, stage explicit paths, preserve attribute-controlled line endings, inspect the diff stat, and avoid sweep staging combined with environment overrides. No task requires commits merely to advance its workflow.
