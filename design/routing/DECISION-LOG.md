# Assurance Router Decision Log

Version: 0.2 Audited. Date: 2026-08-28. Status: Audited.
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
| D-004 | 2026-08-28 | Obligations are capability ids, catalog extended by two ids | Confirmed | |
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
| D-016 | 2026-08-28 | Q-001 closes with V21 affected-unit testing and V22 input fuzz testing | Confirmed | |
| D-017 | 2026-08-28 | Policy binds every capability obligation to explicit gate ids | Confirmed | |
| D-018 | 2026-08-28 | The router has no human downgrade override | Confirmed | |
| D-019 | 2026-08-28 | Git acquisition is impure and receipts bind content | Confirmed | |
| D-020 | 2026-08-28 | Full routing uses a validated policy-root recipe | Confirmed | |
| D-021 | 2026-08-29 | Local self-grading is recorded and deferred, not solved here | Deferred | |
| D-022 | 2026-08-29 | Template rules ship proposed, never approved | Confirmed | |
| D-023 | 2026-08-29 | The slice calibrates this repository before it routes it | Confirmed | |

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
`read_change_inputs` owns read-only Git I/O. `collect_change_facts` and `build_route` are pure over passed data. Receipt writing is a separate boundary. One new subcommand, `route`.

Because:
Purity lets the monotonic property be property-tested over generated fact sets. Every existing subcommand follows the same shape, so nothing new has to be learned.

Options considered:
- Pure functions plus CLI: testable, matches existing structure.
- Methods on a router class holding a repo handle: fewer arguments, much harder to test the monotonic property in isolation.

Consequences:
Easier: exhaustive classification and route tests need no filesystem. Harder: the status-aware reader and its byte parser need separate integration tests.

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
The design proposed twelve obligation names. Catalog review in D-016 found that ten map to existing capabilities. Distribution shares V08 with contract validation. Cross-platform and hostile-environment checks are V12 adaptations. Affected-unit testing and input fuzz testing are not present.

Decision:
Obligations are capability ids. The catalog is extended with V21 and V22 per D-016, and rules name capability ids rather than a parallel vocabulary.

Because:
Two names for one concept is the drift the skill warns about everywhere else. One catalog means pass 14 keeps evaluating one list, and a receipt omission can name the reviewed capability it skipped.

Options considered:
- Extend the catalog: one vocabulary, requires touching a reviewed artifact.
- Separate obligation vocabulary with a mapping table: reads more naturally, needs a second file kept in sync forever.
- Obligations only, ignore the catalog: simplest now, and the receipt could never name which reviewed capability an omission skipped.

Consequences:
Easier: one source of truth. Harder: extending the catalog is itself a verification-authority change, so it forces the full route and deserves its own review.

Revisit when:
An evidence method cannot be represented without distorting an existing capability definition.

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
Rules bind each capability obligation to explicit gate ids in the routing policy per D-017. Gate-owned coverage metadata is deferred.

Because:
Explicit recipes are easier to trust while the system is young. More importantly, `gate_definition_hash` currently binds thirteen fields and none of them describe coverage, so adding `covers` without extending the hash would let someone change what a gate claims to cover without invalidating its approval.

Options considered:
- Explicit gate ids: trustworthy, more verbose policy.
- Coverage metadata now: flexible, and creates an approval hole until the hash is extended.

Consequences:
Easier: no approval hole, and R-012 is machine-checkable. Harder: the policy repeats capability-to-gate bindings across rules.

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

## D-016: Q-001 closes with two new capability ids

Date: 2026-08-28
Status: Confirmed
Area: EDD 4.3, SLICE-001 M1

Context:
The proposed evidence vocabulary contained twelve labels. A lexical match was not enough because capability ids name methods, not job names. All twenty catalog definitions were compared by purpose, computer work, and agent work.

Decision:
Eight existing capability ids cover ten labels. Static maps to V09. Contract and distribution map to V08, with distribution treated as validation of a generated package boundary. Mutation maps to V01. Replay maps to V07. Performance maps to V14. Independent review maps to V17. Test integrity maps to V18. Cross-platform and hostile-environment map to V12. Add V21 Affected-unit testing and V22 Input fuzz testing.

Because:
V11 selects affected checks but does not execute their assertions, so calling affected-unit testing V11 would merge selection with evidence. V15 perturbs environmental failures, and V02 generates stateful action sequences. Neither covers hostile input-byte and value generation. The repository's fuzz harness makes that distinction directly. Distribution, cross-platform, and hostile-environment are scopes or adaptations already named by V08 and V12, not new methods.

Options considered:
- Add V21 through V25: preserves every provisional label and duplicates existing methods.
- Add only V21 and V22: keeps method identities distinct while allowing several route labels to converge on one capability.
- Add no ids: would call test selection test execution and fault injection input fuzzing.

Consequences:
M1 becomes a bounded two-entry catalog edit. Route policies use capability ids only, so the provisional labels do not become a second vocabulary.

