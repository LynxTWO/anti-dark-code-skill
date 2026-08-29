# Assurance Router Decision Log

Version: 0.1 Draft. Date: 2026-08-28.
Companion documents: ARCHITECTURE.md, ENGINEERING.md, SLICE-001-route-shadow.md.

The documents state what is true. This log preserves why, what else was considered, and what would reopen the question.

## Rules

1. Every Decision Block in the ADD and EDD gets an entry here with a sequential ID.
2. Changing a decision never edits the old entry. Write a new entry that supersedes it and link both ways.
3. Stubs and shortcuts are decisions. Log them with their payback trigger.
4. An agent proposing work that conflicts with a logged decision must surface the conflict, not code around it.
5. At every document audit, scan for entries whose Revisit trigger has fired.

## Index

| ID | Date | Decision | Status | Superseded by |
|---|---|---|---|---|
| D-001 | 2026-08-28 | Routing is infrastructure, not a numbered pass | Confirmed | |
| D-002 | 2026-08-28 | Pure functions plus one CLI subcommand | Confirmed | |
| D-003 | 2026-08-28 | Standard library only, no new dependency | Confirmed | |
| D-004 | 2026-08-28 | Obligations are capability ids, catalog extended | Confirmed | |
| D-005 | 2026-08-28 | `--level` becomes an escalate-only override | Confirmed | |
| D-006 | 2026-08-28 | Agent hints may raise, never lower | Confirmed | |
| D-007 | 2026-08-28 | Route input is the final diff, limitation documented | Confirmed | |
| D-008 | 2026-08-28 | `independent_review` is recorded, not enforced | Confirmed | |
| D-009 | 2026-08-28 | No numerical risk score | Confirmed | |
| D-010 | 2026-08-28 | The fact collector does not reuse `changed_files()` | Confirmed | |
| D-011 | 2026-08-28 | Selective CI is sequenced after selective local | Confirmed | |
| D-012 | 2026-08-28 | Gate coverage metadata deferred | Deferred | |
| D-013 | 2026-08-28 | No cheapest-gate optimizer in version one | Deferred | |
| D-014 | 2026-08-28 | Shadow artifacts live beside the receipt | Assumed | |
| D-015 | 2026-08-28 | Design documents live in `design/routing/` | Confirmed | |

---

## Entries

## D-001: Routing is infrastructure, not a numbered pass

Date: 2026-08-28
Status: Confirmed
Area: ADD 1, ADD 15

Context:
Routing has to decide which passes were invalidated, including whether the prose preflight of pass 00 needs to run at all. That places it underneath the numbered passes.

Decision:
Routing lives under passes 00, 10, and 14 as infrastructure. No new numbered pass is added.

Because:
A pass cannot sit underneath itself. If routing were pass 17, it could not satisfy the freshness portion of pass 00 without a circular dependency. Framing routing as an occasional activity also loses the workflow half, which is where the model-token savings are.

Options considered:
- Infrastructure under 00, 10, 14: correct ordering, wider prose diff across SKILL.md and three references.
- New numbered pass 17: narrow prose diff, but circular against pass 00 and strands the workflow router.
- Pass 14 only: smallest change, drops the workflow router entirely.

Consequences:
Easier: routing is always true rather than something to remember to run. Harder: the documentation change touches SKILL.md and three reference files, so the review surface is larger.

Revisit when:
A second subsystem needs the same treatment and the prose pattern proves unmaintainable.

## D-002: Pure functions plus one CLI subcommand

Date: 2026-08-28
Status: Confirmed
Area: ADD 5

Context:
The router must be exhaustively testable, including on Windows, without constructing a git repository for every case.

Decision:
`collect_change_facts` and `build_route` are pure. Only the receipt writer touches disk. One new subcommand, `route`.

Because:
Purity lets the monotonic property be property-tested over generated fact sets. Every existing subcommand follows the same shape, so nothing new has to be learned.

Options considered:
- Pure functions plus CLI: testable, matches existing structure.
- Methods on a router class holding a repo handle: fewer arguments, much harder to test the monotonic property in isolation.

