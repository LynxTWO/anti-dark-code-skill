# Changelog

## Unreleased

Not a release. These land in the next tagged version.

### Release and Install Provenance

Four guards, added after `unified.7` shipped a tag that did not reproduce the core distributed from it and notes that did not describe everything the release carried. Both defects were found by an independent reviewer at a consuming repository, and neither was caught by anything in this repository, because nothing checked them.

- **The installer refuses a source that is not at a release tag.** `install` and `bootstrap` classify the source as `git-tag`, `git-untagged`, `git-dirty`, or `non-git` and block the two moving kinds unless `--allow-untagged-source` is passed after review. A plain extract stays allowed: it cannot drift. This is the guard that would have stopped the original mistake.
- **`--expect-core-digest` binds an install to a published release.** The installer refuses unless the source core hashes to the expected digest, and the recorded `source_core_sha256` then lets a reviewer check the install against the release without rerunning anything.
- **`release-check` verifies a tag against itself.** It extracts the tag, recomputes the core digest, optionally compares it to the digest the release publishes, runs distribution validation on that extract, and returns nonzero on failure. Verifying a release by reading the working tree that produced it proves nothing about the tag.
- **Release notes must describe what the release changed.** `release-check` reports every file under `references/` or `assets/` that changed since the previous tag without being named in the new notes. Mechanical version-string churn is ignored so the check stays worth reading. Run against the historical tags, this reports the `unified.7` digest mismatch and its undescribed template change, and passes `unified.8`.

The deterministic suite grows by source-provenance classification across all four source kinds, both installer refusals, tag-reproduction failure and success, an undescribed reference change, and the version-churn exclusion. Counting everything below, it now stands at 144 tests, of which 131 pass and 13 skip on a Windows workstation without symlink privilege; a host that can create links runs about a dozen more.

### Mutation and Fuzz Coverage

- Pilots mutation testing on the highest-stakes modules and records what survived in `tools/MUTATION-FINDINGS.md`, including the gaps it did not close.
- Fuzzes `validate_flowback_proposal_bytes`, the one function here that parses a stranger's file, against 19,000 inputs across five strategies: bit-flips, uniform random bytes, truncation, filename attacks, and an adversarial set covering terminal escapes, bidirectional overrides, homoglyphs, credential shapes, invalid UTF-8, and inputs shaped to provoke catastrophic backtracking. Four invariants: never raises, never hangs, fails closed, and can still accept a valid proposal. The fourth exists because the other three are satisfied by a validator that rejects everything.
- Fault-injects gate termination: a gate that never returns, one that spawns a background process and then hangs, and one that ignores `SIGTERM`. The orphan case is the one that separates process-tree termination from child termination, and it was proven to have teeth by swapping the tree kill for a direct one and watching it fail.

### Cross-Platform Verification

- Adds a test workflow. This repository previously had none: the two existing workflows trigger only on `incoming/**` and `metrics/**`, so an ordinary code change ran no checks at all, and three stacked pull requests reached review untested on any platform.
- The suite now runs on Linux, macOS, and Windows, plus a second Python on Linux for forward drift, and validates a clean distribution archive rather than the working tree.
- The matrix found real defects on its first runs. macOS had never passed: it places temporary directories under `/var`, a symlink to `/private/var`, and the managed-path guards correctly refuse to write through a link-like component, so 29 tests failed before exercising anything. Windows failed four more: a symlink call that raised instead of skipping, a filesystem `chmod` that Windows git cannot see, fixtures written as CRLF and compared against LF from a `git archive`, and a shell pipeline into `tar` with a backslashed drive path. All were test portability rather than product defects.
- One was subtler. A marker path embedded two string levels deep, with the outer level not raw, reached the gate's parser as a truncated unicode escape whenever the temp directory sat under `C:/Users`, so the gate died of a `SyntaxError` instead of hanging and the test reported a termination failure that had not happened. Local Windows testing could not find it, because that workstation's temp directory contains no escape-forming sequence.
- Branch protection requires one aggregating context rather than one name per matrix leg. Pinning every leg by name makes the settings page a second implementation of the workflow's matrix, which is the standing drift risk `SKILL.md` names, with a failure mode where a renamed job leaves pull requests waiting on a check that no longer exists. The aggregating job runs with `if: always()`, so it checks each dependency's result explicitly; without that it would report success no matter what happened upstream.

