# Anti-Dark-Code

A skill that teaches AI coding assistants (Claude Code, Codex, Gemini CLI, and others) to work on codebases from evidence instead of guesswork: map what actually runs, prove claims or record them as unknowns, hold risky changes behind approval gates, and verify work with deterministic checks instead of confident prose.

- **Plain-language overview**: https://lynxtwo.github.io/anti-dark-code-skill/
- **Version**: `2026.08.06-unified.4` (see `CHANGELOG.md`)

One model-neutral core, repo-local calibration, and deterministic local tooling. No network calls, no telemetry, no dependencies beyond Python 3 for the optional tooling.

## Quick start if you are new to all of this

You do not need to understand any of the machinery. If you use an AI coding assistant, paste this into it (one line):

```text
Install the anti-dark-code skill for me: download https://github.com/LynxTWO/anti-dark-code-skill to a temporary folder, place its inner anti-dark-code folder into my assistant's skills directory (~/.claude/skills/ for Claude Code, ~/.agents/skills/ for Codex or Gemini), delete the downloaded copy, and confirm by reading the skill's VERSION file. Then tell me what it can do.
```

Your assistant will ask permission to run a download command and a copy command. That is normal for this one-time install; approve them. If your assistant says it cannot download things, do the by-hand steps below yourself, then tell it where you put the folder.

Prefer doing it by hand? Open https://github.com/LynxTWO/anti-dark-code-skill in your browser, click the green **Code** button, then **Download ZIP**. Unzip it and copy the inner `anti-dark-code` folder so you end up with:

| Your assistant | Final result |
|---|---|
| Claude Code | `~/.claude/skills/anti-dark-code/SKILL.md` exists |
| Codex or Gemini | `~/.agents/skills/anti-dark-code/SKILL.md` exists |

Three by-hand pitfalls, named so you can dodge them:

- `~` means your home folder (on Windows, `C:\Users\<you>`). Folders starting with a dot are hidden by default: press Cmd+Shift+. in the Mac Finder or Ctrl+H in most Linux file managers to reveal them.
- If the `skills` folder does not exist yet, create it.
- If you end up with `anti-dark-code` inside another `anti-dark-code`, move the inner one up a level. A double-nested copy fails silently, with no error anywhere.

If any of that sounds tedious: use the paste method above instead. That is what it is for.

Then close your assistant and open it again inside the folder of the project you care about (skills are discovered when a session starts), and ask things like:

- "Use anti-dark-code to map this project and tell me what actually runs."
- "Audit this codebase with anti-dark-code before I change anything."
- "What do we NOT know about this repo? Record the unknowns."
- "Set up automatic checks for this project and walk me through approving them."

Four things to know, in plain terms:

1. **The checks this skill sets up never run without your approval.** Commands it wants to run are written into a file as proposals; nothing executes until you approve each one and confirm. You can simply never approve anything, and it will only ever look.
2. **It refuses to guess.** Everything it records is marked as proven, likely, or unknown, with the evidence cited. If it cannot prove something, it says so instead of sounding confident.
3. **It keeps its notes inside your project.** Maps, checklists, and open questions live in a small folder in the project so the next session remembers. It asks before creating them, and they are ordinary text files you can read and delete.
4. **It works on any language or stack.** The skill adapts what it checks to what your project actually is.

## Already using an older version?

**If the skill just lives in your assistant's skills folder** (no per-project installs): replacing the folder is the whole upgrade. Paste this into your assistant:

```text
Update my anti-dark-code skill: replace the anti-dark-code folder in my
assistant's skills directory with the latest one from
https://github.com/LynxTWO/anti-dark-code-skill and confirm the new
version by reading its VERSION file.
```

**If you installed it into projects** (there is a `.agents/skills/anti-dark-code/` folder inside a repository): upgrade each project by re-running the installer from the new core. It preserves your project's `calibration/` knowledge, verifies the repository binding, and stops on conflicts instead of overwriting:

```bash
python3 /path/to/new/anti-dark-code/scripts/adc.py install --repo /path/to/repo --hosts all --apply
```

