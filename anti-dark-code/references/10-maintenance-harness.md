# Reference: Maintenance Harness and Drift Prevention

Use this reference after the first anti-dark-code rollout when you want the repo to keep telling the truth as new code lands.

**Mode:** docs-only plus light repo-fit automation. No application code edits.

For confidence levels, the unknowns entry shape, and the canonical approval-gated areas list, see `00-conventions.md`.

## Goal

Install or update a lightweight maintenance harness that keeps future work aligned with the repo steering files, system map, coverage ledger, unknowns files, approval gates, and protected rationale comments.

Stop the repo from drifting back into dark code after the first cleanup pass.

The harness should make the safe path easier:
- plain change intent
- small evidence-backed updates
- required doc updates for risky changes
- approval gates for protected areas
- explicit unknowns instead of guesswork
- obvious sensitive-logging mistakes caught early
- coverage drift noticed before it piles up
- protected anti-dark-code comments kept accurate or replaced when code changes
- language and transcreation boundaries kept separate from runtime truth

## When to use this reference

Use it when one or more fit:
- the steering files, map, unknowns, and reviews already exist
- comment-only passes already illuminated important code paths
- the repo needs guardrails for future contributors
- PRs are starting to touch risky areas without updating docs
- the repo has drift risk from scripts, CI or CD, release tooling, support tools, remote config, feature flags, notebooks, or mixed runtimes
- reviewers need help catching stale, removed, or weakened safety comments

Run this after the first mapping and review passes.

Run it again when the repo gains a new runtime, new control-plane path, new protected area, or a repeated drift pattern.

## Deliverables

Create or update repo-fit maintenance assets. Possible targets:
- `.github/pull_request_template.md`
- `CONTRIBUTING.md`
- `docs/contributing/ai-workflow.md`
- `docs/review/maintenance-harness.md`
- lightweight CI or policy-check scripts already compatible with the repo
- reviewer checklists or ownership docs when automation is not practical
- a maintenance validator or equivalent policy check when the repo already has a fit place for it

Do not create all of these by default. Use the smallest set that matches the repo's actual tooling.

Also create or update:
- `docs/unknowns/maintenance-harness.md`

## What the harness must do

### 1. Keep future work tied to repo evidence

Require future contributors to start from current repo truth:
- steering files
- system map or service map
- coverage ledger when present
- unknowns files relevant to the touched area
- logging audit when telemetry or sensitive data is touched
- adversarial or scenario review notes when the touched slice already has them

Do not let a contributor claim the repo is understood more broadly than the current evidence supports.

### 2. Enforce a plain change record

Each non-trivial PR or task summary must state:
- what changed
- why it changed
- what remains unclear
- what risk changed, if any
- what approval was needed, if any
- what docs were updated
- what tests or checks were run

Short. Factual.

### 3. Require doc updates when risky areas change

When a change touches architecture, protected areas, control-plane paths, critical flows, or non-obvious runtime entrypoints, require one or more of:
- system map update
- runbook update
- ADR update
- README update
- service or module manifest update
- unknowns update
- rollback note
- observability note
- release-path note
- localization or transcreation boundary note

Do not build a doc graveyard. Require only the docs that help the next engineer understand the change.

### 4. Keep unknowns visible

Require contributors to write down uncertainty instead of smoothing it away. Unknowns use the entry shape from `00-conventions.md`.

If a change uncovers a new dark area, the PR or task should update the unknowns file before pretending the area is understood.

### 5. Protect approval-gated areas

Require explicit human approval before edits that touch the approval-gated areas in `00-conventions.md`, plus repo-specific high-risk areas already named in the steering files.

If the repo already has ownership files or approval routing, align the harness to them. If not, create a clear reviewer checklist instead of inventing fake automation.

### 6. Catch obvious logging and telemetry drift

Add the lightest repo-fit checks that can catch risky regressions.

Good examples:
- grep or lint checks for obvious secret or token logging
- rules that reject raw request or response body logging in risky paths
- rules that reject cookies, session IDs, signed URLs, or raw personal data in docs, examples, tests, comments, screenshots, or commit text
- reviewer checklist items for crash reporting, analytics, traces, and prompt or tool logging in AI-heavy repos

Do not pretend a simple pattern check proves the repo is safe. Name the limit of the check.

### 7. Keep coverage honest