### Locale Independence

- **Fixes a product defect.** `git_output` decoded git's stdout with `text=True` alone, which uses the machine's locale encoding: `cp1252` on a default Windows install, ASCII under `LC_ALL=C`. Git emits UTF-8. `core.quotepath` hides this for paths by escaping them, but not for a branch name, a tag name, the repository path from `rev-parse --show-toplevel`, or diff content, so a repository under a non-ASCII directory decoded wrong or not at all. On Windows the failure was especially quiet: the decode raised inside subprocess's reader thread, `stdout` came back `None` while `returncode` was `0`, and the caller crashed on `None.strip()`. Both git wrappers now pin UTF-8 with `surrogateescape`, which round-trips rather than corrupting values that are compared and hashed.
- Adds a regression test that runs in a child process with the locale forced, because the parent's encoding is fixed at interpreter start and every runner in the matrix defaults to UTF-8, where the unfixed code passes. Reverting the fix turns it red with `raised-AttributeError` for a non-ASCII commit subject and `corrupted` for a non-ASCII branch name.
- Adds a hostile-environment job to the required gate: non-UTF-8 locale, a temp root containing a space and non-ASCII characters, and `core.autocrlf` rewriting line endings on checkout. Each of the three has already produced a real failure in this repository.

### Documentation

- Names the Python floor. The README said "no dependencies beyond Python 3"; the real floor is 3.12, set by `tarfile.extractall`'s `filter` argument.

## 2026.08.22-unified.8

A provenance release. It supersedes `2026.08.22-unified.7` for distribution and changes no reference text relative to the current core.

Two defects in the `unified.7` release made that tag unusable as a distribution source, both found by an independent reviewer at a consuming repository:

- **The `v2026.08.22-unified.7` tag does not reproduce the core that was distributed from it.** Two commits landed on the release branch after the tag and both touch the distributed core (`scripts/adc.py`, `tests/test_adc.py`). A managed install taken from the branch tip therefore carried post-tag bytes while recording `2026.08.22-unified.7` as its source version. Extracting the tag yields core digest `511dfaf51f01b2ba677bb7f421c2f19a...`; the distributed bytes hash to `575383c9383dbe13521c229ab15dd571...`. A version string that does not bind to specific bytes is a claim, not evidence.
- **The `unified.7` notes state "It adds no new lessons," which is inaccurate.** That release also carried ADC-LOCAL-015, a separately promoted new lesson adding the new-producer checklist to `references/14-deterministic-verification.md`. It was promoted on its own branch before the release commit and was never described in the release section.

This release states the full contents of the current core plainly:

- **Recovered repairs (from `unified.7`).** The fourteen lessons that `unified.6` promoted from truncated proposals were re-staged from their source and their reconstructions repaired across `00-conventions.md`, `07-adversarial-review.md`, `10-maintenance-harness.md`, `11-remediation-loop.md`, `15-dogfeeding-flowback.md`, and `assurance-contracts.md`. Unchanged here; see the `unified.7` section for the itemized repairs.
- **Separately promoted lesson (from `unified.7`, previously undisclosed).** ADC-LOCAL-015 adds the new-producer checklist to `references/14-deterministic-verification.md`: a gate added to an audited evidence family is not done when it passes, but when the audit validates its record inside the set, the producer invalidates any standing audit before writing, and the record obeys the family's evidence canon.
- **Tooling fixes (after the `unified.7` tag).** `scripts/adc.py` now names the remedy when a proposal comparison cannot reach a merge base, instead of returning an unexplained refusal, with regression coverage in `tests/test_adc.py`.

### Release Integrity

