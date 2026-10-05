# Local lesson update for unified.17

Reviewed 2026-10-03 against source commit
`ea12d57b10430670dd67e26b7da3da8b9de6e59d` and the clean
`v2026.09.27-unified.16` baseline. The owner requested justified local skill
changes and checks; publication and consumer rollout are deferred.

## Evidence and scope

The earlier multi-machine inventory is retained privately under the ignored
`.anti-dark-code/runs/lessons-v17-review/` directory. Its remote-machine, branch
and GitHub claims are inherited evidence, not independently verified in this
review. Private consumer identities and paths must not enter public artifacts.

The two relevant local queues were reopened. The larger queue now contains
eight exact `ready` values and five `observing` values, including a newly added
installed-tool-interface observation. The mobile queue's candidate has
`Status: ready (proposal only; shared core unchanged)` and an unsupported public
scope. It is a promotion proposal, but the current exporter will not select it.
Normalize the status to exactly `ready`, review the public scope and incorporate
useful safeguards before a later authorized export. Do not edit consumers here.

The general pipeline-status and isolation rules already exist. Treat the nine
queued families as proposed clarifications, not nine wholly absent rules. Use
one canonical home for each addition and retain observed baseline successes.

## Proposed instruction changes

| Family | Canonical reference | Acceptance obligation |
| --- | --- | --- |
| Destination write identity | `assurance-preservation.md` | The actual child retains and uses the verified object binding; replacement/unmount faults cannot redirect writes or recreate a destination on another filesystem. |
| Shell verdict integrity | `specialist-process-verdicts.md` | Distinguish scanner error from no findings; retain producer status; check syntax once per file. Preserve the existing pipeline rule. |
| Tool isolation escape hatches | `assurance-claim-proof.md` | Observe probe/stub activation, protected state and cleanup; inspect service buses, agent sockets, prompts and cached temp paths. An unchanged timestamp alone is insufficient. |
| Safety-query failures | `07-adversarial-review.md` | Reject failed, malformed or unexpectedly empty safety evidence; distinguish valid emptiness and enumerate every relevant backing resource. |
| Dependency fallback semantics | `07-adversarial-review.md` | Select explicit semantics when the default can violate the contract; exercise missing preconditions and any deliberately accepted fallback. |
| Rollback snapshot uncertainty | `assurance-preservation.md` | Separate present, absent and unavailable state before mutation; preserve evidence rather than guessing destructive restoration. |
| Inherited descriptor collisions | `assurance-native-execution.md` | Reserve descriptors outside the receiver's actual range, without assuming a universal minimum; prove lock denial at the last protected step without incidental holders. |
| Inherited capability claims | `assurance-native-execution.md` | Validate the expected object identity and required lock state; limit both handles and environment claims to intended descendants. |
| Native engine acceptance | `assurance-runtime-boundaries.md` | Exercise changed paths and missing APIs on the shipped engine/artifact before manual assistive-technology handoff; keep those outcomes distinct. |

Use a section in the existing native-execution recipe. Do not add a recipe,
change the assurance index or duplicate its authority boilerplate.

Three maintainer clarifications may accompany these changes:

- `host-claude-code.md`: report a classifier denial; use host-supported approval,
  an already owner-approved permitted wrapper, or owner execution. Preserve
  source integrity and binding. Do not disguise an operation to evade denial or
  generalize an old host observation into a permanent product limitation.
- `15-dogfeeding-flowback.md`: selection compares the entire status,
  case-insensitively, to `ready`; shared staging requires `--public`. Reopening
  `staged` entries requires a reviewed readiness decision, not an automatic flip.
- `orchestration-mode.md`: separate-file ownership does not isolate a shared Git
  index. Use worktrees or serialize staging and commits; inspect the exact staged
  diff and existing owner changes before committing.

Other memory-only lessons remain deferred. Existing negative-search guidance
already addresses much of the search and absence family. Do not add a universal
digest-generation or merge procedure without inspecting its evidence and need.

## Held observations

Keep all five local observations on hold: plan-snippet execution, wrapper PID
meaning, inherited-handle lifetime, shell-sourcing semantics and installed-tool
interfaces. Keep the inherited remote keyword-weight observation on hold too.
The native-execution additions do not promote PID or mount-lifetime observations;
the shell additions do not promote the sourcing observation. Another incident
does not automatically establish readiness.

## Local verification

Use the six synthetic cases in [lessons-v17](evals/lessons-v17/README.md), with
blind fresh evaluators, a clean tagged baseline and a frozen edited state. One
trial per case per state is a diagnostic sample; record every obligation, answer,
quote, miss and supplied-file hash. Scores by the rule author are not independent
scoring. Baseline success narrows the change; it does not prove reliable behavior.
The three-case draft omitted isolation, fallback, rollback, native-engine and
maintainer obligations. Do not claim those from unrelated trials.

