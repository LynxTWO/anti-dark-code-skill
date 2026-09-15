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
