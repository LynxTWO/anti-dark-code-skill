# Assurance Router Decision Log

Version: 1.0. Date: 2026-08-30. Status: Audited.
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
| D-049 | 2026-08-30 | Route freezes by value even when given a mapping proxy | Confirmed | |
| D-050 | 2026-08-30 | Snapshot object width stays bound to the resolved merge base | Confirmed | |
| D-051 | 2026-08-30 | Symlink guards carry platform evidence and separate target text | Confirmed | |
| D-052 | 2026-08-30 | Unmerged side presence comes from modes, not object ids | Confirmed | |
| D-053 | 2026-08-30 | parse_raw_z is public for any raw git output | Confirmed | |
| D-054 | 2026-08-30 | Mutation verdicts are platform-qualified | Confirmed | |
| D-055 | 2026-08-30 | Route is not picklable, and does not need to be | Confirmed | |
| D-056 | 2026-08-30 | The missing-promisor case is blocked, not closed | Open | |
| D-057 | 2026-08-30 | The T540P was reachable, and the diagnosis was wrong | Corrected | |
| D-058 | 2026-08-30 | Linux is a required replay host, and it runs in CI | Confirmed | |
| D-059 | 2026-08-30 | macOS is verified for the suite and is not a replay host | Confirmed | |
| D-060 | 2026-08-30 | The missing-promisor case is proven with a real transport | Confirmed | |
| D-061 | 2026-08-30 | The requirement register names a file, so it proves nothing | Reopened | D-070 |
| D-062 | 2026-08-30 | The canonical full set belongs to the gates, not the policy | Confirmed | |
| D-063 | 2026-08-30 | A receipt binds content, not timestamps, and never its own store | Confirmed | |
| D-064 | 2026-08-30 | This repository's policy ships with every rule unapproved | Confirmed | |
| D-065 | 2026-08-30 | A hard-link test passed on Linux for the wrong reason | Confirmed | |
| D-066 | 2026-08-30 | The record carries two hosts, and the verdict is a function of them | Confirmed | |
| D-067 | 2026-08-30 | M3 needed an executable traceability gate | Reopened | D-070 |
| D-068 | 2026-08-30 | Mutation authority requires a real test runner and exact restoration | Confirmed | |
| D-069 | 2026-08-30 | M4 is blocked by its plan, not by D-061 | Resolved | |
| D-070 | 2026-08-30 | Node-id reachability is necessary and not sufficient evidence | Open | |
| D-071 | 2026-08-30 | A classifier is what makes a path authority, and it is checked at load | Confirmed | |
| D-072 | 2026-08-30 | A submodule is refused, not bound | Confirmed | |
| D-073 | 2026-08-30 | An unreadable repository fingerprint refuses the binding provisionally | Superseded | D-083 |
| D-074 | 2026-08-30 | Candidate routes are a separate shadow-only type | Confirmed | |
| D-075 | 2026-08-30 | Gate execution consumes one verified receipt and its exact identity | Confirmed | |
| D-076 | 2026-08-30 | Verified execution authority is a closed in-memory context | Confirmed | |
| D-077 | 2026-08-31 | A gate lifecycle and a receipt binding ask different questions | Confirmed | |
| D-078 | 2026-08-31 | The self-grading guard enumerates shapes instead of sampling one | Confirmed | |
| D-079 | 2026-08-31 | N-08 was a test that proved nothing, cited as evidence | Confirmed | |
| D-080 | 2026-08-31 | Per-change EDD evidence starts at a review-trailer anchor | Confirmed | |
| D-081 | 2026-08-31 | The historical live-mutant scan is retired behind maintained guards | Confirmed | |
| D-082 | 2026-08-31 | Self-grading probes source and managed installed layouts | Confirmed | |
| D-083 | 2026-08-31 | An unreadable fingerprint raises a typed receipt refusal | Confirmed | |
| D-084 | 2026-08-31 | Worktree-writing gates remain stale for this slice | Confirmed | |
| D-085 | 2026-08-31 | Filter neutralization is verified, not assumed | Confirmed | |
| D-086 | 2026-08-31 | The self-grading guard covers every prefix the installer writes | Amended | D-091 |
| D-087 | 2026-08-31 | A mutation target must match exactly one place | Confirmed | |
| D-088 | 2026-08-31 | Neutralize through the environment, and refuse only what that cannot reach | Confirmed | |
| D-089 | 2026-08-31 | Calibration is authority, and it lives outside the skill tree | Amended | D-091 |
| D-090 | 2026-08-31 | A decision id cited in code must exist | Amended | |
| D-091 | 2026-08-31 | Every routing-owning pass reference is a guard probe | Confirmed | |
| D-092 | 2026-08-31 | Host-generated pytest cache is not install provenance | Confirmed | |
| D-093 | 2026-09-01 | Self-grading authority is a classifier contract, not a path sample | Confirmed | |
| D-094 | 2026-09-01 | A stronger guard supersedes a redundant mutation row | Confirmed | |
| D-095 | 2026-09-02 | An unskipped local survivor is a survivor on every host | Amended | D-104 |
| D-096 | 2026-09-02 | A parallel replay requires a clean coordinator tree | Amended | D-103 |
| D-097 | 2026-09-02 | A helper that adc.py loads is authority by its name | Superseded | D-100 |
| D-098 | 2026-09-02 | A worker's collection tree stays inside its clone | Amended | D-101 |
| D-099 | 2026-09-02 | The coordinator reports a worker row's own reason | Amended | D-102 |
| D-100 | 2026-09-02 | Every shipped script is verification authority by location | Confirmed | D-107 |
| D-101 | 2026-09-02 | A worker owns its pytest environment as well as its rootdir | Amended | D-105 |
| D-102 | 2026-09-02 | A worker diagnostic is one bounded terminal-safe line | Amended | D-106 |
| D-103 | 2026-09-02 | Serial evidence labels dirt, and serial writes require clean endpoints | Confirmed | |
| D-104 | 2026-09-02 | A skipped survivor needs exact catching-test attribution | Confirmed | |
| D-105 | 2026-09-02 | A worker owns its interpreter and its configuration, not only its pytest options | Confirmed | |
| D-106 | 2026-09-02 | The serial console renders a diagnostic the same way the coordinator does | Amended | D-115 |
| D-107 | 2026-09-02 | D-100's contract reaches every scripts directory, and its statement does not say so | Open | |
| D-108 | 2026-09-02 | A walkthrough check compares committed bytes, not a checkout | Confirmed | |
| D-109 | 2026-09-02 | A host record is current only at the commit that produced it | Confirmed | |
| D-110 | 2026-09-02 | A survivor with no catching host is a survivor, not an unverified row | Confirmed | |
| D-111 | 2026-09-02 | A worker does not inherit flags that change what a test means | Confirmed | |
| D-112 | 2026-09-02 | The suite's git reads only configuration the run wrote | Confirmed | |
| D-113 | 2026-09-02 | M08 was held by the host, not by the suite | Confirmed | |
| D-114 | 2026-09-02 | Evidence files under design/routing keep LF on every checkout | Confirmed | |
| D-115 | 2026-09-02 | Every console field from the matrix passes through the renderer | Confirmed | |
| D-116 | 2026-09-02 | The harness line closes on a stopping rule, not on a quiet round | Open | |

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
The owner asked whether acquisition should read from an isolated repository representation rather than the live repository, after enumerating git configuration keys had failed twice. I costed that option and recommended against it. The costing was wrong, which N-07 established: a bare shared clone of a 345-file repository takes 0.10 to 0.34 seconds and stores 38,477 logical bytes, not the 5.6 seconds and 38 megabytes I reported. I had read `du -sb` bytes as megabytes and timed one cold run. The second argument was misapplied as well: the 82 percent raw-to-blob mismatch rules out using our own hash to detect unstaged changes, and says nothing about using one as a boundary digest, which is what was actually built.

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

Correction, 2026-08-30:
This entry first said "about 27 kilobytes". That was a measurement taken on a small synthetic repository and attributed to the 345-file one, which is the same class of error as the figure it was correcting. The 345-file clone is 38,477 logical bytes.

Scope of the ruling:
This rules out the clone forms tested: `--bare --shared`, and by the same capability argument a full bare clone. It does not rule out a representation that carries a complete index and worktree snapshot, because none was built or measured. That remains an open architecture question rather than a closed one.

Revisit when:
A representation appears that can observe index and worktree state without executing candidate configuration, or the worktree source is dropped from routing entirely.

## D-049: Route freezes by value even when given a mapping proxy

Date: 2026-08-30
Status: Confirmed
Area: ADD 5, EDD R-048 and R-052, SLICE-001 M2

Context:
`Route.__post_init__` copies a plain mapping but trusts an existing `MappingProxyType`. A mapping proxy is a read-only view of its backing mapping. It does not make that backing data immutable. Round eight mutated the backing dictionary and a nested set after direct construction and after `dataclasses.replace`; both Route values changed.

Decision:
Every Route construction copies obligation keys and converts every gate collection to a fresh `frozenset`, even when the input is already a mapping proxy. The fresh dictionary is then wrapped for read-only access. Input wrapper type grants no exemption.

Because:
The field owns routing authority. Its immutability must depend on its stored value, not on the type the caller chose to wrap around mutable state.

Consequences:
The focused table adds direct and replaced Routes built from proxies with mutable backing dictionaries and mutable nested gate sets. Mutating any source after construction must leave the Route unchanged.

Revisit when:
Route obligations move to a dedicated immutable value type that copies and validates at its own boundary.

## D-050: Snapshot object width stays bound to the resolved merge base

Date: 2026-08-30
Status: Confirmed
Area: ADD 5, EDD R-046 and R-051, SLICE-001 M2

Context:
M47 removes the merge-base width seed. The suite still passes because its cross-source test supplies a 64-character committed row before a 40-character staged row. The first row seeds the mutant, and the second row still fails. With only the 64-character row beside a resolved 40-character merge base, M47 accepts it and reports the snapshot complete.

Decision:
The resolved merge-base object id establishes repository width before any diff row is parsed. A focused test supplies one row with the other supported width and must fail M47.

Because:
Agreement among changed sources is weaker than agreement with the repository state that produced them.

Consequences:
M47 remains a blocking survivor until the focused test fails it. An unresolved base still blocks completeness, so a malformed first row cannot authorize a shortcut.

Revisit when:
Acquisition asks Git for the repository object format through a separately verified command and binds that result into the snapshot.

## D-051: Symlink guards carry platform evidence and separate target text

Date: 2026-08-30
Status: Confirmed
Area: ADD 5, EDD R-050 and R-053, SLICE-001 M2

Context:
Windows replay reports M37 and M46 as survivors because the symlink test skips without link privilege. Under Ubuntu in WSL, the current test passes and each mutant fails it. M48 removes the link target text while retaining the `symlink:` marker. That mutant passes on both hosts. M36 also survives, although a corrected hard-link probe shows why topology is needed.

Decision:
Keep `lstat`, topology, symlink identification, and target text. Record platform evidence beside a host-local mutation verdict. Add one hard-link case that fails M36 and one target assertion that fails M48.

Because:
A skip is not a cross-platform survivor, and a type marker does not prove which target the link names.

Consequences:
M37 and M46 are held on the supported Linux path. M36 and M48 still block the pure-layer gate. The matrix must not flatten a platform skip into a repository-wide claim.

Revisit when:
The replay harness runs required host legs itself and records one verdict per platform.

## D-052: Unmerged side presence comes from modes, not object ids

Date: 2026-08-30
Status: Confirmed
Area: ADD 5, EDD R-037 and R-051, SLICE-001 M2

Context:
The parser rejects an unmerged row when both object ids are zero. Ubuntu Git 2.43 emits `:000000 100644 <zero> <zero> U` for a plain worktree `git diff --raw -z --no-abbrev` during a real conflict. Adding copy detection causes Git to fill the new object id, which is why the production command and the existing integration test pass.

Decision:
For `U`, determine whether a side exists from its mode. Continue to refuse a scored row, a committed row, or a row where both modes are null. Accept a real mode paired with a null worktree object id. Test both the production flag set and plain raw output, and state which forms the public parser accepts.

Because:
Worktree object ids can be null even when the mode says the side exists. Treating object presence as side presence repeats the same rule in two incompatible ways.

Consequences:
The test that rejects both-null modes remains. A new real-Git case holds the object-null form. The public parser remains narrower than real plain raw output until the parser change lands.

Revisit when:
The minimum supported Git versions stop emitting this form or the parser becomes private to one fixed command contract.

## D-053: parse_raw_z is public for any raw git output

Date: 2026-08-30
Status: Confirmed
Area: ADD 5, Q-01 question 1

Context:
Codex asked whether `parse_raw_z` is a public parser for any raw git output or a private helper for the flags acquisition happens to use. The answer decides whether Q-02 needed a code fix or only a narrower document contract.

Decision:
It is public for any raw git output.

Because:
ADD section 5 already lists it among the public interfaces, and the suite calls it directly at 46 sites with payloads that acquisition never produces. A parser documented as public and exercised as public is public. Narrowing the contract to `_DIFF_FLAGS` would also have made the Q-02 defect unreachable by definition rather than fixed, which is the wrong way to close a finding: the conflict form Codex found is real git output whether or not our own flags produce it.

Consequences:
The grammar must accept every raw form git emits, not only the forms these flags produce. That is a wider obligation and it is the one the interface already advertises.

Revisit when:
The parser gains a caller that supplies output from a different command family.

## D-054: Mutation verdicts are platform-qualified

Date: 2026-08-30
Status: Confirmed
Area: Q-06, mutants/matrix.json, mutants/replay.py

Context:
M37 and M46 attack symlink handling. They survive on Windows because the symlink test skips, and Codex showed both are caught under WSL2 Ubuntu. A single unqualified verdict cannot carry both facts, and the Windows answer had been standing in for the repository's.

Decision:
Each replay result records the host: platform, release, python, git, and the skip count. A row is `caught` when any recorded host caught it, `caught elsewhere` when this host did not but another did, and `SURVIVED` only when no host has caught it. A skip is a fact about the host, not evidence about the code.

Because:
The alternative reading, that a mutant survives because the local host cannot exercise the guarantee, is exactly the false-gap problem the superseded-mutant handling already solved in the other direction.

Consequences:
Cross-platform results enter the matrix as reported evidence attributed to the reporter, not as measurements made here. M37 and M46 carry Codex's Ubuntu result on that basis.

Revisit when:
A required platform leg is added, which would make one host's silence a failure rather than a gap.

## D-056: The missing-promisor case is blocked, not closed

Date: 2026-08-30
Status: Superseded by D-060
Resolution: A `git daemon` on loopback supplies the filtering transport this decision said was missing. The case is now proven end to end and held by M52. The reasoning below is kept because it is why no test was invented in the meantime.
Area: R-043, Q-05, D-036

Context:
`GIT_NO_LAZY_FETCH=1` is set, and the test asserts the control is present rather than the behaviour it prevents. Codex traced a real lazy fetch in round five, so the defect was real. Neither of us has since built the case as a checked-in test.

Decision:
Record this as blocked and unknown rather than closed. The test keeps its downgraded docstring, which says what it asserts and what it does not.

Because:
This host cannot build a blobless clone: a local file transport ignores the partial-clone filter, and the resulting objects are packed, so no single loose object can be removed. Inventing a test that passes without exercising a real missing promisor object would be the exact failure this cycle keeps finding.

The likely path is a transport that honours filtering, such as a local `git daemon`, which would let a real blobless clone be built in a fixture. That adds a daemon to the test environment, which is an environment decision rather than a code one and is not taken unilaterally.

Consequences:
R-043 stays open. The isolation claim rests on the control being present plus Codex's round-five trace, and the documents say so.

Revisit when:
A test environment that honours partial-clone filtering is agreed, or the promisor case is demonstrated another way.

## D-055: Route is not picklable, and does not need to be

Date: 2026-08-30
Status: Confirmed
Area: ADD 7, Q-01 question 3

Context:
Codex asked whether `Route` is expected to support `pickle` or `deepcopy`. Measured against the committed source: `copy.copy` succeeds and the copy stays immutable, while `copy.deepcopy` and `pickle.dumps` both raise `TypeError: cannot pickle 'mappingproxy' object`.

