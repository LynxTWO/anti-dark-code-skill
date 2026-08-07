# Migration from Any Existing Anti-Dark-Code Installation

This guide applies whether the current installation is:

- a separate Claude Code or Codex skill
- an older shared Anti-Dark-Code core
- a repo-local customized fork
- a partial installation with only some references or scripts
- a mixed installation spread across `.agents`, `.claude`, `.gemini`, `.codex`, or `.anti-dark-code`
- a repository with existing invariants, gates, ledgers, findings, or other local memory
- a repository with no calibration yet

The safety rule is simple:

> The clean universal core flows into a repository. Repository knowledge stays inside that repository. General lessons flow back only as reviewed proposals.

Never use one repository's customized skill or calibration directory as the starting point for another repository.

## 1. Back Up Before Changing Anything

Keep a copy of every existing Anti-Dark-Code location until the new installation validates and the repository has completed at least one successful reviewed pass.

Common locations include:

```text
~/.agents/skills/anti-dark-code/
~/.claude/skills/anti-dark-code/
~/.gemini/skills/anti-dark-code/
~/.codex/skills/anti-dark-code/
<repo>/.agents/skills/anti-dark-code/
<repo>/.claude/skills/anti-dark-code/
<repo>/.gemini/skills/anti-dark-code/
<repo>/.codex/skills/anti-dark-code/
<repo>/.anti-dark-code/
```

A backup is for recovery and comparison. It is not an approved source for another repository.

## 2. Establish One Clean Shared Core

Place the `anti-dark-code/` directory from this package in one version-controlled shared location.

A practical layout is:

```text
~/.agents/skills/anti-dark-code/    canonical shared core
~/.claude/skills/anti-dark-code/    symlink or thin adapter
```

A user-level symlink may be used only as a host-discovery alias for the clean shared core. Never symlink a repository's `.agents/skills/anti-dark-code/`, `calibration/`, Claude adapter, or `.anti-dark-code/` run directory to the shared core or another repository. Repo-local managed paths must be real paths. The installer refuses symbolic-link or Windows-junction components and nested link-like entries before dry-run or apply.

The shared core contains `SOURCE-SCOPE.json`. The installer uses that marker to distinguish a clean universal core from an old, unknown, or repo-calibrated source.

Do not put repo-owned `calibration/` beside the shared source core.

Do not merge an old repo-local `SKILL.md`, `references/`, `scripts/`, or `assets/` tree into the clean core. Extract individual general lessons for review instead.

Before migration, replace any symlinked or junction-backed repo-local skill or artifact path with a real directory. Do not solve this by copying another repository's local calibration. Install a fresh managed core, then migrate only reviewed same-repo facts.

## 3. Validate the Correct Layer

Use explicit validation modes during migration.

Validate a clean extracted release or ZIP candidate with strict distribution rules:

```bash
cd /path/to/package/anti-dark-code
python3 scripts/adc.py validate --mode distribution
python3 -m unittest discover -s tests -v
```

Distribution mode rejects runtime `incoming/`, repo calibration, managed-install metadata, symlinks or junctions, `__pycache__`, and `.pyc` files.

Validate a deployed shared core, which may contain staged proposals under `incoming/`, with:

```bash
python3 /path/to/shared/anti-dark-code/scripts/adc.py validate \
  --skill /path/to/shared/anti-dark-code \
  --mode universal
```

Universal mode excludes ordinary files in the runtime-only proposal inbox and repo calibration from core policy checks. It rejects symlinked or junction-backed inbox entries because proposal staging must not be redirected. It reports Python runtime caches as warnings. This lets the tests and validator run from a real shared installation rather than assuming a pristine package directory or an outer `MIGRATION.md`.

After installing into a repository, validate that copy with:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py validate \
  --skill .agents/skills/anti-dark-code \
  --mode installed