- The distributed core at tag `v2026.08.22-unified.8` has core digest `b554a5a481b6f58caa111546f3309759412d38dc7520b8c10534a391427130de`, verified by extracting the tag into a clean directory and recomputing, not by reading the working tree.
- Consumers should install from a tag, never from a branch tip, and may compare their `.adc-managed.json` `source_core_sha256` against the digest published above.

## 2026.08.22-unified.7

**Erratum, added in `unified.8`:** two claims in this section are inaccurate and are corrected there rather than rewritten here. This release also carried ADC-LOCAL-015, a separately promoted new lesson, so "adds no new lessons" describes only the repair scope. The `v2026.08.22-unified.7` tag also does not reproduce the core distributed from this release; use `2026.08.22-unified.8` or later as a distribution source.

A correctness release. `2026.08.20-unified.6` promoted fourteen lessons from proposals whose multi-line fields had been truncated in staging, so their reference text was reconstructed from titles and surviving fragments. The full proposals were re-staged afterwards. This release compares the reconstructions against the restored sources and repairs what the reconstruction lost. It adds no new lessons.

Two independent audit passes produced these findings, the second run specifically to falsify the first. The second pass refuted one claim outright and narrowed two others; those corrections are reflected below.

### Repaired Promotions

- `11-remediation-loop.md`: the revert-mutation baseline rule described the wrong failure. Version control cannot restore a file it does not track, so on a new unit the restoring checkout fails with an unknown-pathspec error and the mutation stays in place. The text said the checkout destroys the unit instead. The danger is a mutation that survives the revert, and the closing green run is what exposes it.
- `11-remediation-loop.md`: the surviving-mutant rule offered "a missing test or untested behavior" as its two possibilities. Those are the same thing, which made the sentence an instance of the unfalsifiable-check class this skill defines. The alternatives are a missing test or an equivalent mutant, and the equivalent-mutant response was absent entirely: the mutated code was not load bearing, so the honest close is to delete the dead branch, name which mechanism really owns the behavior, and re-prove with a load-bearing mutation. The unit is not done until one goes red.
- `11-remediation-loop.md`: hang-as-third-outcome kept the bounding requirement but lost the reason and the remedy. A hang is worse evidence than a pass because it also blocks every later proof, and the fix is to bound cleanup waits downstream of a mutated safety action and surface expiry as a typed failure.
- `11-remediation-loop.md`: the guard-case rule lost its placement. A guard belongs in the finding's own smallest-safe-step rather than in follow-up work, must cover the form the change newly catches rather than one that already worked, and a probe an author ran once is not a guard because it does not run again.
- `07-adversarial-review.md`: three of the five field-observed shapes of the unfalsifiable-check class had been replaced by three plausible but unobserved ones. The observed shapes are restored. Two obligations were missing: naming the class requires sweeping the whole verification surface, because a remediation written after the class is named can introduce fresh instances of it, and a documentation restatement must cite the probe that proves it, which is the cheap discriminator between a restatement and an unverified claim hiding among verified ones.
- `assurance-contracts.md`: the isolation-claim rule downgraded the claim to `inferred` when a probe cannot run but never required the gate to fail. A probe that tests nothing is indistinguishable from a passing probe, so silence must not score as success.
- `assurance-contracts.md`: the self-certification rule kept the general defect and lost both practical traps: scope the scan to the whole document, because a live verdict often sits in a different section than the one a first replacement checks, and distinguish a live claim from accurate history so closing a check never requires deleting true history.
- `00-conventions.md`: audited-set evidence defined the claim but omitted its ordering. A producer record written after an audit attempt is unaudited however green its own run was, and a producer writing new evidence must invalidate any standing audit first.
- `10-maintenance-harness.md`: environment contention lost the requirement to name the holder before proposing a timing remedy, and to record a required tool exclusion beside the gate as an environmental prerequisite the repository cannot enforce from the inside.
- `10-maintenance-harness.md`: audited dependency state lost the rule that every restore goes through the reviewed path, leaving only the no-restore flag and the hash gate.
- `15-dogfeeding-flowback.md` and `scripts/adc.py`: the reference opened by telling readers to anchor identity to what a repository cannot casually change, while the rest of the same paragraph and the shipped code correctly do the opposite. Forks share root commits by design, so anchoring identity there would accept an upstream repository's calibration inside every fork of it. Both surfaces now state the same rule: the remote is the exclusivity signal and keys the binding, root commits explain a mismatch without overruling it, and a root-commit mismatch is the stop condition. Binding behavior is unchanged.

