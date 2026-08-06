# Reference: Orchestration Mode

Use this reference when the harness can spawn subagents or run journaled multi-agent workflows, and the active pass would benefit from fan-out. This is a **runnable mode**, like `combined-03-06-loop.md`, not a numbered pass.

**Mode:** inherits the active pass's mode. A read-only pass stays read-only for every subagent.

If the harness has no subagent facility, skip this file entirely. Every pass runs inline as written. This mode changes execution shape only. It never changes pass content, pass order, approval gates, or evidence rules.

## Rules that do not bend

- One numbered pass at a time. Fan-out lives inside a pass: many slices, many lenses, one pass.
- Subagents never write the shared deliverables. The orchestrator is the single writer.
- Every subagent claim carries a citation (file plus line, or the exact command and output). No citation means the claim caps at `inferred` no matter how confident it sounds.
- Subagents inherit the pass mode. In read-only passes they must not build, test, migrate, push, or execute repo code.
- Do not force `verified` where the stack cannot be safely exercised. Record the next best check instead.

## What runs where

| Work | Runs as |
| --- | --- |
| Deterministic enumeration: find, du, git log, extension counts, citation-existence checks, dedup, progress counts | Plain shell. Never a paid agent. |
| Wide per-slice recon (pass 02, 04, 05 slice work) | Mid-tier model, medium effort. High effort only for the riskiest slice. |
| The single highest-risk slice (deploy, migrations, auth, secrets, money) | One model tier up from the recon default. |
| Adversarial challengers and cross-slice synthesis (pass 07, 08, map synthesis) | High tier, few calls, condensed input. |
| Orchestrator synthesis and deliverable writing | The orchestrator itself, reading condensed reports, not the raw repo. |

Omitting a model choice usually inherits the session model, often the most expensive tier. On a wide fan-out that is the worst cost profile. Choose the tier per stage on purpose.

### Gate truth

Repo gates (build, test, lint, validators) are free ground truth, but they execute repo code. Only run them when the user owns the repo or has said it is safe to execute. On an inherited or unknown repo, read the package scripts and CI definitions first and record what the gates would do.

When gates do run:

- Run long gates in the background before launching the fan-out so they overlap it.
- Capture the real exit code. `cmd 2>&1 | tail` reports tail's exit code, so a red suite reads as success. Use `${PIPESTATUS[0]}`, a `--json` output file, or grep the summary line.
- Anything a gate proves needs no agent verification. Record it as `verified` with the command as evidence.

## Deterministic verification planner integration

When pass `14` has produced a local plan:

- use its selected capabilities and confidence levels instead of inventing a new gate shape
- launch deterministic gates before paid fan-out when they can settle claims cheaply
- stop deeper fan-out after a cheap blocking failure unless a second failure is needed for diagnosis
- pass subagents compact failure packets and the smallest relevant source slice
- never send full green logs or ask an agent to monitor command progress
- record gate command, source identity, and real exit code as evidence

A repo-local coverage ledger may let fan-out skip fresh, guarded surfaces. A changed invalidation path reopens them.

## The verified promotion rule

This rule exists because unsupervised fan-out drifts on evidence labels.

- A subagent claim enters the ledger at `inferred`, with provenance: run id, agent label, and the citation.
- It is promoted to `verified` only when one of these holds:
  1. The orchestrator personally re-opened the citation and it says what the claim says.
  2. Two independent subagents with different lenses corroborate the same citation.
  3. A deterministic command settles it. Execution beats opinion.
- Spend promotion effort risk-first. Personally re-check every top-risk citation (deploy, migrations, auth, secrets, money). Sample at least one citation per subagent below that. A subagent that fails its sample check has its whole report treated as `inferred` pending re-check.
- Label the claim, not the hope. A config or text claim can be `verified` by reading the file. The live behavioral guarantee it implies stays `inferred` until observed. "The workflow YAML has no approval gate" is verifiable; "deploys always block on approval" is not, from text alone.
- Record what was not promoted and why. The label must be auditable, not asserted.

## Verification economics for finding passes

For passes that produce findings or challenge claims (07, 08, 11):