Consequences:
Easier: exhaustive tests with no filesystem. Harder: the collector needs its git output passed in rather than fetching it inline.

Revisit when:
The pure layer needs repository state that cannot be passed as data.

## D-003: Standard library only

Date: 2026-08-28
Status: Confirmed
Area: ADD 8.2

Context:
A schema validator or a glob library would shorten the implementation.

Decision:
Standard library only, matching the rest of `adc.py`.

Because:
Every import has to survive the hostile-environment matrix, the clean distribution check, and installation into repositories the tool does not control. `fnmatch` already backs the existing glob filtering.

Options considered:
- Standard library only: no new failure surface, slightly more hand-written validation.
- Add jsonschema: better error messages, a new dependency in a tool that installs itself into other repositories.

Consequences:
Easier: distribution stays clean. Harder: policy validation is hand-written and needs its own tests.

Revisit when:
The core adopts a dependency for another reason.

## D-004: Obligations are capability ids

Date: 2026-08-28
Status: Confirmed
Area: EDD 4, ADD 7

Context:
The design proposed twelve obligation names. Seven already exist in `assets/verification-capabilities.json` under different names: static is near V09, contract is near V08, mutation is V01, replay is V07, performance is V14, independent review is V17, test integrity is V18. Five have no existing id.

Decision:
Obligations are capability ids. The catalog is extended with the genuinely new ones, provisionally V21 to V25, and rules name capability ids rather than a parallel vocabulary.

Because:
Two names for one concept is the drift the skill warns about everywhere else. One catalog means pass 14 keeps evaluating one list, and a receipt omission can name the reviewed capability it skipped.

Options considered:
- Extend the catalog: one vocabulary, requires touching a reviewed artifact.
- Separate obligation vocabulary with a mapping table: reads more naturally, needs a second file kept in sync forever.
- Obligations only, ignore the catalog: simplest now, and the receipt could never name which reviewed capability an omission skipped.

Consequences:
Easier: one source of truth. Harder: extending the catalog is itself a verification-authority change, so it forces the full route and deserves its own review.

Revisit when:
Q-001 closes and the real count of new capabilities is known.

## D-005: `--level` becomes an escalate-only override

Date: 2026-08-28
Status: Confirmed
Area: EDD 4 R-013

Context:
`gates --level N` currently accepts 0 to 3 with default 0, and every existing document example and test passes it.

Decision:
`--level` stays and may raise above the computed route. It may never lower it. A lowering attempt exits 2 and names the route minimum.

Because:
This preserves the authority split exactly: deterministic tooling establishes the minimum, judgment may raise it. It also keeps every existing invocation working, which a deprecation would not.

Options considered:
- Escalate-only override: preserves the split, no migration.
- Keep both fully independent: zero risk, leaves a documented way to under-verify.
- Deprecate `--level`: cleanest end state, breaks every current invocation at once.

Consequences:
Easier: no migration, and the flag gains a clear meaning. Harder: `run_gates` needs to know about routes, so the two subsystems couple at one point.

Revisit when:
Route receipts are the normal path and manual level selection is rare.

## D-006: Agent hints may raise, never lower

Date: 2026-08-28
Status: Confirmed
Area: ADD 8.6, ADD 14

Context:
Deterministic tooling cannot always tell whether behavior changed. An agent can often see that it might have.

Decision:
Agents may supply hints such as "possible public contract change". Hints can only raise the route. No hint, and no agent statement, may lower it.

Because:
The value of an agent here is catching semantic changes a path glob cannot see. The danger is an agent concluding a change looks harmless. Allowing only one direction keeps the value and removes the danger.

Options considered:
- Escalate-only hints: keeps agent value, no downgrade path.
- No hints at all: simplest, loses real semantic signal.
- Hints may adjust either direction with justification: the justification is exactly what cannot be verified.

Consequences:
Easier: the trust boundary is one sentence long and testable. Harder: an agent that believes the route is too heavy has no recourse except asking a human.