### Deterministic-First Contract

- `14-deterministic-verification.md`: the shell exit-code contract covered pipelines and not conjunctions. The composition that collapses a gate to a one-line result is itself a trust boundary. A pipeline reports its last stage, so a verdict piped into a summarizer is discarded; a conjunction short-circuits, so cleanup and revert steps chained behind a failing gate never run. The two compose into a worse case, where masking a failure lets the chain proceed and report success with the safety step apparently confirmed. One idiom loses the verdict and the other loses the safety step, so no single fix covers both.

### Release Evidence

- Adds `normalize_pdf_bytes` and `normalized_pdf_sha256` to `scripts/adc.py`, and `normalized_pdf_sha256` to the brief's provenance. A print-to-PDF engine restamps `/CreationDate` and `/ModDate` on every render, so `pdf_sha256` identifies one artifact and can never be reproduced. The normalized digest is the reproducibility claim, and two independent renders of this brief on different days now produce the same normalized digest. Both remain integrity checks over committed bytes: neither proves the PDF was regenerated from the current HTML, and only an actual re-render does. That gap is recorded rather than papered over with a check that cannot fail.
- Fixes chip crowding in the evidence-language rows of the brief and the website. The `verified`, `inferred`, and `unknown` chips sit in a grid track sized for two-digit pass numbers, and a fixed track does not grow, so they overflowed into the body text. This fix was authored before `2026.08.20-unified.6` shipped but was merged into a branch that had already merged to `main`, so it never reached a release.
- Removes both fully promoted proposals from the inbox. A clean distribution archive previously failed `validate --mode distribution` because the runtime-only inbox shipped inside it.

### Hardening

- Bounds the untrusted-fork history that the proposal-intake workflow downloads onto a privileged runner. It checked the candidate out with `fetch-depth: 0`, which lets a fork choose how much work the runner does. A bounded depth keeps the merge base present for the normal case. It does not degrade gracefully outside that case: `validate-incoming` compares with a three-dot diff and has no two-dot fallback, so a branch point older than the window leaves the candidate shallow with no merge base and validation fails closed. Like any workflow change, this is unverified until it runs on the default branch. The identical change to the efficiency-ledger workflow followed separately, because that workflow triggers on edits to itself and the ledger validator had to reach the default branch before it could accept a change combining that file with anything else.
- Fixes that validator. `validate-ledger-pr` accepted a receipt-free change only when the changeset was exactly `.github/workflows/efficiency-ledger.yml`, so it refused every legitimate combined change, including one that also edits the sibling intake workflow. It now passes any change that adds no receipt and touches neither the ledger nor either generated summary, and still refuses ledger data or a summary that moves without a new receipt. `--allow-workflow-maintenance` is accepted for compatibility and no longer consulted, because a deployed workflow still passes it. Found by this release's own pull request failing CI.
- Replaces the one non-ASCII character in the shipped skill, an arrow in the system-map template, against this skill's own ASCII-only writing rule.

### Tests

- 125 tests, of which 114 pass and 11 skip on this host. Adds a fixture-pair regression proving PDF normalization collapses timestamp differences while preserving content differences, which goes red if the normalization is reduced to an identity function, and extends the release-surface test to the normalized digest.

## 2026.08.20-unified.6

### Promoted Lessons