Decision:
Route is an in-process value. Pickling and deep copying are not supported, and the mapping proxy that prevents them is kept.

Because:
Nothing serializes a Route directly. Receipts serialize through `receipt_payload`, which reads a Route and builds a plain dictionary of authoritative fields, so the wire format never touches the object. Making Route picklable would mean giving up the proxy or adding a reduce hook that hands out a mutable mapping, and the immutability it protects has now been the subject of four findings: P-03, L-07, N-05, and Q-01. Trading that for a capability no caller needs is a bad exchange.

`copy.copy` working is enough for the shallow-copy cases that exist, and it preserves immutability rather than defeating it.

Consequences:
A future caller that needs a Route across a process boundary must serialize the receipt payload, not the Route. If one ever needs the object itself, the answer is a conversion function, not a reduce hook.

Revisit when:
A caller needs a Route across a process or cache boundary and the receipt payload cannot carry it.

## D-059: macOS is verified for the suite and is not a replay host

Date: 2026-08-30
Status: Confirmed
Area: CI, D-054, D-057

Context:
The owner scoped macOS out on the grounds that no real macOS host is available. The CI matrix in `.github/workflows/tests.yml` already runs `macos-latest`, so the suite does have a real macOS result on every pull request.

Decision:
Keep macOS as a suite platform, where it is genuinely covered, and state that it is not a mutation replay host. Do not describe macOS as out of scope generally, because that would understate what CI already proves.

Because:
Two different claims were being collapsed. Running the suite on macOS is real coverage and has been for some time. Replaying the mutation matrix on macOS is not done and is not planned, so no coverage is claimed there. Neither statement is served by a single word like "unverified".

There is still no macOS host anyone here controls, so a failure on that leg can be read but not reproduced locally. That is a real limit and is separate from whether the leg runs.

Consequences:
Any statement about macOS names the suite or the matrix. `unverified` without a subject is not accurate for macOS.

Revisit when:
Someone acquires a macOS host, or the matrix gains a macOS leg.

## D-058: Linux is a required replay host, and it runs in CI

Date: 2026-08-30
Status: Confirmed
Area: D-054, R-043, CI

Context:
The mutation matrix is the repository's coverage record, and until now it ran only on a developer's machine. Its verdicts were a local artifact a reviewer had to trust. Windows cannot answer the symlink rows, so M37, M46, and M48 depended on someone with a Linux machine remembering to run them.

The owner approved making Linux required verification authority.

Decision:
Add a required `mutation-replay` job on `ubuntu-latest` that replays the whole matrix on every pull request, and add it to the `required` aggregator. Linux only. Windows and macOS keep their suite legs and are not replay hosts.

Because:
Linux observes every guarantee the matrix names. On a real Linux host the full suite reports 374 passed and 1 skipped, against 361 passed and 14 skipped on Windows, and the single Linux skip is a test of Windows process termination, which is the mirror image of a gap rather than one. An earlier draft said Linux runs with no skips at all; that came from running the router file alone and was not exact. Windows skips the symlink tests, which is why its verdicts need qualifying in the first place; a replay there reports what the host could not see. Running the matrix on a host that cannot answer it would put host facts into a coverage gate.

The cost is small enough that sampling is not worth its complexity. The suite takes about four seconds on Linux against seventeen on Windows, so the full matrix finishes in a few minutes.

This also removes a failure mode that already happened once. A rewrite on this branch deleted a test, the suite stayed green because a deleted test cannot fail, and only a matrix verdict flipping caught it. That signal should not depend on anyone remembering to look.

Consequences:
A surviving mutant now fails a pull request. The job runs without `--write`: the committed matrix is the record under review, and a job that rewrote it would be grading its own work. A second step fails the job if replay left the tree dirty, because an unrestored source would make the verdicts describe a tree nobody reviewed.

Verified: the aggregator was exercised directly and fails on both `failure` and `skipped`, so it is not a check that cannot fail.

Revisit when:
Replay time becomes a burden, or a second replay host is added.

## D-057: The T540P was reachable, and the diagnosis was wrong

Date: 2026-08-30
Status: Corrected, 2026-08-30
Area: D-058, CI

Context:
This entry previously read "The T540P is unreachable, and the blocker is the tailnet policy". That was wrong, and the error was mine rather than the environment's.

Correction:
The tailnet policy was already correct. It permits `autogroup:member` to `autogroup:self` as `autogroup:nonroot`, and it needed no edit. The local account is `daniel-boyd`. Verified from Windows:

    tailscale ssh daniel-boyd@daniel-boyd-thinkpad-t540p 'id -un; hostname'

returns `daniel-boyd` and `daniel-boyd-ThinkPad-T540p`.

Because:
I tried fourteen names and never the hyphenated one, then reasoned from the uniform refusal that no SSH rule existed. That inference does not hold. `autogroup:nonroot` admits any non-root account that exists on the host, and Tailscale refuses a name that is not a local account with the same message it uses when no rule matches. Identical text for two different causes, and I read the evidence as proof of the wrong one.

The failure was treating "every attempt failed the same way" as evidence about the policy, when it was equally consistent with never having supplied a real account name. A negative result across a list I chose says as much about the list as about the system, and the entry stated the stronger conclusion without marking it as inference.

Consequences:
The T540P is a usable Linux host: Ubuntu 24.04.4 LTS, kernel 7.0.0-28-generic, Python 3.12.3, git 2.43.0, four cores. No tailnet policy change was made or needed.

D-058 stands on its own merits rather than on this: CI replay is required because the matrix should not depend on any one machine being reachable. The T540P is now a second recorded replay host, not a replacement for it.

## D-060: The missing-promisor case is proven with a real transport

Date: 2026-08-30
Status: Confirmed
Area: R-043, Q-05, D-056, D-036

Context:
D-056 recorded this as blocked because a local file transport ignores a partial-clone filter, so no genuinely missing object could be built. The owner approved adding a git daemon to the test environment.

Decision:
Hold the guarantee against a real blobless clone served over `git://` by a daemon bound to loopback for the life of one test class. `PartialCloneAgainstRealGitDaemonTests` carries it and M52 holds the guard.

Because:
The daemon ships with git, so nothing is installed and nothing machine-wide changes. It listens on loopback on a free port, serves one temporary repository, and is terminated in teardown.

The proof is end to end rather than a flag check. The clone is genuinely missing the base blob and records a promisor remote. The diff acquisition actually runs exits 128 under the guard and leaves the object missing. The same command without the guard exits 0 and writes the object, so the network really was reachable. Full acquisition reports `ADC-ROUTE-COMMITTED-UNREADABLE` and fetches nothing.

Reaching a missing object needs a specific fixture shape, and this is the part worth remembering. Acquisition runs three raw diffs, and a raw diff wants object ids rather than object content. The one exception is inexact rename detection, which scores similarity by reading both blobs. An exact rename shares its object with the tip, so the tip checkout fetches it and nothing is ever missing. Earlier attempts here had no rename across the base at all, and they reported the change complete with the guard removed. Those fixtures would have passed whether or not the control existed.

The counterfactual is asserted rather than assumed: the unguarded run must fetch the object, or the guarded result is not evidence of anything.

Consequences:
R-043 closes. The older flag-presence test stays, because it runs on hosts where a daemon cannot, and its docstring no longer claims a real clone is impossible. The class skips with a stated reason when the daemon does not start or the clone comes back complete, rather than asserting against a fixture that proves nothing.

Revisit when:
Acquisition gains a command that reads blob content outside rename detection, which would widen the exposure this holds.

## D-061: The requirement register names a file, so it proves nothing

Date: 2026-08-30
Status: Reopened by D-070
Area: SLICE-001 section 11, ENGINEERING section 12

Context:
The slice's definition of done says S-024 through S-051 pass before receipt work starts. Each acceptance criterion names an R id as its evidence, and the evidence table in ENGINEERING gives every one of them the same answer: `test_route.py`.

Measured rather than asserted. Of the 51 criteria, 50 name an R id and S-014 names none. Six of those ids appear anywhere in the suite. Forty-four do not, and 27 of the 28 criteria that gate receipt work are among them.

Decision:
Record this as a known gap and do not treat the gate as verified. Receipt work proceeded anyway, and the reason is stated below rather than hidden.

Because:
An evidence column that answers `test_route.py` for every requirement is true of all of them and therefore distinguishes none. It cannot fail, which is the class 07-adversarial-review names, applied to the register itself. Reading it as a passing gate would be exactly the substitution this cycle keeps finding: a claim standing in for a check.

The substance is better than the bookkeeping. The behaviours those criteria describe are what this cycle built, the suite is green, and 60 mutants are caught, which is stronger evidence of coverage than an id in a table. Blocking the owner's requested work on a mapping artifact would put process ahead of evidence.

What is missing is the link, and the failure it would catch is real: this branch lost a test to a slice edit and gained a shadowed duplicate from the fix, and neither was visible in a green suite.

Consequences:
No statement anywhere may cite "S-024 through S-051 pass" as verified. The honest form is that the suite covers these behaviours and the mapping is unbuilt.

Revisit when:
Someone maps R ids to named tests and adds a check that every registered id resolves to a test that exists, with a shrinking list of untraced ids so the gap cannot quietly grow.

## D-062: The canonical full set belongs to the gates, not the policy

Date: 2026-08-30
Status: Confirmed
Area: M3, R-045, D-045

Context:
`load_policy` takes the canonical full set as a separate argument. Nothing recorded where a real caller should get it.

Decision:
It lives in `gates.json` under `canonical_full_set`, and the `route` command refuses when it is absent or has no passes.

Because:
A policy that could define what "full" means could shrink it and still look complete, which is the whole reason the loader takes it from the caller instead of reading it from the policy. Putting it in the policy file would undo that by the back door. The gate configuration is the natural owner: it already decides which gates exist, are enabled, and are approved.

Refusing on absence matters as much as the location. An empty full set is a comparison every recipe passes, so a missing one has to block rather than default.

Consequences:
The gates template ships the key with empty values and a note. An installing repository fills it in before the router will run.

## D-063: A receipt binds content, not timestamps, and never its own store

Date: 2026-08-30
Status: Confirmed
Area: R-017, D-010, M57, M58, M59

Context:
Both of these were found by running the command, not by reading it.

The first receipt written with `--write` failed its own verification. The binding covers untracked files, the receipt lands under `.anti-dark-code/runs/`, so writing it changed the worktree it bound.

Reverting a change then left the receipt stale. The router's fingerprint tuple carries size and mtime, and reusing the whole tuple made the binding depend on a clock.

Decision:
Exclude the run store from the binding, and bind path and content only.

Because:
Written receipts are outputs. A record that invalidates itself the instant it is written is not a record.

The exclusion is narrow on purpose. Only `.anti-dark-code/runs/` is dropped, never `.anti-dark-code` as a whole: the router deliberately does not filter that tree because policy and gate files sit near it, and a wider exclusion would let an escalator change without making a single receipt stale. M57 holds the width.

On timestamps, the EDD already says freshness binds bytes, executable modes, and symlink targets. It does not say mtime, and a route does not depend on one. The deeper cost is behavioural: a receipt that stays stale after the bytes are restored binds the fact that something happened rather than the state, and a check that cries stale for no reason is one people learn to ignore. Content already carries hard-link topology, so a same-content relink still moves the binding, and size is implied by the digest.

Consequences:
`.anti-dark-code/runs/` is git-ignored. M59 holds mtime independence and M60 holds the exit code, because text saying STALE beside a success status is worse than no receipt.

## D-064: This repository's policy ships with every rule unapproved

Date: 2026-08-30
Status: Confirmed
Area: M3, D-022, SLICE-001 section 10

Context:
The `route` command needs an installed policy. Approving a rule is what lets a route skip work, and the slice puts that behind a stop-and-ask.

Decision:
Install the policy with every rule `proposed`. Against this repository the router returns the full recipe: level 3, force_full, all five gates, no rules matched.

Because:
A proposed rule loads and never matches, and a fact matching no rule forces full, so an unread policy runs everything. That is the correct resting state for a subsystem whose failure mode is running less verification than a change deserved, and it is what shadow mode means in this slice.

Approving individual rules is an owner decision with real consequences, and it is not taken by the agent that wrote them.

Consequences:
The router is installed, exercised, and currently saves nothing, which is intended. The gate ids mirror the jobs in `tests.yml`, including `mutation-replay` from D-058, so the policy names checks that actually exist.

Revisit when:
The owner reads the rules and approves any of them, or the shadow comparator from M4 has enough recorded runs to argue a rule is safe.

## D-065: A hard-link test passed on Linux for the wrong reason

Date: 2026-08-30
Status: Confirmed
Area: M36, R-050, D-058

Context:
The first clean replay on a real Linux host reported M36 surviving there while Windows caught it. Nothing in the code is platform-conditional, so the difference had to be in the test.

Decision:
Keep the end-to-end test and add `test_path_topology_alone_moves_the_fingerprint`, which takes two fingerprints with nothing in between.

Because:
`test_replacing_a_file_with_a_hard_link_is_detected` asserts a boundary violation after a hard-link swap holding bytes, size, and mtime equal. On Linux git refreshes the index during acquisition, the boundary fires on the index rather than on topology, and the test passes with topology disabled.

Measured, not argued. With topology disabled on Linux, `index_state` changes across acquisition, the violation is still reported, and the test still passes. On a clean tree the topology field moves from `(1, ino, mode)` to `(2, ino, mode)`, so the detector was never at fault.

The new test runs no acquisition, so no index can move, so nothing but path topology can differ. Content, size, and mtime are asserted equal, which means a pass cannot be explained by any of them. M36 is now caught on both hosts, and on Linux the new test is the one that fails while the old one still passes.

This test's own docstring already records removing a timestamp side channel from it in an earlier round. That fix removed one channel and left another, and one host could not see the difference. The general lesson is not about hard links: an end-to-end assertion has as many ways to pass as the system has signals, and the number of them that are the intended one is usually one.

Consequences:
The old test keeps its end-to-end coverage with the limitation written into its docstring rather than left implied.

## D-066: The record carries two hosts, and the verdict is a function of them

Date: 2026-08-30
Status: Confirmed
Area: D-054, D-057, D-058

Context:
Every active row now has a verified result from Windows 11 with Python 3.14.2 and git 2.50.1, and from the T540P running Ubuntu 24.04.4, kernel 7.0.0-28-generic, Python 3.12.3, git 2.43.0.

Decision:
56 active rows, both hosts on all of them. 53 caught on both. Three caught on Linux where Windows skips the test that holds them. No survivors and nothing unverified. `derive_verdict` computes the label from every recorded result.

Because:
The old code read the verdict off whichever host finished the run, so identical evidence produced "caught" when Linux went last and "caught elsewhere" when Windows did. A coverage record that changes with replay order is describing the operator rather than the code.

Caught anywhere is caught, because a guarantee held on one host is held. Caught everywhere and caught somewhere stay distinct: the second means a host could not check it, which is a fact worth keeping rather than averaging away. Every host skipping stays separate again, because it is evidence nobody looked.

M48 closes here. It was a survivor in round eight, then unverified once verdicts were host-qualified, and it is caught on Linux.

Consequences:
Both trees are verified restored by digest against HEAD after a replay, the remote one included, after a probe once left a mutated file behind and the results were read as real behaviour.

Revisit when:
A third host is added, or a row disagrees between hosts for a reason other than a skip, which would mean the code is platform-conditional where nobody intended it.

## D-067: M3 needed an executable traceability gate

Date: 2026-08-30
Status: Reopened by D-070
Area: D-061, M3, SLICE-001 section 11

Context:
D-061 correctly found that a file-level evidence label could not verify the M3 prerequisite, then let receipt work proceed because the suite and mutation results were substantively strong. Round ten checked the gate itself. R-049 through R-055 were absent from the confirmed register, S-014 had no requirement link, and no machine check resolved registered requirements to collected tests or typed non-test evidence.

