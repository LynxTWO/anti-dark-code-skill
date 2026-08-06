# Reference: Calibrated Local Mode

Use this pass to install or update anti-dark-code inside a new or existing repo without turning the shared skill into a repo-specific fork.

**Mode:** docs, skill files, and calibration only. Do not change application behavior.

## Goal

Create one repo-local skill that:

- carries the current shared core
- learns the repo's actual architecture and invariants
- reuses exact local gates instead of rediscovering them
- preserves repo-specific knowledge across context resets
- can be updated without erasing local calibration
- can propose general lessons upstream without silently modifying the shared skill

## Canonical Layout

Use this layout unless the repo already has a documented equivalent:

```text
.agents/skills/anti-dark-code/
  SKILL.md
  VERSION
  references/
  scripts/
  assets/
  agents/
  calibration/
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

The `.agents/skills/anti-dark-code/` directory is the canonical repo copy. Host adapters may point another discovery location at it. Do not maintain independent Claude, Codex, and Gemini cores.

## Ownership Boundary

### Managed core

The shared installer owns:

- `SKILL.md`
- `VERSION`
- `references/`
- `scripts/`
- `assets/`
- `agents/`
- `.adc-managed.json`

Treat these files as read-only inside the repo. If the repo discovers a general improvement, record a candidate in calibration instead of patching the core locally.

### Repo-owned calibration

The repo owns `calibration/`. Preserve it across core updates.

- `repo-profile.json` is deterministic inventory, not narrative architecture.
- `invariants.md` stores load-bearing repo truths and approval boundaries.
- `system-map.md` stores accumulated architecture and rule authority.
- `gates.json` stores exact, reviewed command arrays and machine constraints.
- `verification-plan.json` records how all 20 capabilities apply.
- `coverage-ledger.md` prevents expensive re-audits of fresh, guarded surfaces.
- `findings-ledger.md` prevents settled work from being rediscovered.
- `upstream-candidates.md` queues repo-agnostic lessons.
- `upstream.json` records source version and flow-back policy, not a hardcoded personal path.

## Install or Update

Use the bundled deterministic installer from the shared skill root:

```bash
python scripts/adc.py install --repo /path/to/repo
```

That command is a dry run. Apply only after reviewing the plan:

```bash
python scripts/adc.py install --repo /path/to/repo --apply
```

The installer:

1. Copies managed core files to `.agents/skills/anti-dark-code/`.
2. Preserves `calibration/`.
3. Refuses to overwrite locally modified managed files unless `--force` is explicit.
4. Writes checksums to `.adc-managed.json`.
5. Creates a thin Claude Code adapter when requested or detected.
6. Leaves Codex and Gemini CLI on the canonical `.agents/skills` copy.
7. Initializes missing calibration templates without replacing existing records.

Do not use automatic upstream write-back as part of installation.

## New Repo Bootstrap

After installation:

```bash
python .agents/skills/anti-dark-code/scripts/adc.py probe --repo . --write
python .agents/skills/anti-dark-code/scripts/adc.py plan --repo . --write
```

Then review:

- repo-type classification
- risk signals and their evidence paths
- proposed capability statuses
- proposed gate commands
- execution and hardware cautions

Run pass `01` and pass `02` to turn the deterministic profile into human-readable steering and architecture truth.

## Existing Repo Bootstrap

Before writing calibration, inspect existing:

- steering files
- architecture docs
- ADRs and runbooks
- CI workflows and package scripts
- test configuration
- coverage and findings records
- sibling repos and external control planes

Import fresh, evidence-backed facts into calibration. Mark stale or contradictory facts as stale, inferred, or unknown. Do not convert old prose into verified truth merely because it exists.

## Freshness Rules

Calibration earns trust only while aligned with the code.

Record at least:

- last verified date
- source commit or version when available
- evidence paths
- what changes invalidate the entry
- next check when confidence is below verified

Preflight should treat pass `02` as a diff when the system map is fresh. It should fall back to a wider map when the relevant directories, manifests, trust boundaries, or control planes changed.

## Host Discovery

Load `host-adapters.md` only after the canonical local copy exists.

- Codex and Gemini CLI can use the canonical `.agents/skills` location.
- Claude Code receives a thin adapter that points to the canonical copy.
- Other hosts receive a small pointer in their existing instruction surface.

Host adapters may change discovery and tool syntax. They must not duplicate or fork core policy.

## Safety Rules

- Do not execute repo code during installation or probing.
- Do not install testing dependencies automatically.
- Do not overwrite local calibration.
- Do not overwrite edited core files without surfacing the conflict.
- Do not place absolute developer paths in committed calibration.
- Do not let a repo-local skill write directly into a user-level or shared skill.

## Acceptance Checklist

Calibrated local mode is complete when:

- one canonical repo-local core exists
- host discovery points to that core without policy duplication
- all calibration files exist or are deliberately deferred
- the repo profile and verification plan were generated deterministically
- proposed gates are exact command arrays and remain unexecuted until allowed
- core update ownership and calibration ownership are documented
- flow-back is proposal-only