- Promotes the eight verification lessons from proposal `flowback-0a6794d23314` and the six mutation-discipline lessons from proposal `flowback-52ed79f5435b` into the references: unfalsifiable checks as a named finding class with a falsifying-input test (`07-adversarial-review.md`), guard cases for widening fixes and gate-named fix sets plus a revert-mutation proof discipline covering committed baselines, hang-as-third-outcome, and surviving-mutant diagnosis (`11-remediation-loop.md`), isolation-property probes and the self-certification anti-pattern (`assurance-contracts.md`), harness environment contention and audited dependency-lock state (`10-maintenance-harness.md`), audited-set evidence as its own claim (`00-conventions.md`), record-equality and child-context handoff cautions in gate authoring (`14-deterministic-verification.md`), and per-component repository-identity reporting (`15-dogfeeding-flowback.md` plus `adc.py`, which now names whether the remote identity or the root commits failed a binding check while remaining fail-closed).
- Both source proposals were staged with truncated multi-line fields (see the fix below), so the promoted text was reconstructed from titles, surviving fragments, and proposed targets. Source repositories should re-stage any lesson whose promoted form lost substance.
- Promotes the determinism lesson queued by a calibrated repository: ordering keyed on a parsed value is not total over raw representations; canonical comparators tie-break on the raw representation and determinism suites include a fixture pair of distinct representations of one parsed value (`14-deterministic-verification.md`, `07-adversarial-review.md`).
- Merges five field-tested reference sections from the maintainer's working branch: exclusion and single-owner claims need live second-claimant probes and untested else branches fail closed (`07-adversarial-review.md`), history rewrites strand cited identifiers (`09-artifact-gc.md`), self-matching process selectors (`10-maintenance-harness.md`), characterizing components outside the repo and sweeping text references after moves (`11-remediation-loop.md`), and capability-restricting build flags (`14-deterministic-verification.md`).
- Removes both fully promoted proposals from the pending inbox; Git history retains the review record.

### Tooling

- Fixes flow-back staging truncation: `parse_candidates` now preserves wrapped continuation lines in candidate fields instead of keeping only each field's first line, with a regression test. Previously staged public proposals carried first-line-only fields.
- Adds `scripts/work_receipt.py`: a stdlib-only helper that sums token usage, tool calls, and the covered time window from agent-session transcripts and prints a measured WORK line for a pull-request body. Documented in `16-community-feedback-and-efficiency.md`; measured numbers and human-equivalent estimates never blend.
- Expands the deterministic suite to 122 tests, including the continuation-line regression, per-component binding detail, and four work-receipt cases.

### Release Surfaces

- Adds the README banner, updates every release surface to `2026.08.20-unified.6`, and repairs the README version line that `2026.08.18-unified.5.1` failed to bump (its release predated running the release-surface test; the test caught it after the fact).

## 2026.08.18-unified.5.1

### License Provenance

- Ships the FSL-1.1-MIT license text inside the distributed core (`anti-dark-code/LICENSE.md`) so every managed install carries the license with the software, as the license's Redistribution clause requires. Root `LICENSE.md` remains the repository copy; the core copy is byte-identical.
- No reference, template, script, or policy changes from 2026.08.09-unified.5.

## 2026.08.09-unified.5

### Evidence and Assurance Contracts

- Adds a repository-neutral assurance-contract reference for claim closure, finalization, branch activation, hardware capability measurement, nested recovery, transactions, concurrency, subprocesses, native ABI boundaries, lockfiles, provenance, releases, signing, compatibility, UI evidence, providers, and hot paths.
- Requires terminal coverage labels and explicit dependency, shipping, and end-to-end reachability evidence instead of treating reference search or project inclusion as runtime proof.
- Tightens negative-search evidence, cleanup safety, self-review of freshly shipped high-risk fixes, calibrated detectors, producer exit-code handling, and shared-worktree orchestration.

### Deterministic Gate Identity

