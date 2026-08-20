# Reference: Post-Rollout Remediation and Verification Loop

Use this reference after the first anti-dark-code rollout when you want the outputs to turn into a bounded remediation program instead of sitting in docs.

**Mode:** bounded edits under approval rules. Slice-aware. Stop points required.

For confidence levels, the unknowns entry shape, the canonical approval-gated areas list, and default deliverable paths, see `00-conventions.md`.

## Goal

Turn current anti-dark-code outputs into:
- a ranked remediation backlog
- bounded safe-fix batches
- evidence-gap checks for uncertain items
- approval packets for protected areas
- touched-slice verification after each batch
- a clear next slice instead of a vague sense of progress

Keep work evidence-backed. Keep batches small. Keep protected areas behind approval. Keep coverage claims honest. Keep language boundaries from becoming hidden mechanics or policy.

## When to use this reference

Use it when the repo already has most or all of these:
- steering files
- `docs/architecture/system-map.md` or `docs/architecture/service-map.md`
- `docs/architecture/coverage-ledger.md` and `docs/architecture/repo-slices.md` when needed
- one or more files under `docs/unknowns/`
- `docs/security/logging-audit.md` when telemetry matters
- `docs/review/adversarial-pass.md` when the repo is large, old, mixed, or high-risk
- `docs/review/scenario-stress-test.md` and `docs/review/scenario-scorecard.md` when the repo has been break-tested

If those inputs are missing or stale, refresh them first. Do not build remediation on top of outdated maps.

## Companion references

- `00-preflight.md` for the canonical preflight that decides whether remediation can start now or earlier passes need a refresh
- `10-maintenance-harness.md` for guardrails for future contributors, before or after the first remediation wave
- `03-critical-path-comments.md` when a backlog item is best handled as comment-only clarification
- `06-writing-hygiene.md` after any step that writes comments, docs, commit text, PR notes, ADRs, or unknowns files
- `combined-03-06-loop.md` for bounded slice-by-slice comment loops with immediate cleanup
- `12-transcreation-boundary.md` when a backlog item involves locale, copy ownership, authored content, generated prose, saved text, or source-language assumptions
- `assurance-contracts.md` when a fix carries a verification, recovery, publication, native-runtime, provenance, compatibility, or user-visible policy claim

## Step 0: Preflight and stale-artifact check

Run `00-preflight.md` first. The remediation-loop's preflight needs are a strict subset of what `00-preflight.md` covers, so do not duplicate the work - open it, run it, and use its recommendation to decide whether Step 1 can start now or whether an earlier pass needs to refresh first.

The duplication here is intentional: the preflight reference is also a first-class entry point for engagements that begin without remediation in mind. Pass `11` cross-links to it so a remediation-led engagement still gets the same gate.

Stop conditions stay the same regardless of where preflight was triggered:

- a new runtime or control-plane path landed after the map was written
- the ledger no longer reflects touched slices
- a recent telemetry change was never audited
- a recent protected-area change happened without current approval notes
- a recent locale or copy change touched saved text, hashes, ids, policy, or mechanics without a boundary note
- a comment loop would now run on a stale slice plan

## Step 1: Build the remediation backlog

Use current anti-dark-code outputs as inputs.

Create or update:
- `docs/review/remediation-backlog.md`
- `docs/unknowns/remediation-pass.md`

Use the `remediation-backlog.md` template under `assets/templates/`.

Rules:
- do not guess
- do not claim full coverage unless the ledger supports it
- no application code in this pass
- separate findings into:
  1. safe-to-fix now
  2. approval-gated
  3. needs more evidence
- rank each item by risk and likely user or system impact
- group items by slice, subsystem, runtime unit, or control-plane path when that helps
- name exact files, paths, runtime units, scripts, jobs, CI or CD paths, release paths, or control-plane boundaries
- include evidence source, smallest safe next action, and verification needed
- call out holes caused by hidden entrypoints, out-of-repo control surfaces, sibling repos, submodules, release tooling, remote config, feature flags, notebooks, admin tools, support scripts, migrations, one-shot ops scripts
- call out holes caused by English-only assumptions, shared components hiding copy policy, locale overlays targeting unapproved fields, or rendered text mixed with runtime truth