Decision:
M3 should have waited. Strong aggregate evidence did not authorize crossing a prerequisite that could not fail. M3 is accepted retroactively now that `requirement-evidence.json` covers R-001 through R-055, mapped node ids resolve against whole-suite collection, S-014 links R-053, and the only untraced ids are the fixed M4 set R-013, R-018, and R-022.

Because:
The missing link had already hidden two concrete failures: one deleted test and one shadowed duplicate. A gate that cannot distinguish one requirement from another cannot establish that either is held. The replacement check compares the confirmed ledger, verification ledger, and evidence map; inventories every `test_*.py`; rejects duplicate and uncollected definitions; resolves mapped node ids; validates typed mutation and review evidence; and permits the untraced set only to shrink.

Consequences:
D-061 closes for M3. M3 is no longer review-gated. This does not approve M4: its three requirements remain explicitly untraced because their behavior is not built.

Revisit when:
A registered requirement needs a new evidence type, or the untraced set needs to grow. Either change requires review rather than a looser parser.

## D-068: Mutation authority requires a real test runner and exact restoration

Date: 2026-08-30
Status: Confirmed
Area: D-058, D-066, R-053, M61 through M63

Context:
The required T540P replay exposed three harness failures. The runner assumed an ambient `python` command although the host provided only `python3`. Reading mutation targets as text normalized a committed CRLF file to LF during restoration. After switching to the current interpreter, the host lacked pytest; `python -m pytest` exited 1 and the harness labeled the launcher error as a caught mutant without running a test.

Decision:
Launch suites with `sys.executable`, mutate and restore raw bytes, and accept exit 0 or 1 only when the final line is an anchored pytest outcome summary. M61, M62, and M63 hold those controls. T540P replay uses a disposable virtual environment under `/tmp` with pytest installed by the same command shape as CI, not a machine-wide alias or package change.

Because:
A nonzero process is not automatically test evidence. The replay must prove that pytest collected and answered the configured suite, and a temporary mutation must restore the exact source bytes rather than an equivalent Python program. Hash checks cover all four mutable source families after every authoritative replay.

Consequences:
The matrix now has 63 rows: 59 active and 4 superseded. Fifty-six active rows are caught on both Windows 11/Python 3.14.2 and T540P Linux/Python 3.12.3; M37, M46, and M48 are caught on Linux where Windows skips their symlink test. No row survives or remains unverified. No current macOS result was observed in this round; the macOS claim remains limited to the configured CI suite.

Revisit when:
Pytest changes its terminal-summary grammar, another suite runner is supported, or a mutation source uses bytes that are not UTF-8 for the replacement fragment.

## D-069: M4 is blocked by its plan, not by D-061

Date: 2026-08-30
Status: Resolved
Area: M4, R-013, R-018, R-022, D-064

Context:
Closing D-061 makes the M3 evidence reviewable, but it does not make the next milestone executable. The current plan's own self-review says Task 10 omits the before-and-after check and leaves receipt loading, freshness, full-recipe selection, and runner integration as placeholders. Task 11 defines a comparator without connecting it to a full gate run.

There is a second contradiction. D-064 keeps every installed rule `proposed`, so the authoritative route is full and selects every gate. The planned comparator reads that route's `selected_gate_ids`; it therefore sees no omitted gates and cannot gather evidence about what any proposed rule would have omitted. The comparator cannot produce the evidence D-064 names as an alternative to owner approval.

Decision:
Do not start M4 from the current plan. Revise and review the plan first. It must define a candidate shadow route that may evaluate proposed rules without granting execution authority, bind before-and-after repository identity to each gate result for R-018, show the real `run_gates` integration while still running the canonical full set for R-022, and map R-013, R-018, and R-022 to exact collected tests before implementation begins.

Because:
Implementing the snippets as written would produce a comparator that records no meaningful omissions and a runner that verifies freshness only before work. That would check boxes without satisfying the requirements the boxes name.

Consequences:
M4 remains not started. No selective execution is enabled, no policy rule is approved, and no gate-runner behavior changes in round ten.

Resolution in round twelve:
The reviewed Tasks 10 through 12 named the missing seams, and M4 implemented them in order. R-013, R-022, and R-018 now have exact collected runner evidence; a separate `CandidateRoute` evaluates proposed rules but is refused by both receipt authority and executable gate selection; real gate outcomes feed `shadow.json`. No policy rule was approved and no selective execution was enabled.

Revisit when:
Reopen if a future M4 consumer reconnects candidate data to receipt authority or executable selection, or stops binding comparison to real gate outcomes.

## D-070: Node-id reachability is necessary and not sufficient evidence

Date: 2026-08-30
Status: Open
Area: D-061, D-067, M3, R-005, R-017, R-019, R-021

Context:
The independent review of round ten checked whether the tests mapped by D-067 exercised the full requirement rather than merely collecting. Four did not.

R-017 and R-019 require submodule state. No router, receipt, or test module names submodule behavior, and the implemented `ChangeInput` model has no `submodule_state` field matching the EDD record. Their mapped tests cover other parts of the requirements only.

R-005 and R-021 require real self-grading path classes to force full. Their map named one test that manually constructs a CI fact. With an in-memory copy of the installed rules marked approved, measured routes for `anti-dark-code/scripts/adc_route.py`, `anti-dark-code/assets/verification-capabilities.json`, and `anti-dark-code/references/00-preflight.md` were Level 2 product, Level 2 schema, and Level 0 docs routes, all with `force_full` false. The installed rules remain proposed, so this does not currently permit a skip, but it disproves the registered requirements and the first M3 acceptance.

The same review found that ENGINEERING still labeled R-013, R-018, and R-022 as tested even though the executable map, D-067, and D-069 called them unimplemented. The file-level evidence claim had survived beside the machine-readable correction.

Decision:
Reopen D-061 and M3 review. Schema version 2 of `requirement-evidence.json` marks R-005, R-017, R-019, and R-021 `partial` and keeps their live tests as incomplete evidence. R-013, R-018, and R-022 remain unimplemented. The reviewed untraced set is those seven ids and may only shrink without another review. ENGINEERING must state partial or unbuilt status rather than naming `test_route.py` as complete evidence.

Do not repair the four M3 requirements by silently adding authority rules, changing a hard escalator, or inventing submodule semantics. The slice guardrails reserve those changes for explicit owner and design review.

Because:
Resolving a node id proves that a test can run. It does not prove that the test's assertions cover every clause in the requirement. Partial evidence is still useful, so the map retains it and labels it rather than deleting it or treating it as complete.

Consequences:
M3 remains implemented but review-gated. M4 remains not started for both reasons: M3 has four partial prerequisites, and D-069 still blocks the M4 plan. Round eleven must close or deliberately redesign the four partial M3 requirements before it can rule on M4 eligibility.

Revisit when:
An owner-reviewed authority-path contract and a submodule-state contract have exact collected tests and implementation evidence, or the confirmed requirements are explicitly revised through the design documents.
## D-071: A classifier is what makes a path authority, and it is checked at load

Date: 2026-08-30
Status: Confirmed
Area: M3, R-005, R-021, D-064, D-070

Context:
D-070 reopened R-005 and R-021 after finding that their only mapped test built a CI fact by hand. The round-eleven review measured every path class the requirement names against the installed classifier, with the rules approved in memory as D-064 defers rather than removes.

Eleven classes were measured. Five took ordinary routes: the router itself and the installer took the Level 2 product route, the capability catalog and the shipped policy template took the Level 2 schema route, and a routing-owning pass reference took the Level 0 docs route. Two more forced full for a reason that was not the requirement: `calibration/gates.json` and the installed routing policy matched no classifier glob at all, so they were unmapped, and an unmapped path forces full because its confidence is unknown. Only four classes forced full because something had graded them as authority.

D-070 recorded three of the five. The two it missed were the installer and the policy template.

Decision:
Authority is stated in the classifier and enforced at load.

The shipped policy template classifies the router, the receipt writer, the installer, the capability catalog, every `calibration/*.json`, and every `references/*.md` with the effect `verification-authority`, which the template's existing force-full rule already matches. `load_policy` then refuses any policy under which a self-grading path could take a route below the full recipe.

The guard checks that property directly. It classifies each path in `SELF_GRADING_PATHS` and asks whether every rule that could fire on the resulting facts still leaves `force_full` true. An unmapped path is not a failure: confidence `unknown` forces the full recipe on its own.

The first version of this guard checked only the classification, on the reasoning that a path classified as authority whose force-full rule was deleted would match no rule, become an unrouted fact, and force full anyway. **That reasoning was wrong, and this decision records it rather than quietly correcting it.** `build_route` sets `fired` on any match, so the unrouted fallback never runs when some other rule matches. Measured: deleting the `verification-authority` rule and approving one rule matching `effects: ["verification-authority"]` at `minimum_level: 0`, with the classifier untouched, took **ten of the eleven classes below the full recipe** and the first guard accepted that policy. Row M68 holds the corrected guard against exactly that reversion.

Every rule is considered, approved or not. A proposed rule is one review away from approval, and load is the last moment where refusing is cheap.

Because:
The alternative was a hard escalator inside `build_route`: a path list in code that forces full whatever the policy says. It was rejected. Routing authority already lives in one reviewable place, and a second copy in code would be invisible to the reader approving the policy, which is the same drift the project refuses elsewhere. A classifier entry is data a reviewer reads; a guard that refuses to load an under-classifying policy is not a second routing rule, because it computes no route.

Narrowing R-005 and R-021 to what the classifier happened to cover was also rejected. The requirement was not wrong. The classifier was.

Consequences:
An installed policy predating this change is refused at load with the offending paths named, and updating from the template resolves it. A repository that wants a cheaper route for its own authority paths cannot have one, which is the point. Six classifier entries are added, so a self-grading path now emits two facts, one ordinary and one authority; the monotonic union takes the higher, which is what makes the addition safe.

The guard cannot prevent a future round from deleting a `SELF_GRADING_PATHS` entry. `test_each_named_self_grading_path_exists` holds the list against the tree so a stale entry fails rather than passing silently, but the list itself is a review record, like `REVIEWED_UNTRACED`. See U-015.

Revisit when:
A repository that installs this skill needs a self-grading path this list does not name, or the router gains a module that grades other code.

## D-072: A submodule is refused, not bound

Date: 2026-08-30
Status: Confirmed
Area: M3, R-017, R-019, D-070

Context:
D-070 recorded that no router, receipt, or test module named submodule behavior. The round-eleven review built a real parent repository with a real submodule and measured what that absence costs.

`worktree_identity` keeps each entry's path and its content-and-topology field and deliberately drops size and mtime, because a route does not depend on a timestamp. A gitlink is not a regular file, so it has no content digest: its field is the constant `special:<directory mode>:<topology>`. Nothing in it moves when the submodule does.

Measured, with no timestamp handling and no adversary: an ordinary edit to a tracked file inside the submodule left the receipt binding byte-identical while git reported the parent dirty. Moving the submodule's checked-out commit to a different commit did the same. A control change to an ordinary tracked file moved the binding, so the harness was sound. A receipt taken before either change still verified as fresh.

Acquisition had the matching gap. A gitlink record parsed as an ordinary modification, the snapshot called itself complete, and no problem code was raised.

Decision:
Fail closed. Bind nothing about a submodule and refuse the tree instead.

`_repo_fingerprint` marks a listed path that is a directory with `GITLINK_MARK`. The test is "is a directory", not "mode 160000", because git lists a directory here for exactly the cases where it will not look inside one: a gitlink from `ls-files`, and an untracked embedded repository from `ls-files --others`, which arrives with a trailing slash. Both hold another repository's state, and the fingerprint can bind neither. An ordinary untracked directory is recursed into and listed as its files, so it is unaffected; a test holds that counterexample. `Binding` carries `unsupported_paths`, inside the hashed authoritative payload. `verify_receipt` returns not fresh with `ADC-STALE-009` whenever the current binding names one, before comparing any other field. `route --write` refuses to write a receipt for such a tree, and `route` prints the unbindable paths on the read-only path too. The raw parser records `ADC-ROUTE-SUBMODULE-UNSUPPORTED` for mode `160000` on either side, which withdraws snapshot completeness and forces the full recipe.

R-017 is amended to match: freshness binds content, modes, index entries, and symlink targets, and refuses to certify a tree holding state it cannot bind. R-019 needed no amendment. It already said unsupported records block selective routing, and a gitlink is now one.

Because:
Binding real submodule state was the other option, and it is the better end state. It was not taken now because it is a larger surface than it looks: nested submodules, uninitialized submodules, a submodule whose HEAD is detached, one whose remote is unreachable, and the recursion policy for each. Every one of those is a real-repository fixture this slice has not built, and a partial implementation of submodule binding is the same failure D-070 exists to record — evidence that resolves and does not cover the clause.

Refusing is not a smaller version of binding. It is a different, complete guarantee: no receipt over such a tree can ever claim freshness.

Consequences:
A repository containing a submodule cannot use routing receipts and always takes the full recipe. That is a real cost, and it is the honest one until submodule state is bound.

`SCHEMA_VERSION` becomes 2. A receipt written under schema 1 was produced by code that could not see a submodule, so it is refused as a schema mismatch rather than compared field by field. Receipts are local run artifacts under an ignored path, so nothing durable is invalidated.

`test_the_identity_alone_still_cannot_see_the_submodule_move` records the blindness rather than hiding it. A later change that claims to bind submodule state has to move that assertion, which is where a reviewer will look.

Revisit when:
Submodule state is bound for real, with a fixture per Git behavior the claim depends on, or a repository that installs this skill needs receipts over a tree containing one.

## D-073: An unreadable repository fingerprint refuses the binding provisionally

Date: 2026-08-30
Status: Superseded by D-083
Area: M4, R-017, R-018, `_repo_fingerprint`

Context:
`_repo_fingerprint` returns `("unreadable",)` when either `git ls-files` call fails. `worktree_identity` and `_identity_and_unsupported` previously unpacked that one-item sentinel into two names, leaking a `ValueError` traceback at exactly the boundary where a clean refusal matters.

Three narrow alternatives remain owner-reviewable: (1) raise a typed `ReceiptError` and refuse to construct or verify a binding; (2) return an identity that can never match, making every receipt over the failed read stale; or (3) treat the read as an incomplete snapshot, force the full recipe, and refuse a receipt in the same shape as D-072.

Decision:
Implement alternative 1 provisionally. `_identity_and_unsupported` recognizes the sentinel and raises `ReceiptError`; the route writer, route verifier, and routed gate preflight catch that type, print `REFUSED`, and return 2. No digest is minted for a failed read.

Because:
Two unrelated acquisition failures must not compare as one identity, and the receipt layer cannot honestly turn a mid-read Git failure into a complete snapshot. The typed refusal is the narrowest change that closes the crash without inventing authority or weakening M4.

Consequences:
Binding construction and verification fail closed with a named error instead of a traceback. This is provisional implementation evidence, not owner approval of the long-term unreadable-state model; round thirteen may replace it with alternative 2 or 3 while preserving clean refusal.

Revisit when:
The owner selects the durable unreadable-fingerprint semantics in round thirteen, or another fingerprint sentinel is introduced.

## D-074: Candidate routes are a separate shadow-only type

Date: 2026-08-30
Status: Confirmed
Area: M4, D-064, D-069, receipt authority, gate selection

Context:
D-064 keeps shipped rules proposed, so the authoritative route runs the canonical set and cannot reveal what those rules would have omitted. Measuring proposed rules therefore needs a second representation, but letting that representation share the authoritative `Route` type would make one forgotten condition sufficient to narrow execution. While connecting the comparator, a second authority gap became visible: receipt freshness compared the binding without recomputing the authoritative `run_id`, so edited route fields could still be reported fresh.

Decision:
`CandidateRoute` is a distinct immutable type with constant `candidate-shadow` provenance. It evaluates approved and proposed rules, returns no candidate for an incomplete snapshot, and serializes only into `shadow.json`. The receipt writer and executable selector reject it by type. The comparator consumes the actual gate summary, uses the closed outcome vocabulary `pass`, `fail`, `config-error`, `stale`, `not-run`, and `skipped`, and treats every non-pass omission as a miss only when every candidate-selected gate passed.