- Adds bounded, reviewed, non-sensitive per-gate environment overlays and an optional sparse-environment mode.
- Records only environment key names and an opaque execution fingerprint in dry runs, summaries, and failure packets; raw overlay values are omitted and scrubbed from retained child output.
- Refuses secret-like overlay variable names and bounds variable count and value size.
- Binds conventional gate proposals to the exact manifest files that produced them and invalidates approval when those files change.
- Prevents punctuation-normalized package script names from colliding and refreshes stale repository profiles when writing a new plan.
- Preserves approved repo-owned or auto-discovered gates across bounded profile refreshes when their exact source binding still verifies, while invalidating changed bindings and disappeared unbound auto-discovered gates.
- Makes bootstrap dry runs preview bounded gate changes and any owner-confirmation reset without writing calibration.
- Ships a subtree `.gitattributes` rule so checksummed managed installs retain LF bytes on Windows checkouts.

### Mutation and Regression Guidance

- Promotes the bounded mutation-pilot, absolute-count reporting, presentation-surface separation, stale-cache detection, and separate test-typechecking lessons from the incoming proposal inbox.
- Expands the deterministic suite to 116 tests, including regressions for environment privacy and execution, exact-bound gate preservation and invalidation, bounded-profile omissions, canonical fresh/migrated bootstrap previews, package-runner replacements, linked-source and duplicate-gate rejection, managed-install LF stability under `core.autocrlf=true`, conventional-source staleness, gate-id collisions, profile refresh, public proposal intake, workflow-only contribution handling, proposal diagnostic escaping, proposal-local public ids, immutable quarantined proposals, qualified-pair controls, canonical summaries, release-surface/PDF provenance synchronization, wrapper help, adapter/counter-semantics separation, and opt-in efficiency receipts.

### Public Proposal Intake

- Adds an explicit fork-and-pull-request path plus a no-Git issue form for community lessons, while keeping the inbox an untrusted quarantine that is never executed, installed, shipped, or promoted automatically.
- Requires shared-inbox staging to use public mode. The generator withholds the source commit, removes known repository-name/path variants, assigns proposal-local ordinal ids, permits only repo-agnostic or reviewed generic repo-shape scopes, redacts credential-like values and raw commit ids, and fails closed when the bounded public format is invalid.
- Adds content-hash, canonical-structure, path, field, pre-read size, control-character, all-raw-HTML, URI, credential, link, terminal-safe diagnostic, and one-file-diff validation.
- Adds read-only `pull_request_target` validation that executes workflow and validator logic from the trusted base revision, checks out fork content only as data, and never runs candidate scripts. The introducing pull request requires manual validation because a new workflow does not run until it exists on the default branch.
- Removes the fully promoted proposal inbox from the pending branch so proving-repository names, commit ids, and local evidence paths do not remain in the live quarantine. Git history retains the review record.

### Honest Efficiency Evidence

- Adds an offline, standard-library receipt helper for explicit host-reported numeric usage, controlled same-provider/model/adapter/counter-semantics/task comparisons, privacy-stripped public export, strict validation, and deterministic aggregation.
- Keeps actual usage separate from savings, requires matching adapter/counter semantics, reporting month, settings/tools/fixture/oracle digests, and fresh same-contract passing outcomes before computing a token delta, retains negative results, and never combines unlike provider/model/adapter/usage-semantics/task-class strata.
- Forces LF for managed-core and content-hashed public data, compares generated summaries as canonical bytes, and ignores local run, receipt, and flow-back artifacts at their point of creation.
- Adds a public JSON schema, empty ledger and honest initial summary, trusted-base receipt PR validation, exact mirrored website data, and an opt-in measurement reference. No prompts, responses, paths, repository/user ids, or raw host logs are collected.
- Updates the README, contribution guide, migration guide, all sixteen field-brief passes, PDF, and GitHub Pages site to `.5`; adds PDF/source hash provenance and a release-surface synchronization test; historical exact savings remain explicitly unmeasured until controlled public pairs exist.

## 2026.08.06-unified.4

### Real-Repo Write and Execution Hardening

