# Routine usage review integration

Owner request: implement ordinary-task feedback before .15. PR60 is draft again.
Scope: opted-in local lifecycle records and structured self-review, two-machine
activation after verification, existing data preserved, release preparation updated.
No classifier, model-grading service, transcript archive, forced continuation,
publication, fabricated label or automatic acceptance of a successful Stop event.

Existing source: adc_usage.py collects counters and has only manual feedback;
feedback tables on both real machines had zero rows. The new workflow must live
outside skill activation so non-activations enter the observed denominator.

Design: Codex UserPromptSubmit creates a private pending review keyed by hashed
thread/turn identity and injects a short task-closeout instruction. Stop records
completion only. No prompt, answer, cwd or transcript path is retained. Missing
identity leaves a fixed diagnostic without blocking work; disabled opt-in writes nothing.
The agent submits labels against the exact review ticket. Uncertain cases stay
unknown; reviewer identity class, outcome basis, optional evidence hashes and the
reported skill version remain explicit. These are reports, not ground truth.

New hashed identity fields on Codex usage events connect tickets to the existing
root-task groups. Reconciliation tolerates collector lag and refuses ambiguous
links or overwrites of independently supplied feedback. Private summary output
reports pending, linked, reviewed and conflicting records; trigger results are
split by reviewer class. Historical manual labels keep unknown provenance.

Use an additive table enabled explicitly in the existing schema-1 ledger;
rollback keeps old tables/counters/consent and can disable review hooks. Before
upgrading live collector paths, pause schedules, take consistent private backups,
review existing permissions and verify summaries. Stage host definitions without
erasing other hooks. Native host trust must be satisfied for exact definitions.

Tests: unrelated concurrent threads, copied records, child/root linkage, late
usage, missing/ambiguous identity, duplicate hook delivery, disabled consent,
unknowns, explicit vs implicit labels, false positives/misses, failures, human
feedback conflict, malformed/oversized hostile hook payloads and metadata privacy.
Run the full suite and final host integration on the 5950X and Linux, validate
clean distribution, update all .15 release artifacts and required CI evidence.

Primary host references inspected 2026-09-15:
https://learn.chatgpt.com/docs/hooks
https://learn.chatgpt.com/docs/agent-configuration/agents-md
Observed local CLI: 0.154.0-alpha.6.2; hooks feature stable and enabled.
Hooks require native trust, merge matching sources, and supply turn_id plus
session_id. Exact session/thread interpretation must be checked with native
hook evidence before activation claims. Synthetic hook tests alone do not prove
host delivery or future agent compliance. No model-performance claim follows.

## Development observations

The Linux native Codex 0.154.0-alpha.6.2 test used an owned synthetic project,
reviewed both exact hook definitions through the native trust UI and asked only
for a file containing `4` plus a newline. UserPromptSubmit delivered the reminder;
the agent submitted a self-review without a user request to invoke the skill.
Stop recorded completion. The output bytes matched the requested file. The
collector read three per-response records and ignored three cumulative mirrors;
the hook's hashed session/turn identifiers matched the native usage thread/turn.
One review linked to one task group, with no missing label or ambiguous link.
This is one integration observation, not a compliance rate. The initial invocation
label was unknown, exposing unclear non-use instructions. The reminder now defines
implicit as no explicit skill request, including non-use. No synthetic labels or
usage are copied into the normal-work measurement report or public receipts.

Development checks passed: 54 focused usage/source/review tests and 6 subtests.
An earlier development full-suite run passed 712 tests, with 4 Windows-only skips
and 550 subtests; source changed during that run, so it is not final source-bound
release evidence. Final native Windows delivery and clean-source campaigns remain
required before the two-machine activation and release-readiness claims.

The first clean-source 5950X Windows run completed at `438bfbcd549b402d51c25885c8072416d4ef5670`:
706 passed, six cleanup failures and four POSIX-only skips. All six failures were
WinError 32 while removing the synthetic ledger. The new test inspection helper
used a SQLite transaction context without closing its connection. It now uses
`contextlib.closing`; production review functions already close their handles.
No cleanup assertion, runtime timeout or privacy check was relaxed. The original
failure log is retained with the private campaign evidence. A clean-source rerun
is required before readiness; the earlier failures are not counted as passes.

The label command needs ledger write access under the current host sandbox.
Operations now documents a narrow extra writable root for workspace-write sessions;
read-only sessions can leave labels pending. Activation preserved sandbox modes
and added only the selected private ledger root where needed. Existing .14 skill
discovery remains separate from the pinned .15 candidate collector/helper runtime.

## Native Windows module-path finding

The native Windows hook reached the helper with valid string lifecycle, session
and turn fields but failed the private-ledger preflight. A temporary diagnostic in
the owned synthetic project retained only input types, byte counts, code locations
and a redacted error from the fixed permission-check script. It stored no prompt
or raw native identity. Windows PowerShell reported that `Get-Acl` was found in
Microsoft.PowerShell.Security but the module could not load. The native host's
PowerShell 7 module path was inherited by the explicitly selected Windows
PowerShell 5.1 checker; direct SSH checks used a different parent environment.

Remedy: scope PSModulePath to the checker executable's own system Modules folder
for that child process only. Preserve the caller's environment and all owner/ACL
requirements. Add a Windows regression with an incompatible module path and verify
the native hook again. Do not weaken permissions, accept an unchecked ledger or
increase timeouts to mask this failure. Temporary diagnostics are confined to the
synthetic project and must be removed after the investigation.

The discriminating Windows regression failed on the preceding source at the
private-ACL assertion and passed with scoped module resolution (10.61 s and
21.50 s). It covers both checking and initializing a private ledger while leaving
the inherited environment unchanged. The first fixture did not reproduce the
failure because omitting the built-in module path lets Windows PowerShell prepend
it; that non-discriminating run is retained but is not evidence for the fix.
The corrected fixture places an unloadable module ahead of the built-in path, as
in the native host. Native diagnostics were removed from project hook discovery.
