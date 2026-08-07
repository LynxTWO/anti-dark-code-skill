# Reference: Calibrated Local Mode

Use this pass to install, migrate, or update Anti-Dark-Code inside a new or existing repository without turning the shared skill into a repo-specific fork or importing another repository's assumptions.

**Mode:** docs, skill files, and calibration only. Do not change application behavior.

## Goal

Create one repo-local skill that:

- carries the current universal managed core
- learns this repository's actual architecture and invariants
- reuses exact local gates instead of rediscovering them
- preserves repo-specific knowledge across context resets
- binds that knowledge to one repository identity
- can be updated without erasing local calibration
- can propose general lessons upstream without silently modifying the shared skill

## Canonical Layout

Use this layout unless the repository already has a documented equivalent:

```text
.agents/skills/anti-dark-code/
  SKILL.md
  VERSION
  SOURCE-SCOPE.json
  references/
  scripts/
  assets/
  agents/
  calibration/
    README.md
    repo-binding.json
    repo-profile.json
    invariants.md
    system-map.md
    gates.json
    verification-plan.json
    coverage-ledger.md
    findings-ledger.md
    upstream-candidates.md
    upstream.json
  .adc-managed.json
```

The `.agents/skills/anti-dark-code/` directory is the canonical repo copy. Host adapters may point other discovery locations at it. Do not maintain independent Claude, Codex, and Gemini policy cores.

## Ownership Boundary

### Managed core

The shared installer owns:

- `SKILL.md`
- `VERSION`
- `SOURCE-SCOPE.json`
- `references/`
- `scripts/`
- `assets/`
- `agents/`
- `.adc-managed.json`

Treat these files as read-only inside the repository. If the repository discovers a general improvement, record a candidate in calibration instead of patching the core locally.

### Repo-owned calibration

The repository owns `calibration/`. Preserve it across core updates, but never transplant it into an unrelated repository.

- `repo-binding.json` binds calibration to one hashed repository identity.
- `repo-profile.json` is deterministic inventory, not narrative architecture.
- `invariants.md` stores load-bearing repo truths and approval boundaries.
- `system-map.md` stores accumulated architecture, rule authority, trust, and external control planes.
- `gates.json` stores exact reviewed command arrays and machine constraints.
- `verification-plan.json` records how all 20 capabilities apply.
- `coverage-ledger.md` prevents expensive re-audits of fresh, guarded surfaces.
- `findings-ledger.md` prevents settled work from being rediscovered.
- `upstream-candidates.md` queues repo-agnostic lessons.
- `upstream.json` records source version and proposal-only flow-back policy.

## Clean Source Requirement

Normal installation must come from a clean shared core containing a valid `SOURCE-SCOPE.json` marker.

The installer blocks a source by default when it:

- lacks a valid universal marker
- is located inside the target repository
- contains a repo-local `.adc-managed.json` installation manifest
- contains a populated top-level `calibration/` directory
- contains bound, enabled, pre-approved, path-contaminated, or otherwise unsafe calibration templates
- contains internal symlink or junction entries

A repo-local installed copy may contain useful local knowledge. That does not make it a safe source for another repository.

`--allow-unsafe-source` exists for reviewed recovery from a legacy or local source. It never permits source-side calibration to be copied. Unsafe calibration templates remain blocked.

## Repository Binding

`calibration/repo-binding.json` uses a hashed canonical Git origin when an origin exists. SSH and HTTPS forms of the same normal remote resolve to the same identity. Root history is retained only as hashed evidence, so the first commit does not change the binding. A local Git repository without an origin, and a non-Git repository, use a hash of the resolved repository location. Raw remotes and personal paths are not stored.

Binding states:

- `new`: no calibration exists yet
- `match`: calibration belongs to the current repository identity
- `unbound`: legacy calibration exists without a binding
- `invalid`: the binding record is malformed or contains unsafe entries
- `mismatch`: calibration belongs to a different repository identity

The installer creates a binding for new calibration.

Legacy unbound calibration requires explicit review and `--accept-unbound-calibration`.
The flag applies only to the `unbound` state. An invalid binding or symlink-contaminated calibration must be repaired or quarantined.

A deliberate repo move, fork, or remote identity change may require `--rebind-calibration`. Rebinding records the previous hashed id. It must not be used to import unrelated calibration.

## Install or Update

Use the bundled deterministic installer from the clean shared skill root.

Dry run:

```bash
python3 scripts/adc.py install --repo /path/to/repo
```

Apply only after reviewing source safety, binding status, conflicts, and legacy locations:

```bash
python3 scripts/adc.py install --repo /path/to/repo --apply
```

The installer:

1. Verifies the source marker and calibration templates.
2. Rejects repo-local or repo-calibrated sources by default.
3. Copies managed core files to `.agents/skills/anti-dark-code/`.
4. Preserves the target repository's calibration.
5. Refuses to overwrite locally modified managed files unless `--force` is explicit.
6. Writes checksums to `.adc-managed.json`.
7. Creates a thin Claude Code adapter when requested or detected.
8. Leaves Codex and Gemini CLI on the canonical `.agents/skills` copy.
9. Initializes missing clean calibration templates without replacing existing records.
10. Writes or verifies `repo-binding.json`.
11. Reports legacy calibration locations without silently combining competing stores.
12. Never copies top-level calibration from the installation source.

Do not use automatic upstream write-back as part of installation.

## New Repository Bootstrap

From the clean shared source:

```bash
python3 scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --hosts all
```

Review the dry-run plan, then apply:

```bash
python3 scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --hosts all \
  --apply
```

