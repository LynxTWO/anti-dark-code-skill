# Anti-Dark-Code Skill, Unified 2026-08-06

This package replaces separate model-specific copies with one model-neutral core, repo-local calibration, optional host adapters, and deterministic local tooling.

Version: `2026.08.06-unified.3`

## What It Does

- Evaluates all 20 verification capabilities for every repository.
- Selects, defers, or rejects capabilities instead of forcing every technique into every project.
- Installs one canonical repo-local copy at `.agents/skills/anti-dark-code/`.
- Keeps repo-specific learning under `calibration/` so it survives managed-core updates.
- Binds calibration to one hashed repository identity to prevent accidental cross-repo transfer.
- Gives Claude Code a thin adapter instead of a second editable policy tree.
- Lets Codex and Gemini CLI use the canonical `.agents/skills` copy.
- Uses local deterministic scripts for profiling, planning, changed-slice routing, exact gate execution, real exit codes, compact summaries, failure packets, checksums, and flow-back staging.
- Keeps source-side repo calibration out of every installation.
- Prevents repo-local lessons from silently rewriting the shared skill.

## The Three-Layer Model

```text
clean universal shared core
        |
        v
managed repo-local core
        |
        v
one-repository calibration
```

The shared core may flow downward into many repositories.

Calibration never flows sideways from one repository to another.

General lessons may flow upward only as reviewed proposals.

## Package Layout

```text
Anti-Dark-Code-Skill-Unified-2026-08-06/
  README.md
  AUDIT-AND-DESIGN.md
  MIGRATION.md
  CHANGELOG.md
  MANIFEST.sha256
  anti-dark-code/
    SKILL.md
    VERSION
    SOURCE-SCOPE.json
    agents/openai.yaml
    references/
    assets/
    scripts/adc.py
    tests/test_adc.py
```

`SOURCE-SCOPE.json` identifies the directory as a clean universal source core. A populated top-level `calibration/` directory does not belong in that shared source.

## Recommended Shared Installation

Keep one version-controlled shared core and let each host discover that same directory.

```text
~/.agents/skills/anti-dark-code/    canonical shared core for Codex and Gemini CLI
~/.claude/skills/anti-dark-code/    symlink or thin adapter to the same core
```

On systems that support directory symlinks:

```bash
SHARED=/path/to/shared/anti-dark-code
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
ln -s "$SHARED" "$HOME/.agents/skills/anti-dark-code"
ln -s "$SHARED" "$HOME/.claude/skills/anti-dark-code"
```

Use a directory junction or thin adapter where symlinks are unavailable.

Do not use a repo-local customized copy as the shared source for another repository.

## Validate the Package

From the clean shared skill root:

```bash
cd /path/to/shared/anti-dark-code
python3 scripts/adc.py validate
python3 -m unittest discover -s tests -v
```

Ordinary `python3` is sufficient. The unit suite validates a clean package copy so its own runtime `__pycache__` does not create a false packaging failure. The strict package validator still rejects `__pycache__` and `.pyc` files that are actually present in the package being validated.

## Bootstrap a New Repository

Dry run first:

```bash
python3 /path/to/shared/anti-dark-code/scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --hosts all
```

Apply after reviewing the plan:

```bash
python3 /path/to/shared/anti-dark-code/scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --hosts all \
  --apply
```

Bootstrap does not execute repository code and does not install dependencies.

## Migrate an Existing Repository

Read `MIGRATION.md` before applying changes.

The installer reports whether existing calibration is:

- `new`
- `match`
- `unbound`
- `invalid`
- `mismatch`

Trusted same-repo legacy calibration requires explicit acceptance:

```bash
python3 /path/to/shared/anti-dark-code/scripts/adc.py bootstrap \
  --repo /path/to/repo \
  --accept-unbound-calibration \
  --apply
```

A reviewed move, fork, or remote identity change may require:

```bash
--rebind-calibration
```

Do not use a rebind to legitimize calibration copied from an unrelated repository.

The installer also blocks an unmarked, repo-local, managed-install, or repo-calibrated source by default. `--allow-unsafe-source` exists for advanced recovery after manual review. Even then, source-side calibration is ignored and contaminated templates remain blocked.

When legacy calibration is accepted, moved from the fallback location, or explicitly rebound, all migrated gates are reset to disabled and proposed. Global execution confirmation is reset as well. Old approvals do not survive migration.

## Repo-Local Layout

```text
.agents/skills/anti-dark-code/
  SKILL.md
  VERSION
  SOURCE-SCOPE.json
  references/
  scripts/
  assets/
  agents/
  .adc-managed.json
  calibration/
    README.md
    repo-binding.json
    repo-profile.json
    verification-plan.json
    gates.json
    invariants.md
    system-map.md
    coverage-ledger.md
    findings-ledger.md
    upstream-candidates.md
    upstream.json
```

The managed core is updated from the clean shared source.

The repository owns `calibration/`.

`repo-binding.json` prevents silent reuse in another repository. It stores hashes, not the raw Git remote or a personal path.

## Review the Generated Calibration

The most important files are:

```text
.agents/skills/anti-dark-code/calibration/repo-binding.json
.agents/skills/anti-dark-code/calibration/repo-profile.json
.agents/skills/anti-dark-code/calibration/verification-plan.json
.agents/skills/anti-dark-code/calibration/gates.json
.agents/skills/anti-dark-code/calibration/invariants.md
.agents/skills/anti-dark-code/calibration/system-map.md
```

The repo probe is bounded. It supplies evidence of presence, not proof of absence. Human-readable steering and architecture work still provide meaning, rule authority, trust boundaries, and external control-plane knowledge.

## Run Gates

Dry run:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py gates \
  --repo . \
  --level 1
```

Before execution, review each proposed gate. For every command you approve, set:

```json
"enabled": true,
"review_status": "approved"
```

After every enabled gate is approved, set:

```json
"owner_confirmed_safe_to_execute": true
```

Any new or changed generated gate resets that confirmation. Package-script gates also carry a source fingerprint, so a changed script is blocked until the plan is refreshed and reapproved.

Then run:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py gates \
  --repo . \
  --level 1 \
  --allow-exec
```

Gate execution is refused if calibration is unbound or belongs to another repository identity.

For changed-slice routing:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py gates \
  --repo . \
  --level 1 \
  --changed-from HEAD~1 \
  --allow-exec
```

Successful checks collapse to a compact summary. Failures create a bounded JSON packet and retain a pattern-redacted log under `.anti-dark-code/runs/`. Pattern redaction reduces exposure but cannot prove that every sensitive value was removed.

## Dogfeeding and Flow-Back

Repo-specific facts stay in calibration.

General lessons begin in:

```text
.agents/skills/anti-dark-code/calibration/upstream-candidates.md
```

Stage ready lessons as a proposal:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py flowback --repo .
```

To place a proposal in the clean shared skill's `incoming/` folder:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py flowback \
  --repo . \
  --parent /path/to/shared/anti-dark-code \
  --stage-to-parent
```

Flow-back requires matching repo calibration and a clean universal parent. It does not edit shared core files. Promotion remains a human-reviewed change.

## Core Safety Rules

- Never transplant `calibration/` between unrelated repositories.
- Never use a repo-local fork as another repository's normal installation source.
- Never import old gates as enabled or approved.
- Never treat legacy prose as verified truth without current evidence.
- Never let a local repo write directly into shared core policy.
- Never spend model intelligence on work a compiler, schema, dependency graph, seed, assertion, diff, checksum, or reviewed deterministic command can perform exactly.

Use agents for judgment. Use the computer for mechanics and evidence.