Revisit when:
The V21 or V22 definitions cannot describe a real gate without absorbing another capability's purpose.

## D-017: Policy binds every capability obligation to explicit gate ids

Date: 2026-08-28
Status: Confirmed
Area: EDD R-012, ADD 14

Context:
Parallel `obligations` and `gate_ids` arrays can both be nonempty while carrying no relationship. That shape cannot prove which gate satisfies which capability, so R-012 would accept an unrelated approved gate.

Decision:
Each rule's `obligations` field maps a capability id to a nonempty set of explicit gate ids. The route unions gate ids per capability. Policy validation rejects an unknown, duplicate, disabled, or unapproved gate before selective execution.

Because:
The coverage claim must live in the policy while gate coverage metadata remains deferred under D-012. Binding the relationship in the hashed policy closes the gap without adding `covers`, `tags`, or an optimizer to `gates.json`.

Options considered:
- Policy-local capability-to-gate map: machine-checkable now and consistent with D-012.
- Parallel arrays: smaller shape, no provable coverage relation.
- Gate-owned coverage metadata: the future design, blocked until the approval hash binds it.

Consequences:
Policies are more verbose. R-012 becomes executable rather than a reviewer inference.

Revisit when:
D-012 closes and gate-owned coverage metadata can replace the policy-local map without weakening approval binding.

## D-018: The router has no human downgrade override

Date: 2026-08-28
Status: Confirmed
Area: EDD 2, EDD 6, ADD 14

Context:
The first draft said requirements never decrease, then named `operator_override` as a human downgrade path. A receipt with a recorded reason would still authorize less evidence than the deterministic minimum.

Decision:
The router and receipt have no downgrade override. An agent or human may raise the route. A human may record why required evidence is unavailable, but the receipt stays incomplete and cannot authorize selective execution.

Because:
A reason explains a gap but does not verify it. This preserves D-005, D-006, and D-009 in every execution path.

Options considered:
- No downgrade: one authority rule and one monotonic property.
- Human downgrade with a reason: auditable, but the route no longer establishes a hard minimum.

Consequences:
An exceptional change may require the existing full-verification path or remain blocked. The receipt never presents an exception as satisfied evidence.

Owner review, 2026-08-28:
This decision diverges from the original design source, which said a human may approve a recorded exception with the reason written into the route receipt. The divergence was surfaced to the owner with both options stated, and the owner confirmed D-018 as written. The reasoning accepted: a reason explains a gap but does not verify it, and a router that can be overridden is not a minimum. A waiver mechanism is deferred rather than rejected, and needs its own authority, attestation format, expiry, and enforcement path before it returns.

Revisit when:
The owner defines a separate waiver authority, attestation format, expiry, and enforcement path outside route computation.

## D-019: Git acquisition is impure and receipts bind content

Date: 2026-08-28
Status: Confirmed
Area: ADD 4 to 6, EDD R-017 to R-019

Context:
A function taking `repo` and `base` and invoking Git is not pure. The current repository identity helper hashes porcelain status text, which does not change when one dirty byte sequence is replaced by another dirty byte sequence.

`current_source_identity` is unsuitable for receipt binding for a second and independent reason. It passes pathspec exclusions for `.agents/skills/**`, `.claude/skills/**`, `.gemini/skills/**`, `.codex/skills/**`, and `.anti-dark-code/**` to `git status`. Those exclusions are correct for its own job, which is judging whether an installed core is dirty, and they were deliberately set that way. They are wrong for a receipt, because a change to `calibration/gates.json` or `calibration/routing-policy.json` would leave the identity unchanged and the receipt fresh. That is the same blindness D-010 found in `changed_files`, reappearing in verification rather than collection. Any helper the router borrows must be checked for both properties: does it hash content, and does it see the whole tree.

Decision:
`read_change_inputs` is the read-only impure boundary and returns a canonical ChangeSnapshot. `collect_change_facts` and `build_route` are pure. Receipt freshness binds content, modes, index entries, symlink targets, and submodule state, then checks that identity before and after each gate.

Because:
The split keeps property tests honest and prevents status-shape equality from being mistaken for content identity. The after-check prevents a concurrent mutation from turning output from different bytes into accepted evidence.

Options considered:
- Separate acquisition and pure classification with content identity: testable and tamper-evident.
- Call a repo-reading collector pure given Git behavior: concise, but false and difficult to test exhaustively.
- Reuse porcelain status identity: cheap, but stale content can retain the same digest.

Consequences:
The reader needs integration tests for NUL paths, status variants, modes, and submodules. Gate execution pays two bounded identity checks.

Revisit when:
A repository snapshot or lease can hold all selected inputs immutable through gate exit.

## D-020: Full routing uses a validated policy-root recipe

Date: 2026-08-28
Status: Confirmed
Area: ADD 13 and 14, EDD R-022

Context:
`force_full` had no defined set of passes, capabilities, or gates. Using ordinary changed-file applicability after setting the flag could still omit a gate. An invalid policy also cannot safely define its own fallback.