`verify_receipt` also recomputes `run_id` after the foreign-schema guard and refuses a same-schema authoritative payload whose digest does not match. Candidate reconstruction therefore starts from a fresh, internally consistent receipt.

Because:
Shadow evidence must be able to describe a cheaper hypothetical route without ever becoming permission to run one. A separate type makes that boundary structural, and comparing against real gate outcomes makes the record evidence rather than a disconnected forecast.

Consequences:
Every routed executable run remains authoritative and, under the shipped proposed-only policy, canonical-full. Its run directory may also contain `shadow.json`, which records both authoritative and candidate gate ids, every real outcome, missed omissions, and the candidate route class. M4 is implemented without approving a rule or enabling selective execution.

Revisit when:
The owner reviews accumulated shadow records for a rule, or any consumer proposes accepting candidate data at an authority boundary.

## D-075: Gate execution consumes one verified receipt and its exact identity

Date: 2026-08-30
Status: Confirmed
Area: M4, R-018, receipt authority, gate execution

Context:
The round-twelve independent review found two races after the first M4 implementation. Receipt preflight verified the repository, but `run_gates` treated the identity immediately before `Popen` as a new baseline and compared only the post-gate identity with it. A repository change after preflight but before launch could therefore be accepted. The command also read and verified the receipt, then read the path twice more for route selection and candidate reconstruction, so replacement between reads could feed unverified bytes to execution and shadow evidence.

The runner itself exposed the first boundary while it was repaired. `current_source_identity` used ordinary `git status`, which refreshed index metadata after receipt verification and changed the repository fingerprint even though no source byte moved.

Decision:
Complete stable run-artifact setup before receipt creation and before executable preflight. Read receipt JSON once, validate every required object layer, verify that exact object, and freeze its authoritative payload. Route selection and candidate reconstruction consume only that immutable verified object; replacement of the receipt path afterward has no authority.

Carry the verified receipt's worktree identity and `run_id` into `run_gates` and its summary. Immediately before every `Popen`, compare a fresh identity with the verified identity; a mismatch records `stale` in phase `before-launch`, starts no subprocess, and returns 2. The existing post-gate comparison remains and records phase `during-gate`. Gate-planning Git diagnostics use `--no-optional-locks` so the runner does not refresh the index after preflight.

Candidate provenance is refused in both live-object and serialized-mapping form. Malformed receipt JSON, including a non-object root or binding, refuses with exit 2 rather than reaching mapping access and a traceback.

Because:
Freshness is authority over exact bytes, not permission to choose a later baseline. Verification is meaningful only when every authority consumer uses the same object that was checked and every gate starts against the same repository identity that object bound.

Consequences:
The process-level seam tests mutate the repository and replace the receipt immediately after verification; neither reaches execution authority. M75 through M82 hold the preflight identity comparison, single-read receipt consumption for both route and candidate data, serialized candidate refusals, receipt shape and exit-code refusals, and the read-only Git diagnostic.

Revisit when:
The gate runner moves receipt verification into another process, or execution is redesigned around an operating-system snapshot that makes the preflight-to-launch boundary atomic.

## D-076: Verified execution authority is a closed in-memory context

Date: 2026-08-30
Status: Confirmed
Area: M4, R-018, policy authority, gate configuration

Context:
A second independent review found two more path-replacement seams. Receipt preflight validated `gates.json`, but `run_gates` read that path again to choose commands. Candidate reconstruction likewise reloaded `routing-policy.json` after verification. An attacker able to swap and restore either path between those reads could supply unverified execution or shadow inputs while leaving the pre-launch repository identity unchanged. The review also found that the first `route --write` acquired change facts before creating the stable run-store ignore file, then bound the later state.

Decision:
The verified receipt context carries the frozen authoritative payload, validated policy object, canonical gate-configuration bytes, verified worktree identity, and verified run id. Routed gate selection and execution parse only those carried gate bytes. Candidate reconstruction consumes only the carried validated policy. Neither authority consumer reloads a calibration path after verification.

Create the stable run-store ignore file before change acquisition on a write. This makes the added path part of both emitted facts and repository identity during a first write. A syntactically valid policy or gate document with a non-object root refuses with exit 2 before schema access.

Because:
Preflight protects a set of inputs, not just a receipt file. Every decision made after it must consume the same policy, gate configuration, route payload, and repository state that preflight accepted.

Consequences:
Process-level swap-and-restore tests prove that later policy or gate bytes cannot authorize execution. M83 through M87 hold the gate snapshot, policy snapshot, first-write acquisition order, and clean root-shape refusals. A first receipt written in a repository without the run-store ignore may route more conservatively because that setup path is now visible to acquisition.

Revisit when:
Execution authority moves to a separate process with an authenticated, serialized preflight context.
## D-077: A gate lifecycle and a receipt binding ask different questions

Date: 2026-08-31
Status: Confirmed
Area: M4, R-018, D-063, D-075

Context:
Round twelve implemented R-018 by capturing repository identity immediately before and immediately after each real gate subprocess, and closed the requirement with ten collected nodes and an empty `untraced` list.

Both captures used `worktree_identity`, which keeps each entry's path and its content-and-topology field and deliberately drops size and mtime. D-063 is right about why: a receipt binds what a route depended on, a route does not depend on a timestamp, and a receipt that goes stale after its bytes are restored trains a reader to ignore staleness.

R-018 asks a different question. Its clause is "when an input changes after preflight **or during a gate**, then that gate result is marked stale". A gate that rewrites a tracked file, uses the changed value, and restores the original bytes satisfies that antecedent exactly, and leaves the bound identity equal at both ends.

Measured against the real runner, not argued: a gate whose command wrote `during` to a tracked file, read it back, and then restored the original passed cleanly with exit 0, no stale row, and `outcomes` recording `pass`. Its own redacted log recorded `gate observed during`. The gate's result depended on content that was not in the tree when the run ended, which is the evidence R-018 exists to reject.

Decision:
The gate lifecycle gets its own identity. `lifecycle_identity` digests the same entries as the binding, with the same run-store exclusion, and keeps size and mtime. `run_gates` captures both before and after each gate and marks the gate `stale` when **either** moves.

The stale row records both pairs plus `restored_during_gate`, so a reader can tell a change that survived the gate from one the gate put back. What a receipt binds is unchanged: `worktree_identity`, `collect_binding`, and `verify_receipt` keep D-063 semantics exactly.

Because:
The two questions are genuinely different and had been answered with one value. "Is this the tree the receipt bound" must ignore timestamps. "Did anything touch the tree while this gate ran" must not.

Deriving both from the one fingerprint pass the runner already performs keeps the cost where it was and avoids a second implementation of the rule.

Consequences:
A gate that rewrites a tracked file with identical bytes, or otherwise moves an mtime inside the repository, is now `stale` rather than `pass`. That is stricter, and it is intended: a gate that writes into the tree it is verifying is exactly the case R-018 names. Ignored paths and the run store are out of scope, so a gate's own logs and generated artifacts do not stale it, and the counterexample test holds that.

If that strictness proves wrong for a real gate, the fix is to make that gate not write into the worktree, not to widen what counts as unchanged.

The residual is a caller that restores the timestamp along with the bytes. That is a deliberate act rather than an ordinary gate. It is recorded here rather than claimed as covered, and U-016 carries it.

R-018's registered clause is unchanged, because the requirement always said this. It was the implementation that was narrower than the clause, and round twelve's empty `untraced` list asserted a coverage that one measurement disproved.

Revisit when:
A real gate needs to write into the worktree it verifies, or the residual timestamp-restoring case stops being theoretical.
## D-078: The self-grading guard enumerates shapes instead of sampling one

Date: 2026-08-31
Status: Confirmed
Area: M3, R-005, R-021, D-071

Context:
This is the third correction to the same guard, and the pattern is worth naming: each version checked something adjacent to the property rather than the property, and each survived its own tests until someone attacked it.

1. The first version checked whether the classifier graded a path as authority. Wrong, because `build_route` sets `fired` on any match, so a cheap approved rule matching `effects: ["verification-authority"]` suppressed the unrouted fallback. Ten of eleven classes fell below the full recipe with the classifier untouched.
2. The second version checked the routing outcome, but built one fact per classification with `change_kind` "modify" and `source` "unstaged".

`_MATCH_KEYS` lets a rule key on `change_kinds`, `sources`, and `mode_changed`. A rule narrowed to the one shape the probe used therefore satisfied the guard while leaving every other shape to a cheaper rule.

Measured: narrowing the shipped `verification-authority` rule to `change_kinds: ["modify"]` and adding an approved rule matching `["delete", "add", "rename"]` at `minimum_level: 0` loaded clean, and **deleting `anti-dark-code/tests/test_route.py` then routed at Level 0**. Ten of the eleven classes were reachable that way. Deleting a router test is the plainest self-grading act there is.

Decision:
The guard enumerates the cross-product of every dimension a rule can key on: all nine change kinds, all four sources, and both mode-changed values, for each classification of each self-grading path. A policy is refused unless every shape leaves `force_full` true.

The refusal names one concrete failing shape and counts the rest, because "a delete of this path routes cheaply" is what a reader acts on and a list of sixty-four is not.

Because:
A guard that samples is a guard an adversary aims around, and twice now the aim did not even need to be deliberate: a plausible narrowing of a rule was enough. The cross-product is 72 shapes per classification, against a load cost previously measured at 0.000205 seconds and a fingerprint at 0.148 seconds in the same command. Enumerating is affordable; sampling was never the cheaper option, only the shorter one.

Consequences:
A policy that narrows an authority rule by change kind, source, or mode flag is refused at load unless another rule still forces full for the shapes it gave up. The shipped template is unaffected: its `verification-authority` rule keys on effect alone and therefore matches every shape.

M90 holds the enumeration against reversion to sampling.

The lesson generalizes beyond this guard. Three times the check was written against the shape of the current attack rather than the shape of the guarantee. `test_every_shape_of_a_self_grading_change_forces_full` now asserts the guarantee directly, over the real policy, so a future narrowing has to move that test rather than slip past a probe.

Revisit when:
`_MATCH_KEYS` gains a dimension. The enumeration must gain it in the same change, and a test should fail if it does not.

## D-079: N-08 was a test that proved nothing, cited as evidence

Date: 2026-08-31
Status: Confirmed
Area: M2, R-054, N-08

Context:
N-08 was raised in the round-six adversarial review and never addressed. No fix commit, no decision, no verdict in eight subsequent rounds, and it reproduced verbatim at `b9b1e71`.

`test_a_globally_configured_filter_is_also_neutralized` called `_install_filter`, which runs `git config` with no `--global`, writing the local repository config. The "global" test was therefore mechanically identical to the local one directly above it. Nothing in the file set `GIT_CONFIG_GLOBAL`.

`requirement-evidence.json` cited that test as evidence for R-054, whose clause is "given global filters ... no program starts". The evidence resolved, collected, and passed, and did not exercise the clause.

Decision:
The test declares the driver in an isolated global config file, sets `GIT_CONFIG_GLOBAL` for the acquisition call so the router's own git subprocesses inherit it, and asserts its own fixture before trusting its result: the driver must be visible through effective config and absent from local config.

Because:
Without the fixture assertion the test passes whether or not the global config is in effect, which is exactly how it survived eight rounds. A test that cannot fail for the reason it exists is not evidence, and one cited in a traceability map is worse than none, because it consumes the attention that would have found the gap.

Consequences:
`_filter_overrides` is unchanged: it already discovers drivers through effective configuration, so the guarantee held all along. What was missing was any proof of it. M91 mutates discovery to `--local` and is caught, which is the evidence R-054 always claimed.

This is the second time a test in this repository was found to be present, collected, and inert. `a4949a8` records the first. The suite-reachability guards added in round ten catch a test that never runs; neither they nor the traceability map can catch a test that runs and asserts the wrong thing.

Revisit when:
Another cited test is suspected of the same. The check is cheap: mutate the production behaviour it claims to hold and see whether it fails.

## D-080: Per-change EDD evidence starts at a review-trailer anchor

Date: 2026-08-31
Status: Confirmed
Area: EDD 17, SLICE-001 sections 9 and 11

Context:
SLICE-001 claimed that the EDD section 17 checklist was satisfied for every change. That claim cannot be reconstructed. Commit `a92c869` carried a live mutant through a green suite, and `a4949a8` records a test that was present but absent from the run. The required workflow also runs only for pull requests and pushes to `main`, so it has no record for most intermediate branch commits.

Decision:
Withdraw the per-change claim for the range before `ea8733c`. The replacement for that range is a slice-level claim: the current suite passes, the latest PR 23 base passed the required three-platform matrix and distribution checks, the branch delta has Windows suite evidence and two-host mutation evidence, no runtime dependency was added, and the complete mutation matrix has no survivor.

From `ea8733c` forward, every commit carries the exact trailer `EDD-Checklist: satisfied`. The trailer records a deliberate review of all five EDD section 17 items. It does not invent CI coverage for intermediate branch commits; the evidence beside the commit must still say which host or required workflow ran.

Because:
A retrospective tick would erase known counterexamples. A named forward anchor gives item 5 a durable artifact and gives later audits a point they can check without pretending missing historical runs exist.

Consequences:
The slice checklist is qualified rather than retrospectively checked. Commits after the anchor without the trailer violate this decision. The slice-level platform statement continues to distinguish acceptance coverage, required-branch CI, and the branch delta.

Revisit when:
The required workflow starts recording every branch commit, or a stronger signed review artifact replaces the trailer.

## D-081: The historical live-mutant scan is retired behind maintained guards

Date: 2026-08-31
Status: Confirmed
Area: mutation evidence, D-068, EDD 11

Context:
Round thirteen reran the historical scan over 164 commits. Fifty-eight commits carried a matrix, with 2,994 active row and commit pairs in pass one and 7,423 in pass two. It again found `a92c869` with M01 as the only live-mutant state and exactly 12 matrix-drift pairs. Roughly one hundred commits added since the earlier scan produced no new historical state.

Decision:
Retire the standing historical rerun. `MutationMatrixIntegrityTests` now holds row identity, targets, results, host records, and harness behavior at HEAD. The required `Tests` aggregator holds the candidate at pull-request and `main` integration boundaries.

Because:
The scan is useful forensic evidence, but repeated history-wide execution has stopped finding new states. Maintained guards fail where a new defect can still ship.

Consequences:
The CI guard does not see intermediate branch commits. A mutant introduced and fixed before the pull request or merge is therefore absent from CI history, but it also does not ship. The historical scan remains available for an investigation and is no longer a standing slice gate.

Revisit when:
The matrix schema changes, an integrity guard regresses, or evidence suggests a live mutant reached a reviewed integration boundary.

## D-082: Self-grading probes source and managed installed layouts

Date: 2026-08-31
Status: Confirmed
Area: M3, R-005, R-021, D-071

Context:
D-071 named literal source-tree paths. A policy could classify those spellings as authority, classify the managed `.agents/skills/anti-dark-code/` spellings as ordinary product code, pass the load guard, and route the installed router below the full recipe.

Decision:
The load guard checks each source-tree path and the corresponding managed installed path. Paths already rooted in `.agents/skills/` or `.github/` are checked once. The existing cross-product over change kind, source, and mode remains unchanged.

Because:
The installer changes the path spelling, not the authority of the file. A guard that protects only the development layout does not protect the repository that consumes the skill.

Consequences:
`test_source_only_authority_cannot_hide_the_installed_router` fails against the source-only guard and passes with the installed alias included. At D-082 confirmation, M92 reverted the guard to the literal list and was caught on Linux and Windows. D-093 later made that implementation-specific reversion inert; D-094 records the measured Linux survivor, supersedes M92, and replaces it with M96 against the stronger canonical-classifier contract. The source existence test still checks real source files; policy loading checks both layouts.

Revisit when:
The managed install root changes or another supported installer places authoritative files under a third repository-relative prefix.

## D-083: An unreadable fingerprint raises a typed receipt refusal

Date: 2026-08-31
Status: Confirmed
Area: M4, R-017, R-018, D-073, `_repo_fingerprint`

Context:
D-073 implemented alternative 1 provisionally. Alternatives 2 and 3 would either create a synthetic identity that can never match or move the failure into snapshot completeness.