After installation:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py probe --repo . --write
python3 .agents/skills/anti-dark-code/scripts/adc.py plan --repo . --write
```

Then review:

- repository binding status
- repo-type classification
- risk signals and their evidence paths
- proposed capability statuses
- proposed gate commands
- execution and hardware cautions

Run pass `01` and pass `02` to turn deterministic inventory into human-readable steering, architecture meaning, trust boundaries, and rule authority.

## Existing Repository Migration

Read the package `MIGRATION.md` before applying.

Before writing calibration, inspect existing:

- steering files
- architecture docs
- ADRs and runbooks
- CI workflows and package scripts
- test configuration
- coverage and findings records
- existing Anti-Dark-Code directories
- sibling repos and external control planes

Classify old content by purpose.

Replace old universal policy with the clean core. Import only fresh, evidence-backed facts that belong to this same repository. Mark stale, contradictory, or uncertain facts as stale, inferred, or unknown.

Do not convert old prose into verified truth merely because it exists.

Do not import gates as enabled or approved. The installer deterministically resets migrated or rebound gates to disabled and proposed, and clears global execution confirmation.

### Trusted unbound calibration

After confirming it belongs to this repository:

```bash
python3 scripts/adc.py install \
  --repo /path/to/repo \
  --accept-unbound-calibration \
  --apply
```

### Reviewed repository identity change

After confirming a move, fork, or remote change:

```bash
python3 scripts/adc.py install \
  --repo /path/to/repo \
  --rebind-calibration \
  --apply
```

## Multiple Legacy Stores

A repository may contain more than one old calibration or customized skill location.

Do not let the installer merge two populated stores blindly.

Use this order:

1. Identify which store has the strongest same-repo evidence.
2. Back up all stores.
3. Choose one canonical calibration.
4. Compare other stores one file class at a time.
5. Preserve contradictions as unknowns.
6. Convert old gates into disabled proposals.
7. Verify the new binding.
8. Retire old stores only after successful local use.

The historical `.anti-dark-code/calibration` fallback may be migrated only when the canonical target does not already contain calibration. Other detected stores remain for manual review.

## Freshness Rules

Calibration earns trust only while aligned with the code.

Record at least:

- last verified date
- source commit or version when available
- evidence paths
- changes that invalidate the entry
- next check when confidence is below verified

Preflight should treat pass `02` as a diff when the system map is fresh. It should fall back to a wider map when relevant directories, manifests, trust boundaries, or control planes changed.

A matching repo binding proves identity continuity, not factual freshness.

## Host Discovery

Load `host-adapters.md` only after the canonical local copy exists.

- Codex and Gemini CLI can use the canonical `.agents/skills` location.
- Claude Code receives a thin adapter that points to the canonical copy.
- Other hosts receive a small pointer in their existing instruction surface.

Host adapters may change discovery and tool syntax. They must not duplicate or fork core policy.

## Physical Path Isolation

User-level host discovery may use a symlink or adapter that points to the clean shared core. Repo-local managed state may not.

The following repo-local paths must be real paths with no symbolic-link or Windows-junction component and no nested link-like entry:

- `.agents/skills/anti-dark-code/`
- `.agents/skills/anti-dark-code/calibration/`
- `.claude/skills/anti-dark-code/SKILL.md`
- `.anti-dark-code/` run and flow-back artifact paths

This prevents a repository from redirecting writes into the shared core, another repository, or an unrelated filesystem location. The installer checks this rule during both dry-run and apply. Calibration writers, gate artifacts, and flow-back staging also fail closed.

Do not solve host discovery by symlinking the repo's skill directory to the user-level core. Install the managed copy and let host adapters point inward to that canonical repo copy.

## Validation by Layer

Use `validate --mode distribution` for a release candidate, `validate --mode universal` for a live shared core that may contain `incoming/`, and `validate --mode installed` for a repo-local managed copy. Installed validation uses `.adc-managed.json` for core integrity and verifies the repo binding. It does not misclassify expected repo-owned calibration as contamination.

## Gate and Flow-Back Isolation

Deterministic gate planning and execution are refused when calibration is unbound, invalid, or mismatched. An enabled applicable gate that is blocked by review or stale source evidence returns exit code `2` even in dry-run mode.

Flow-back is also refused when local calibration does not match the current repository identity.

When staging to a parent, the parent must be a clean universal source core. A repo-local parent with calibration is not accepted.

## Safety Rules

- Do not execute repo code during installation or probing.
- Do not install testing dependencies automatically.
- Do not overwrite local calibration.
- Do not overwrite edited core files without surfacing the conflict.
- Do not allow repo-local managed paths to traverse symbolic links or Windows junctions.
- Do not place secrets or raw personal paths in committed calibration.
- Do not copy one repo's calibration into another repo.
- Do not use a repo-local fork as another repo's normal source.
- Do not let a repo-local skill write directly into a user-level or shared skill.
- Do not approve migrated gates automatically.
- Do not use `--force`, `--accept-unbound-calibration`, `--rebind-calibration`, or `--allow-unsafe-source` as batch defaults.

## Acceptance Checklist

Calibrated local mode is complete when:

- one canonical repo-local core exists
- its source came from a clean universal core or a documented reviewed recovery
- host discovery points to the canonical core without policy duplication
- `repo-binding.json` matches the current repository
- no foreign repo names, paths, gates, findings, or invariants appear in calibration
- all calibration files exist or are deliberately deferred
- the repo profile and verification plan were generated deterministically
- proposed gates are exact argument arrays and remain unexecuted until reviewed
- migrated gates begin disabled and proposed
- core update ownership and calibration ownership are documented
- installed validation passes against `.adc-managed.json` and the current repo binding
- repo-local managed paths contain no symbolic-link or Windows-junction components and no nested link-like entries
- flow-back is proposal-only
