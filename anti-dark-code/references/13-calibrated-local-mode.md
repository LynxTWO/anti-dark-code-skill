# Calibrated local installation and migration

Compatibility reference 13. Load for explicit install, update, bootstrap or migration work. A one-off [task](../SKILL.md) needs no installation. This workflow changes skill files and calibration only, within existing authorization.

## Ownership and layout

The canonical project copy is .agents/skills/anti-dark-code/. Managed files are SKILL.md, VERSION, SOURCE-SCOPE.json, references/, scripts/, assets/, agents/ and .adc-managed.json. Repository-local changes belong in calibration/, not an independently edited core.

Keep these calibration names and existing schemas:

| File | Purpose |
| --- | --- |
| README.md, repo-binding.json | Local contract and hashed repository identity |
| repo-profile.json, verification-plan.json | Deterministic inventory and [capability assessment](verification-capabilities.md) |
| invariants.md, system-map.md | Local truths, rule authority, trust/control-plane boundaries |
| gates.json | Exact command arrays, approvals, constraints and source bindings |
| coverage-ledger.md, findings-ledger.md | Coverage freshness and finding dispositions |
| upstream-candidates.md, upstream.json | General lesson queue, version and proposal-only policy |

Templates remain in assets/templates/calibration/. Preserve target calibration during updates; never copy source calibration sideways.

## Source and physical boundaries

Normal sources require a valid universal SOURCE-SCOPE.json and clean templates. The installer rejects sources inside the target, managed installations, populated top-level calibration and internal links/junctions. Git sources must be clean and at a release tag; use a reviewed tag/extract plus its independently obtained published digest.

Repo-local managed core, calibration, Claude adapter and .anti-dark-code/ output paths must have real components and no nested link-like entries. User-level host aliases may point at a clean shared core; never symlink repository-managed state to it. Use [host adapters](host-adapters.md).

Recovery flags are never batch defaults: --force surfaces reviewed managed-file conflicts; --allow-unsafe-source permits reviewed legacy-source recovery but still excludes source calibration and unsafe templates; --allow-untagged-source accepts a deliberately reviewed unreleased source. None grants execution authority.

## Review and apply

From the clean shared skill root, dry-run first:

~~~bash
python3 scripts/adc.py install --repo /path/to/repo --expect-core-digest <published-digest>
python3 scripts/adc.py bootstrap --repo /path/to/repo --hosts all --expect-core-digest <published-digest>
~~~

Choose install for managed-core updates or bootstrap for install/profile/plan. Inspect source integrity, binding, conflicts, legacy stores and proposed gate changes. Add --apply only within authorization for that reviewed plan. These commands do not execute repository code or install testing dependencies.

Bootstrap dry-run previews bounded discovery, affected gate IDs/actions/reasons, change count and confirmation resets without calibration writes. Preserve an approved gate whose exact source binding still verifies even if bounded discovery misses it. Changed/removed bound sources invalidate that approval.

## Binding and migration

States remain new, match, unbound, invalid and mismatch. Identity hashes normalized Git origin, or resolved location without an origin. Root commits are hashed continuity evidence; they do not override a remote mismatch. Matching identity is not factual freshness.

Read MIGRATION.md from the reviewed source package before applying; it is not part of the installed managed core. Inspect existing instructions, maps, CI, tests, coverage, findings, skill stores and external boundaries. Back up competing stores, select the canonical same-repository evidence, preserve contradictions, and retire older stores only after successful use. The historical .anti-dark-code/calibration fallback migrates only when canonical calibration is absent.

--accept-unbound-calibration requires reviewed same-repository legacy provenance and cannot accept invalid records. --rebind-calibration requires a reviewed move/fork/identity change; never use it for unrelated calibration. Migrated, accepted or rebound gates reset to disabled/proposed and clear global execution confirmation. Do not import old prose as verified truth.

## Verify the result

Validate the correct layer: distribution for clean releases, universal for shared cores with an inbox, installed for managed copies. Installed validation checks .adc-managed.json integrity, path safety and current binding.

Generate probe/plan artifacts with --write only when authorized. Review exclusions, classifications, risk evidence, capability statuses, exact gates and hardware constraints. A bounded scan proves presence; unrecognized source extensions and missing external runtime access remain limitations. Use [Understand](tasks/understand.md) and [Verify](tasks/verify.md) for needed interpretation.

gates.json is an owner-controlled trust record, not a signature. Review command, cwd, environment, inputs, timeout, approval and source binding together; untrusted branch booleans grant nothing. Gate planning/execution refuses unsafe binding; applicable enabled gates blocked by review or drift return 2 even without execution. [Flowback](15-dogfeeding-flowback.md) also requires matching binding and a clean universal parent.

Record freshness date, source identity, evidence, invalidators and next checks. Complete when canonical ownership, binding, integrity, reviewed proposals and limitations are recorded; stop at unsafe paths, foreign calibration, unresolved conflicts or unauthorized changes.
