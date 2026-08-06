# Reference: Conventions, Vocabulary, and Shared Shapes

Use this reference whenever another pass tells you to record an unknown, label evidence, score risk, or tag coverage status. Every other pass in this skill links here instead of restating the same vocabulary. Keep this file the single source of truth for those shapes.

**Mode:** definitional. No code changes. No deliverables produced from this file alone.

## Confidence levels

Use exactly these three labels. Do not invent intermediates.

- `verified` - direct repo evidence supports the claim. Cite the file, line, command, or doc that proves it.
- `inferred` - repo evidence is consistent with the claim but does not prove it. Name the gap that prevents `verified`.
- `unknown` - repo evidence is missing, contradictory, or only available outside the repo (vendor console, sibling repo, runtime telemetry).

Downgrade rather than flatten. If a check would force `inferred`, do not write `verified`.

## Risk levels

Use exactly these four labels. Pick the one that matches the worst plausible blast radius if the issue is real.

- `low` - annoyance or local cleanup; recoverable in minutes
- `medium` - meaningful regression, slow recovery, scoped blast radius
- `high` - user-visible incident, data corruption risk, security exposure within one trust zone
- `critical` - money movement, account takeover, data loss, privacy breach, irreversible state change, multi-tenant or cross-trust-zone exposure

## Status vocabulary

### Coverage ledger status

- `unscanned` - not yet touched by any pass
- `mapped` - architecture inventory complete for the area
- `commented` - critical-path comments added
- `audited` - logging or telemetry audit complete
- `reviewed` - adversarial or scenario pass ran
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

## Unknowns entry shape

Every pass that records an unknown writes the same entry shape into a file under `docs/unknowns/`. Use this canonical structure. Do not add or rename fields.

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

Use exactly these four statuses in `calibration/verification-plan.json`:

- `selected` - evidence shows the capability belongs in the current plan
- `candidate` - useful if a named condition or oracle is confirmed
- `deferred` - useful later; the trigger and reason are recorded
- `not_applicable` - current repo evidence does not support it

A status is not permission to install a dependency or execute repo code.

## Sensitive data classes

Treat as high risk wherever they appear (logs, comments, tests, docs, examples, screenshots, commit messages).

- passwords, password hashes, reset tokens, magic links, one-time codes
- session IDs, cookies, JWTs, API tokens, OAuth tokens, CSRF tokens
- secrets, API keys, signing keys, encryption keys, private certificates
- database connection strings
- raw personal data beyond the minimum safe identifier
- full request or response bodies that may carry secrets or personal data
- signed URLs and pre-signed upload data
- invite or activation codes that grant access
- biometric, health, financial, legal, location, child, student, psychometric, or otherwise regulated data
- assessment, survey, scoring, or training answers tied to an identifiable person
- prompts, model outputs, or tool traces that carry user-entered sensitive data

## Approval-gated areas

Edits to these areas require explicit human approval before any change. Document findings first, propose the smallest safe edit, then stop.

- auth, access control, sessions, secrets, crypto
- billing, payroll, money movement, purchases, entitlements
- deletion, retention, export, compliance workflows
- migrations, backfills, data repair
- concurrency or locking that can corrupt state
- privileged CI or CD, release tooling, support tools with production reach
- repo-specific protected areas already named in steering files

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

## Default deliverable paths

Use the repo's existing convention first. Fall back to these only when the repo has none.

| Artifact | Default path |
|---|---|
| Steering | `AGENTS.md` and tool-specific siblings at repo root |
| System map | `docs/architecture/system-map.md` (or `service-map.md` if the repo already uses that name) |
| Coverage ledger | `docs/architecture/coverage-ledger.md` |
| Repo slices | `docs/architecture/repo-slices.md` |
| Logging audit | `docs/security/logging-audit.md` |
| Adversarial pass | `docs/review/adversarial-pass.md` |
| Scenario stress-test | `docs/review/scenario-stress-test.md` |
| Scenario scorecard | `docs/review/scenario-scorecard.md` |
| Remediation backlog | `docs/review/remediation-backlog.md` |
| Safe-fix plan | `docs/review/safe-fix-plan.md` |
| Evidence-gap check | `docs/review/evidence-gap-check.md` |
| Approval packets | `docs/review/approval-packets.md` |
| Maintenance harness | `docs/review/maintenance-harness.md` |
| Unknowns | `docs/unknowns/<pass-name>.md` |

## Writing rules (cross-pass)

- Plain words. Short sentences. Active voice when it reads cleaner.
- ASCII punctuation and straight quotes only.
- Commas, periods, or parentheses instead of long dashes.
- Name the subject, the risk, and the safeguard directly.
- Avoid stock transitions, stock wrap-up lines, mirror-contrast slogans, hype, and apology filler.
- Merge any caller-supplied banned-term list as a hard rule.

Run `06-writing-hygiene.md` after any pass that writes text.