- Verifies and fixes repo-local symlink-blind writes. Install, calibration, adapter, run-artifact, and flow-back paths now fail closed on symbolic-link or Windows-junction components and nested link-like entries.
- Keeps user-level host-discovery aliases compatible with a shared universal core while requiring real repo-local managed directories.
- Uses atomic file replacement for managed-core copies, calibration-template copies, and staged flow-back proposals.
- Treats invalid or link-contaminated calibration as repair-or-quarantine work instead of allowing `--accept-unbound-calibration` to override it.
- Makes blocked gate plans return exit code `2` in dry-run mode as well as execution mode.
- Launches each executed gate in a separate process group and makes a best-effort process-tree termination on timeout.
- Records timeout termination details in bounded failure packets.
- Makes auto validation treat the canonical repo-local path as installed state even when that path is an unsafe symlink, so the validation error cannot be hidden by resolving to the shared target.

### Scan Isolation and Validation Modes

- Excludes `.agents/skills`, `.claude/skills`, `.gemini/skills`, and `.codex/skills` from repository profiling, source identity, and changed-slice routing.
- Detects legacy `.codex/skills/anti-dark-code/calibration` alongside the other supported legacy locations.
- Adds explicit `distribution`, `universal`, `installed`, and `auto` validation modes.
- Keeps distribution validation strict against `incoming/`, repo calibration, managed-install metadata, symbolic links or junctions, `__pycache__`, and `.pyc` artifacts.
- Lets a deployed universal core validate and run its unit suite with staged flow-back proposals and without outer distribution documents.
- Validates installed repo copies through `.adc-managed.json`, managed-core hashes, the core digest, source metadata, local calibration JSON, calibration link safety, and repository binding.
- Allows ordinary live-core flow-back proposals while rejecting symlinked or junction-backed `incoming/` inbox entries.
- Excludes `.codex/skills` from Git worktree identity as well as content scans.

### Migration and Regression Coverage

- Updates repository-neutral migration guidance for symlinked legacy layouts, layered validation, blocked dry-run status, installed-copy integrity, and process-tree timeout behavior.
- Preserves strict package-artifact checks without requiring `python3 -B`.
- Adds regression tests for blocked dry runs, installed-copy validation, universal-core `incoming/` isolation, distribution rejection of runtime inboxes, repo-local link refusal, linked flow-back destinations, sibling-skill isolation across profiling and change routing, and timeout process-tree termination.

## 2026.08.06-unified.3

### Cross-Repo Calibration Isolation

- Adds `SOURCE-SCOPE.json` so installers can identify a clean universal source core.
- Adds `calibration/repo-binding.json` with a hashed one-repository identity.
- Blocks unbound legacy calibration until `--accept-unbound-calibration` is explicit.
- Blocks mismatched calibration until a reviewed `--rebind-calibration` is explicit.
- Records prior hashed repository ids when a binding is deliberately changed.
- Refuses deterministic gate execution and flow-back from unbound or foreign calibration.
- Verifies that a flow-back parent is a clean universal core.
- Reports legacy calibration locations without silently merging competing stores.
- Resets migrated or rebound gates to disabled and proposed, and clears global execution confirmation.
- Uses canonicalized Git remotes for stable binding across a first commit and ordinary SSH-to-HTTPS remote changes.

### Installation Source Hardening

- Blocks unmarked, repo-local, and repo-calibrated installation sources by default.
- Adds `--allow-unsafe-source` for advanced reviewed recovery only.
- Never copies top-level source calibration, even when the recovery override is used.
- Excludes the shared `incoming/` proposal inbox from repo-local managed copies.
- Rejects contaminated calibration templates even under the source override.
- Validates that template bindings are unbound and template gates are disabled and unapproved.
- Preserves nested calibration templates in managed repo copies while still excluding top-level repo calibration and proposal inboxes.
- Rejects a shared flow-back parent that carries a repo-local managed-install manifest.

### Migration and Documentation

- Rewrites `MIGRATION.md` for any old, partial, mixed, model-specific, or repo-customized installation.
- Makes same-repo fact migration, gate conversion, host consolidation, rollback, and multi-repo safety explicit.
- Removes project-specific migration guidance from operational references.
- Clarifies that the universal core flows downward, repo calibration stays local, and only reviewed general proposals flow upward.
- Generalizes personal-path validation beyond two hardcoded developer paths.