For large, mixed, or risky repos, require the coverage ledger to move when a meaningful slice changes.

Examples:
- a touched `legacy-unclear` slice may need a status update or a new unknown
- a newly mapped control-plane path may need a new slice entry
- a completed audit may change a slice from `mapped` to `audited`
- a blocked area may need a clearer reason and next pass

Do not force ledger churn for tiny low-risk edits outside tracked slices.

### 8. Keep protected anti-dark-code comments alive when guarded paths change

Treat protected anti-dark-code comments as part of the repo's safety and maintainability layer.

Protected comments capture:
- rationale
- invariants
- trust boundaries
- failure modes
- side effects
- ordering constraints
- idempotency assumptions
- security or privacy assumptions
- operator or repair warnings
- concurrency assumptions
- non-obvious rollback hazards
- language, locale, or rendered-copy boundaries that must not become hidden truth

If a change deletes, moves, or materially rewrites a protected anti-dark-code comment, the same change must:
- add a replacement comment near the surviving code that preserves the lost rationale or warning, or
- add an intentional removal note in the PR, task summary, or designated maintenance record that explains why the comment is no longer needed

Silent removal is not allowed.

If a comment no longer matches the code, update it in the same change. Do not leave stale safety comments behind. Do not weaken a protected comment into a vague restatement.

Comments that only restate obvious syntax are not protected by this rule.

### 9. Separate hard gates from reviewer guidance

Make the harness honest about what is automated and what is manual.

Hard gates:
- required PR fields
- required docs for protected-area changes
- policy checks for obvious secret logging patterns
- ownership or approval routing where the repo already supports it
- comment continuity checks when the repo has a fit place to run them

Reviewer guidance:
- challenge fake certainty
- ask for unknowns to be written down
- ask whether a hidden entrypoint or control-plane path was touched
- ask whether comments, runbooks, or rollback notes now drift from the code
- ask whether a removed protected comment was replaced or intentionally retired with a note

Do not label a human review habit as an automated guarantee.

### 9a. Prove gate work and shipped artifact shape

A checked CI box or zero exit code is not enough. Where the repo has tests, multiple targets, plugins, native dependencies, generated outputs, or release packaging, make the gate prove the expected work occurred:

- assert discovered and executed test counts, including a zero-discovery failure
- assert expected target, configuration, platform, and architecture tuples
- assert required artifact members, versions, sizes, hashes, and provenance receipts
- assert expected plugin or dynamic-discovery registrations
- assert warning or policy baselines against the logs that produced collected bytes
- retain the real producer exit code instead of a summarizer or output-filter exit code

Keep assertions scoped. A manifest proves its declared shape, not that every feature works. An allowlisted failure is tracked debt, not healthy behavior.

Calibrate detector thresholds against clean and known-bad fixtures. A lint that reports routine clean behavior trains reviewers to ignore it. Record why the threshold separates meaningful drift, keep a positive fixture that crosses it, and review threshold changes as behavior changes.

### 9b. Control the harness environment and audited state

- Keep verification artifacts that need exclusive file access out of trees that developer tooling indexes. Editors, language servers, indexers, and sync clients hold transient handles, and a cleanup or rename step then fails intermittently with timeouts that read as flaky gates. Put scratch and gate artifacts in a dedicated untracked directory the tooling ignores. Where a handle-enumeration mechanism exists, use it to diagnose contention before blaming the gate; where none exists, treat absence of contention as unproven rather than ruled out.
- Treat audited dependency state as read-only during builds. Where lock files are audited evidence, a routine build that implicitly restores or rewrites them silently mutates the evidence and invalidates the audit. Name the frozen or no-restore flag for the repo's package manager in the harness prerequisites, run verification builds with it, and gate on an unchanged lock-file hash.

### 10. Add repo-fit comment continuity checks

When the repo has a fit place for automation, add the lightest useful validator for protected comment continuity.

Good examples:
- a diff check that flags removal of protected comments without a nearby replacement
- a PR template checkbox that asks whether protected comments were removed, replaced, or intentionally retired
- a reviewer checklist item for guarded paths with existing anti-dark-code comments
- focused tests that prove the validator catches silent removal and allows valid replacement

Do not claim the validator can infer meaning perfectly. Name its limits. Treat it as a drift detector, not proof of comment quality.