```

Installed mode verifies `.adc-managed.json` hashes and the core digest, checks the source marker and version, rejects link-like calibration entries, parses local calibration JSON, and confirms that the repository binding matches. A valid installed copy no longer fails merely because it contains ordinary repo-owned calibration.

`--mode auto` detects installed copies from their managed manifest or canonical repo location. Use explicit modes for release automation.

The test suite is expected to pass with ordinary `python3`. `python3 -B` is not required. It builds clean distribution fixtures internally, so test-created `__pycache__` files do not become packaging false positives.

Stop if the selected validation mode fails.

## 4. Migrate One Repository at a Time

Never perform a blind multi-repo copy.

For each repository, run a dry bootstrap from the clean shared source:

```bash
python3 /path/to/shared/anti-dark-code/scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --hosts all
```

Review the JSON plan before adding `--apply`.

The plan reports:

- source-scope safety
- managed-file conflicts
- existing calibration locations
- whether calibration is new, matching, unbound, invalid, or mismatched
- whether old fallback calibration can be migrated safely
- which source calibration files would be ignored
- which explicit migration flag is required, if any

A dry run does not execute repository code or install dependencies.

## 5. Understand the Repository Binding

Every repo-local calibration now contains:

```text
calibration/repo-binding.json
```

The binding stores a hashed repository identity. It does not store the raw Git remote or a personal absolute path.

The installer assigns one of these states:

| State | Meaning | Normal action |
|---|---|---|
| `new` | No existing calibration was found | Apply normally |
| `match` | Calibration belongs to this repository identity | Apply normally |
| `unbound` | Legacy calibration exists without a binding | Review it, then explicitly accept it |
| `invalid` | The binding file is malformed, incomplete, or contains unsafe entries | Repair it or quarantine the affected calibration. It cannot be accepted automatically |
| `mismatch` | Calibration is bound to another repository identity | Stop unless this is a verified move, fork, or remote change |

### Accept trusted legacy calibration

Use this only after confirming the old calibration came from the same repository:

`--accept-unbound-calibration` applies only to the `unbound` state. It does not override an invalid binding or symlink safety failure.

```bash
python3 /path/to/shared/anti-dark-code/scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --hosts all \
  --accept-unbound-calibration \
  --apply
```

### Rebind after a reviewed repository identity change

Use this only when the repository was deliberately moved, forked, or given a new remote and the calibration still applies:

```bash
python3 /path/to/shared/anti-dark-code/scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --hosts all \
  --rebind-calibration \
  --apply