Decision:
Confirm alternative 1. `_identity_and_unsupported` raises `ReceiptError` for the unreadable sentinel. Receipt construction, verification, and routed preflight catch that type, print `REFUSED`, return 2, and mint no digest.

Because:
Two failed reads are not evidence that the repository had the same state. The receipt layer has enough information to refuse and not enough information to build an identity or a complete snapshot.

Consequences:
D-073 is superseded. The owner can still reopen the model if repository acquisition and receipt binding are combined under one typed failure context.

Revisit when:
Another fingerprint sentinel is introduced or acquisition gains an object that can carry this failure without losing its cause.

## D-084: Worktree-writing gates remain stale for this slice

Date: 2026-08-31
Status: Confirmed
Area: M4, R-018, D-077

Context:
D-077 marks a gate stale when it changes content or repository-local lifecycle metadata, even if it restores the original bytes. The current repository gate file has no executable `argv`, and `owner_confirmed_safe_to_execute` is false, so no reviewed real gate contradicts that strictness.

Decision:
Keep D-077 unchanged for SLICE-001. A future mutation-replay command or other gate that writes must run in an isolated checkout, not in the worktree whose receipt it verifies.

Because:
Accepting a restored write would accept a result computed against content absent from the final tree. No current executable gate needs that exception.

Consequences:
M88 continues to hold the stale condition. A proposed gate that needs repository-local writes must supply isolation evidence before approval.

Revisit when:
A real reviewed gate cannot avoid writing into its verification target and the owner is prepared to change R-018 rather than weaken it silently.
## D-085: Filter neutralization is verified, not assumed

Date: 2026-08-31
Status: Confirmed
Area: M2, R-034, R-054, K-01, N-08, D-079

Context:
`_filter_overrides` neutralizes every content filter the repository declares by emitting `-c filter.<name>.clean=` and the smudge, process, and required companions. Git splits a `-c` argument on the **first** `=`. A driver named `a=b` therefore produced `-c filter.a=b.clean=`, which git read as the key `filter.a` with the value `b.clean=`, leaving `filter."a=b".clean` untouched.

A repository reaches such a driver from its own `.gitattributes` with `*.txt filter=a=b`, and `git check-attr` resolves it: `payload.txt: filter: a=b`.

Measured against the real `read_change_inputs`, with the payload writing outside the worktree so the acquisition boundary could not notice it:

    driver 'plain'   program executed: False   complete=True   problems=()
    driver 'a=b'     program executed: True    complete=True   problems=()

So repository-controlled code executed during acquisition, and the snapshot still called itself complete with no problems, which means a selective route would also have been authorised. Both halves of R-034 and R-054 failed at once, and the boundary fingerprint did not backstop it because a payload writing anywhere outside the repository leaves no trace inside it.

D-079 had just repaired the *test* that was supposed to hold this clause. The test was inert; the code underneath it was also wrong. Fixing the test is what made the code reachable to review.

Decision:
Verify the neutralization rather than assume it. After building the overrides, re-read each discovered driver's `clean`, `smudge`, and `process` keys with the overrides applied. Any key that still resolves to a non-empty value is reported, acquisition records `ADC-ROUTE-FILTER-UNNEUTRALIZED`, and **the worktree comparison is not run at all**.

Skipping the comparison is the point. Refusing to route afterwards would already have started the program: the guarantee these requirements state is that no repository program starts, not merely that no shortcut is granted.

The check uses `config --get`, not `--get-regexp`. A `-c` override does not replace a file's value, it adds one, and `--get-regexp` lists both, so the neutralized key came back carrying its original program beside the empty override and every ordinary driver read as live. `--get` returns the value git would actually use. The key travels as an ordinary argument rather than half of a `-c` pair, so a name containing `=` reaches it intact.

Because:
The bug was in a string built from an attacker-influenced name, and the class of such bugs is not closed by escaping one character. Asking git what it will actually do closes the class: any future spelling that defeats the override is reported by the same check, without anyone having to anticipate it.

This is the third time a fixed list or a constructed string was the wrong shape here. `core.fsmonitor` was closed, then `diff.external`, then filters were discovered rather than listed. Discovery was right and its execution was still wrong.

Consequences:
A repository whose filter driver cannot be neutralized does not get a worktree comparison, so its snapshot is incomplete and the full recipe is forced. That is a real loss of routing precision for such a repository, and it is the correct trade: the alternative is executing its code.

An ordinary driver such as git-lfs is unaffected, and `test_an_ordinary_filter_still_allows_a_complete_snapshot` holds that counterexample. M93 and M94 hold the refusal and the `--get` semantics.

The cost was measured, not estimated. Acquisition went from a fixed number of git subprocesses to `1 + 3N` extra in the number of configured filter drivers: one discovery call, then a `config --get` for each driver's `clean`, `smudge` and `process`. On this repository, which has one globally configured driver, that is 12 git calls to 16 and 0.400s to 0.472s, a median increase of 18 percent. A synthetic repository with 25 drivers went from 0.225s to 1.771s. The growth is linear and the constant is a subprocess, so a repository with many drivers pays visibly. One `config --list` would answer in a single call and is the obvious optimisation if that ever matters.

Revisit when:
Git gains a way to disable content filters wholesale, which would replace discovery and override with one flag.

## D-086: The self-grading guard covers every prefix the installer writes

Date: 2026-08-31
Status: Amended by D-091
Area: M3, R-005, R-021, D-071, D-078, D-082

Context:
D-082 extended the self-grading guard from source-layout paths to the managed installed layout by deriving a second spelling under `.agents/skills/`. `adc.py` defines four such prefixes in `HOST_SKILL_TREE_PREFIXES`: `.agents/skills`, `.claude/skills`, `.gemini/skills`, and `.codex/skills`. `install_skill` writes instruction authority to `.claude/skills/anti-dark-code/SKILL.md` whenever hosts is `all` or the default `auto` and a `.claude` directory or `CLAUDE.md` exists.

Measured: a policy that splits the shipped `**/SKILL.md` classifier entry into exactly the two spellings the guard probed **loaded clean**, and `.claude/skills/anti-dark-code/SKILL.md` then routed at Level 0 with `force_full` false in all 72 change shapes, including a delete.

This is the fourth correction to this guard and the second of its exact kind: D-078 replaced one sampled fact shape with the whole cross-product, and the path set stayed a literal enumeration that the product's own installer already outran.

Decision:
`INSTALLED_SKILL_PREFIXES` names all four prefixes, and every source path under `anti-dark-code/` is probed under each. `test_the_guard_covers_every_installer_prefix` compares that tuple against `adc.HOST_SKILL_TREE_PREFIXES` and fails if they drift.

`adc.py` is not imported by `adc_route.py`. The router is the thing the installer installs, and a dependency in that direction is a cycle. The list is therefore a deliberate copy with a test that makes the copy honest.

Because:
A guard whose coverage is a literal list needs something that fails when the list falls behind. Every previous correction to this guard added coverage; none added a way to notice the next gap. The drift test is the part that generalizes.

Consequences:
Nineteen probe paths become forty-three. The load-time cost is unchanged in kind and remains far below the fingerprint the same command runs.

The residual is a fifth prefix. `TOOLING_PATH_PREFIXES` also names `.anti-dark-code/`, which holds calibration rather than a skill tree; the drift test covers only the skill-tree set, and a future host prefix added to `adc.py` will fail that test rather than pass silently.

Revisit when:
The installer supports a prefix that is not a skill tree, or the drift test fails.
## D-087: A mutation target must match exactly one place

Date: 2026-08-31
Status: Confirmed
Area: M2, S-014, S-050, R-053, D-068

Context:
`replay.py` applies a row with `original.replace(old, new, 1)`. One occurrence is rewritten. The matrix integrity guard added in round ten checks that a row's original text is *present* in its source, and presence is not the same question.

**Five** active rows matched two places each in a committed state. M02, M03, M04, M05 and M40 name lines that exist in `build_route` and again in `build_candidate_route` or `CandidateRoute.__post_init__`, which round twelve added. Each row mutated the `build_route` copy, left the candidate copy running, and reported `caught`. The matrix therefore recorded coverage of lines that nothing had tested.

A sixth, M91, was ambiguous only inside this round. It was made so by this round's own commit `30c577c`, where `_live_filter_programs` copied the driver-discovery loop out of `_filter_overrides`. The first version of this decision said "one round earlier by this branch", which read as round fourteen's doing. It was round fifteen's, an hour before the guard that caught it, and replaying the uniqueness rule over `afdc2b4` and `57e941f` shows five ambiguous rows at both, not six.

Decision:
`test_every_mutant_target_occurs_exactly_once` fails on any active row whose text matches more than once. Superseded rows are exempt, because they describe a tree that no longer exists.

The rows are repaired two different ways, according to why they were ambiguous:

- M91's duplication was removed. `_filter_driver_names` is now the one discovery, called by both the override builder and the verification.
- M02 through M05 and M40 are anchored to the `build_route` copy they were always testing, with enough surrounding text to be unique, and each note says so.

Because:
A guard that checks presence answers "can this row be applied" and reads as if it answered "does this row hold its line". The distance between those two questions is exactly where five rows sat. Removing a duplicate is better than anchoring around it, so the one case where deduplication was available took it.

Anchoring is a documentation change, not a behavioural one. Applying the pre-anchor and post-anchor text of all five rows to the same source produces byte-identical mutants, because `build_route` and `Route.__post_init__` already preceded their candidate twins and `replace(old, new, 1)` was always rewriting them. What the anchoring buys is that the row now says which copy it tests, and the uniqueness guard can hold it there.

Consequences:
The candidate-route copies of those five lines are not held by a mutation row. They are shadow-only: a `CandidateRoute` cannot reach receipt authority or executable gate selection, so a defect there is a measurement error rather than a skipped check. That is recorded as U-017 rather than closed.

This is the second guard on this branch that checked an adjacent property rather than the property. D-078 records the first.

Revisit when:
The candidate builder's union logic is unified with `build_route`, which would remove the duplication and let the original rows cover both paths again.
## D-088: Neutralize through the environment, and refuse only what that cannot reach

Date: 2026-08-31
Status: Confirmed
Area: M2, R-034, R-054, D-085

Context:
D-085 stopped repository code executing during acquisition by verifying the neutralization and skipping the worktree comparison when any driver survived it. That is safe and it has a cost: a repository whose driver name the `-c` form cannot express never gets a worktree comparison, so unstaged paths never reach its receipt's `changed_files`.

Measured, before this decision:

    ordinary repository: complete=True   sources=['unstaged']
    refused repository : complete=False  sources=[]

Routing was unaffected, because an incomplete snapshot forces the full recipe either way. The record was poorer, and the only remedy available to that repository was renaming its driver.

Three alternatives were measured rather than argued.

No command can enumerate changed paths without converting content. `diff --raw`, `ls-files -m`, `status --porcelain` and `diff --name-only` all ran the filter; only `check-attr` did not. So there is no cheap stat-only fallback.

A scoped pathspec exclusion does work: `check-attr` identifies which paths select the driver, and excluding them keeps records for everything else without executing anything. It was rejected. With a repository-wide `* filter=X` attribute it excludes everything and collapses back to refusing, and it trades an absolute guarantee, that the converting command is never run, for a conditional one, that the command was run but told to skip those paths.

`GIT_CONFIG_COUNT` with numbered `GIT_CONFIG_KEY_n` and `GIT_CONFIG_VALUE_n` pairs carries the key and the value separately, so no name is inexpressible. Measured against a driver named `a=b`: the effective `filter.a=b.clean` becomes empty, the diff exits 0, and the program does not run.

Decision:
Neutralize through the environment when this module owns the runner. Verify the result with the same `--get` check D-085 introduced, and fall back to D-085's refusal when a driver is still live.

A caller that injected its own runner gets the refusal instead. There is no way to add an environment to a runner this code did not build, and assuming it worked is exactly the assumption D-085 exists to remove.

No git version check is made. Git before 2.31 ignores these variables, and the verification catches that with no help. A version test could disagree with the measurement about the thing the measurement already settled.

Because:
The refusal was a correct answer to a question that had a better one. Keeping it as the fallback means the guarantee never depends on the environment form being right, so this adds precision without moving the safety floor.

Consequences:
A repository whose driver name contains `=` now keeps its worktree comparison, and the record loss described above is gone.

Acquisition costs `1 + 3N` extra git subprocesses in the number of configured drivers: one discovery call, then a `config --get` per driver for `clean`, `smudge` and `process`. Measured here, with one globally configured driver, 12 git calls became 16 and 0.400s became 0.472s. A synthetic repository with 25 drivers went from 0.225s to 1.771s. Growth is linear and the constant is a subprocess; one `config --list` would answer in a single call if that ever matters.

`_live_filter_programs` treats an unreadable key as live. The runner reports any nonzero exit as `None`, which covers both "not set" and "git refused the command", and those are opposite answers.

Revisit when:
Git gains a way to disable content filters wholesale, or the per-driver cost shows up in a real repository.

## D-089: Calibration is authority, and it lives outside the skill tree

Date: 2026-08-31
Status: Amended by D-091
Area: M3, R-005, R-021, D-071, D-078, D-082, D-086

Context:
D-086 extended the self-grading guard to the layouts the installer writes by deriving a spelling under each host prefix for every path starting `anti-dark-code/`. Two entries did not start that way. The gate configuration and the routing policy were already spelled `.agents/skills/anti-dark-code/calibration/...`, so the derivation never touched them, and calibration was probed in exactly one spelling of the five `adc.py` enumerates.

`adc.calibration_dir()` returns `.anti-dark-code/calibration` whenever a managed install is absent, which is the ordinary case for a repository that has not installed the skill into a host tree.

Measured: narrow the shipped `**/calibration/*.json` classifier entry to the one probed spelling, grade the others cheaply, and the policy loads. `.anti-dark-code/calibration/routing-policy.json` — the router's own policy file — then routes at Level 0 in all 36 measured shapes.

Separately, the shipped calibration templates under `anti-dark-code/assets/templates/calibration/` were absent from the list entirely. `initialize_calibration` copies them into every fresh install, so they decide what an installing repository routes, and the same technique put them below the full recipe.

D-086's own Consequences section named this residual and dismissed it: "TOOLING_PATH_PREFIXES also names `.anti-dark-code/`, which holds calibration rather than a skill tree". That distinction was the error. Calibration is the authority; where it lives is incidental.

Decision:
Derive spellings two ways, because a path can move for two independent reasons. A file inside the skill tree moves when the tree is installed under a host prefix. A calibration file moves when there is no managed install at all, independently of any host prefix. `CALIBRATION_ROOTS` covers `.anti-dark-code/calibration/` plus the four skill-tree calibration directories, and any probe path containing `/calibration/` is derived under each.

The shipped calibration templates join `SELF_GRADING_PATHS`.

Because:
This is the fifth correction to this guard, and the first four each added coverage for the shape of the attack in front of them: classification instead of outcome, one sampled fact shape, one hardcoded prefix, then one prefix list. A rule that says how a path can move outlives the next attack in a way that a longer list does not.

Consequences:
Forty-three probe paths become more, and the load-time cost stays far below the fingerprint the same command runs.

The residual, stated rather than dismissed this time: the derivation is keyed on the literal segment `/calibration/`. A future authority directory with a different name would need its own rule, and `test_the_guard_covers_every_installer_prefix` holds only the skill-tree half against `adc.HOST_SKILL_TREE_PREFIXES`.

Revisit when:
`calibration_dir()` gains another fallback, or authority moves into a directory this rule does not name.

## D-090: A decision id cited in code must exist

Date: 2026-08-31
Status: Amended
Area: M2, M3, D-088, D-089

Context:
D-088 and D-089 were referenced by four comments in `adc_route.py`, four in `test_route.py`, and three places in the round-sixteen handoff, while neither existed in the decision log. Codex found it as the first act of round sixteen, before any of the verification that round was handed.

The round-sixteen handoff also told its reader to begin with `HANDOFF-BACK-ROUND-FIFTEEN.md`, which had never been written.