For each backlog item include:
- title
- area or slice
- risk level
- why it matters
- evidence found
- confidence (`verified` | `inferred` | `unknown`)
- approval needed (`yes` or `no`)
- recommended next reference or pass type
- smallest safe next step
- verification plan
- owner if known
- current status (`open` | `ready` | `in progress` | `blocked` | `deferred` | `fixed`)

## Step 1a: Reproduce before fixing when practical

For behavior findings, prefer a failing invariant, exact diff, seed replay, minimized action trace, property counterexample, architecture rule, or performance budget before editing.

The implementation agent should not own the only verification opinion. Use the finding-class rules in pass `07` and deterministic gates in pass `14`.

### Characterizing a component outside the repo

When the misbehaving component sits outside the repo (a device, a driver, a third-party service, a vendored engine), the reproduction forms above stop short: the repo can be instrumented, the component cannot. Its error code is usually the only evidence. Characterize the component before reclassifying its failures. A matrix run before the edit beats a classification rule changed on one sample.

Run a bounded probe matrix that varies one request parameter at a time across several inputs, with a known-good peer, a prior version, or a second instance as a control. The control is what separates a component fault from a request the caller got wrong. Probe an isolated, disposable, or owned instance. If the only reachable instance is production, shared, metered, or someone else's, the probe is an approval-gated action rather than a free one.

Then shape the fix to what the matrix showed:

- Prefer changing the request over reinterpreting the failure code. Reshaping a request plan leaves the classifier honest. Widening a retry or tolerate list weakens it for every other caller, including callers the probe never covered.
- Scope the workaround to the exact identity the probe covered (vendor, model, firmware or version), and gate it on a condition the code can check at runtime. An identity the code cannot observe is an unconditional workaround wearing a scope label. Cite the probe receipt in the code comment.
- A probe separates request shape from component state. It does not separate cause from coincidence. A failure that repeats at every probed shape is a state problem, and its cause stays `inferred` until an independent second incident or a control run rules the alternatives out.

## Step 2: Implement safe fixes in bounded batches

Use `docs/review/remediation-backlog.md` and the coverage ledger.

Pick only backlog items that are:
- verified or strongly evidenced
- not approval-gated
- behavior-preserving, comment-only, docs-only, or narrow redaction and hardening changes
- small enough to review cleanly

Before editing, create or update `docs/review/safe-fix-plan.md` with, for each selected item:
- exact files to change
- why the change is safe now
- what behavior must remain unchanged
- tests or checks to run
- docs to update
- rollback note
- observability note if relevant
- whether the item is comment-only, docs-only, or behavior-preserving code cleanup

Load only the matching sections of `assurance-contracts.md` before implementing or accepting a strong claim. Its checklists refine this step; they do not broaden approval or execution permission.

Edit rules:
- keep changes small and single-purpose
- do not bundle unrelated fixes
- keep unknowns explicit
- stop and document if a selected item turns out to touch a protected area or hidden control-plane path
- update `docs/unknowns/` if new uncertainty appears
- update the coverage ledger statuses after the fixes
- after edits, run `06-writing-hygiene.md` on all touched text
- if the selected work is comment-only, use `03-critical-path-comments.md` and then `06`, or use `combined-03-06-loop.md`

### Bounded execution rule for Step 2

Do not let one remediation run march across the repo.

Default limits unless the user gives a different bound:
- review checkpoint after 10 commits
- hard stop after 20 commits for review
- stop sooner if the current slice is complete, a new protected-area dependency appears, or evidence goes soft

