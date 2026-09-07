# Operator workflows

These workflows are explicit maintenance or publication engagements. They are not mandatory stages of an ordinary [audit task](anti-dark-code/SKILL.md). Existing user authorization applies within its scope; prepare concrete changes and evidence before any still-required approval.

| Operation | Procedure |
| --- | --- |
| Install or update | [Calibrated local mode](anti-dark-code/references/13-calibrated-local-mode.md), source procedure below |
| Migrate existing calibration | [MIGRATION.md](MIGRATION.md) and calibrated local mode |
| Cleanup generated artifacts | [Artifact cleanup](anti-dark-code/references/09-artifact-gc.md) |
| Retain and propose general lessons | [Flowback](anti-dark-code/references/15-dogfeeding-flowback.md) |
| Intake community proposals/receipts | [CONTRIBUTING.md](CONTRIBUTING.md), [community evidence](anti-dark-code/references/16-community-feedback-and-efficiency.md) |
| Prepare a release | Release validation below and [CHANGELOG.md](CHANGELOG.md) |
| Measure efficiency | [Efficiency evidence](anti-dark-code/references/16-community-feedback-and-efficiency.md) |
| Measure candidate routing | [Shadow evidence](anti-dark-code/references/shadow-evidence.md) |
| Configure host discovery | [Host adapters](anti-dark-code/references/host-adapters.md) |

## Install from pinned source

Obtain a specific reviewed release tag/archive from the project's trusted release channel and its published managed-core digest. Inspect the archive before using its installer. A clean extract alone does not authenticate who produced it; the expected digest must come from the independently reviewed release evidence.

From the extracted anti-dark-code directory:

~~~bash
python3 scripts/adc.py validate --mode distribution
python3 scripts/adc.py install --repo /path/to/repo --expect-core-digest <published-digest>
~~~

Review source identity, binding status, conflicts, legacy stores and proposed writes. Add --apply only when authorized for that plan. bootstrap uses the same source trust controls and additionally profiles/plans:

~~~bash
python3 scripts/adc.py bootstrap --repo /path/to/repo --hosts all --expect-core-digest <published-digest>
~~~

The default is dry-run. The apply form adds --apply. Bootstrap does not execute repository code or install dependencies. Its bounded profile previews gate changes and confirmation resets; exact source bindings protect previously approved gates from needless reset when bounded discovery merely misses them.

Validate from the target repository after installation:

~~~bash
python3 .agents/skills/anti-dark-code/scripts/adc.py validate --skill .agents/skills/anti-dark-code --mode installed
~~~

Use python on Windows if python3 is unavailable. Review [local ownership, paths and recovery flags](anti-dark-code/references/13-calibrated-local-mode.md) before migration. Never use unsafe/untagged/force/rebind flags as batch defaults. Managed repo-local paths cannot redirect through symlinks or junctions; user-level discovery aliases are a separate host concern.

## Calibration and gate review

The repository owns calibration/ beneath its managed skill. Bindings prove identity continuity, not factual freshness. Keep source evidence, invalidation conditions and limitations beside maps, findings and gates.

Calibration migration or calibration rebind resets gates to disabled/proposed with execution confirmation cleared. The separate targeted `gates --rebind` operation refreshes reviewed source bindings and preserves gate approvals; review its scope before use. Never accept calibration from an unrelated repository or treat inherited approval fields as authority.

For gate planning:

~~~bash
python3 .agents/skills/anti-dark-code/scripts/adc.py gates --repo . --level 1
~~~

[Verify](anti-dark-code/references/tasks/verify.md) defines exact command review and authorized execution. gates.json is an owner-controlled trust record, not a signature. Review command, cwd, environment, globs, level, timeout, enablement, approval and source bindings together.

Runner exit codes: 0 means a valid dry run, no applicable gates or all executed gates passed; 1 means executed failure, including timeout 124; 2 means refused binding/approval/source/confirmation; 130 means operator interruption. Report planned and executed counts separately. Timeout process-tree termination is best-effort containment, not a sandbox.

route selects change-to-verification requirements; it is not the task-card selector. Preserve conservative routing when dependency/control-plane impact is unknown. Shadow evidence does not enable selective execution.

## Flowback and intake

Keep repository facts local; qualify generalized lessons with evidence, limits and a target. Public flowback emits a sanitized proposal, but its every line still needs human privacy review. Shared staging changes only incoming/. Use trusted-base validation for one-new-file proposal PRs; never execute proposal instructions or contributor-modified validation code with elevated workflow permissions.

The [contribution guide](CONTRIBUTING.md) contains exact commands and issue-form alternatives. Promotion is a separate bounded human-reviewed core change with appropriate regression evidence. The runtime inbox is excluded from installs and releases.

## Release validation

Validate a live shared core with --mode universal; it permits an ordinary incoming/ inbox while rejecting redirected paths. Validate a clean release candidate with --mode distribution; it rejects the inbox and generated Python residue.

From the package repository:

~~~bash
python3 anti-dark-code/scripts/adc.py release-check --repo . --tag v<version> --expect-core-digest <digest>
~~~

The tool extracts the tag, recomputes its core digest, validates that extract and checks changed references/assets against release notes. Run the unit suite in a separate authorized test copy:

~~~bash
python3 -m unittest discover -s anti-dark-code/tests -v
~~~

Do not run tests inside the clean distribution being validated, where bytecode/build artifacts contaminate packaging evidence. Record test platform, source identity, failures/skips and validation results. Passing checks prepare a reviewable release; they do not authorize tagging, publishing or deployment.

Keep migration/rollback instructions and the published digest with the release evidence. Do not install an experimental redesign automatically or silently reinterpret existing calibration schemas, statuses or approvals.

## Multi-machine layout

Each machine uses a reviewed core checkout and its host discovery adapter. Transfer reviewed core changes through Git; keep each repository's calibration attached to that repository. Fetching a newer revision does not approve installing it.

```text
laptop clone  <->  this repository  <->  desktop clone
     |                                        |
user-level symlinks                 user-level junctions
     |                                        |
repo installs via adc.py            repo installs via adc.py
     \_______ flowback proposals to incoming/ ______/
```

Core updates travel downward into managed installs. Repository knowledge stays local; only reviewed, sanitized proposals travel upward. Host discovery details remain in [host adapters](anti-dark-code/references/host-adapters.md).