```

A rebind records the previous hashed repository id in the binding history.

Do not use `--rebind-calibration` to make a copied calibration directory appear legitimate in an unrelated project.

## 6. Classify Existing Material Before Importing It

Do not migrate files by filename alone. Classify their purpose.

| Existing content | Migration treatment |
|---|---|
| Universal workflow, evidence rules, pass definitions, and safety policy | Replace with the clean new core |
| Claude, Codex, Gemini, or other host mechanics | Replace with the new thin adapter or host addendum |
| Same-repo invariants | Review and move the supported facts into `calibration/invariants.md` |
| Same-repo architecture and rule authority | Review and move supported facts into `calibration/system-map.md` |
| Same-repo commands and machine cautions | Convert into disabled, proposed entries in `calibration/gates.json` |
| Coverage history | Import only if the evidence and invalidation triggers remain current |
| Findings history | Import only if status, evidence, and next action remain accurate |
| General lessons that may help other repos | Put them in `calibration/upstream-candidates.md` for proposal-only flow-back |
| Logs, snapshots, scratch scripts, generated reports, or temporary artifacts | Quarantine and review separately |
| Repo-specific edits made inside old core files | Extract the local fact or general lesson. Do not copy the entire core file |
| Unknown or contradictory material | Mark it unknown, stale, or deferred. Do not promote it to verified truth |

The old material is evidence to review, not authority to inherit.

## 7. Keep Repo Knowledge in the Same Repo

The canonical local location is:

```text
<repo>/.agents/skills/anti-dark-code/calibration/
```

Never copy that directory into another repository as a template.

This includes:

- repository names
- local paths
- architecture assumptions
- trust boundaries
- invariants
- gate commands
- hardware notes
- test expectations
- findings
- coverage claims
- replay seeds
- remote-system assumptions

A similar tech stack does not make two repositories the same system.

## 8. Convert Old Gates Safely

Old prose commands and shell snippets may be useful, but they are not pre-approved.

Convert each reviewed command into an exact argument array. Imported gates must begin disabled and proposed:

```json
{
  "id": "typecheck",
  "level": 0,
  "argv": ["npx", "tsc", "--noEmit"],
  "enabled": false,
  "review_status": "proposed",
  "source": "migrated from a same-repo legacy gate record",
  "confidence": "inferred",
  "timeout_seconds": 300,
  "resource_class": "light",
  "cwd": ".",
  "include_globs": ["**/*.ts", "**/*.tsx"],
  "exclude_globs": []
}
```

Then:

1. Verify what the command actually runs.
2. Verify its working directory and environment requirements.
3. Confirm it cannot deploy, mutate production data, publish, or install unknown dependencies.
4. Run it manually when appropriate.
5. Change `review_status` to `approved` only after review.
6. Set `enabled` to `true` only when it belongs in the selected confidence level.
7. Set `execution_policy.owner_confirmed_safe_to_execute` to `true` only after all enabled gates are reviewed.

A migrated gate never inherits approval from an old document.

Each executed gate runs in a separate process group. A timeout is recorded as gate exit `124`, and the runner makes a best-effort attempt to terminate the entire process tree before returning a failed run. This is containment, not a sandbox.

When the installer accepts unbound calibration, rebinds calibration, or moves fallback calibration into the canonical location, it resets every migrated gate to `enabled: false` and `review_status: proposed`. It also resets global execution confirmation. This is deterministic protection, not merely a documentation rule.

## 9. Handle Multiple Existing Installations

When several old copies exist inside the same repository:

1. Choose the calibration that has the strongest same-repo evidence.
2. Compare the others against it.
3. Merge facts manually, one category at a time.
4. Preserve contradictions as unknowns until settled.
5. Do not let the installer merge two populated calibration stores silently.
6. Keep old directories read-only until the new calibration is verified.

The installer may detect legacy calibration under `.anti-dark-code`, `.claude`, `.gemini`, or `.codex`. Only the historical `.anti-dark-code/calibration` fallback is eligible for limited missing-file migration, and only when the canonical target does not already contain calibration. Other stores remain visible for manual review.

## 10. Treat Customized Old Cores as Donors, Not Sources

An old repo-local customized skill may contain valuable learning. It is still not a clean installation source.

The normal rule is:

```text
clean shared core -> repo-local managed core
old repo-local core -> reviewed local facts or upstream proposals only
```

The installer blocks a source that:

- lacks a valid universal source marker
- sits inside the target repository
- contains a repo-local `.adc-managed.json` installation manifest
- contains top-level repo calibration
- contains bound or contaminated calibration templates
- contains internal symlink or junction entries

`--allow-unsafe-source` exists only for advanced recovery after manual review. Even with that flag, source-side calibration is ignored and never copied. Contaminated calibration templates remain blocked.

Prefer fixing or replacing the source instead of using the override.

## 11. Apply the Installation

For a clean repo or a repo with matching calibration:

```bash
python3 /path/to/shared/anti-dark-code/scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --hosts all \
  --apply
```

After application, verify:

```text
.agents/skills/anti-dark-code/SKILL.md
.agents/skills/anti-dark-code/SOURCE-SCOPE.json
.agents/skills/anti-dark-code/.adc-managed.json
.agents/skills/anti-dark-code/calibration/repo-binding.json
.agents/skills/anti-dark-code/calibration/repo-profile.json
.agents/skills/anti-dark-code/calibration/verification-plan.json
.agents/skills/anti-dark-code/calibration/gates.json
```

Confirm that the binding status is `match` when assessed in that repository.

Validate the installed copy through its managed manifest and repo binding:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py validate \
  --skill .agents/skills/anti-dark-code \
  --mode installed
```