**If you are coming from a version before repository binding existed** (the old separate Claude and Codex variants, or any copy without `calibration/repo-binding.json`): read `MIGRATION.md` first. The installer will flag your calibration as `unbound` and require an explicit `--accept-unbound-calibration`; accepting deliberately resets every gate to disabled and proposed, because old approvals do not survive migration. That is protection, not breakage: review the gates once and re-approve.

## For senior developers

Everything below this point is the operator manual: the three-layer trust model, deterministic tooling (`adc.py`), repository binding, gate approval semantics, exit codes, and flow-back. The short version of what you are looking at:

- **One universal core, many hosts.** The skill ships as a single model-neutral tree; each assistant discovers it through its own path (symlink or junction at user level). Host-specific behavior lives in small addenda, never in forked cores.
- **Repo installs are managed and checksummed.** `adc.py bootstrap` places a checksummed core copy (local edits are detected and block the next upgrade rather than being prevented outright) plus a repo-owned `calibration/` overlay (invariants, system map, exact gates, ledgers) that survives core upgrades. Installation and profiling never execute repository code.
- **Calibration is bound to one repository** by hashed identity. Foreign or unbound calibration is refused for gate execution and flow-back; migration resets all gate approvals by design.
- **Gates are exact argv arrays with three locks** (per-gate approval, recorded owner confirmation, an explicit exec flag), real exit codes, bounded failure packets, and process-tree timeout kills. Blocked plans exit `2` even in dry runs, so CI can tell clean from blocked.
- **Knowledge flows one way.** Core flows down into repos; repo lessons flow up only as sanitized, content-hashed proposals into `incoming/` for human review. A compromised repo cannot rewrite the shared skill.
- **The design rule underneath**: never spend model intelligence on work a compiler, schema, diff, seed, or reviewed deterministic command can settle exactly. Agents do judgment; the computer does mechanics and evidence.

Read next: `anti-dark-code/SKILL.md` (the pass router and evidence rules), `anti-dark-code/references/` (one file per pass), `MIGRATION.md` (adopting or upgrading existing installations), `AUDIT-AND-DESIGN.md` (why it is shaped this way).

### Multi-machine pattern

Clone this repository once per machine, point each host's user-level skills path at the clone's `anti-dark-code/` directory (symlink on Linux and macOS, junction on Windows), and let git be the transport:

```text
laptop clone  <->  this repository  <->  desktop clone
     |                                        |
user-level symlinks                 user-level junctions
     |                                        |
repo installs via adc.py            repo installs via adc.py
     \_______ flowback proposals to incoming/ ______/
```

Set `ADC_PARENT_SKILL` to your clone's `anti-dark-code/` path so `flowback --stage-to-parent` needs no `--parent` argument. Do not use file-sync services (OneDrive, Dropbox) on the clone; partial syncs and conflict copies corrupt git repositories and will fail this skill's clean-source validation.

## Contributing, and a note on trust

Issues and pull requests are welcome. `main` is protected: all changes land by pull request and are reviewed by the maintainer alone.

Be aware of what this repository is: **skill text becomes instructions executed by AI assistants with their operator's authority.** A malicious or careless change here would run, in effect, with the hands of everyone who installs it. Contributions are therefore reviewed as executable code, strictly. The same caution applies to you: if you fork this skill, review what you ship.

---

## What It Does

- Evaluates all 20 verification capabilities for every repository.
- Selects, defers, or rejects capabilities instead of forcing every technique into every project.
- Installs one canonical repo-local copy at `.agents/skills/anti-dark-code/`.
- Keeps repo-specific learning under `calibration/` so it survives managed-core updates.
- Binds calibration to one hashed repository identity to prevent accidental cross-repo transfer.
- Gives Claude Code a thin adapter instead of a second editable policy tree.
- Lets Codex and Gemini CLI use the canonical `.agents/skills` copy.
- Uses local deterministic scripts for profiling, planning, changed-slice routing, exact gate execution, real exit codes, compact summaries, failure packets, checksums, and flow-back staging.
- Excludes repo-level host skill trees under `.agents/skills/`, `.claude/skills/`, `.gemini/skills/`, and `.codex/skills/` from repository evidence so tooling does not distort repo classification.
- Returns exit code `2` when a gate plan is blocked, including dry runs, and terminates timed-out gate process trees on a best-effort basis.
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