Commit guidance:
- one commit usually covers one backlog item, one slice checkpoint, or one tightly related docs plus code unit
- do not let a commit sprawl across unrelated slices
- after each commit or small batch, update the plan, coverage ledger, and unknowns notes before moving on
- if clean commit boundaries are impossible, stop early and ask for review

### Moves and extractions

A rename or extraction is only half-checked. Symbolic references - imports, types, call sites - are the half a refactoring tool rewrites, and a compiler, type checker, or failed import catches most of what it misses. References held as text sit outside that graph: a path or filename inside a string survives the move unchanged and stays green until something runs it. The weaker the static checking in the language, the more of the move lands in that unchecked half.

The usual holders are release and CI scripts, coverage, lint, and container build configs, dynamic loaders that resolve modules or classes by name, docs citing exact paths, and tests or guards that read source files from disk to assert ordering or invariants.

Before a move or extraction is called done:

- sweep specific to broad: the old relative path first, then the old directory segment, then the bare basename. A path assembled from parts never matches the full path, and the basename alone is the noisiest of the three.
- confirm the basename is distinctive before acting on basename hits. Repeated names are normal (`Program.cs`, `index.ts`, `__init__.py`, `main.go`), and a hit may belong to a different file that did not move. Editing that one is a new bug, not a repair.
- cover the test, script, workflow, config, and docs trees, not just the source tree. Exclude build output and vendored trees or the sweep drowns in its own artifacts.
- treat every surviving hit as a required edit or a recorded decision.
- close the sweep in the same change as the move where you can, and before the wave ends at the latest. Rerun it after each follow-up move, where stragglers cluster.

A green build after a move proves the symbols resolved. It does not prove the move is complete, and where there is no build step it proves nothing at all.

### TODO lifecycle

A safe fix sometimes has to leave a `TODO` behind because the full fix is approval-gated, blocked on evidence, or larger than the current commit budget. Track every such TODO end-to-end so it does not become the next generation of dark code.

Lifecycle:

1. **Plant** - the TODO comment names the area, the reason, and the unknowns or backlog entry it points to. A bare `TODO: fix this` is not allowed in remediation work.
   ```ts
   // TODO(adc): redaction here is shallow because the trace SDK formats the body
   // upstream. Tracked in docs/review/remediation-backlog.md#auth-trace-redaction
   // and docs/unknowns/logging-audit.md#auth-trace-shape.
   ```
2. **Track** - every planted TODO has a matching backlog row (or unknowns row, when evidence is still soft). The row carries the same status vocabulary the rest of the workflow uses (see `00-conventions.md`).
3. **Clear** - when the underlying work lands, the TODO is removed in the same change that closes the row. The change record names both the TODO removal and the row that closed.
4. **Audit** - the maintenance harness (pass `10`) should add a reviewer-checklist item asking whether new `TODO(adc:` lines were planted with backlog references, and whether any cleared TODOs left behind a stale comment.

If a TODO outlives the engagement that planted it, the next preflight should treat it as a stop condition and decide whether the row still makes sense before any new pass extends it.

## Step 3: Resolve evidence gaps for blocked or uncertain items

Can run in parallel with Step 2 for blocked items. Do not wait for every safe fix to land if a gap is holding a risky item open.

Read-only pass unless a doc-only update is needed.

Create or update:
- `docs/review/evidence-gap-check.md`
- `docs/unknowns/evidence-gap-pass.md`

For each item:
- state the claim that is not yet proven
- list the exact files, scripts, workflows, configs, or docs checked
- state what evidence supports the concern
- state what evidence is still missing
- state the confidence level (`verified` | `inferred` | `unknown`)
- name the next best repo-local check
- name any out-of-repo boundary that blocks certainty
- downgrade confidence where needed instead of flattening uncertainty away

Focus on:
- hidden runtime entrypoints
- CI or CD and release paths
- migrations and backfills
- support scripts and admin tools
- remote config and feature flags
- notebooks and one-shot ops scripts
- sibling repos, submodules, mirrored trees, external control planes
- locale, copy, authored-content, generated-prose, saved-text, and render-on-read boundaries