`--mode auto` also selects installed validation when `.adc-managed.json` is present. Do not validate an installed copy as a universal source. Its repo-owned `calibration/` directory is expected local state, while `.adc-managed.json` is the authority for managed-core integrity.

If calibration was migrated or rebound, inspect `migrated_gate_approvals` in the apply result and confirm every old gate is disabled and proposed.

Do not remove the legacy copy until installed validation passes.

## 12. Consolidate Host Copies

After the canonical repo copy works:

- Codex and Gemini can use `.agents/skills/anti-dark-code/` directly.
- Claude Code should use a thin adapter that points to the canonical copy.
- Other hosts should use a pointer or minimal discovery adapter.
- Retire duplicate editable host cores.

Do not maintain separate policy trees for each model.

## 13. Verify Isolation Before Removing Old Files

Check all of the following:

- The shared source has no top-level `calibration/` directory.
- The repo-local skill, calibration, adapter, and run paths contain no symlink or junction components and no nested link-like entries.
- The repo-local `repo-binding.json` matches the current repository.
- No other repository's names, paths, gates, findings, or invariants appear in this repo's calibration.
- Imported gates remain disabled and proposed until reviewed.
- `execution_policy.owner_confirmed_safe_to_execute` is false after gate migration.
- Installed validation passes against `.adc-managed.json` and the repo binding.
- The managed core matches `.adc-managed.json` or every difference is understood.
- The repo profile and system map describe this repo, not a donor repo.
- Flow-back candidates state general rules without private paths or project assumptions.

A blocked dry gate plan returns exit code `2`, even without `--allow-exec`. Treat that as a migration stop, not as a successful no-op.

Run a normal dry gate plan before executing anything:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py gates \
  --repo . \
  --level 1
```

Gate planning and execution are refused when calibration is unbound, invalid, or foreign. A blocked dry run exits with status `2`; it does not report a successful plan merely because `--allow-exec` was absent.

## 14. Use Proposal-Only Flow-Back

Broad lessons belong first in:

```text
calibration/upstream-candidates.md
```

Stage a proposal from the bound local repo:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py flowback --repo .
```

To place it in the clean shared core's review inbox:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py flowback \
  --repo . \
  --parent /path/to/shared/anti-dark-code \
  --stage-to-parent
```

Flow-back refuses unbound or foreign calibration. It also refuses a parent that is not a clean universal core.

The proposal does not edit shared references or scripts. Promotion remains a separate human-reviewed and tested change.

## 15. Update Existing Repo Copies Later

Run the installer again from the clean shared source.

It will:

- preserve matching repo-owned calibration
- verify the repository binding
- compare managed-file checksums
- stop on locally modified managed core files unless `--force` is explicit
- ignore any source-side top-level calibration
- refresh source version and core digest metadata

Use `--force` only for understood managed-core conflicts. It does not override binding or source-safety decisions.

## 16. Roll Back Safely

If migration fails:

1. Stop before executing gates.
2. Restore the backed-up repo-local skill and calibration.
3. Keep the new shared core separate.
4. Compare the dry-run plan and binding status.
5. Resolve one conflict class at a time.
6. Repeat the dry run.

Do not solve a migration conflict by copying a known-working calibration from another repository.

## 17. Batch Migration Rule

For many repositories, automate only the repeatable outer loop:

```text
for each repo:
  dry run
  save plan
  stop on blocked status
  require repo-specific review
  apply only approved flags
  verify binding and isolation
```

Do not apply `--accept-unbound-calibration`, `--rebind-calibration`, `--allow-unsafe-source`, or `--force` globally across a list of repositories.

Each flag represents a separate human judgment about one repository.