These user-level aliases are only for host discovery of the shared core. Never symlink a repository's `.agents/skills/anti-dark-code/`, its `calibration/`, its Claude adapter, or `.anti-dark-code/` run-artifact paths to the shared core or another location. Repo-local managed paths must be real paths so one repository cannot write into shared or foreign state. The installer fails closed on symbolic-link or Windows-junction components and nested link-like entries.

Do not use a repo-local customized copy as the shared source for another repository.

## Validate the Correct Layer

A release or ZIP candidate must pass strict distribution validation:

```bash
cd /path/to/package/anti-dark-code
python3 scripts/adc.py validate --mode distribution
python3 -m unittest discover -s tests -v
```

A live shared core may contain reviewed or pending flow-back proposals under `incoming/`. Validate that working copy with:

```bash
python3 scripts/adc.py validate --mode universal
```

Universal validation ignores ordinary proposal files in the runtime-only `incoming/` inbox and reports them as a warning. It rejects symlinked or junction-backed inbox entries because proposal staging must not be redirectable. Distribution validation rejects the entire inbox so proposals cannot leak into a shipped package or repo-local installation.

An installed repository copy carries repo-owned calibration and `.adc-managed.json`. Validate it from the repository root with:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py validate \
  --skill .agents/skills/anti-dark-code \
  --mode installed
```

`--mode auto` detects an installed copy when `.adc-managed.json` is present and treats the canonical repo-local `.agents/skills/anti-dark-code/` path as installed. Installed validation checks managed-core hashes, calibration path safety, and the repository binding while treating ordinary `calibration/` files as local state rather than universal-source contamination.

Ordinary `python3` is sufficient. The unit suite builds clean temporary package fixtures, so its own runtime `__pycache__` does not create a false packaging failure. Distribution validation still rejects `__pycache__` and `.pyc` files that are actually present in a release candidate.

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

After application, validate the installed copy with `--mode installed` before trusting repo-local calibration or gates.

## Migrate an Existing Repository

Read `MIGRATION.md` before applying changes.

The installer reports whether existing calibration is:

- `new`
- `match`
- `unbound`
- `invalid`
- `mismatch`

`--accept-unbound-calibration` applies only to reviewed legacy calibration that has no binding. An `invalid` binding is not accepted by that flag. Repair it or quarantine the affected calibration before migration.

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
A dry gate plan returns exit code `2` when an enabled applicable gate is blocked by review status, stale source evidence, or calibration binding. This lets CI and agent harnesses distinguish a clean plan from a blocked plan without executing repository code.

Then run:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py gates \
  --repo . \
  --level 1 \
  --allow-exec
```

Gate planning and execution are refused if calibration is unbound, invalid, or belongs to another repository identity.

For changed-slice routing:

```bash
python3 .agents/skills/anti-dark-code/scripts/adc.py gates \
  --repo . \
  --level 1 \
  --changed-from HEAD~1 \
  --allow-exec
```

Successful checks collapse to a compact summary. Failures create a bounded JSON packet and retain a pattern-redacted log under `.anti-dark-code/runs/`. When a gate times out, the runner terminates its POSIX process group or Windows process tree on a best-effort basis and records the termination result in the failure packet. Pattern redaction reduces exposure but cannot prove that every sensitive value was removed.

## Gate Runner Exit and Timeout Semantics

The gate runner uses these top-level exit codes:

- `0`: valid dry-run plan, no applicable gates, or all executed gates passed
- `1`: one or more executed gates failed, including a timeout recorded as gate exit `124`
- `2`: planning or execution was refused because calibration, approval, source fingerprints, or owner confirmation were unsafe
- `130`: interrupted by the operator

A timeout launches each gate in its own process group. On POSIX systems the runner signals the process group. On Windows it uses a new process group and falls back to `taskkill /T /F`. This is best-effort containment, not a sandbox. A child that deliberately detaches from the process group may require stronger operating-system isolation.

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
