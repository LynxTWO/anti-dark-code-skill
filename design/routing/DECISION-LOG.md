# Assurance Router Decision Log

Version: 0.7. Date: 2026-08-29. Status: Round-five review blocked.
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
| D-024 | 2026-08-29 | Classification keeps every matching entry, not the first | Confirmed | |
| D-025 | 2026-08-29 | Unreadable git records are reported, never dropped | Confirmed | |
| D-026 | 2026-08-29 | Git acquisition neutralizes repository-configured execution | Confirmed | |
| D-027 | 2026-08-29 | Acquisition proves framing and preserves copy and mode signals | Confirmed | |
| D-028 | 2026-08-29 | Fact output validates enums and has one cross-platform order | Confirmed | |
| D-029 | 2026-08-29 | Capability count has one executable source of truth | Confirmed | |
| D-030 | 2026-08-29 | A validated policy is an immutable typed value | Confirmed | |
| D-031 | 2026-08-29 | Git acquisition blocks content filters and lazy fetch | Confirmed | |
| D-032 | 2026-08-29 | Raw parsing enforces Git record semantics | Confirmed | |
| D-033 | 2026-08-29 | Copy detection remains unlimited until exhaustion is structured | Confirmed | |
| D-034 | 2026-08-29 | Git path matching preserves literal characters | Confirmed | |
| D-035 | 2026-08-29 | Agent hints carry validated requirements, not computed evidence | Confirmed | |
| D-036 | 2026-08-29 | Lazy fetch is disabled, not tuned | Confirmed | |
| D-037 | 2026-08-29 | Metadata fingerprints are diagnostic only | Confirmed | |
| D-038 | 2026-08-29 | Policy validation proves loader provenance and the canonical full set | Confirmed | |
| D-039 | 2026-08-29 | Raw grammar is enforced across each record and the payload | Confirmed | |
| D-040 | 2026-08-29 | Hints use typed values and approved capability-gate bindings | Confirmed | |
| D-041 | 2026-08-29 | Route results are immutable and every full-recipe field has a mutation guard | Confirmed | |
| D-042 | 2026-08-30 | Policy authority is revalidated, not transferred by a token | Confirmed | |
| D-043 | 2026-08-30 | Boundary identity includes index bytes and path topology | Confirmed | |
| D-044 | 2026-08-30 | Git object format and status grammar come from repository context | Confirmed | |
| D-045 | 2026-08-30 | Every Route construction path freezes nested authority data | Confirmed | |
| D-046 | 2026-08-30 | Mutation records contain replay inputs and run through one harness | Confirmed | |
| D-047 | 2026-08-30 | Cost evidence names units and isolation properties | Confirmed | |
| D-048 | 2026-08-30 | Acquisition stays on the live repository, for capability not cost | Confirmed | |

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

## D-024: Classification keeps every matching entry, not the first

Date: 2026-08-29
Status: Confirmed
Area: ADD 5, EDD 5, EDD 4 R-026

Context:
The plan classified a path by returning on the first matching classifier glob. Codex raised this as part of G-005: template glob order becomes load-bearing, and a broad early entry can classify an authority path as prose. In the shipped classifier `*.md` matches `anti-dark-code/SKILL.md`, which is precisely the collision.

Decision:
`collect_change_facts` emits one fact per matching classifier entry. A path matching no entry emits exactly one fact with confidence `unknown`.

Because:
Keeping every match means every rule that would fire does fire, and the existing monotonic union decides the result. First-match-wins would drop a reading before any rule could see it, and the drop would be invisible. Taking a maximum across matches instead would require inventing a precedence order among sensitivities such as `auth` and `billing`, which are not ordered and should not be forced into a rank.

Options considered:
- One fact per matching entry: no precedence invented, nothing lost, more facts.
- First match wins: fewest facts, and glob order silently decides authority.
- Maximum across matches: one fact per path, and it needs a total order over dimensions that do not have one.

Consequences:
Fact count grows with classifier overlap rather than with the diff alone. That is bounded by the classifier size. Rules must stay single-fact and positive, which R-015 already requires, otherwise duplicate facts could change a match outcome rather than only adding to it.

Revisit when:
Fact volume from overlap becomes a measured problem, or a dimension gains a genuine total order.

## D-025: Unreadable git records are reported, never dropped

Date: 2026-08-29
Status: Confirmed
Area: ADD 5, EDD 5, EDD 4 R-024

Context:
The plan's parser returned an empty list for garbage, a truncated header, and a rename missing its destination. Codex flagged this in G-006 as the remaining fail-closed gap: the caller could not tell an empty change from an unreadable one.

Decision:
`parse_raw_z` and `parse_untracked_z` return a `RawParse` carrying parsed rows and stable reason codes. Those codes union into `ChangeSnapshot.problems`, and `ChangeSnapshot.complete` is true only when the base resolved and no problem was recorded.

Because:
A silent skip is the dangerous case. Routing must know its picture of the change is incomplete before it can refuse to authorize a shortcut. Reporting rather than raising also lets one bad record be described without discarding the records that parsed correctly, which keeps the failure diagnosable.