#### Comment-continuity grep sketch

A minimal drift detector can be a `git diff` filter that flags deleted comment lines marked with a protected sentinel. Adopt a sentinel the repo agrees to (for example `// adc:` for "anti-dark-code" or a longer prefix the repo prefers), then run the check on the diff range a PR introduces.

```bash
# Flag any removed lines that carried the adc: sentinel between BASE and HEAD.
# Returns non-zero (and prints offenders) when silent removal is detected.
git diff --unified=0 "$BASE..$HEAD" -- '*.ts' '*.tsx' '*.js' '*.py' '*.go' '*.rs' \
  | awk '/^diff --git/{file=$0} /^-[^-].*adc:/{print file; print $0}' \
  | { ! grep -q . ; }
```

Limits to name in the harness doc:

- The check sees deletions only. A protected comment that was rewritten into a vague restatement still passes - only human review catches that.
- It depends on contributors using the agreed sentinel. New protected comments without the sentinel are invisible to this check.
- It does not understand "moved to a nearby line." A delete plus an add of an equivalent comment three lines down still flags as a delete; reviewer judgment closes that.
- File globs need to match the repo's languages. Tune them; do not ship generic globs as truth.

Treat the snippet as a drift detector. Pair it with the PR-template checkbox for "protected comment continuity" so reviewers can record an intentional removal note when appropriate.

### 11. Install a repo-fit verification plan

Evaluate all 20 capabilities through pass `14`. Store the result in `calibration/verification-plan.json` or the repo's equivalent.

Do not install all 20 as tools. Select the smallest set justified by repo evidence. Record candidates and triggers so the plan can grow deliberately.

### 12. Use an explicit confidence ladder

Separate fast edit checks from task, merge, and scheduled checks.

- Level 0: changed-slice static, schema, architecture, format, type, and lint checks
- Level 1: affected unit, contract, integration, and replay checks
- Level 2: selected property, fuzz, monkey, mutation, performance, and fault checks
- Level 3: full suite, soak, migration, platform, broad mutation, and long statistical checks

Run cheap blockers first. Do not spend full-suite time after a cheap gate already failed.

### 13. Emit compact verdicts and failure packets

Green output should be one line plus an artifact path. A failure packet should contain the first actionable failure, real exit code, command, source identity, seed or trace when relevant, bounded redacted output, replay command, and full local log path.

Keep retained redacted logs off the agent context unless the bounded packet is insufficient.

### 14. Preserve replayable regressions

A failure found by fuzzing, a random UI monkey, a stateful model, production diagnostics, or manual testing should become a minimized seed, trace, fixture, property, or regression test when practical.

Keep random exploration after stateful testing is added. Different exploration styles find different failures.

### 15. Add change-impact routing

Use imports, ownership, coverage, schemas, content, generated files, events, and gate globs to choose affected checks. Static imports alone do not capture shared configuration, deployment, or control-plane edges.

### 16. Guard emergent systems at world level

For games, simulations, recommenders, schedulers, markets, and other emergent systems, keep at least one fixed-input aggregate canary in the full or scheduled suite. Targeted tests can all pass while distributions become pathological.

Record the canary's intended range, false-positive history, and rerun cost.

## What to put in `docs/review/maintenance-harness.md`

Record:
- what maintenance assets were added or updated
- which rules are hard gates
- which rules are reviewer checks only
- which repo areas trigger doc updates
- which protected areas require approval
- which logging or telemetry checks exist
- which protected comment continuity checks exist
- where the harness still relies on human review
- what future slices or runtimes still need harness support

Short and practical.

## What to put in `docs/unknowns/maintenance-harness.md`

Use the unknowns entry shape from `00-conventions.md`.

Good examples to record:
- a release path that lives partly outside the repo
- a CI system the repo references but does not define locally
- a vendor dashboard that changes runtime behavior
- a sibling repo that owns deploy or migration behavior
- a native or engine layer that current checks do not cover
- a protected comment continuity rule that still depends on manual review

## Repo-fit branches

Pick the branches that match the repo. A mixed repo may need more than one.

**Service or web app:** PR template, protected-path approval checks, logging policy checks, system map and runbook update triggers, CI paths that deploy/seed/migrate/backfill, protected comment continuity in auth, billing, deletion, webhook paths.