Revisit when:
A reviewed rule can be shown to encode a downgrade safely with deterministic evidence.

## D-007: Route input is the final diff

Date: 2026-08-28
Status: Confirmed
Area: EDD 4 R-007

Context:
If commit A changes an auth schema and commit B reverts it, the final base to HEAD diff shows nothing, so the escalation disappears.

Decision:
Route from the final diff only. Document the limitation explicitly.

Because:
A touched-then-reverted path is genuinely not in the shipped change, and this matches how CI and human reviewers see the work. The union over branch commits is more conservative but pins a whole branch to full verification because of one early experiment.

Options considered:
- Final diff, documented: simple, deterministic, matches reviewer view. Side effects of the reverted commit, such as a migration already run, stay invisible.
- Union over branch commits: never loses an escalation, accumulates stale escalations.
- Final diff plus history-rewrite detection: the middle option, and the detector is the part worth keeping.

Consequences:
Easier: one comparison, easy to explain. Harder: a reverted change with external side effects is not caught by routing and must be caught by review.

Revisit when:
A routing miss is traced to a reverted commit.

## D-008: `independent_review` is recorded, not enforced

Date: 2026-08-28
Status: Confirmed
Area: EDD 4, ADD 10

Context:
A rule can set `independent_review: true`, but `agents/` currently holds only `openai.yaml`, and there is no attestation format.

Decision:
The receipt records that independent review was required and whether it was recorded. The gate runner warns and does not block. Enforcement stays with human review and branch protection.

Because:
Blocking would require inventing an attestation format and answering who signs it, inside a slice that is supposed to be read-only. Recording is honest about what the tool can prove today.

Options considered:
- Record, do not enforce: honest, keeps slice 1 read-only.
- Block gate execution until attested: strong guarantee, invents a trust mechanism mid-slice.
- Omit the field entirely: avoids a field nothing honors, and loses the audit trail.

Consequences:
Easier: no new trust machinery. Harder: the requirement is advisory until something enforces it.

Revisit when:
An attestation mechanism exists, or a review requirement is observed to be ignored.

## D-009: No numerical risk score

Date: 2026-08-28
Status: Confirmed
Area: ADD 14

Context:
A weighted score is the obvious way to combine many facts into one decision.

Decision:
Hard minimums and unions. No score, no thresholds, no weights.

Because:
Scores create arbitrary thresholds and strange interactions. A critical trigger can be diluted by unrelated low-risk facts. Union and maximum cannot dilute anything, and the result is explainable by naming which rule fired.

Options considered:
- Hard minimums and unions: explainable, testable, monotonic by construction.
- Weighted score with thresholds: flexible, and dilution is a correctness bug waiting to happen.

Consequences:
Easier: the monotonic property is provable, and every decision names a rule. Harder: expressing "slightly risky" requires a rule rather than a number.

Revisit when:
A real case cannot be expressed as a rule.

## D-010: The fact collector does not reuse `changed_files()`

Date: 2026-08-28
Status: Confirmed
Area: ADD 14 guardrail 4, EDD 4 R-014

Context:
`changed_files()` already unions base diff, working diff, and untracked paths. It then filters through `is_tooling_relpath`, which drops `.agents/skills/` and `.anti-dark-code/` per `TOOLING_PATH_PREFIXES`. Those prefixes contain `calibration/gates.json` and the proposed `calibration/routing-policy.json`.

Decision:
The router gets its own collector. It must see tooling paths, and it must read status information rather than names only.

Because:
Reusing the existing helper would make the router structurally blind to the two hardest escalators in the design. That is the classifier grading itself, arriving through a helper function rather than through policy. The existing helper is also `--name-only`, so it carries no rename, deletion, or mode information.

Options considered:
- Separate collector: correct, some duplication of the union logic.
- Reuse with a flag to disable filtering: less duplication, and one wrong default silently reintroduces the blindness.

Consequences:
Easier: the router sees everything. Harder: two collectors exist, and they must not drift. R-014 is the test that keeps them honest.