- Fan out one challenger per lens, blind to the other challengers. Use the specialty-stack trap lists in `07-adversarial-review.md` as the lens catalog.
- Scale verification by stakes. A top-risk defect claim gets two independent verifiers: one told to refute it, one told to trace the concrete trigger path. Lower-risk claims get one refuter.
- Verifiers receive the claim and the cited code only, never the finder's narrative. Default to refuted when uncertain.
- Design and remediation suggestions are not adversarially verified. They get one cheap reality-check pass against the repo.
- Cap verification volume. Pass overflow through labeled `unverified` and log the drop count. Silent truncation is a coverage lie.

## Fan-out shapes per repo type

Pick the branch that fits. Mixed repos slice by runtime unit first, then apply the matching branch per unit. Do not flatten specialty stacks into one shape.

**Game repo.** Slices: client, authoritative server, tools, content-pipeline code, CI and CD. Challenger lenses: client authority, live economy, save and replay and anti-cheat, narrative text claiming unimplemented mechanics. Determinism claims are settled by running the engine twice with one seed and diffing, which is free and stronger than any second opinion.

**Mobile or native app.** Slices: shared or JS layer, native bridges, local storage, build and provisioning, release tooling. Lenses: secure storage, permission flows, bridge validation, SDK payload capture.

**Infra-as-code repo.** Slices: per module, per environment overlay, state backend, pipeline permissions. Lenses: IAM sprawl, remote state, secret drift, runner powers. Applying changes is not a safe check. `verified` comes only from read evidence or plan output already on disk. Otherwise cap at `inferred` with a named next check.

**AI or data system.** Slices: pipelines, notebooks, evals, routing, prompt and tool schemas. Lenses: prompt and response logging, data lineage, quiet routing changes, remote-config control planes.

**Locale-heavy or content-heavy repo.** Slices: per rendered-text surface, overlay or compile pipeline, saved-prose stores. Lenses: copy parsed as truth, id renames, saved strings participating in replay or hashes.

## Budget and recovery

- Quote the fan-out shape to the user before launching: agent count times tier, per stage. Do this every time after a usage-limit event. A thoroughness request does not silently override budget reality.
- Checkpoint between the wide recon stage and any deeper or more expensive stage. Let evidence gate the next tier.

## Tier calibration at checkpoints

Verification produces the calibration signal for free, but only if you instrument it. Record every verdict per task family (dimension, slice, or claim type), and at each checkpoint compute the per-family survival rate before deciding what the next batch runs on. Data left in the journal calibrates nothing.

- Two ordinal dials, not one: tier raises the capability ceiling; effort buys deliberation depth on the same ceiling. Word both ordinally; some harnesses expose effort only globally.
- Refutations shaped like misunderstanding (a wrong model of how parts interact) are a ceiling signal. Raise tier for that family, or stop it and bank what survived.
- Failures shaped like incomplete coverage (stopped early, traced one path of four, shallow verdicts) are a diligence signal. Raise effort.
- Both signals on a bounded scope: raise both dials. Cost is rate times scope, and the scope is small.
- No failure signal: change nothing. A winning recipe is not an invitation to tune.
- Record each checkpoint decision with its input rates in the run report, so the next engagement inherits the calibration instead of rediscovering it.
- Give every unit of paid work its own agent call with a deterministic, byte-stable prompt. No timestamps, no randomness. That is what makes resume-from-cache replay work.
- On a crash or usage-limit death, resume the same run id. Completed calls replay free. Treat the call that was in flight at death as suspect and re-run it.
- Do not stop a healthy in-flight run to retrofit an improvement. Killed agents re-run from scratch and eat the savings. Note the improvement for the next pass.
- Monitor by reading the journal with shell tools. Never spawn an agent to summarize progress.
- Clean your own scratch when the pass ends: distill results into the pass deliverables, then tier and clear working files per `09-artifact-gc.md`. An orchestrated run must not leave unexplained artifacts behind.

## Fabricated specificity guard

Subagents import context from their environment: working directory names, tool descriptions, prior conversations. A repo name, version, owner, or purpose that does not appear in gathered evidence is not evidence. Strip it or mark it `inferred` with its source named as assumption.

## Acceptance checklist

An orchestrated pass is done when:

- the pass's own acceptance checklist passes unchanged
- every ledger claim sourced from a subagent carries provenance and an honest label under the promotion rule
- the deliverables state what the fan-out did not cover, including verification overflow
- the user saw the cost shape before the fan-out ran
- a dead run can be resumed by run id without re-paying for completed work