Options considered:
- Report problems alongside rows: fail closed, diagnosable, one extra field to thread through.
- Raise on the first bad record: loud, and loses every other record plus the ability to describe the change at all.
- Skip silently: simplest, and indistinguishable from a clean empty diff, which is the failure this subsystem exists to prevent.

Consequences:
Every caller must consult `complete` rather than only counting inputs. The reason codes are part of the receipt contract and must stay stable once published.

Revisit when:
A record type currently reported as unknown becomes understood well enough to classify.

## D-026: Git acquisition neutralizes repository-configured execution

Date: 2026-08-29
Status: Confirmed
Area: ADD 5, ADD 14, EDD 7

Context:
A scratch repository set `core.fsmonitor` to a repository-controlled script. One call to `read_change_inputs` started that script three times while returning a complete snapshot. The subprocess code starts trusted Git, but Git then interprets local configuration that can name an executable.

Decision:
Every Git acquisition call disables `core.fsmonitor` on the command line and sets `GIT_OPTIONAL_LOCKS=0`. The hostile-repository test installs a filesystem-monitor script that would write a sentinel, runs every acquisition command, and asserts that the sentinel does not exist. Any later Git option that can start a repository-configured process receives the same deny-by-default treatment before use.

Because:
The router is verification authority. A candidate repository must remain data while its route is computed. Read-only Git subcommands do not establish that boundary when repository configuration can start code.

Options considered:
- Neutralize executable configuration and optional writes for every command: keeps the current Git byte interface and enforces the boundary at one runner.
- Trust local Git configuration: fewer flags, and repository code runs before routing has decided what evidence is required.
- Reimplement Git object and index reading: avoids Git configuration and adds a large parser that this slice does not need.

Consequences:
The default runner owns a documented Git configuration allowlist. Tests cover the real subprocess, not only an injected runner. A failed neutralization blocks selective routing and produces no receipt.

As shipped, 2026-08-29:
Broader than this decision first described. Every call carries `--no-optional-locks`, `-c core.fsmonitor=false`, and `-c diff.external=`, and every diff adds `--no-ext-diff`; the default runner also sets `GIT_OPTIONAL_LOCKS=0`. `diff.external` was included because it is a second configuration path that names a program, and the flags are prefixed through one `_isolated()` helper so a future call cannot quietly skip them. Two tests cover this: a hostile repository whose filesystem monitor would write a sentinel, and a fingerprint of the index and worktree taken before and after acquisition. The second is not decorative; without the lock flags git refreshes the index during an ordinary read, and the test fails.

Revisit when:
A new acquisition command reads configuration that can invoke another process, or Git changes the filesystem-monitor configuration contract.

## D-027: Acquisition proves framing and preserves copy and mode signals

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 6, EDD R-019, R-024, R-027 to R-029

Context:
The round-three probes found three losses. A nonempty raw payload without its final NUL and a header with invalid mode and object columns both produced `complete = true`. `-C` reported a copy from an unchanged source as an add. A staged record that changed content and executable mode was classified as modify because its object ids differed.

Decision:
Parsers validate the terminating NUL and every supported header field before accepting a row. A successful merge-base result must contain one nonempty object id. Raw diffs use unchanged-source copy detection with explicit limits, and limit exhaustion makes the snapshot incomplete. Any mode transition remains explicit even when the record also changes content. Every violation adds a stable problem code and makes the snapshot incomplete.

Because:
`ChangeSnapshot.complete` is the correct single guard from D-025 only if acquisition reports every way its view can be incomplete. Copy provenance and executable mode are routing inputs, not display details.

Options considered:
- Validate framing and preserve all routing signals: supports a meaningful `complete` predicate.
- Keep best-effort rows and trust field count: accepts corrupt transport as a complete diff.
- Hash worktree files during parsing to infer every case: mixes acquisition with parsing and is unnecessary for these status signals.

Consequences:
Real Git tests cover add, modify, delete, rename, unchanged-source copy, pure mode, content-plus-mode, type change, unmerged, staged versus unstaged overlap, and copy-detection limit behavior. Parser fixtures cover corrupt bytes and states the host filesystem cannot create. Git similarity remains a heuristic for changed copies, so the policy must not treat a plain add as proof that no source exists.

As shipped, 2026-08-29:
One deliberate divergence. This decision called for explicit copy-detection limits with exhaustion making the snapshot incomplete. The implementation pins `diff.renameLimit=0`, which is unlimited, and so removes the failure mode rather than detecting it. Detecting exhaustion would require reading git's stderr, which the runner does not currently return, and an undetected truncation is the silent fidelity loss this decision exists to prevent. Measured on 2026-08-29, and the measurement settles the trade-off rather than estimating it.

- This repository, full acquisition: 0.202s.
- A real foreign repository of 345 tracked files and 3395 commits, acquiring a 400-commit range: 0.235s for 264 inputs, and detection found 11 copies and 6 renames that the earlier flags would have reported as plain adds.
- A synthetic repository of 3000 files, every one renamed and modified in one commit, which is the worst case for inexact detection: 1.89s with `diff.renameLimit=0`, finding all 3000 renames. With git's default limit the same diff takes 0.10s and finds **zero** renames, reporting 6000 unrelated adds and deletes instead.

The default limit does not fail loudly. Git writes `exhaustive rename detection was skipped` to stderr, and the runner returns stdout only, so the router would have accepted a change set with every rename source silently missing. That is the precise failure this decision exists to prevent, and it is why removing the failure mode was chosen over detecting it.