Decision:
A valid policy contains one root `full_recipe` object. It selects Level 3, the repository's full pass and capability set, and explicit approved gate ids without changed-file glob filtering. If the policy or full recipe cannot validate, routing exits 2 and emits no selective receipt. The caller uses the documented full-verification command outside the router.

Because:
`force_full` needs one deterministic meaning. A broken policy cannot be trusted to describe its own safe fallback.

Options considered:
- Validated policy-root recipe: repository-specific and machine-checkable.
- Derive full from matching rules: an unmapped path could still omit work.
- Hard-code every repository's full route in the universal core: safe only for one repository shape.

Consequences:
Every policy must declare and validate its full recipe before rules load. Missing or invalid policy blocks routing but does not block the existing documented full verification path.

Revisit when:
The calibration schema gains a different repository-bound source of canonical full verification.

## D-021: Local self-grading is recorded and deferred, not solved here

Date: 2026-08-29
Status: Deferred
Area: ADD 14 guardrail 3, EDD 12

Context:
In CI the trusted-base pattern already exists: `proposal-intake.yml` and `efficiency-ledger.yml` both check out a trusted base and run it against the candidate as data. Locally there is no such separation. A developer changing the router computes the route with the changed router, and a developer changing the classifier order changes what their own change classifies as.

Decision:
Record the gap. Do not build a local trusted-base mechanism in SLICE-001.

Because:
The gap is real but inert while routing is advisory. SLICE-001 cannot skip anything, so a self-graded route causes no missing verification. Building a local stash-and-compare mechanism now would grow the slice for a risk that cannot yet cause harm, and the mechanism should be designed against real shadow evidence rather than ahead of it.

Options considered:
- Record and defer: honest, keeps the slice bounded, names the trigger.
- Solve now with a local trusted-base computation: thorough, and significantly larger for a risk with no current consequence.
- Leave it unrecorded: the gap would be rediscovered at the worst moment, when someone proposes enabling selective execution.

Consequences:
Closing this is a precondition of selective local execution, not of this slice. The hard escalators in the policy still force the full route for any change to router code, so a self-graded route is conservative by construction today.

Revisit when:
Selective local execution is proposed. This decision must close before that slice starts.

## D-022: Template rules ship proposed, never approved

Date: 2026-08-29
Status: Confirmed
Area: EDD 5 Rule, SLICE-001 section 10

Context:
The first plan shipped the routing policy template with three rules marked `review_status: approved`. The slice guardrail says adding a rule to the policy requires stopping and asking the owner. Codex found the contradiction.

Decision:
Every rule in the shipped template carries `review_status: proposed`. An installing repository must read each rule and approve it before routing produces anything.

Because:
A shipped file that arrives approved grants routing authority the installing repository never reviewed. `gates.json` already ships everything disabled and proposed for the same reason, and `load_policy` already rejects unapproved rules, so the enforcement exists and only the template was wrong.

Options considered:
- Ship proposed: matches the gates.json precedent, costs one review step per install.
- Ship approved: usable immediately, and hands out authority nobody read.
- Proposed in the template, approved in this repository's own copy: the shape adopted, since this repository reviews its rules under D-023.

Consequences:
A fresh install routes nothing until its owner approves rules. That is the intended friction. Tests that exercise routing must approve their fixture rules explicitly, which also documents what each rule grants.

Revisit when:
A reviewed default rule set is proven safe enough across consuming repositories to justify shipping it live.

## D-023: The slice calibrates this repository before it routes it

Date: 2026-08-29
Status: Confirmed
Area: SLICE-001 sections 3 and 9

Context:
This checkout has no `.agents/skills/anti-dark-code/` and no `.anti-dark-code/`. The shipped `gates.json` template contains zero gates and `owner_confirmed_safe_to_execute` is false. The plan's real-repository walkthrough and its closing evidence both assumed calibration that does not exist.

Decision:
SLICE-001 gains a calibration task before the route command is exercised. It installs the managed core into this repository, adds a routing policy whose rules the owner approves here, and defines four gates matching the existing CI jobs: `validate-core`, `full-suite`, `distribution`, and `hostile-environment`. Those four are also this repository's `full_recipe`.

Because:
A router with nothing to route against cannot produce the evidence the slice promises. Mirroring the four CI jobs means the full recipe is already known to be a real, passing verification set rather than an invented one.

Options considered:
- Calibrate this repository: the router is proven against real anti-dark-code changes, and the four gates are already trusted because CI runs them.
- Fixture repository only: keeps the checkout clean, and never proves the router against real history.
- Defer the walkthrough to SLICE-002: smallest slice, and Task 13 loses its end-to-end evidence.

Consequences:
The repository gains a calibration tree it did not have, which is itself verification authority and therefore a hard escalator. Gates stay dry-run: nothing executes without `--allow-exec`, and `owner_confirmed_safe_to_execute` stays false until the owner sets it deliberately.

Revisit when:
The calibration tree needs to differ from the CI job set, or a consuming repository needs a different bootstrap path.