### Test Harness Fix

- Fixes the unit-suite packaging false positive caused by the suite's own runtime `__pycache__` files.
- The suite now validates a clean temporary package copy and runs with ordinary `python3`.
- Strict package validation still rejects packaged `__pycache__` directories and `.pyc` files.
- Expands deterministic coverage for clean-source enforcement, source-calibration exclusion, binding creation, stable remote identity, unbound migration, migration gate resets, mismatch rejection, explicit rebind, template completeness, template contamination, foreign-gate refusal, managed-parent refusal, and neutral operational guidance.

## 2026.08.06-unified.2

### Deterministic Gate Hardening

- Detects npm, pnpm, Yarn, or Bun for package-script gates.
- Creates generated gate suggestions disabled and marked `proposed`.
- Requires each enabled gate to be marked `approved` before execution.
- Resets global execution confirmation when generated gates are added, changed, or become stale.
- Fingerprints package-script definitions and blocks a previously approved gate when the underlying script changes.
- Includes committed, uncommitted, and untracked files in changed-slice routing.
- Retains pattern-redacted gate logs and redacts command fields in failure packets.
- Adds microsecond run ids and gate-definition hashes to avoid artifact collisions.

### Calibration and Probe Hardening

- Tracks commit and worktree status for profile freshness.
- Migrates pre-install fallback calibration into the canonical repo-local skill.
- Uses calibration templates from the selected source skill during installation.
- Prunes installed skill trees during repo enumeration.
- Reduces false generated-output and security signals from ordinary `export` and tokenizer code.
- Adds stricter package, capability-catalog, path, and generated-artifact validation without creating `__pycache__` files.
- Expands the deterministic unit suite from 8 to 15 tests.

## 2026.08.06-unified.1

### Unified

- Replaced separate Claude and Codex core trees with one model-neutral skill.
- Preserved optional OpenAI metadata under `agents/openai.yaml`.
- Added host addenda for Claude Code, Codex, Gemini CLI, and generic harnesses.
- Added a thin Claude repo adapter that points to the canonical `.agents/skills` copy.

### Added

- Pass `13`: calibrated local mode.
- Pass `14`: deterministic verification planner.
- Pass `15`: dogfeeding and proposal-only flow-back.
- Machine-readable catalog for all 20 verification capabilities.
- Repo-type adaptations for service/web, frontend, monorepo, library/SDK, game/simulation, mobile/native, infrastructure, AI/data, CLI/desktop, small/new, and mixed repos.
- Repo-owned calibration templates.
- Managed-core installer with checksums and conflict detection.
- Bounded deterministic repo probe.
- 20-capability planner and confidence ladder.
- Exact gate schema, dry-run runner, owner-confirmation gate, real exit-code capture, local logs, and bounded failure packets.
- Content-hashed flow-back proposals and parent inbox staging.
- Skill validator and unit tests.

### Incorporated from Repo-Local Dogfeeding

- calibration-first operation
- fresh-surface re-audit avoidance
- finding-class verification effort
- exact gate reuse and machine constraints
- canonical-rule delegation across projections and adapters
- aggregate canaries for emergent behavior
- output-count probes and configuration unwiring
- aggregation-semantics review
- chunking metamorphic tests
- dependency graph enforcement
- observational diagnostics and replayable UI monkey failures

### Changed

- Updated preflight, steering, architecture, slicing, adversarial review, scenario stress, maintenance, remediation, and orchestration references to use deterministic planning and calibration.
- Updated templates with capability ids, confidence levels, exact gates, failure packets, replay memory, rule authority, and freshness triggers.

### Safety

- No automatic dependency installation.
- No repo-code execution during install, bootstrap, or probe.
- Gate execution requires both `--allow-exec` and recorded owner confirmation.
- Repo-local flow-back cannot directly mutate shared core files.