**Monorepo:** slice-aware ownership, coverage ledger updates for touched risky areas, package or app specific doc triggers, hidden scripts/tools/support paths, comment continuity rules that do not overclaim coverage across sibling packages.

**Frontend-only:** analytics and browser storage review, feature flags and remote config review, UI-triggered risky flows, route copy ownership, localization boundaries, release and build-path notes, continuity checks for comments that explain trust edges, storage behavior, telemetry limits.

**Mobile or native:** native bridge changes, local or secure storage changes, push and background task review, crash and analytics payload review, locale or platform text surfaces, app-store or platform release-path notes, continuity checks for comments around permissions, bridges, background execution.

**Game repo:** client vs server trust edges, entitlement and live-ops changes, editor tool or import-hook changes, analytics and crash reporting, authored text versus mechanic truth, serialized asset exclusions and adjacent doc rules, continuity checks for comments in authoritative gameplay, economy, anti-cheat, live-ops paths.

**Infra-as-code:** state backend and IAM approval gates, module and environment overlay notes, runner permission review, plan/apply/import/drift-repair paths, continuity checks for comments that explain destructive or privilege-bearing behavior.

**AI or data system:** prompt/response/tool-trace logging checks, notebook and support-script review, data lineage and eval-path notes, routing layer and remote-prompt-store boundaries, batch jobs and backfills with live data reach, continuity checks for comments that explain model-routing, eval assumptions, live-data safeguards.

## Rules

- Lightweight and repo-fit.
- Do not invent platforms, bots, or CI features the repo does not use.
- Prefer existing workflow surfaces before adding new ones.
- Do not claim automation covers what still depends on human review.
- Do not let one path stand in for a whole repo.
- Do not let a low-risk template become an excuse to skip protected-area approval.
- Do not let protected rationale comments disappear silently.

## Harness safety rules

- Gate commands are argument arrays, not shell strings.
- Execution remains dry-run until explicitly allowed.
- Heavy gates name machine or runner constraints.
- No tool or dependency is installed automatically.
- Failure packets and retained logs use pattern-based redaction. They still require care before sharing.
- The harness distinguishes configured checks from checks actually run.
- Managed skill core and repo-owned calibration are not mixed.
- Never select a process by full command line for a destructive action.

## Self-matching process selectors

A harness normally runs an agent command through an interpreter wrapper (`bash -c`, `cmd.exe /c`, `powershell -Command`) whose own argument list contains the command text. Any selector that matches full command lines therefore also matches the caller's own wrapper. This fires even when no process of the intended kind is running, so an ordinary cleanup step can terminate the agent's shell while the real target is absent.

- Do not use a full-command-line selector to signal or terminate. `pkill -f` and `Get-CimInstance Win32_Process | Where-Object CommandLine -match ... | Stop-Process` both select the caller.
- Prefer a process id captured when the harness spawned the process. A saved id cannot match the caller.
- To reach a process the agent did not spawn, resolve the pattern to ids first, drop the current process and its ancestors, then signal only what remains.
- Treat name matching (`pkill -x`, `killall`, `Stop-Process -Name`) as a last resort. It still hits the caller when the target name equals the harness interpreter, and it hits unrelated work when the name is a shared runtime such as a language interpreter. Confirm the real name with `ps -o comm=` or the platform equivalent; some systems compare a truncated name, and a launcher can carry a different name than the binary it starts.
- Keep a destructive process action in its own call. A wrapper terminated by a signal abandons the rest of its chain, so queued build, test, or commit steps never run and their silence is easily misread as success.
- Full-command-line search stays appropriate for read-only inspection, where the caller's own wrapper is an expected result.

Measured on a POSIX host: an interpreter wrapper running a full-command-line kill terminated itself on a signal and skipped every later step in the same call, while the id-resolving form with self and ancestor exclusion completed normally. The exit status varies by host and signal, so do not treat any single number as the signature.

## Acceptance checklist

The final result should:
- make future anti-dark-code drift less likely
- fit the repo's actual workflow and tooling
- separate hard gates from reviewer judgment
- keep protected areas behind approval
- keep unknowns visible
- keep coverage claims honest
- keep critical-path comments from going stale
- require replacement or intentional retirement when protected comments disappear
- keep language and transcreation policy from drifting into hidden mechanics
- catch obvious sensitive-logging drift early
- avoid bloated process for low-risk changes