Cost scales roughly linearly across the measured range: 100 changed paths 0.11s, 300 paths 0.17s, 6000 paths 1.86s, against a fixed overhead near 0.10s.

The honest consequence: a commit that renames several thousand files exceeds the one-second goal in EDD section 3. Correctness is preferred there. A change of that shape is rare, it forces the full route anyway on most policies, and losing every rename source is worse than waiting two seconds.

Mode transitions are carried by a `mode_changed` field on both `ChangeInput` and `ChangeFact` rather than only by `change_kind`, because a record that changes content and mode together has unequal object ids and would otherwise lose the signal.

Revisit when:
Git adds a raw status or object format that the validated grammar does not yet support, or the runner gains a stderr channel and exhaustion can be detected directly.

## D-028: Fact output validates enums and has one cross-platform order

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-002, R-026, R-030 to R-032

Context:
D-024 correctly keeps every matching classifier entry. The implementation still accepted invalid classifier, source, and change-kind values. Its canonical sort omitted `related_path`, so two copies from one source changed order across Python hash seeds. `fnmatch.fnmatch` also normalized case on Windows, which made the same Git path and policy classify differently from Linux.

Decision:
Validate all classifier and input enum values before emitting a fact. Match Git paths with case-sensitive, slash-normalized semantics on every platform. Deduplicate facts, then sort by every serialized `ChangeFact` field, treating a missing `related_path` as an empty string.

Because:
Closed sets are not enforced by declaring frozensets. Receipt bytes cannot depend on a process hash seed or the host operating system. D-024 adds facts monotonically, but each fact must still be valid and canonical.

Options considered:
- Validate and sort the full record: one deterministic contract and early policy errors.
- Trust policy validation elsewhere: leaves the public pure function able to emit invalid facts.
- Preserve host-native glob case behavior: familiar to `fnmatch`, and incompatible with cross-platform receipt identity.

Consequences:
Tests inject one invalid value for every enum, compare several hash seeds, cover duplicate rows, and run a case-collision fixture. These tests supplement the existing broad-plus-specific match test rather than changing D-024.

As shipped, 2026-08-29:
Implemented as described. One honest limit on the test: `test_glob_matching_is_case_sensitive_on_every_platform` can only fail on a case-insensitive host, because `fnmatch` is already case-sensitive on Linux and macOS. It caught the defect on Windows. The cross-platform CI matrix is what makes this requirement enforceable, not the test alone.

Revisit when:
The policy schema introduces a dimension with non-string values or defines explicit case-insensitive matching.

## D-029: Capability count has one executable source of truth

Date: 2026-08-29
Status: Confirmed
Area: EDD 11, SLICE-001 M1

Context:
`CAPABILITY_COUNT` replaced the five runtime literals and two `test_adc.py` literals found in round two. The new contiguity test then introduced `range(1, 23)`, which is another count contract and will need a manual edit for V23.

Decision:
Runtime code and count-derived tests use `adc.CAPABILITY_COUNT`. Tests may name V21 and V22 to preserve D-016, but they do not derive the total from a new integer literal. A drift check searches for count derivation rather than only the previous number.

Because:
A scanner that knows only the last stale number repeats the same repair at the next catalog extension. Identity assertions and count assertions have different jobs.

Options considered:
- Reuse `CAPABILITY_COUNT`: one count contract while retaining explicit V21 and V22 tests.
- Keep `range(1, 23)`: readable today and stale at V23.
- Derive the expected ids only from the catalog: cannot detect a missing id in the middle without an independent upper bound.

Consequences:
The contiguity test imports the count constant. Future capability additions change one count plus the catalog, while the V21 and V22 identity tests remain unchanged.

Revisit when:
Capability ids stop being a contiguous `VNN` sequence.

## D-030: A validated policy is an immutable typed value

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-016, SLICE-001 M2

Context:
The round-four review changed a nested rule from proposed to approved after `load_policy` returned. The loaded value changed with the caller's object and then produced a cheap route. `build_route` also accepts an ordinary mapping, so the type boundary does not prove validation happened.

Decision:
`load_policy` returns a deeply immutable `ValidatedPolicy`. Rules, classifier entries, recipes, passes, capability ids, and gate ids use canonical immutable records. `build_route` accepts only this type. The capability catalog and canonical full-set inputs are mandatory at load time. No internal count default is allowed.

Because:
Validation is a trust boundary only if later mutation and unvalidated callers cannot bypass it. D-020 requires the full recipe to be Level 3 and to name the repository's canonical full set.

Options considered:
- Frozen typed records: validation state is visible in the type and nested mutation is impossible.
- Deep-copy JSON dictionaries: removes aliasing but still lets `build_route` receive an unvalidated dictionary.
- Revalidate on every route: safe but repeats work and leaves the interface ambiguous.

Consequences:
Policy tests mutate every source container after load. Full-recipe validation has its own Level 3 and full-set checks. Receipt serialization receives one canonical policy shape.

As shipped, 2026-08-29:
`ValidatedPolicy`, `ValidatedRule`, and `ValidatedRecipe` are frozen dataclasses built from copies, and `build_route` raises `TypeError` on a plain mapping so validation cannot be skipped at a call site. Verified against the original attack: mutating the caller's nested rule from proposed to approved after load no longer changes the route.

