# Candidate promotion checks for unified.17

`cases.json` covers the nine queued lesson families and three maintainer-operation
lessons. It uses synthetic requests without consumer names or private evidence.
The rule author fixes the yes/no obligations before trials and scores each answer
with supporting quotes. Scoring is not independent review.

Each fresh agent reads a pinned skill and relevant references, then answers two
requests in one context without running the proposed operations. The method in
`cases.json` describes run 1: one baseline and one treated trial per case, Codex
subagents, author-scored. On the owner's instruction, runs 2 and 3 added two more
trials per case per state with Claude subagents, scored blind by fresh subagents
that were not told the skill state, every score then read by the reviewing agent.
Obligations that passed every baseline trial received baseline-only runs 4 and 5
before any pruning. The rule applied: keep an addition only when a baseline trial
missed its obligation; prune the rest and leave the lesson queued in its
repository as `rejected` with this evidence named, so a new incident can reopen
it. Shared host instructions and the paired request remain possible influences.
Report counts and misses per host; this small sample does not establish
reliability, cross-model performance or causal savings.

Outcome (`evidence-2026-10-03-runs-2-5.json`): two additions kept, the final-step
lock denial check (five baseline misses of five) and the held-handle destination
binding (one of five); sixteen pruned with their text retained in the evidence
file and in `../../lessons-unified-17-plan.md`.

Standard-tier check (`evidence-2026-10-04-sonnet-baseline.json`): on the owner's
decision, three Sonnet 5.5 trials per case ran against the unified.17 text, which
omits the sixteen pruned additions and carries the two kept ones, scored blind by
fresh subagents. No obligation missed in 27 scored reviews, so the sixteen rejections
stand on Fable 5.1, Codex and Sonnet 5.5 evidence and the two kept additions were met
on Sonnet. The trial and scorer models share a vendor family; Gemini remains
unexamined. Counts only; this is not a reliability estimate.

The baseline is the clean `v2026.09.27-unified.16` archive. The treated state is a
frozen copy of the edited managed core. Evidence records source refs and hashes
of all supplied managed files, agent identifiers, paired cases, answers, scores
and quotes. Do not inherit results after editing a tested instruction.

Existing baseline successes constrain additions: preserve the working general
rule and add only a demonstrated, useful specificity gap. An observed consumer
failure can justify a narrow clarification even if one synthetic baseline
already succeeds. Keep that counterevidence visible.

The inherited-handle case tests ready descriptor-collision and environment-claim
lessons. It does not promote held observations about wrapper PID changes or
mount lifetime. Likewise, the shell case does not promote the held shell-sourcing
lesson. A second incident alone does not automatically promote an observation;
readiness still needs scope, duplication and evidence review.

Run the existing documentation contracts, unit suite and universal validator
after edits. Validate an uncontaminated managed-core copy in distribution mode.
These are local acceptance checks. Release checks, host CI, publication,
installation and queue status updates remain separate work.