## Step 4: Prepare approval packets for protected areas

Start as soon as an approval-gated item has enough evidence. Do not wait for unrelated evidence gaps in other slices.

No application code edits.

Create or update `docs/review/approval-packets.md`.

For each approval-gated item:
- exact area and files
- protected-area category
- why the risk matters
- current evidence
- smallest safe edit after approval
- what could break
- verification plan
- rollback plan
- what human decision is required
- which unknowns still block the edit, if any

## Step 4a: Police test and baseline changes

When the fix changes tests, snapshots, fixtures, timeouts, mocks, coverage, mutation configuration, or architecture exceptions:

- name the behavior contract that changed
- show why the old expectation was wrong or incomplete
- reject skip, delete, broaden, or re-record changes made only to obtain green
- have a verifier review the test change separately from the implementation
- preserve the pre-fix reproducer when it remains useful

## Step 5: Re-run the verification loop on touched slices only

Run after each meaningful safe-fix batch and again at the end of a remediation wave.

Inputs:
- updated coverage ledger
- remediation backlog
- recent code diffs
- updated unknowns files
- logging audit
- adversarial pass
- scenario stress-test

Check whether recent fixes actually closed the targeted holes without creating new dark areas.

Do:
- update coverage statuses honestly
- confirm docs match current code
- confirm no new hidden entrypoints or control-plane paths were introduced
- confirm no sensitive data was added to logs, comments, tests, docs, examples, screenshots, or commit text
- confirm protected areas were not edited without approval
- identify what remains uncovered
- estimate the next slice to run
- name whether `04`, `07`, `08`, or `10` should rerun on the touched slice

Extra checks when they fit:
- if observability code changed, rerun the logging audit on the touched slice
- if a control-plane path changed, refresh the map or adversarial notes for that slice
- if comment-only work landed, confirm the comments still match the code after the final cleanup pass

## Step 6: Install or refresh the maintenance harness when the repo is ready

Use `10-maintenance-harness.md` when the repo needs ongoing guardrails for future contributors.

Good times to run 10:
- right before a broad remediation wave (PR and review guardrails in place first)
- right after the first remediation wave (lock in the new rules)
- after the repo gains a new runtime, new release path, new control-plane path, or new protected area
- after the repo gains locale packs, transcreation tooling, generated prose, or a new saved-text contract

## Optional companion loop: combine 03 and 06 slice by slice

Use this loop when the next useful work is comment-only clarification on critical paths. Especially useful when the coverage ledger shows risky slices still hard to explain but not yet needing logic changes.

How to run:
1. pick the next uncovered or weakly explained slice from the coverage ledger
2. run `03-critical-path-comments.md` on that slice only (or use `combined-03-06-loop.md`)
3. immediately run `06-writing-hygiene.md` on all touched comments, docs, summaries, and unknowns files
4. commit that slice as one bounded unit
5. update the coverage ledger and `docs/unknowns/critical-paths.md`
6. repeat on the next slice

Stop rules for the comment loop:
- review checkpoint every 10 commits
- hard stop after 20 commits for review unless the user says continue
- stop sooner if the slice touches a protected area, reveals stale maps, or uncovers a hidden control-plane path that needs a different pass first

Good summaries after each slice:
- what code path was clarified
- which invariants or edge cases the new comments explain
- what remains unclear
- which next slice should run
- whether the repo is still in comment-only mode or now needs a behavior-preserving cleanup pass

## Acceptance checklist

The result should:
- turn the first rollout into an actionable backlog instead of a pile of notes
- keep safe fixes bounded and reviewable
- keep protected areas behind approval
- turn evidence gaps into explicit checks instead of guesses
- verify touched slices after each batch
- keep the coverage ledger honest
- give the user a clear stop point for review
- make the next slice obvious
- track every planted TODO from creation to clearance