Revisit when:
The policy schema changes or another trusted loader produces the same typed value.

## D-031: Git acquisition blocks content filters and lazy fetch

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-027, SLICE-001 M2

Context:
The filesystem-monitor sentinel passed, but a real repository clean filter still ran during `read_change_inputs`. It wrote a new worktree file and the snapshot remained complete. Git can also fetch a missing promisor object unless lazy fetch is disabled.

Decision:
D-026 remains the governing boundary and this entry extends its required controls. Acquisition must neutralize effective `filter.<driver>.clean`, `filter.<driver>.smudge`, and `filter.<driver>.process` commands, disable required filter failure, add `--no-textconv`, and set both `--no-lazy-fetch` and `GIT_NO_LAZY_FETCH=1`. If effective configuration cannot be neutralized, acquisition is incomplete. Tests use real clean and process filters that would write sentinels. An offline partial-clone case verifies that no fetch is attempted.

Because:
A fixed list covering one demonstrated command family does not prove that a candidate repository stays data. Offline behavior is also a product requirement.

Options considered:
- Neutralize every effective execution family and test each one: keeps the Git byte interface with a wider preflight.
- Use lower-level acquisition with no worktree conversion: a stronger boundary, with more implementation work.
- Keep only the filesystem-monitor test: already refuted by the clean-filter probe.

Consequences:
The isolation helper has an explicit inventory and a hostile test per family. The default runner no longer inherits a path to on-demand object fetching.

As shipped, 2026-08-29:
Wider than the decision describes, and built in three layers rather than as a longer list of keys, because enumerating keys had failed twice. Only the worktree comparison converts content, so only it can start a filter; the other three acquisitions read objects or names and are safe by construction. Drivers are discovered with `git config --get-regexp ^filter\.`, which reads configuration as data and finds a global driver such as git-lfs alongside a local one, and each is overridden to no command with `required=false`. Because the neutralized set still cannot be proven complete, acquisition fingerprints the repository before and after and records `ADC-ROUTE-BOUNDARY-VIOLATED` if anything moved, turning an unknown path from a silent escape into a recorded one.

The fingerprint's first version walked the directory tree and cost 14.4 seconds on a real 345-file repository, because it crawled 62,245 build artifacts, taking acquisition from 0.235s to 21.3s. Scope is now what git reports, tracked plus untracked-not-ignored: 0.412s on the same repository. The accepted limit is a write into an ignored directory, which cannot alter a route.

Revisit when:
A Git command or configuration key adds another program or network path.

## D-032: Raw parsing enforces Git record semantics

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-024 and R-028, SLICE-001 M2

Context:
The current parser rejects malformed character counts but accepts status `A100`, score `R999`, mode `777777`, and mixed 40 and 64 digit object ids. Each record returns with no problem.

Decision:
Raw records validate the supported Git modes, one repository object-id width, null-side consistency, and the status-specific score grammar. C and R require scores from 0 through 100. Only statuses documented to accept a score may carry one. A semantic violation records `ADC-ROUTE-MALFORMED-RECORD` and makes the snapshot incomplete.

Because:
Framing alone does not establish that the parsed row is a Git record. An impossible row cannot be accepted as complete input to verification authority.

Options considered:
- Encode the documented raw grammar: narrow and deterministic.
- Keep regular-expression shape checks: accepts impossible records.
- Trust Git output without parsing checks: fails the transport boundary from D-025.

Consequences:
Parser tables include status and score boundaries, modes, object widths, and status-specific null sides. Repository object format is acquired once and checked against every row.

As shipped, 2026-08-29:
Modes are the closed set git writes, both object ids must share a width, and a similarity score is allowed only on C and R and only from 0 to 100. Implementing it produced a wrong rule that a real-git test caught before commit: requiring a null object and a null mode to agree on both sides broke every unstaged record, because git writes a null object with a real mode there. The rule is one-directional, and the accepted shape has its own test with the real record quoted.

Revisit when:
Git adds a status, mode, score rule, or object format that the parser does not know.

## D-033: Copy detection remains unlimited until exhaustion is structured

Date: 2026-08-29
Status: Confirmed
Area: ADD 11, EDD 3, EDD R-029, SLICE-001 M2

Context:
D-027 called for a bounded copy search with detected exhaustion. Git's default limit reported a synthetic 3000-file rename as 6000 unrelated adds and deletes. The runner discards the warning on stderr. Unlimited detection found all sources in 1.89 seconds.

Decision:
Keep `diff.renameLimit=0` until the runner retains a tested exhaustion signal. The one-second target applies to this repository and ordinary changes up to roughly one thousand paths. A several-thousand-path rename may exceed it. If a limit returns, exhaustion makes the snapshot incomplete.

Because:
Provenance loss is a correctness failure. A short delay on an unusual full-route change is the smaller cost.

Options considered:
- Unlimited detection: measured, complete, and occasionally slower than the target.
- Default limit with discarded stderr: fast and silently incomplete.
- Bounded detection with stderr retained and tested: acceptable when the runner has that channel.