A comment reading "See D-088" where there is no D-088 is worse than no comment. It asserts that a rationale was recorded and reviewed, and a reader who goes looking finds nothing and cannot tell whether the decision was lost, renamed, or never made.

Nothing caught this. `RequirementTraceabilityTests` resolves R-ids and test node ids against real sources; no check resolved D-ids, and the suite passed at 436 with eight dangling references in it.

The original implementation was narrower than this decision: it named six
top-level Python files and only top-level routing Markdown. A citation in a
nested script, test, or routing document could therefore bypass the guard.

Decision:
`test_every_referenced_decision_exists` derives its claimed scope from every
`*.py` below `anti-dark-code/scripts/` and `anti-dark-code/tests/`, plus every
`*.md` below `design/routing/`. It collects every `D-0\d\d` citation from those
sources and fails on any that has no `## D-0xx` heading in
`DECISION-LOG.md`. The log's headings are definitions, and its prose is not
treated as citation failures.

Because:
The project's own rule is that a claim names its evidence. A decision id is a claim that evidence exists at a known address, and it is the cheapest kind to check.

Consequences:
A decision must be written before, or in the same change as, the first code that cites it. Writing the code first and the decision later is what happened here, and the gap survived a full suite, a validation run, a 95-row mutation replay, and a five-agent adversarial audit.

Revisit when:
Decision ids gain a second home, or a document deliberately references a decision from another repository.

## D-091: Every routing-owning pass reference is a guard probe

Date: 2026-08-31
Status: Confirmed
Area: M3, R-005, R-021, D-071, D-086, D-089

Context:
The self-grading guard represented the three routing-owning pass references
with only `00-preflight.md`. That was enough while the shipped classifier used
one broad `**/references/*.md` authority entry, but the classifier accepts
exact globs too. A policy could retain authority for `00-preflight.md` and
grade `10-maintenance-harness.md` and
`14-deterministic-verification.md` as cheap prose.

Measurement replaced the broad authority entry with that exact
`00-preflight.md` entry and appended a cheap broad reference entry. The
existing installed-spelling probes rejected the installed `00-preflight.md`,
but neither source reference that owns the other passes appeared in the
diagnosis. They were outside the guard's authority set.

Decision:
`ROUTING_OWNING_PASS_REFERENCES` names all three pass-owning references, and
`SELF_GRADING_PATHS` expands each one into a guard probe. The regression
requires the load error to name `10-maintenance-harness.md` or
`14-deterministic-verification.md`.

Because:
One representative path cannot stand for a classifier that may distinguish
exact paths. Layout derivation answers where one authority file can move; it
does not answer which distinct files own routing passes.

Consequences:
D-086 and D-089 are amended by measurement. Their installer-prefix and
calibration-layout derivations remain necessary, but neither establishes that
one source representative covers distinct authority files. The guard gains
two source references and their managed-install spellings; a policy that
cheaply classifies either now fails at load.

Revisit when:
A new reference owns a routing pass, or routing ownership moves out of the
reference set.

## D-092: Host-generated pytest cache is not install provenance

Date: 2026-08-31
Status: Confirmed
Area: M2, source provenance, install integrity

Context:
`.pytest_cache` was already an ignored repository directory, but
`managed_source_files()` independently excluded only `__pycache__` and `.git`
at every depth. A real pytest cache carries its own `.gitignore` containing
`*`, so Git did not report the host-generated state as dirt. The managed-file
walk nevertheless included its bytes in the core digest. A tag could therefore
remain clean while its recorded install digest changed for data no install
would be meant to distribute.

Decision:
`managed_source_files()` excludes `.pytest_cache` at every depth, alongside
`__pycache__` and `.git`. The provenance regression builds a tagged fixture
core with the real cache `.gitignore` and a cache payload, then requires both
the file set and the provenance digest to remain unchanged and the source to
remain a clean `git-tag`.

Because:
Host-generated runner state is not distributed source authority and must not
alter install provenance.

Consequences:
The provenance boundary now matches the ignored pytest runner state for both
the shipped file set and the digest derived from it. A cache cannot cause
spurious digest drift or make an otherwise immutable tagged source appear to
have different install bytes.

Revisit when:
The distributed core intentionally includes pytest runner artifacts, or a new
host-generated directory is excluded by source-control and install policy but
not by the provenance walk.

## D-093: Self-grading authority is a classifier contract, not a path sample

Date: 2026-09-01
Status: Confirmed
Area: M3, R-021, R-053, D-071, D-086, D-089, D-091

Context:
The self-grading guard derived source, installed, and calibration spellings
from a short list of representative paths.  ENGINEERING names broader authority
classes: mutation and validator harnesses, repository metadata, source-scope
provenance, every workflow, project manifests and locks, as well as router,
policy, pass, and test authority.

Measured with every rule approved in memory: a policy that classified each of
`design/routing/mutants/replay.py`, `.gitattributes`, `.gitignore`, or
`anti-dark-code/SOURCE-SCOPE.json` as exact docs/prose loaded.  A policy that
kept only `.github/workflows/tests.yml` as authority and classified the rest of
`.github/workflows/**` as docs/prose also loaded.  Each affected target routed
below the full recipe in all 72 change-kind, source, and mode shapes.

Decision:
When a nonempty classifier is paired with any current or proposed rule that
does not force full, `load_policy()` requires every exact entry in
`AUTHORITY_CLASSIFIERS`.  The entries are the canonical classifier forms for
all ENGINEERING self-grading classes.  A policy may add another matching fact,
but it cannot replace a required authority class with an exact representative
or a cheap exception.  The existing per-path, per-layout, and per-shape guard
stays in place; it proves rule behaviour after the class contract proves the
classifier cannot omit a class.

Because:
One path can demonstrate a class only while the classifier cannot distinguish
that path.  It can distinguish exact paths, so representative probing leaves an
attacker-controlled partition.  Retaining the canonical authority glob means
an exact cheap entry still coexists with an authority fact and therefore cannot
lower the route.

Consequences:
Any nonempty classifier paired with a current or proposed non-force-full rule
must carry every named authority class or fail closed at load.  This includes a
policy that removed every authority-labelled entry and retained only an exact
cheap exception.  A classifier-free policy, or a policy whose rules all force
full, remains compatible because it cannot route a classified path cheaply.
All shipped rules remain proposed.  Adding a future authority class requires
adding its canonical classifier entry, the drift test, and a review; it cannot
silently inherit a cheap generic classification.  M96 holds the load-time
enforcement and was caught on both T540P Linux and Windows in the final
authoritative Round Sixteen replay.

The machine-checkable Python authority set is root and nested
`pyproject.toml`, `requirements*.txt`, `Pipfile`, `*.lock`, `setup.py`,
`setup.cfg`, `pytest.ini`, and `tox.ini`.  `**/scripts/adc*.py` deliberately
covers every dynamically imported `adc` helper, including receipt, routing,
and efficiency controls.  `design/routing/mutants/*` deliberately includes
both harness code and `matrix.json`.

Revisit when:
ENGINEERING changes a self-grading class or the router gains classifier syntax
whose coverage cannot be represented by the canonical entries.

## D-094: A stronger guard supersedes a redundant mutation row

Date: 2026-09-01
Status: Confirmed
Area: M3, R-021, D-082, D-093, M92, M96

Context:
The final frozen-head T540P replay at `0a26531` ran all 96 rows and found one
local survivor: M92, which replaces `_self_grading_guard_paths()` with the
literal `SELF_GRADING_PATHS`.  The earlier Linux record had caught M92 before
D-093 added the canonical classifier contract.

The changed outcome is expected.  With the exact M92 reversion in force, a
nonempty classifier with a cheap current or proposed rule cannot narrow
`**/scripts/adc*.py` to the source spelling: D-093 rejects the missing
canonical class before `_check_self_grading()` runs.  The two compatibility
branches are also safe.  An empty classifier grades the installed router as
unknown and routes full; a policy whose rules all force full still routes the
installed router at Level 3 with `force_full=true`.

Decision:
M92 is superseded by M96.  M92's historical attack no longer changes routing
behaviour under any policy that can load, while M96 attacks the stronger
load-time class-contract enforcement that now prevents it.  Keep the
source/installed-layout derivation and its direct tests as defense in depth;
do not make a redundant mutant fail merely to preserve an old count.

Because:
A mutation row is evidence only while its replacement can falsify the named
guarantee.  Once a stronger independent guard makes the replacement inert, a
surviving mutant is evidence of supersession rather than a reason to add a
test that encodes obsolete implementation structure.

Consequences:
The matrix remains 96 rows and now has 91 active rows and 5 superseded rows.
The T540P report retains the measured M92 survivor as the reason for the
transition; the durable matrix clears obsolete host results from the
superseded row.  M96 remains active and was caught on the same T540P run.

Revisit when:
The canonical classifier contract is removed, narrowed, or replaced by a
mechanism that no longer covers managed installed script spellings.

## D-095: An unskipped local survivor is a survivor on every host

Date: 2026-09-02
Status: Amended by D-104
Area: M3, R-053, D-054, D-068, `derive_verdict`, `Mutation replay (Linux)`

Context:
`replay()` folded the local result into the row's stored results before it
decided anything, and `derive_verdict` then read "caught anywhere" as caught.
The matrix stores one result per host and no commit per result, so the stored
foreign result comes from another host and, in practice, another commit. A
row the other host once caught therefore could not fail a replay on this
host: a fresh local SURVIVED became "caught elsewhere", left the not-caught
list, and the exit stayed 0. Only the "(here: SURVIVED)" note said otherwise.

Measured twice. Round sixteen's own authoritative T540P write replay at
`0a26531` recorded M92 as a local survivor and still exited 0 with `96
mutants, 0 not caught: none`; its report's `local_survivor_ids` names M92
while its summary names nothing. In this round, an uncommitted edit that
removed the one test holding M57 made the serial replay print `caught
elsewhere (here: SURVIVED)` and `1 mutants, 0 not caught: none`, exit 0. The
CI job runs the same function, so the `Mutation replay (Linux)` job, which
the round-sixteen handoff described as failing on any survivor, could not
have failed on a Linux survivor for any of the 88 rows Windows had once
caught. At `92e028e` its log shows no `(here: SURVIVED)` line, so no current
row was masked; the mechanism was.

Decision:
`derive_verdict` returns SURVIVED when any host result is SURVIVED with zero
skipped tests, before it counts catches. A host that ran every test and did
not catch the mutant has observed a survivor, and no other record can soften
that. "Caught elsewhere" remains the label only for a local survivor under a
skipped test, and `replay()` discloses those rows on a separate summary line
so a reader sees what this host did not observe. M97 holds the branch.

Because:
The other host's record answers a different question, on a different host,
usually at a different commit. Merging it before deciding made the summary
describe the matrix's past rather than the tree under test.

Consequences:
Linux runs every test, so every Linux survivor now fails the replay and the
CI job. Windows skips the symlink test on every row, so a Windows-only
survivor under that skip still rests on the Linux record; the disclosure line
names it. M37, M46, and M48 keep "caught elsewhere". No current row changes
verdict. The round-sixteen handoff's claim that CI "fails on any survivor"
was false until this decision and is true now for the required Linux host.

Revisit when:
A result records its commit, so a stale foreign record can be recognized
directly rather than by skip count; or a second replay host without skips is
added.

## D-096: A parallel replay requires a clean coordinator tree

Date: 2026-09-02
Status: Amended by D-103 for serial replay
Area: M3, R-053, D-068, D-084, `run_parallel`, `_verify_coordinator_sources`

Context:
Serial replay mutates and tests the working tree. Parallel replay clones the
committed HEAD into each worker. The round-sixteen identity comparison proved
the two agree at a clean commit, `f3d08a4`. The coordinator preflight froze
only the matrix, the harness, and the active mutation targets against HEAD,
so a dirty suite, policy, fixture, or an untracked `conftest.py` passed
preflight while the clones tested something else.

Measured: with one uncommitted edit renaming
`test_only_the_run_store_is_excluded_from_the_binding` in `test_receipt.py`,
a file no row mutates, `replay.py M57 --jobs 1` reported `19 passed` and
SURVIVED here, and `replay.py M57 --jobs 2` reported `1 failed, 19 passed`
and caught. Both exited 0 (D-095 covers the exit), both recorded commit
`92e028e`, and neither report said the tree differed from it.

Decision:
`_verify_coordinator_sources` first requires `git status --porcelain` to be
empty in the coordinator. Any tracked modification or untracked file makes
every active row inconclusive with `working tree differs from HEAD`, before a
clone or worker exists. Serial replay is unchanged: it replays the disk by
design, and `--write` remains serial-only. M98 holds the refusal.

Because:
A parallel verdict describes HEAD. Refusing a tree that is not HEAD is the
only way the report's `commit` field can be read literally. Freezing more
files would chase the suite's input set, which includes the policy, the
capability catalog, the fixtures, and any future `conftest.py`.

Consequences:
CI is unaffected: the job runs on a fresh checkout and already refuses a
dirty tree after the run. A developer must commit before a parallel replay,
the discipline D-068 already asks for. A Windows checkout made under
`core.autocrlf=true` still fails the older frozen-source comparison, because
its worktree bytes differ from the LF blobs; the workaround is a clone made
with `core.autocrlf=false`, which is what `prepare_clone` uses for workers.
That limitation is recorded here, not fixed.

Revisit when:
The report records the working-tree status and a reviewer prefers a labelled
dirty run to a refusal; or serial replay gains the same refusal.

## D-097: A helper that adc.py loads is authority by its name

Date: 2026-09-02
Status: Superseded by D-100
Area: M3, R-005, R-021, D-093, ENGINEERING section 12

Context:
ENGINEERING section 12 names "any imported helper that can change collection,
hashing, validation, selection, execution, installation, or distribution" as
a self-grading class and promises that a newly imported helper not
represented in the path table "makes the table test fail closed until
reviewed". Nothing derived the loaded set. The classifier reaches helpers
only through `**/scripts/adc*.py`, a naming convention, so the promise held
for the three helpers that happen to carry that name.

Measured with every rule approved in memory:
`anti-dark-code/scripts/receipt_store.py`, a name adc.py could load tomorrow,
routed as Level 2 product code with `force_full` false, in both the source
and the `.claude` installed spelling. `work_receipt.py`, the one script
outside the convention, is a standalone transcript summarizer that adc.py
never names; it routes the same way and is not a self-grading class, which is
why it had not been a hole.

Decision:
`test_every_script_adc_loads_is_authority_by_name` enumerates
`anti-dark-code/scripts/*.py`. A script is either authority by name, matching
`adc*.py`, or it is in `REVIEWED_STANDALONE_SCRIPTS` and adc.py must not
name it. Any other script fails the table. The test also asserts that the
canonical `**/scripts/adc*.py` classifier is present.

Because:
The naming convention is the only link between a loaded helper and the
authority classifier. Making the convention executable is what turns the
section 12 promise from prose into a gate.

Consequences:
A helper added under another name fails the suite in the commit that adds it,
until it is renamed or reviewed into the standalone set. The standalone set
can only hold scripts adc.py does not name. No route changes for any path in
the current tree.

Revisit when:
adc.py gains an import mechanism the text scan cannot see, or a helper must
carry a non-`adc` name for a reason a reviewer accepts.

## D-098: A worker's collection tree stays inside its clone

Date: 2026-09-02
Status: Amended by D-101
Area: M3, R-053, D-084, D-096, `run_suite`, parallel workers

Context:
A worker runs its suite from the coordinator root with an absolute path into
its clone, so that detached helpers never hold the clone open (D-084). With
no `--rootdir` and no configuration file, pytest derives its rootdir from the
common ancestor of the invocation directory and the suite path. When the
coordinator lives beneath the host temp directory, that ancestor is the temp
directory itself, and pytest's session collects it: every entry of the
machine-wide temp directory is scanned and stat-ed at each row's start.