Revisit when:
The existing helper gains status information for another reason.

## D-011: Selective CI is sequenced after selective local

Date: 2026-08-28
Status: Confirmed
Area: EDD 14

Context:
The `required` aggregator in `tests.yml` refuses unless every dependency reports exactly `success`. A skipped job fails it. Selective routing produces skipped jobs by design.

Decision:
Selective CI execution is scheduled strictly after selective local execution, and is out of scope for slice 1.

Because:
Making the aggregator route-aware is itself a verification-authority change that forces the full route, and it should not be attempted while the router has no shadow evidence behind it. The current aggregator behavior is correct and should not be weakened to accommodate an unproven router.

Options considered:
- Sequence CI after local: keeps the aggregator strict until there is evidence.
- Change the aggregator now: parallelizes the work, weakens the one stable required context before the router has earned it.

Consequences:
Easier: CI stays trustworthy throughout. Harder: CI savings arrive later than local savings.

Revisit when:
Shadow results support enabling one route class locally.

## D-012: Gate coverage metadata deferred

Date: 2026-08-28
Status: Deferred
Area: ADD 10

Context:
Rules could name obligations and let gates declare `tags`, `covers`, and `scope`. That is more flexible than naming explicit gate ids.

Decision:
Rules name explicit gate ids for now. Coverage metadata is deferred.

Because:
Explicit recipes are easier to trust while the system is young. More importantly, `gate_definition_hash` currently binds thirteen fields and none of them describe coverage, so adding `covers` without extending the hash would let someone change what a gate claims to cover without invalidating its approval.

Options considered:
- Explicit gate ids: trustworthy, more verbose policy.
- Coverage metadata now: flexible, and creates an approval hole until the hash is extended.

Consequences:
Easier: no approval hole. Harder: the policy repeats gate ids across rules.

Revisit when:
`gate_definition_hash` is extended to bind `tags`, `covers`, and `scope`. That extension must land first.

## D-013: No cheapest-gate optimizer in version one

Date: 2026-08-28
Status: Deferred
Area: ADD 10

Context:
Given obligations and gate coverage, a solver could pick the cheapest covering set.

Decision:
Not built. Explicit route recipes only.

Because:
An optimizer is hard to trust and hard to explain, and it would be selecting less work using metadata that is not yet bound by the gate hash.

Revisit when:
D-012 is closed and shadow evidence exists for the affected route classes.

## D-014: Shadow artifacts live beside the receipt

Date: 2026-08-28
Status: Assumed
Area: EDD 4.3 Q-003

Context:
Shadow comparisons produce a miss record that needs a home. `metrics/ledger/` exists for public efficiency receipts with a schema under `metrics/schemas/`.

Decision:
Shadow artifacts are written to `.anti-dark-code/runs/<run-id>/shadow.json`, beside the route receipt, which matches the existing local run artifact convention. Promotion to `metrics/` is deferred.

Because:
`metrics/` is repository-owned publication machinery for this repository. Local run artifacts are the documented home for per-run output, and a consuming repository needs somewhere to put shadow results without adopting the publication path.

Status is Assumed because it is inferred from the existing convention rather than chosen against a stated need. Q-003 closes it after thirty comparisons.

Revisit when:
Q-003 closes, or shadow results need to be published rather than reviewed locally.

## D-015: Design documents live in `design/routing/`

Date: 2026-08-28
Status: Confirmed
Area: EDD 10

Context:
The Scaffold Kit convention puts documents in `docs/`. In this repository `docs/` holds `index.html` and `data/efficiency-summary.json`, so it is the published website.

Decision:
`design/routing/` holds the four documents. `docs/` stays the website.

Because:
Writing planning documents into a published site directory would publish them, and would also mean routing must treat this project's own design documents as a distribution surface.

Consequences:
This is also a routing lesson worth carrying into the policy: a `docs/` directory cannot be assumed inert any more than a `.md` extension can.

Revisit when:
A second subsystem needs the same treatment and a flatter layout is preferable.