Consequences:
Performance evidence reports both common and pathological shapes. The acquisition result must grow beyond `bytes | None` before a bounded setting is allowed.

As shipped, 2026-08-29:
Measured rather than estimated. A synthetic repository of 3000 files, all renamed and modified in one commit, takes 1.89s with `diff.renameLimit=0` and finds all 3000 renames; under git's default limit it takes 0.10s and finds zero, reporting 6000 unrelated adds and deletes, and announces that only on stderr, which the runner discards. A real 345-file repository acquires a 400-commit range in 0.412s.

Revisit when:
Git exposes a structured exhaustion result or the runner safely retains and classifies diagnostics.

## D-034: Git path matching preserves literal characters

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-026 and R-032, SLICE-001 M2

Context:
Case-sensitive matching is correct, but replacing backslash with slash changes a legal POSIX filename. The existing case test depends on running on a case-folding host.

Decision:
Match the path text emitted by Git without host separator rewriting. Policy patterns use forward slash for Git directory boundaries. A literal backslash remains a literal character. The case test patches `os.path.normcase` to simulate a case-folding host and asserts classification behavior, without checking which match function was called.

Because:
Repository paths are protocol data at this boundary, not host paths. A behavioral simulation gives every host the same chance to detect a regression.

Options considered:
- Preserve input characters and simulate case folding: host-independent and faithful to Git path data.
- Replace backslashes: convenient on Windows and wrong for a POSIX filename containing one.
- Depend only on the CI platform matrix: useful as a second line, but one local run cannot enforce the contract.

Consequences:
A POSIX real-repository test covers a filename containing backslash. Windows skips only that filesystem fixture. Every host runs the simulated case-folding test.

As shipped, 2026-08-29:
Verified against real git that paths arrive with forward slashes on every platform, including Windows, so the rewrite solved a problem that does not exist. A file named `auth\login.py` had been matching `auth/*` and taking that rule's sensitivity.

Revisit when:
Policy syntax adds an explicit escape or case-insensitive match mode.

## D-035: Agent hints carry validated requirements, not computed evidence

Date: 2026-08-29
Status: Confirmed
Area: ADD 8.6 and 14, EDD R-020, SLICE-001 M2

Context:
`apply_hints` protects rule matches but accepts arbitrary pass, capability, gate, path, and reason strings. An agent can place values in fields that are supposed to describe deterministic router evidence.

Decision:
Hints use a validated type bound to the loaded policy and catalogs. They may raise the level, add known passes and obligations, or set escalation booleans. They may not write `matched_rule_ids`, `unmapped_paths`, or `unknowns`. Unknown hint keys and invalid values are errors.

Because:
Escalation does not need permission to rewrite the explanation of how the route was computed. Invalid requirement ids make a later receipt or gate plan untrustworthy even when they cannot lower the route.

Options considered:
- Validated requirement-only hints: retains semantic escalation and preserves computed evidence.
- Raw route-shaped mappings: simple and accepts invented values.
- No hints: removes a useful signal already settled by D-006.

Consequences:
Hint tests start from routes with nonempty unknown and unmapped sets. Mutation tests prove those values cannot be lost. Invalid pass, capability, gate, reason, and unknown-key cases fail before routing.

As shipped, 2026-08-29:
Hints may write only the five requirement fields, and every pass, capability, and gate is checked against the loaded policy. `matched_rule_ids`, `unmapped_paths`, and `unknowns` are refused outright, so an agent cannot claim a rule matched or a path was mapped. `apply_hints` gained the policy as a third argument.

Revisit when:
A new hint field has a deterministic validation source and cannot lower or rewrite computed evidence.

## D-036: Lazy fetch is disabled, not tuned

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-034, SLICE-001 M2

Context:
Round five ran acquisition in a blobless partial clone. Rename detection started `git fetch`, downloaded a missing blob, and returned a complete snapshot. `fetch.negotiationAlgorithm=noop` was present on the command and the fetch child inherited it.

Decision:
Every acquisition subprocess sets `GIT_NO_LAZY_FETCH=1`. A missing promisor object makes acquisition incomplete. `fetch.negotiationAlgorithm=noop` is not a no-fetch control and must not be described as one.

Because:
Negotiation controls what object reachability information a fetch exchanges. It does not prevent Git from starting a fetch. A candidate remote, credential helper, or remote helper must not execute while verification authority reads repository data.

Consequences:
R-034 includes a real blobless partial clone whose rename comparison needs a missing blob. The test proves that no fetch child starts, no object appears, and the snapshot is incomplete.

As shipped, 2026-08-30:
`fetch.negotiationAlgorithm=noop` is removed from the isolation flags entirely, and `GIT_NO_LAZY_FETCH=1` is set in the runner environment. One honest limit: the fetch could not be reproduced here, because a local file transport ignores the partial-clone filter and the resulting objects are packed, so no single loose object can be removed. The test asserts the control is present rather than the behaviour it prevents, and its docstring says so rather than implying coverage it does not have.

Revisit when:
Git adds a documented command-level no-lazy-fetch option supported by every minimum platform version.

## D-037: Metadata fingerprints are diagnostic only

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-027 and R-034, SLICE-001 M2