Measured on this host, where `TEMP` is `J:\TEMP` and the coordinator clone
sat in a scratch directory beneath it. The first full `--jobs 8` replay at
`3856f11` completed exactly four rows per worker, then 59 rows returned
inconclusive inside the window in which a serial replay ran in another
clone; two rows whose sessions started between deletions completed. Rerunning
failed rows through the worker path alone, with a second serial run started
100 seconds later, reproduced it with the error visible: `ERROR collecting
test session ... FileNotFoundError: [WinError 2] ... 'J:\TEMP\tmpo1xr2yol'`,
`Interrupted: 1 error during collection`, exit 2, about five seconds per
row, while the rows before the window caught normally. Round sixteen's
identical run never saw this because its coordinator lived on `C:` and its
temp on `J:`, which share no ancestor. The Linux job never sees it because
the ancestor is `/`, which pytest refuses as a rootdir.

Decision:
A worker's suite command carries `--rootdir=<clone>`. The clone is the only
directory a worker owns, so it is the only directory its collection tree may
start from. Serial replay is unchanged: it runs from the repository root with
relative paths, and that root is already its rootdir. M99 holds the flag.

Because:
Evidence that depends on where the coordinator happens to sit, or on what
another process does in a shared directory, is not evidence about the mutant.
The failure was fail-closed, so no verdict was wrong, but 59 rows of nothing
is not a replay.

Consequences:
The full parallel replay is repeatable from any coordinator location,
including one beneath the host temp directory, and alongside other pytest
runs on the same host. The layout dependence round sixteen's runs carried
without knowing it is gone.

Revisit when:
pytest changes how it roots a collection tree for arguments outside the
invocation directory, or a worker ever needs to collect outside its clone.

## D-099: The coordinator reports a worker row's own reason

Date: 2026-09-02
Status: Amended by D-102
Area: M3, D-068, D-084, `_validate_worker_result`

Context:
The coordinator validates each worker row against an exact field set before
it reads anything else. A row that could not become evidence carries an
`error` field explaining why: a suite that did not answer, a target that did
not match, a source that did not restore. That field is outside the set, so
every such row was reported as `worker result schema does not match the
required evidence fields`, and the reason the worker had recorded was
discarded with it. The first round-seventeen parallel run reported that
sentence for 59 rows; the cause in D-098 appeared only after the failed rows
were rerun through the worker path by hand.

Decision:
A worker row whose status is not `completed` and which carries a string
`error` is reported as `worker row <status>: <error>`, truncated to 2,000
characters. The row stays inconclusive, no evidence is accepted from it, and
every check on completed rows is unchanged.

Because:
An inconclusive row is a finding only if a reader can act on it. A sentence
about field names names nothing.

Consequences:
Parallel reports carry the worker's diagnostic, including the tail of the
pytest output that `run_suite` already collects. A completed row with an
`error` key is still rejected by the schema check.

Revisit when:
Worker rows gain a structured failure field, or the report format changes.

## D-100: Every shipped script is verification authority by location

Date: 2026-09-02
Status: Confirmed
Area: D-093, D-097, routing classifier, `anti-dark-code/scripts/`

Context:
D-097 inferred whether a script was authority from its `adc*.py` name, then
scanned `adc.py` for a quoted filename or stem to keep the one reviewed
standalone script unloaded. A real importlib load built `work_receipt.py` from
three string fragments and loaded the module while the scan returned no match.
The test therefore checked one spelling, not the load boundary it claimed.

Decision:
Every Python file directly under `anti-dark-code/scripts/` is verification
authority through the canonical `**/scripts/*.py` classifier. The classifier
applies to source and installed spellings. No loader scan or standalone
exception decides authority.

Because:
A conservative directory boundary is stable under dynamic filenames, new
loader functions, and helper renames. This directory ships executable control
code. Treating one script change as ordinary product code saves too little to
justify a second, incomplete loader implementation in a test.

Consequences:
`work_receipt.py` changes now force the full recipe even though `adc.py` does
not currently load that script. M100 holds the directory-wide classifier.

Revisit when:
Standalone product scripts move into a separate directory with its own reviewed
classification contract.

## D-101: A worker owns its pytest environment as well as its rootdir

Date: 2026-09-02
Status: Amended by D-105
Area: D-098, `run_suite`, parallel replay workers

Context:
`--rootdir=<clone>` stopped pytest from loading a `conftest.py` above the clone,
but it did not contain plugin discovery. With `PYTEST_ADDOPTS=-p
external_adc_plugin` and `PYTHONPATH` naming the coordinator, a worker rooted in
its clone passed its test after importing the plugin from outside that clone.

Decision:
A parallel worker removes caller-supplied pytest plugin and option variables,
disables automatic plugin loading, removes caller `PYTHONPATH`, and enables
Python safe-path behavior. Its explicit command, clone, installed pytest, and
private temp root are the only worker inputs inherited by design.

Because:
An external plugin can change collection, outcomes, process behavior, and logs.
A clone-owned rootdir is not an isolation boundary while the caller can inject
code before collection starts.

Consequences:
M101 holds the worker environment boundary. D-104 later applied the same
controlled environment to serial replay and added one explicit tracked outcome
plugin. The coordinator freezes that plugin with the replay source before a
parallel worker may load it.

Revisit when:
The replay suite requires a non-builtin plugin, or pytest changes the variables
that control plugin discovery.

## D-102: A worker diagnostic is one bounded terminal-safe line

Date: 2026-09-02
Status: Amended by D-106
Area: D-099, `_validate_worker_result`, replay console and JSON report

Context:
D-099 limited the worker error payload to 2,000 characters, but returned those
characters unchanged. A payload containing a newline, carriage return, and ANSI
escape retained all three and printed a forged replay summary on the next line.
The JSON report escaped them, but the console did not.

Decision:
Before a worker error reaches the coordinator result, control and format
characters are rendered as visible ASCII escapes and the rendered payload is
limited to 2,000 characters. The useful diagnostic remains, but it cannot add a
terminal line, move the cursor, recolor later output, or hide text direction.

Because:
An untrusted diagnostic is data. Printing it verbatim turns terminal control
bytes into presentation authority.

Consequences:
Reports remain JSON-compatible and completed worker rows remain subject to the
exact schema. M102 holds the sanitization boundary.

Revisit when:
Worker failures become structured fields rendered by a separate presentation
layer.

## D-103: Serial evidence labels dirt, and serial writes require clean endpoints

Date: 2026-09-02
Status: Confirmed
Area: D-068, D-096, serial replay reports, `--write`

Context:
Serial replay tests the working tree and labels every row with `HEAD`. Unlike
parallel replay, it did not say whether the disk differed from that commit.
This is useful during the round-robin workflow, where handoff documents are
edited while a long read-only replay runs, but it is not sufficient authority
for rewriting the matrix.

Three options were measured on the round-eighteen Windows tree. Sixty clean
`git status --porcelain` calls took 27.411 ms median and 59.052 ms p95. Sixty
calls on a seven-path dirty tree took 29.191 ms median and 32.652 ms p95. The
three-row serial mutation check took 173.03 seconds. The most recent full serial
records took 1,524 seconds on T540P and 6,585.939 seconds on Windows.

Decision:
A serial report records the exact porcelain status before and after replay.
Dirty read-only replay remains available. `--write` refuses an initially dirty
tree before running a row and refuses a tree that becomes dirty during replay
immediately before matrix publication. A clean `--write` therefore binds both
endpoints; the report still names the endpoint status.

Because:
Two status calls cost about 58 ms at the measured medians, below 0.004 percent
of the shorter full serial run. Refusing every dirty serial run would discard
useful read-only evidence and would still need the final check to close the
mid-run race. Leaving serial unchanged would save milliseconds while allowing
an ambiguous tree to rewrite the coverage record as if it were `HEAD`.

Consequences:
Round-robin handoff edits no longer prevent read-only mutation work, and their
presence is visible in the report. Authoritative `--write` replay moves to a
clean checkpoint. M103 holds the initial refusal and M104 holds the final
publication check.

Revisit when:
Serial replay moves into a disposable committed clone, or reports bind a full
content identity instead of Git porcelain state.

## D-104: A skipped survivor needs exact catching-test attribution

Date: 2026-09-02
Status: Confirmed
Area: D-095, mutation result schema, exact pytest outcome plugin

Context:
D-095 treats any local survivor with a nonzero skip count as caught elsewhere
when another host caught the row. The count cannot say which test skipped. Two
otherwise identical result sets, one where the skipped test holds the mutant
and one where an unrelated test skipped, both derived `caught elsewhere`.

The required Linux branch remains sound. A clean T540P probe committed a change
that removed the only test holding M57, then ran `M57 --jobs 2`. The row completed
with `19 passed`, zero skips, `SURVIVED`, exit 1, source restoration true, and a
clean endpoint. The gap is limited to a host that both skips and observes a
survivor, which currently means Windows.

Decision:
Each replay row records exact failed and skipped node IDs from the tracked
outcome plugin. A local survivor under skips is `caught elsewhere` only when at
least one exact skipped node ID also failed for that mutant on a catching host.
An unrelated skip, a missing identity list, or an empty intersection leaves the
row `SURVIVED`. Zero-skip survivors retain D-095's unconditional precedence.

Because:
The failed test names the branch that caught the mutant. Skip attribution must
name that same test before another host's result can carry the row. Counts from
two unrelated test sets are not coverage evidence.

Consequences:
The tracked plugin becomes replay authority and runs explicitly with automatic
and caller-supplied plugins disabled. M37, M46, and M48 require refreshed
Windows skipped-node records before the T540P catching-node replay can restore
their `caught elsewhere` verdicts. M105 holds exact attribution and M106 holds
the explicit outcome collector.

Revisit when:
Pytest provides a stable built-in machine-readable outcome format, or the
matrix binds each mutation directly to an independently reviewed holding-test
set.

## D-105: A worker owns its interpreter and its configuration, not only its pytest options

Date: 2026-09-02
Status: Confirmed
Area: D-098, D-101, `run_suite`, replay workers and serial replay

Context:
D-101 removed the pytest option and plugin variables, disabled plugin
autoload, removed the caller's `PYTHONPATH`, and enabled safe-path. Two
layers sit beneath that boundary. The interpreter runs site initialization
before pytest reads an option: with `PYTHONUSERBASE` pointed at a
caller-controlled directory, a `usercustomize.py` and a `.pth` import line in
its site-packages both executed inside a worker whose suite reported `1
passed`; with `PYTHONNOUSERSITE=1` neither ran. And pytest searches for
`pytest.ini`, `tox.ini`, `setup.cfg`, and `pyproject.toml` from the common
ancestor of the invocation directory and the arguments upward, which a
rootdir does not stop: a `pytest.ini` at that ancestor supplied `addopts = -p
external_adc_plugin`, the worker obeyed it, and its row went inconclusive
with an import error. For a worker that ancestor is the host temp directory;
for serial replay it is every parent of the repository, `/tmp` for a T540P
clone.

Decision:
The suite environment drops `PYTHONUSERBASE`, `PYTHONSTARTUP`, `PYTHONHOME`,
`PYTHONEXECUTABLE`, and `PYTHONINSPECT` and sets `PYTHONNOUSERSITE=1`. Every
suite command names an empty `pytest.ini` owned by the run with `-c`, and
serial replay pins `--rootdir` to the repository root so the pin cannot move
it. Both modes. M107 holds the user-site boundary and M108 holds the
configuration pin.

Because:
Code that runs before pytest starts is not contained by anything pytest does.
A configuration file the run did not write is caller input. The inputs a
worker inherits by design remain its explicit command, its clone, the
installed pytest, and its private temp root.

Consequences:
A caller-controlled user site cannot execute in a worker or a serial run. A
configuration file above the clone or the repository cannot change
collection, options, or outcomes. Node ids keep their rootdir-relative
spelling in both modes, so D-104's cross-host attribution is unaffected.
System site-packages, where pytest itself lives, stay in use.

Revisit when:
pytest gains a flag that disables configuration discovery outright, or the
interpreter gains an isolation mode that keeps `PYTHONPATH`.

## D-106: The serial console renders a diagnostic the same way the coordinator does

Date: 2026-09-02
Status: Amended by D-115
Area: D-099, D-102, `replay()` console output

Context:
D-102 renders control and format characters before a worker diagnostic
reaches the coordinator result, so the parallel console is one bounded line
per row. The serial path printed a broken row's error directly. Measured: a
serial `SuiteBroken` whose text carried a newline and an ANSI escape printed
a forged `M01 forged row caught` line on its own line, followed by a
coloured forged summary.

Decision:
`replay()` passes every non-completed row's error through the same renderer
before printing it, in both modes. The JSON report keeps the raw text. M109
holds the serial print path.

Because:
The console is presentation and the summary line is what a reader trusts.
One renderer for both modes removes the asymmetry D-102 left.

Consequences:
No console line can carry a raw control character in either mode. Reports
are unchanged.

Revisit when:
Row failures become structured fields rendered by a separate presentation
layer.

## D-107: D-100's contract reaches every scripts directory, and its statement does not say so

Date: 2026-09-02
Status: Open, owner decision
Area: D-093, D-100, canonical authority classifiers, shipped policy template

Context:
D-100 says every Python file directly under `anti-dark-code/scripts/` is
verification authority by location. The canonical classifier that
implements it is `**/scripts/*.py`, which the D-093 contract requires in
every policy that pairs a nonempty classifier with a non-force-full rule, and
the template ships to every installing repository. Measured with every rule
approved: `tools/scripts/build.py`, `packages/app/scripts/migrate.py`, and
`docs/scripts/render.py` in an installing repository route as verification
authority at Level 3 with `force_full`; under the previous
`**/scripts/adc*.py` entry they took the Level 2 product route. A root-level
`scripts/deploy.py` was already full because nothing maps it.

Decision:
None taken here. The owner chooses between: (1) keep the wide entry and
amend D-100 and ENGINEERING section 12 to say that any nested `scripts/*.py`
in an installing repository is authority; (2) narrow the canonical entry to
the shipped skill's own scripts in both spellings,
`anti-dark-code/scripts/*.py` and `**/anti-dark-code/scripts/*.py`, and
re-measure every self-grading probe; (3) return to name-based authority
behind a stronger loader guard. Option 2 keeps every current self-grading
path forced full, because both the source and the installed spellings match
it.

Because:
Widening a universal contract to close a repository-local hole is a product
decision, not a harness repair, and a decision's text should say what its
contract does.

Consequences:
Until the owner decides, the contract stands as D-100 implemented it, and
this entry records the gap between its statement and its reach.

Revisit when:
The owner answers, or the classifier contract gains per-repository scoping.

Measured in round twenty:
Both options were loaded and routed on Windows at `39d745d` through the real
`load_policy`, `collect_change_facts`, and `build_route`, with every rule
approved in memory. Under both, all 71 self-grading guard paths force the
full recipe. Option 1 forces the full route for `tools/scripts/build.py`,
`packages/app/scripts/migrate.py`, `docs/scripts/render.py`,
`ci/scripts/release.py`, and `src/scripts/__init__.py`; option 2 routes them
as product code and changes nothing else measured. The table is in the D-107
section of `HANDOFF-BACK-ROUND-TWENTY.md`. The choice stays the owner's.

## D-108: A walkthrough check compares committed bytes, not a checkout

Date: 2026-09-02
Status: Confirmed
Area: WALKTHROUGH-SLICE-001, SERIAL-EVIDENCE-ROUND-EIGHTEEN, Windows checkouts

