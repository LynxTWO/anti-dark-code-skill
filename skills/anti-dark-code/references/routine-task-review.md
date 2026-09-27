# Routine task review

Load when enabling or completing opted-in usage feedback. Use the existing private
usage ledger. Counters alone cannot establish skill use, task quality or a missed
activation. This workflow adds observed lifecycle tickets and reported labels;
it does not grade tasks or call a classifier.

## Enable and connect

After the owner authorizes routine reviews, use the private-path prerequisites in
[real-world usage](real-world-usage.md):

```sh
python3 anti-dark-code/scripts/adc.py usage review enable --directory <private-ledger> --opt-in
```

This creates an additive `reviews` table and configuration in the existing ledger.
It preserves counters, opt-in timestamps and manual feedback. Enabling the table
alone does not connect a host. Use the `assets/templates/codex-review-hooks.json`
example to prepare the owner's Codex hooks. Replace placeholders with an approved
Python executable, a pinned reviewed helper and that ledger. Inspect existing
hook sources and preserve unrelated handlers. Use a source copy whose files were
verified, not a mutable consumer checkout.

Codex `UserPromptSubmit` supplies a session/thread identifier and a turn identifier.
The helper hashes these, creates a pending ticket and injects a short instruction
for the working agent to submit labels before its final response. `Stop` records
that the turn stopped. It never means passed, and never forces a continuation.
The helper discards prompt, answer, cwd and transcript-path fields. Invalid or
overlarge inputs emit a fixed warning without blocking the task; when the private
enabled ledger is available, `review_hook_refused` counts refused hook attempts.

Use the current host's native hook review/trust flow for the exact definitions.
No trust-bypass flag or managed-system policy is required by this integration.
Verify actual delivery in a new host session, rather than treating a configuration
file or direct script test as proof. The supported Codex lifecycle contract is
separate from the inspected per-response usage adapter. Host formats may change.
Other hosts retain explicit `usage feedback`; no automatic Claude task-boundary
or cross-host lifecycle claim is made.

## Record a normal closeout

Use the command and ticket supplied by this task's reminder. Never select the
latest global task, borrow another thread's ticket or replay work to manufacture
labels. The helper resolves the ticket only against observed parent usage with
matching thread and turn hashes. Child usage remains in its existing root group.
Collector lag leaves the review awaiting usage; a later authorized tick reconciles
it. Ambiguous matches stay unresolved. Independent manual feedback is preserved
as a conflict rather than overwritten.

The `submit` fields are:

- `used`: yes, no or unknown. The skill must have guided the requested work.
  Reading a reminder, reviewing the skill itself or seeing its name is insufficient.
- `expected`: yes, no or unknown. Judge whether the user's request warranted the
  skill, separately from whether it activated. Include misses and correct non-use.
- `invocation`: explicit if the user requested Anti-Dark-Code, otherwise implicit,
  including non-use. Use unknown when the request is unclear. Explicit requests
  do not measure implicit triggering.
- `quality`: passed, failed or unknown. State the observed acceptance outcome,
  never infer it from a process stopping or an assistant saying it finished.
- `basis`: acceptance-checks, observed-result, owner-feedback or unknown. Known
  quality requires a basis. Acceptance-checks also requires `--evidence-sha256`
  for an existing result artifact. A hash binds evidence; it does not grade it.
- `reviewer`: agent-self-review, human-review or unknown. Do not label an agent's
  own work as independent human review.
- `had-failed-attempt`: yes, no or unknown. A later successful repair does not make
  an observed failed acceptance check disappear.
- `task-class`: map, audit, verify, remediate, install or other.
- `skill-version`: optional declared version of the skill that guided the work.
  Read that actual source when known; the review helper's version is not the
  version of every skill invocation. Omit for non-use or uncertain attribution.

No prompt, explanation prose or raw test output is accepted in labels. At most
four evidence digests are retained. Identical submissions are idempotent;
corrections retain up to 32 prior labels and then refuse further changes for
inspection instead of silently discarding history. These are reviewer reports,
not independent validation or permission to execute a gate.

## Inspect coverage and stop

```sh
python3 anti-dark-code/scripts/adc.py usage review pending --directory <private-ledger>
python3 anti-dark-code/scripts/adc.py usage summary --directory <private-ledger>
python3 anti-dark-code/scripts/adc.py usage review disable --directory <private-ledger>
```

Summary coverage separates observed, submitted, missing-label, linked, awaiting,
ambiguous and conflicting reviews. A stopped turn with no label remains missing.
Usage groups beginning after review opt-in without a linked lifecycle ticket are
reported separately. This time-window count also exposes inactive or untrusted
hooks and includes work while hooks were paused; it is not a task-outcome label.
The confusion matrix is also split by reviewer class; old manual labels have
unknown provenance. Unknown fields, explicit invocations and unsupported task
boundaries remain excluded. Do not infer population precision/recall from this
selected sample or causal savings from natural usage. Agent reminders can be
ignored; missing reviews and native hook warnings make that limit visible.
The reminder and closeout use some task tokens. They make no separate grading
model call; those costs still belong in observed usage.

Disabling usage also stops review writes. Disabling reviews retains history;
remove only the selected hook handlers separately. Rollback can restore the old
collector while retaining the additive table. Pause writers and keep a consistent
private backup before changing live collector paths or ledger permissions. No
new source authorization, history purge or public upload is implied.

Follow this procedure before finishing an observed task. Report failures and non-activations as observed and keep uncertain labels unknown. Recording feedback does not itself count as using the skill.