Context:
The boundary fingerprint records index size and mtime plus tracked and untracked file size and mtime. A hostile runner changed a tracked file after the worktree diff, preserved its size and mtime, and the snapshot returned complete with no inputs or problems.

Decision:
A size-and-mtime fingerprint may support diagnostics and performance measurements. It does not prove that acquisition was read-only. The boundary check uses content identity for the index and every routing-relevant path, or moves acquisition to an isolated copy whose candidate state cannot affect the source repository.

Because:
Metadata can remain equal while bytes change. A detector with that blind spot cannot support the statement that an unknown execution path becomes a recorded failure.

Consequences:
The hostile test mutates a tracked file after its comparison, keeps size and mtime equal, and requires `ADC-ROUTE-BOUNDARY-VIOLATED`. Ignored-path writes remain an explicit side-effect limit, not evidence that no candidate program ran.

As shipped, 2026-08-30:
Content identity is used, and metadata is kept alongside it rather than demoted to diagnostics. Switching to content alone broke the existing boundary test, which exposed the mirror-image blind spot: content cannot see a rewrite with identical bytes, because only the timestamp moves. The fingerprint records size, mtime, and a content digest, so any one of the three moving is enough. Mutants M12 and M13 remove one half each and both are caught, which is the evidence that neither half is decorative.

Measured cost of the content digest: acquisition is 0.474s on this repository and 0.853s on a real 345-file repository. A synthetic 3000-file commit where every file changed is 5.4s, which exceeds the goal in EDD section 3 and is recorded there.

Revisit when:
Acquisition runs against a trusted, immutable repository representation.

## D-038: Policy validation proves loader provenance and the canonical full set

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-035, R-036, and R-049, SLICE-001 M2

Context:
The public frozen dataclasses can be constructed directly. A caller built a `ValidatedPolicy` with a Level 0 empty recipe and an approved cheap rule, then passed the type check. `load_policy` also accepts a Level 3 recipe with only pass 00 and one capability because it has no canonical full-set input.

Decision:
The loader is the only supported constructor for policy authority. The route boundary checks loader provenance or revalidates the immutable value. Loading also requires the caller's canonical pass, capability, and approved gate sets and rejects any incomplete full recipe.

Because:
A class name proves shape, not that validation ran. Level 3 is a label unless the recipe names the repository's reviewed full set.

Consequences:
Tests directly construct every exported policy record and require rejection at `build_route`. Separate tests remove one pass, capability, and gate from the canonical full recipe and require `PolicyError` at load.

Revisit when:
Policy records become private implementation details behind a constructor that callers cannot invoke directly.

## D-039: Raw grammar is enforced across each record and the payload

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-037, SLICE-001 M2

Context:
The parser accepts C and R without scores, A with an existing old side, D with an existing new side, and one payload containing both 40 and 64 digit object ids. Each case returns inputs with no problem.

Decision:
Record validation enforces required C and R scores, status-specific absent sides, legal worktree null-object exceptions, and one object format for the complete payload. Repository object format is an acquisition input, not a record-local guess.

Because:
Per-field character checks accept combinations Git cannot emit. Mixing valid record-local widths does not make a valid repository payload.

Consequences:
Parser tables include every status, required and forbidden scores, absent-side rules, SHA-1, SHA-256, symlink, gitlink, type-change, and conflict records from real Git.

As shipped, 2026-08-30:
One case was deliberately left looser than the decision states. An unrecognised status letter still produces a row with change kind `unknown` and a separate `ADC-ROUTE-UNKNOWN-STATUS` report, rather than being refused as malformed. Refusing it would discard the path, and a lost path is worse than an unknown kind that forces the full route anyway.

Revisit when:
Git documents a new raw status, object format, mode, or null-side form.

## D-040: Hints use typed values and approved capability-gate bindings

Date: 2026-08-29
Status: Confirmed
Area: ADD 8.6 and 14, EDD R-020 and R-039, SLICE-001 M2

Context:
Round five supplied level 999, string `false`, a capability paired with a gate approved only for another capability, and a pair present only in a proposed rule. Every hint was accepted.

Decision:
Hint validation checks value shapes before conversion. Levels use the closed level set. Boolean fields accept booleans only. Obligation additions must be approved capability-gate pairs from the canonical full recipe or approved rules. Proposed rules do not expand hint vocabulary.

Because:
Validating capability and gate membership in separate unions loses the relationship that an obligation asserts. Python truth conversion also turns the string `false` into true.

Consequences:
Invalid shape, range, cross-pair, and proposed-only tests fail with `HintError` before a new Route is built.

Revisit when:
The policy adds a separate reviewed catalog of hint-only obligation bindings.

## D-041: Route results are immutable and every full-recipe field has a mutation guard

Date: 2026-08-29
Status: Confirmed
Area: ADD 5 and 14, EDD R-001, R-003, and R-041, SLICE-001 M2

Context:
`Route` is frozen, but its obligation mapping is a mutable dictionary. A caller can clear it after routing. Three further mutations also passed all 148 router tests: dropping the full recipe's minimum level, dropping its independent-review flag, and dropping the unrouted-fact reason.

Decision:
Every nested Route value uses an immutable canonical representation. Focused tests start from a force-full cause that does not already supply the recipe's level or review flag. Each stable reason code and every full-recipe field has a mutation guard.