Context:
Round eighteen added a walkthrough command that hashes
`design/routing/mutants/matrix.json` from the working tree and asserts
equality with the artifact's `final_annotated_matrix_sha256`. The artifact
records the digest of the committed blob, which has LF line endings. This
machine, the owner's, has `core.autocrlf=true` globally, so a fresh `git
clone` checks the file out with CRLF and the assertion fails with a bare
`AssertionError`. Measured: the literal walkthrough at `08d0576` on a fresh
default clone passed every other expectation and failed this one. Round
eighteen's own run passed because its clone was made with
`core.autocrlf=false`.

Decision:
The walkthrough hashes the committed blob through `git cat-file blob
<commit>:<path>` and prints whether it matches, so the check is independent
of checkout line endings. The commit is named in the command, so the check
cannot drift to a later head.

Because:
A walkthrough step that fails on the owner's default configuration is a
document that says something the tree does not, which is the class of defect
the walkthrough exists to catch. The artifact records a blob digest, and a
blob digest is what the check should compare.

Consequences:
The owner can run the walkthrough from a default clone. Evidence artifacts
keep recording blob digests.

Revisit when:
A walkthrough step needs to bind working-tree bytes rather than committed
bytes.

## D-109: A host record is current only at the commit that produced it

Date: 2026-09-02
Status: Confirmed
Area: D-068, D-104, matrix host records, `--write`

Context:
Round eighteen refreshed ten Windows rows from a clean clone and ran the
full serial `--write` matrix on T540P, then recorded that every active row
carries Windows and Linux records. By count that is true. By commit it is
not: 91 of the 101 active rows carry Windows records taken in rounds sixteen
and seventeen, before D-100 through D-104 changed the router, the harness,
and the suite, and those records carry no exact node identities. Only the
Linux side was replayed in full at the round-eighteen head. The walkthrough
line `recorded on both hosts 101` invites a reader to take both records as
current.

Measured in this round: a full read-only parallel replay at `08d0576`, from a
clean `core.autocrlf=false` clone, processed all 106 rows with `0 not
caught`, exit 0, in 1,169 seconds under three concurrent replays. Its
Windows verdicts agree with all 91 stale records, but one record no longer
describes the head: M68's stored Windows record says ten tests fail under
it, the fresh run says eleven, and the Linux record written at the
round-eighteen head already says eleven. The suite gained a catching test
after the Windows record was written, and the record did not know.

Decision:
A host record is evidence for the commit it was produced at and no other.
The matrix does not store that commit per result, so the artifact and
handoff of the round that writes a record must say which commit and how
many rows it covered. This round refreshes every Windows record from a
full serial `--write` at its implementation head, so every active row's
Windows record carries exact identities from one commit. Done: the full
serial `--write` at `39d745d` processed all 109 rows with `0 not caught`
from a clean clone, changed only `matrix.json`, and its matrix is the
committed matrix, SHA-256 `7660b7533a22dc745b675a0a480bef0d4e87a985c61851faa45d32f8731d2f6f`.
The Linux records were not touched by it and remain round eighteen's, at
`c846660`.

Because:
"Every row carries both records" is a claim about currency as well as
existence. A record that predates the code it describes is a historical
fact, not evidence about the tree under review.

Consequences:
The matrix's Windows records are current at this round's implementation
head with exact identities. Future rounds that change the router, the
harness, or the suite either refresh the affected host records or say which
records predate the change.

Revisit when:
Each stored result records the commit that produced it, at which point
currency can be checked by a test rather than by a handoff.

## D-110: A survivor with no catching host is a survivor, not an unverified row

Date: 2026-09-02
Status: Confirmed; landed in round twenty
Area: D-054, D-095, D-104, `derive_verdict`, Windows replays of new rows

Context:
`derive_verdict` returns `unverified: every host skipped` when no host caught
the mutant and every recorded result skipped at least one test. Windows
skips the symlink test on every row. A new row therefore cannot be
`SURVIVED` on a Windows-only replay: it is `unverified`, it leaves the
not-caught list, and the exit stays 0. D-095 closed this shape for rows
with a stored foreign catch; D-104 gave the harness exact skipped and
failed identities; this branch predates both and still runs first.

Measured: the full parallel replay at `49fed51`, under the first version of
the D-105 test, printed `M107 ... unverified: every host skipped (here:
SURVIVED, 1 skipped)`, then `109 mutants, 0 not caught: none`, exit 0, and
listed M107 on the disclosure line as resting on another host's record when
no other host had a record. The Linux CI job at the same commit, which skips
nothing, reported `109 mutants, 1 not caught: ['M107']`. The mutant was a
real survivor; only the host that could not skip said so.

Decision:
Deferred to round twenty so this round's evidence runs stay at one head. The
intended repair: when no host caught the mutant, the row is `SURVIVED` on
every host, and the console names the exact tests the host skipped so a
reader knows which test might hold it; the `unverified` label is retired.
A later catching host restores `caught elsewhere` through D-104's exact
intersection, as now. The zero-skip branch is unchanged.

Because:
"Nobody could check this" was the honest label before exact identities
existed. With them, a host that ran every test but one and saw the mutant
survive has observed a survivor with one named exception, and a summary that
reads "0 not caught" for it is the D-095 defect in a new place.

Consequences:
Until the repair lands, a Windows-only replay of a new row cannot fail. The
Linux replay job can, and did. Round twenty adds the test, the mutation row,
and the repair, and re-measures M107 on both hosts.

Revisit when:
Round twenty lands the repair, or a host that skips nothing becomes the only
authoritative replay host.

Outcome in round twenty:
The branch is removed. With no catching host the row is `SURVIVED` on every
host, the console names the exact tests the host skipped, and a later
catching host restores `caught elsewhere` through D-104's intersection.
`test_a_row_no_host_caught_is_survived_even_under_skips` and the amended
`test_a_verdict_does_not_depend_on_which_host_ran_last` hold it; M110
reinstates the branch and fails both.

## D-111: A worker does not inherit flags that change what a test means

Date: 2026-09-02
Status: Confirmed
Area: D-101, D-105, `run_suite`, replay workers and serial replay

Context:
D-105 owned where a worker's code comes from: no user site, no caller
plugin path, no configuration file the run did not write. The interpreter
also reads flags that change what a test means. The round-twenty challenger
measured through the real `run_suite`, and the author reproduced it:
`PYTHONWARNINGS=error` turned a probe that emits a `DeprecationWarning`
from `1 passed` into `1 failed`, and `PYTHONOPTIMIZE=2` turned `assert
__debug__` from a pass into a failure. A mutant that survives can therefore
be recorded as caught because the host set a warning filter, which is the
D-095 class again with the environment as the foreign record.

Decision:
The suite environment drops `PYTHONWARNINGS`, `PYTHONOPTIMIZE`,
`PYTHONBREAKPOINT`, `PYTHONPYCACHEPREFIX`, `PYTHONDEBUG`, `PYTHONDEVMODE`,
`PYTHONPROFILEIMPORTTIME`, `PYTHONTRACEMALLOC`, `PYTHONFAULTHANDLER`,
`PYTHONMALLOC`, `PYTHONASYNCIODEBUG`, `PYTHONINTMAXSTRDIGITS`,
`PYTHONNODEBUGRANGES`, `PYTHONPLATLIBDIR`, `PYTHONCASEOK`,
`PYTHONHASHSEED`, `PYTHONVERBOSE`, and `PYTHONPERFSUPPORT`. The locale and
encoding variables stay, because the hostile-environment jobs exist to run
the suite under them. M111 holds the scrub.

Because:
A verdict must depend on the mutant and the suite, not on which warning
filter the shell that launched the coordinator happened to export.

Consequences:
An ambient warning filter or optimization level cannot flip a row. The
bytecode cache prefix cannot point outside the clone.

Revisit when:
The interpreter adds a flag that changes test semantics, which the
env-capture test will not see on its own.

## D-112: The suite's git reads only configuration the run wrote

Date: 2026-09-02
Status: Confirmed
Area: D-085, D-088, D-105, `run_suite`, real-git fixtures, M08

Context:
The suite's real-git fixtures run `git` with the worker's environment. The
challenger measured a `GIT_CONFIG_GLOBAL` file carrying `core.hooksPath`
running a hook from outside the clone during a fixture-shaped `git commit`,
and `core.fsmonitor` running a script during `git status`; the author
reproduced the hook. Round nineteen's WSL2 replay then showed the same
surface deciding a verdict: M08, which drops the `-c` filter overrides,
was caught on Windows, T540P, and the CI runners because each carries a
global git-lfs driver that stayed live, and survived on WSL2, which carries
none. With `GIT_CONFIG_GLOBAL` empty and the system configuration disabled,
the whole route suite passed under M08 on Windows. Nothing in the suite
held that path; the host did.

Decision:
Every git the suite runs reads an empty global configuration file the run
wrote, no system configuration, no system attributes, an empty template
directory, and an XDG directory holding no attributes or ignore file. The
`GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_*`, `GIT_CONFIG_VALUE_*`,
`GIT_CONFIG_PARAMETERS`, `GIT_CONFIG`, `GIT_DIR`, `GIT_WORK_TREE`,
`GIT_COMMON_DIR`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`,
`GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_CEILING_DIRECTORIES`,
`GIT_NAMESPACE`, `GIT_EXEC_PATH`, `GIT_SSH`, `GIT_SSH_COMMAND`,
`GIT_ASKPASS`, `GIT_EDITOR`, `GIT_SEQUENCE_EDITOR`, `GIT_PAGER`,
`GIT_PROXY_COMMAND`, `GIT_EXTERNAL_DIFF`, and `GIT_DIFF_OPTS` variables are
dropped. M112 holds the global-configuration pin.

Because:
The acquisition code under test already neutralizes hostile configuration
(R-034, R-054). The fixtures that build every real-git test did not, so a
host's configuration could execute code in a worker and could decide a
mutant's verdict.

Consequences:
M08 becomes inert on every host, which is what it always was on a host
without git-lfs; D-113 records what happens to the row. The suite runs
without any global git identity, which the CI runners already proved.

Revisit when:
A fixture needs a global git setting, which should then be written into
the run-owned file rather than inherited.

## D-113: M08 was held by the host, not by the suite

Date: 2026-09-02
Status: Confirmed
Area: D-085, D-088, D-094, D-112, M08, M114

Context:
M08 replaces `worktree_isolation = _filter_overrides(run)` with an empty
list. Measured on Windows at `39d745d`: with the host's git configuration,
`test_a_dirty_submodule_makes_the_snapshot_incomplete` fails under M08;
with an empty global configuration and the system configuration disabled,
that test, the five filter tests, and the whole route suite pass under it.
The catch on three hosts was the host's `filter.lfs.required=true` staying
live once the `-c` overrides were dropped. WSL2, with no driver, saw the
mutant survive.

The code explains it. In production the runner is the default one, so
when the `-c` overrides are dropped, `_live_filter_programs` reports every
driver live, `read_change_inputs` builds the D-088 environment runner,
verifies it, and runs the worktree comparison neutralized through it. The
result is the same; only the mechanism differs. A caller-injected runner,
which tests use, is denied that fallback by design, which is why an
injected-runner test noticed the difference only on hosts whose global
configuration declared a driver. On a git older than 2.31, dropping the
overrides turns a neutralization into a refusal, which is the safe
direction. Nothing in the suite held the `-c` path, and nothing needed to.

Decision:
M08 is superseded by M114, which disables the environment neutralization
itself by never setting `GIT_CONFIG_COUNT`. Measured on Windows at this
head: M114 fails `test_a_filter_name_containing_an_equals_cannot_run` and
`test_the_environment_form_expresses_a_name_dash_c_cannot`, both against
fixture-local drivers, so it is caught on every host. The `-c` overrides
stay as defense in depth, as D-094 kept the layout derivation.

Because:
A mutation row is evidence only while its replacement can falsify the
named guarantee. D-088 made the `-c` path's failure recoverable, so
dropping it falsifies nothing; the environment path is the guarantee, and
it had no row.

Consequences:
The matrix gains M114 and records M08 superseded. M08's Windows, T540P,
and CI catches are recorded as environmental, not as coverage. D-112
removes the global configuration that produced them.

Revisit when:
The environment neutralization is removed, or git drops numbered
configuration.

## D-114: Evidence files under design/routing keep LF on every checkout

Date: 2026-09-02
Status: Confirmed
Area: D-108, `.gitattributes`, evidence artifacts, `matrix.json`

Context:
`.gitattributes` scopes `text eol=lf` to `anti-dark-code/**`. The matrix
and the evidence artifacts under `design/routing/` carry no attribute, so a
default Windows clone rewrites their line endings on checkout while `git
status` stays clean, and any check that hashes the checkout disagrees with
the recorded blob digest. D-108 moved the walkthrough check to the blob; the
challenger found the missing attribute as the second root cause.

Decision:
`design/routing/**/*.json` is declared `text eol=lf`. Blob digests and
checkout digests then agree on every host.

Because:
An evidence file whose bytes depend on the reader's checkout settings is
harder to verify than it needs to be.

Consequences:
Existing clones re-normalize on the next checkout of those files.

Revisit when:
An evidence file needs CRLF, which none does.

## D-115: Every console field from the matrix passes through the renderer

Date: 2026-09-02
Status: Confirmed
Area: D-102, D-106, `replay()` console output, `matrix.json`

Context:
D-106 routed a broken row's error through `_terminal_safe_diagnostic` in
both modes and said no console line could carry a raw control character.
The challenger measured the other fields. `replay()` printed a row's id,
name, replacement id, and verdict, and the summary's survivor ids, raw
from `matrix.json`. A row whose name carried a newline and an escape
printed a forged coloured summary line in both modes; the author
reproduced it. Serial replay reads the matrix from the working tree, so an
uncommitted row reaches the console directly; parallel replay needs the
row committed.

Decision:
Every field `replay()` prints that originates in `matrix.json` passes
through the renderer: ids, names, replacement ids, verdicts, and the ids
in the summary. The JSON report keeps the raw values. M113 holds the name
field, which is the one a forged line needs.

Because:
D-106's statement was wider than its code. The renderer is the boundary
between data and presentation, and a boundary that covers one field is not
one.

Consequences:
No console line carries a raw control character from any source, in either
mode. Reports are unchanged.

Revisit when:
Row output becomes structured fields rendered by a separate presentation
layer, as D-106 said.

## D-116: The harness line closes on a stopping rule, not on a quiet round

Date: 2026-09-02
Status: Open; owner decision
Area: SLICE-001 section 9, D-054, D-095 through D-115, the round robin,
`WALKTHROUGH-SLICE-001.md`

Context:
Rounds fourteen through twenty each began by reproducing the previous
round's numbers and each closed with four to six new decisions: D-080 to
D-084, D-085 to D-090, D-091 to D-094, D-095 to D-099, D-100 to D-104,
D-105 to D-110, D-111 to D-115. The count is flat. What moved is the
subject. Through round sixteen the decisions concerned the router and its
inputs. From round seventeen, sixteen of nineteen decisions concern the
replay harness, its evidence files, or its console; the three that touch
the router, D-097, D-100, and D-107, are one question about where
verification authority lives, and D-107 has been with the owner since
round nineteen. The harness findings have one shape: a channel through
which the coordinator's host reaches a worker. Rootdir (D-098), pytest
environment (D-101), user site and configuration files (D-105),
interpreter flags (D-111), git configuration (D-112). After D-112 the
channels the harness has not closed are the ones it cannot write: `PATH`,
which chooses the interpreter and the git binary, that interpreter's
system site-packages, and the operating system. Pinning those means
choosing binaries, which is an environment the owner provides, not a
repair the harness can make.

The owner walkthrough has been the last box since round fourteen. Agents
have passed it on fresh clones four times, in rounds sixteen, eighteen,
nineteen, and twenty. Passing it again is not evidence the owner has seen
it.

Decision:
Proposed to the owner, who decides. The harness line is closed when all
three hold at one commit:

1. A full serial `--write` on Windows and on Linux each report zero not
   caught, and every active row carries an exact-identity record from
   both hosts at that commit.
2. A fresh-context challenger at that commit finds nothing except
   channels the harness cannot own, or reproductions of closed decisions.
3. The owner walkthrough passes literally on a fresh default clone of
   that commit.

When the three hold, no further agent round opens. The remaining work is
the owner's: run the walkthrough, decide D-107 and this rule, mark
SLICE-001, and land the stack. The line reopens only when one of these
fires: a verdict for a real mutant differs between hosts at one commit
without a code change; the walkthrough fails on a fresh default clone; or
the router or the harness code changes, in which case one round verifies
the change and stops.

Because:
A round finds what it goes looking for, and seven rounds at four to six
findings each show that a quiet round will not arrive on its own. An
endpoint has to be a condition at one commit that anyone can check, not a
feeling that the findings have dried up.

Consequences:
Round twenty reports whether the three conditions hold at its final head.
This decision approves no routing rule, does not enable selective
execution, and does not mark SLICE-001 Done; those remain the owner's.

Revisit when:
A reopen condition fires, or the owner replaces the rule.