Retain bounded deterministic reproductions of shell-status, exporter-selection
and shared-index behavior. Run the existing unit suite, universal validation,
distribution validation on a clean managed-core copy, skill frontmatter validation
and plugin metadata drift check. Keep every instruction file below 1200 words and
the identical recipe authority sentence intact. Name all changed references in
`CHANGELOG.md` under `Unreleased`. New tests must verify behavior rather than
matching new prose. Do not bump VERSION or regenerate release artifacts here.

The supported validator form is `adc.py validate --skill <skill> --mode
universal|distribution`; it has no `--repo` option. The generic skill-creator
frontmatter helper rejects the existing `compatibility` key in both the tagged
baseline and edited state. Record that pre-existing helper/schema mismatch and
preserve the field; repository validation is the supported package check.

Descriptor duplication supplies a lower bound, not a reservation against later
redirection, so choose it from the receiver's real descriptor use.
[Linux F_DUPFD manual](https://man7.org/linux/man-pages/man2/F_DUPFD.2const.html).
Lock inheritance depends on the primitive; do not transfer a `flock` assumption
to process-associated record locks.
[Linux flock manual](https://man7.org/linux/man-pages/man2/flock.2.html).
Child descriptor selection and environment inheritance are separate controls.
[Python subprocess documentation](https://docs.python.org/3/library/subprocess.html).

## Later publication and rollout

Prepare a focused PR from a reviewed diff with generalized provenance. For an
authorized release, follow current `OPERATIONS.md`, rather than copying an old
machine-specific script. Verify the clean candidate and release notes before
tagging, then check the tagged extract and downloaded published assets against
the reviewed core digest. Local checks do not establish unrun host CI.

Upgrade consumers only from the reviewed tag/digest. Inspect each checkout,
bindings, local edits, worktrees, stashes and permissions before writing. Preserve
unmerged work; a divergent development clone cannot simply fast-forward. Back up
and review its stale commit before deciding to rebase or retire it. Repository
worktrees receive branch changes through their own checkout/merge operations.

Flip a queue entry only after verifying the exact accepted lesson, release and
canonical reference; status values remain the existing vocabulary. Decide whether
an answered observation is covered/promoted or rejected from its actual lesson,
not from a similar topic. Preserve historical artifact records unless a scoped
annotation is requested. Review discovery copies before resyncing or removing
them. Publication, consumer edits and host configuration remain deferred.

## Pruning after runs 2 to 5

On 2026-10-03 the owner chose the repository's eval bar over incident-only
justification: keep an addition only when a baseline trial without it misses its
obligation. Runs 2 and 3 added two Claude trials per case per state, scored blind
by fresh subagents; every obligation that passed all three baseline trials then
received baseline-only runs 4 and 5. The combined counts are in
`evals/lessons-v17/evidence-2026-10-03-runs-2-5.json`; the run-1 Codex trials are
in `evals/lessons-v17/evidence-2026-10-03.json`. Baseline misses are counted
across both hosts; a miss on either host keeps the text.

| Obligation | Baseline misses | Treated misses | Decision | Canonical file |
| --- | --- | --- | --- | --- |
| `producer_status` | 0 of 5 | 0 of 3 | prune | `references/specialist-process-verdicts.md` |
| `scanner_error` | 0 of 5 | 0 of 3 | prune | `references/specialist-process-verdicts.md` |
| `syntax_per_file` | 0 of 5 | 0 of 3 | prune | `references/specialist-process-verdicts.md` |
| `destination_binding` | 1 of 5 | 0 of 3 | keep | `references/assurance-preservation.md` |
| `query_failure` | 0 of 5 | 0 of 3 | prune | `references/07-adversarial-review.md` |
| `dependency_fallback` | 0 of 5 | 0 of 3 | prune | `references/07-adversarial-review.md` |
| `rollback_unknown` | 0 of 5 | 0 of 3 | prune | `references/assurance-preservation.md` |
| `descriptor_collision` | 0 of 5 | 0 of 3 | prune | `references/assurance-native-execution.md` |
| `inherited_identity` | 0 of 5 | 0 of 3 | prune | `references/assurance-native-execution.md` |
| `descendant_scope` | 0 of 5 | 0 of 3 | prune | `references/assurance-native-execution.md` |
| `final_lock` | 5 of 5 | 1 of 3 | keep | `references/assurance-native-execution.md` |
| `escape_hatches` | 0 of 5 | 0 of 3 | prune | `references/assurance-claim-proof.md` |
| `activation_and_state` | 0 of 5 | 0 of 3 | prune | `references/assurance-claim-proof.md` |
| `engine_acceptance` | 0 of 5 | 0 of 3 | prune | `references/assurance-runtime-boundaries.md` |
| `distinct_accessibility` | 0 of 5 | 0 of 3 | prune | `references/assurance-runtime-boundaries.md` |
| `git_index` | 0 of 5 | 0 of 3 | prune | `references/orchestration-mode.md` |
| `flowback_selection` | 0 of 5 | 0 of 3 | prune | `references/15-dogfeeding-flowback.md` |
| `classifier_boundary` | 0 of 5 | 0 of 3 | prune | `references/host-claude-code.md` |

Two additions stay: the held-handle destination binding and the final-step lock
denial check. The final-step check is the only obligation every baseline trial
missed; its treated trials met it in two of three, so the wording is not yet
binding and remains a candidate for tightening with a fresh baseline. The
destination binding missed once in five baseline trials; two blind scorers
disagreed on a similar in-child re-check in another trial, recorded in the
evidence file, and the keep decision does not depend on that score.

Sixteen proposed additions were removed before commit. Their text is retained
here and in the evidence file so a recurrence can reopen them with a rerun of the
same case; the corresponding queue entries in the consumer repositories should be
marked `rejected` naming this evidence at rollout, with the two kept lessons
marked `promoted`:

- `producer_status` (`references/specialist-process-verdicts.md`): Output matching cannot replace the producer's verdict.
- `scanner_error` (`references/specialist-process-verdicts.md`): A scanner's findings, no-findings and error statuses have distinct meanings; `scan || echo clean` hides errors. Fault-test unreadable inputs and invalid patterns as well as positive matches.
- `syntax_per_file` (`references/specialist-process-verdicts.md`): Invoke syntax checks once per file: `bash -n a b c` checks only `a`, with the remaining names as arguments. Capture every invocation's status.
- `query_failure` (`references/07-adversarial-review.md`): Safety queries must distinguish valid emptiness from failure, malformed or unexpectedly empty results; uncertainty must not become an empty exclusion list. Follow every backing-resource edge and fault-test each failure mode.
- `dependency_fallback` (`references/07-adversarial-review.md`): Inspect dependency defaults that change semantics when preconditions disappear. Select explicit modes when fallback would violate the contract, and test missing preconditions and any deliberately accepted fallback.
- `rollback_unknown` (`references/assurance-preservation.md`): - Snapshot rollback state as present, confirmed absent, or unavailable. Abort before mutation when the snapshot is unknown; failed reads must not authorize deletion during recovery. Test unavailable reads and preserve evidence for later restoration.
- `descriptor_collision` (`references/assurance-native-execution.md`): - Inventory the receiver's fixed descriptor numbers and reserve inherited handles outside that actual range. No numeric minimum is universally safe; test redirections that would replace a handed-down handle.
- `inherited_identity` (`references/assurance-native-execution.md`): - Environment variables describing inherited capabilities are claims. Before skipping acquisition, verify the handle's expected object identity and the required lock state under the actual platform's lock semantics; an open number or matching object kind is insufficient.
- `descendant_scope` (`references/assurance-native-execution.md`): - Limit handles and their environment claims to intended descendants. Remove claims and close unwanted descriptors before launching unrelated long-lived children.
- `escape_hatches` (`references/assurance-claim-proof.md`): Test names and redirected environment variables do not isolate tools that reuse session services, agent sockets, unlock prompts or cached temporary paths. Inspect actual endpoints and cleanup.
- `activation_and_state` (`references/assurance-claim-proof.md`): Use known-positive execution and stub-hit sentinels plus independent protected-state checks; an unchanged store timestamp alone cannot prove isolation.
- `engine_acceptance` (`references/assurance-runtime-boundaries.md`): - Browser or Node API support and bundle compilation do not establish support in a shipped native JavaScript engine. Exercise changed formatter/control paths, locale behavior and missing APIs in the exact native engine and candidate artifact before manual assistive-technology handoff.
- `distinct_accessibility` (`references/assurance-runtime-boundaries.md`): Keep runtime acceptance separate from spoken behavior, gesture activation and focus acceptance.
- `git_index` (`references/orchestration-mode.md`): Separate-file ownership does not isolate Git's shared index and HEAD. Use separate worktrees/branches, or serialize staging and commits through one integrator. Before committing, inspect the exact staged diff against intended ownership and preserve existing owner changes; one agent's commit can otherwise include another's staged work.
- `flowback_selection` (`references/15-dogfeeding-flowback.md`): The tool selects entries whose complete status equals `ready`, case-insensitively; `staged` and `ready (proposal only)` are excluded. Put status commentary elsewhere. Review readiness and prior proposal provenance before reopening a staged entry. [...] `--public` is required. [...] `--mark-staged` is a separate queue-status write.
- `classifier_boundary` (`references/host-claude-code.md`): If a host permission classifier denies an installer or maintenance command, report the exact blocked operation and reason. Use host-supported approval, an already owner-approved permitted wrapper covering that operation, or owner execution. Preserve source/digest and binding checks. Do not disguise the command or weaken permission settings to evade denial; continue independent permitted work.

The validator note above refers to the Codex-side copy of the skill-creator
frontmatter helper, whose allowed-key list predates `compatibility`; the current
Anthropic skill-creator validator accepts the key on both the tagged baseline and
the edited copy. Repository validation remains the supported package check.