Because:
A frozen outer dataclass does not protect a nested dictionary. An authority-path fixture can also hide a missing recipe field when its matching rule supplies the same value.

Consequences:
Mutation tests use discriminating fixtures and fail one field at a time. Route serialization cannot observe caller changes after construction.

Revisit when:
A new Route field or force-full cause is added.

## D-042: Policy authority is revalidated, not transferred by a token

Date: 2026-08-30
Status: Confirmed
Area: ADD 5 and 14, EDD R-035 and R-036, SLICE-001 M2

Context:
`load_policy` still returns a policy when called with no canonical full-set argument. `dataclasses.replace` also copies the loader token into a record whose recipe and rules were replaced. `build_route` accepts that record and can return a cheap route.

Decision:
`full_set` is a required `load_policy` argument. A route boundary must either revalidate the full immutable policy against the canonical inputs or accept an authority object whose validation cannot be transferred to changed fields. A private identity token alone is not policy authority.

Because:
Optional canonical data proves only the policy's local shape. A copied token says one ancestor passed the loader, not that the fields now being routed passed it.

Options considered:
- Revalidate at `build_route`: simple and safe, with a small pure-function cost.
- Keep a token plus a digest over every validated field and canonical input: acceptable if the digest is checked at the route boundary.
- Trust the copied token: rejected because `dataclasses.replace` preserves it.

Consequences:
Tests omit `full_set`, remove one canonical member at a time, and replace every authority field after loading. No changed policy can produce a selective route without another validation.

Revisit when:
Policy records become private values with no public field-copy path.

## D-043: Boundary identity includes index bytes and path topology

Date: 2026-08-30
Status: Confirmed
Area: ADD 5 and 14, EDD R-017, R-034, and R-050, SLICE-001 M2

Context:
The boundary check hashes worktree bytes but records only index size and mtime. A same-size alternate index with restored mtime escaped detection. A tracked file replaced by a hard link with equal bytes, size, and mtime also escaped detection.

Decision:
Hash the resolved Git index bytes. For every routing-relevant path, record `lstat` identity, file type, mode, link count, and the content identity appropriate to that type. Record symlink targets without following them. Resolve Git administrative paths with `git rev-parse --git-path`, including linked worktrees. If portable path identity cannot be established, use an isolated immutable repository representation.

Because:
Index bytes are authority data. Path bytes do not describe whether a file became a symlink or a hard link. Size and mtime do not describe either change.

Options considered:
- Content, metadata, index digest, and path topology: accepted for the current boundary.
- Candidate state in an isolated immutable representation: acceptable after a complete design and measurement.
- Size, mtime, and regular-file bytes only: rejected by the two real probes.

Consequences:
R-050 includes same-size index replacement, content-preserving hard-link replacement, symlink replacement where the host permits it, and linked-worktree index mutation. Each makes acquisition incomplete with `ADC-ROUTE-BOUNDARY-VIOLATED`.

Revisit when:
Acquisition no longer reads candidate-owned mutable state.

## D-044: Git object format and status grammar come from repository context

Date: 2026-08-30
Status: Confirmed
Area: ADD 5 and 14, EDD R-037 and R-051, SLICE-001 M2

Context:
Object width is inferred separately for each parser call. One snapshot therefore accepted a 64-digit committed record and a 40-digit staged record. Real unmerged index and worktree records use null sides that the current `U` rule rejects.

Decision:
Acquire the repository object format once and pass its object-id width through merge-base and every raw parser call. Validate status sides by source using real Git fixtures. Unknown future status letters keep their path, add `ADC-ROUTE-UNKNOWN-STATUS`, and make the snapshot incomplete.

Because:
A repository has one object format across every comparison. Index, worktree, and tree comparisons do not emit identical null-side forms for conflicts.

Options considered:
- Repository format plus source-specific grammar: accepted.
- Per-call width inference and one status table: rejected by mixed-source and real-conflict probes.
- Drop unknown rows: rejected because it loses the changed path.

Consequences:
R-051 uses SHA-1, SHA-256, symlink, gitlink, type-change, staged conflict, and worktree conflict output produced by Git. Mixed widths across separate acquisition calls are malformed.

Revisit when:
Git documents a new object format or raw status form.

## D-045: Every Route construction path freezes nested authority data

Date: 2026-08-30
Status: Confirmed
Area: ADD 5 and 14, EDD R-001, R-041, and R-052, SLICE-001 M2

Context:
`build_route` and `apply_hints` currently freeze obligations, but the public dataclass does not enforce that invariant. `dataclasses.replace(route, obligations={...})` produces a Route whose obligations can be cleared. A mutation that returns a mutable mapping from the hint path also survives the router suite.

Decision:
The Route constructor canonicalizes every nested field in `__post_init__`, or Route becomes private behind one constructor. Tests cover direct construction, `dataclasses.replace`, `copy`, the build path, and the hint path.

Because:
Immutability is a type invariant. Call-site discipline leaves new constructors and copy paths outside the guarantee.

Options considered:
- Constructor-level canonicalization: accepted while Route remains public.
- Private Route plus reviewed factories: acceptable.
- Freeze at selected return statements: rejected by the replace probe and M34.

Consequences:
Every Route observed by a later receipt or runner has immutable obligations, regardless of how it was constructed.

Revisit when:
Route stops crossing a public module boundary.

## D-046: Mutation records contain replay inputs and run through one harness

Date: 2026-08-30
Status: Confirmed
Area: EDD R-041 and R-053, SLICE-001 M2

Context:
`mutants/matrix.json` contains ids, names, verdicts, and old pytest summaries. It does not contain source paths, original strings, or replacements. The 32 rows were reconstructed from prose and current source, so the stored file alone cannot replay them. Two further authority mutants survived.

Decision:
Each mutation row stores source path, original text, replacement text, command, verdict, and observed summary. One checked-in harness requires one original-text match, applies one row, runs the command, restores the source, and verifies a clean worktree. A survivor blocks the pure-layer gate.

Because:
A verdict without its transformation cannot be audited or repeated. Manual reconstruction tests the reviewer's guess rather than the stored mutation.

Options considered:
- Data rows plus one harness: accepted.
- Prose names and manual edits: rejected by this round.
- A third-party mutation package: deferred because the current standard-library harness is enough.

Consequences:
M33 and M34 are recorded in `mutants/round-six-challenge.json`. The original 32 remain qualified until their missing replay fields are supplied and the checked-in harness reproduces them.

Revisit when:
The repository adopts a maintained mutation runner that preserves these replay properties.

## D-047: Cost evidence names units and isolation properties

Date: 2026-08-30
Status: Confirmed
Area: ADD 11, EDD 3 and R-055, SLICE-001 M2

Context:
On the cited 345-file repository, a bare shared clone took 0.160 to 0.770 seconds and stored 38,477 logical bytes, not 5.6 seconds and 38 MB. Its alternates file points to the candidate object store. It has no candidate worktree or index. The 82.32 percent raw-hash mismatch is real, but it compares CRLF worktree bytes with normalized Git blob ids.

Decision:
Cost records state the command, repeated wall times, logical bytes, allocated bytes when relevant, object-sharing mode, and which candidate state is represented. Raw worktree digests are independent boundary identities and are not compared with Git blob ids. A shared bare clone is not evidence for an isolated acquisition design.

Because:
Unit errors and shared storage changed the architecture conclusion. Line-ending normalization does not stop a separate digest from detecting a before-and-after byte change.

Options considered:
- Keep current acquisition while D-043 is implemented: accepted as the next correction.
- Design and measure a non-shared isolated worktree and index: open for later review.
- Reject raw-byte identity because it differs from blob ids: rejected because the identities answer different questions.

Consequences:
The clone cost and the inference drawn from the 82 percent mismatch are withdrawn. Performance remains measured on common and high-path-count inputs, with host and run variance stated.

Revisit when:
An isolated candidate representation covers commits, index, worktree, untracked paths, modes, symlinks, and submodules.

## D-048: Acquisition stays on the live repository, for capability not cost

Date: 2026-08-30
Status: Confirmed
Area: ADD 4 to 6, supersedes the reasoning recorded against D-030

Context:
The owner asked whether acquisition should read from an isolated repository representation rather than the live repository, after enumerating git configuration keys had failed twice. I costed that option and recommended against it. The costing was wrong, which N-07 established: a bare shared clone of a 345-file repository takes 145 to 155 milliseconds and stores about 27 kilobytes, not the 5.6 seconds and 38 megabytes I reported. I had read `du -sb` bytes as megabytes and timed one cold run. The second argument was misapplied as well: the 82 percent raw-to-blob mismatch rules out using our own hash to detect unstaged changes, and says nothing about using one as a boundary digest, which is what was actually built.

Both arguments being wrong, the question was reopened and measured again.

Decision:
Acquisition continues to read the live repository. The isolated representation is refused on capability, not on cost.

Because:
A bare clone has no worktree and an empty index, so it cannot observe three of the four sources routing needs. Measured against a repository with one committed change, one staged change, one unstaged change, and one untracked file:

- committed: observed correctly.
- staged: **observed wrongly**. The clone reported every tracked file as deleted, because it compares its own empty index against HEAD. Origin had exactly one modified path. This is not a gap, it is a false answer that would route as though the tree had been emptied.
- unstaged: invisible.
- untracked: invisible.

The comparisons a clone does isolate are the ones already safe by construction: committed and staged read objects, and untracked reads names. The one comparison that can execute anything is the worktree diff, and that is precisely the one a clone cannot perform at all. So the option isolates what needs no isolation and loses what matters.

`--shared` also does not isolate objects. It writes an alternates file pointing into the candidate object store, so the clone reads the same objects through a different configuration.

Options considered:
- Live repository with discovered filter overrides and a boundary fingerprint: keeps every source, and the boundary is checked rather than asserted per D-030.
- Bare shared clone: cheap, isolates config, cannot see staged, unstaged, or untracked, and answers the staged question incorrectly.
- Full clone: adds object copying cost and has the same capability loss.
- `git worktree add`: writes administrative files into the candidate repository, which breaks the read-only property this is meant to protect.

Consequences:
The boundary continues to rest on discovery plus detection rather than on isolation by construction. D-030's third layer stays load-bearing, which is why its mutants matter.

Revisit when:
A representation appears that can observe index and worktree state without executing candidate configuration, or the worktree source is dropped from routing entirely.
