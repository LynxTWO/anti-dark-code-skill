# Assurance Router Engineering Document (EDD)

Version: 1.0. Date: 2026-08-30. Authors: Daniel Boyd, Claude Opus 5, Codex. Status: Audited.
Companion documents: ARCHITECTURE.md, DECISION-LOG.md, SLICE-001-route-shadow.md.

Rules for placing pieces. Where a section depends on an architecture decision, it references the ADD section number instead of restating it.

---

## 1. One-Page Overview

- **Build philosophy in one line:** the router establishes a minimum, judgment may raise it, and only a reviewed rule backed by deterministic evidence may permit less work.
- **The three goals that outrank the rest:** correctness of the monotonic property, auditability of every omission, and honest measurement before any shortcut is allowed to govern anything.
- **The verification standard:** tests, logs, diffs, and observed behavior. An agent saying the route was right is not evidence. Shadow mode exists because this subsystem cannot be trusted on its own account.
- **Current build boundary:** SLICE-002, the shadow evidence campaign defined in SLICE-001 section 12, per ADD section 15. SLICE-001 is `Done` as of 2026-09-02; no routing rule is approved and selective execution stays disabled until SLICE-002 produces the evidence.
- **Current gate:** M4 is implemented in round twelve. Candidate routes are shadow-only, real gate outcomes feed their comparator, and the human walkthrough remains before slice completion.

## 2. Engineering Principles

1. An unknown means the shortcut has not been earned. It does not mean the code is bad.
2. Combination is union and maximum. Never averaging, never subtraction. Thirty README lines cannot cancel one authentication schema change.
3. A skipped check is an explained decision with a stable reason code, never an absence.
4. The classifier does not grade itself. A change to routing must be judged by the previously trusted router.
5. Deterministic tooling establishes the minimum. Agent judgment and a human may raise it. A human may acknowledge that required evidence is still missing, but that acknowledgement does not lower the route or turn missing evidence into a pass.
6. Purity where it matters: Git acquisition is impure and read-only. Fact classification and route building are pure functions over the acquired snapshot, so they can be tested exhaustively without a repository.
7. No new runtime dependency. The hostile-environment matrix is the cost of every import.

## 3. System Goals

| Goal | Target | How measured |
|---|---|---|
| Correct | adding a changed file never lowers any route field | property test over generated fact sets and hints |
| Auditable | every omitted gate carries a reason code and matched rule id | receipt schema validation |
| Fast | acquisition under one second on a repository of a few hundred tracked files, warm | timed measurement, 2026-08-30. Warm: 0.34 to 0.38s here, 0.70 to 0.89s on a real 345-file repository. Cold is different and the goal does not hold there: a reviewer measured 3.30s cold on the same repository, which could not be reproduced here because a genuinely cold cache was unavailable, so that observation stands unrefuted. A synthetic 3000-file commit where every file changed is several seconds, for the reasons D-027 and D-037 record |
| Deterministic | identical facts produce byte-identical receipts regardless of input order | repeated-run hash comparison |
| Honest | routing misses are counted per route class, not in aggregate | shadow ledger |
| Tamper-evident | changed content, modes, index, submodules, policy, calibration, or gate inputs invalidate a receipt | staleness and concurrent-mutation tests |

## 4. Requirements Ledger

### 4.1 Confirmed requirements

| ID | Requirement | Acceptance test |
|---|---|---|
| R-001 | Adding a changed file never lowers any component of the route | given a route for facts F, when a fact is added, then level is not lower, set fields are supersets, boolean fields do not change from true to false, and `force_full` still dominates |
| R-002 | Identical facts produce byte-stable receipts regardless of input order | given the same facts shuffled, when routed, then the receipt hash is identical |
| R-003 | A path matching no reviewed rule blocks the fast path | given an unmapped path, when routed, then the route is full and the path is listed in unknowns |
| R-004 | `SKILL.md` and `references/**` are never classified as inert documentation | given a change to `SKILL.md`, when routed, then policy validation obligations are required |
| R-005 | Routing code, routing policy, gate configuration, CI, and shared test helpers force the full route | given a change to any such path, when routed, then `force_full` is true |
| R-006 | Renames, deletions, mode-only changes, staged, unstaged, and untracked changes are all represented as facts | given each change kind, when collected, then a fact exists with the correct kind |
| R-007 | A missing or unreliable merge base blocks shortcuts | given an unreachable base, when routed, then the route is full with reason code recorded |
| R-008 | A changed worktree invalidates an existing receipt | given a receipt, when any tracked file changes, then verification returns stale and the runner exits 2 |
| R-009 | Routing policy and gate definition changes invalidate receipts | given a receipt, when policy or gate hash changes, then verification returns stale |
| R-010 | Multiple matching rules union their requirements | given two rules matching one change, when routed, then requirements are the union |
| R-011 | Agent hints may raise but never lower requirements | given a hint, when routed, then the result is a superset of the hint-free route |
| R-012 | Every required obligation has at least one approved selected gate | given a route, when gates are selected, then no obligation is uncovered, or the route is full |
| R-013 | `--level` may raise above the computed route but never lower it | given route level 1, when `--level 0`, then exit 2 with the route minimum named |
| R-014 | The fact collector does not drop `.agents/skills/` or `.anti-dark-code/` paths | given a change to `calibration/gates.json`, when collected, then a fact exists for it |
| R-015 | Rules match one fact at a time with positive predicates only | given a previously matched fact, when any other fact is added, then the first match and its requirements remain present |
| R-016 | Every capability obligation is bound in policy to one or more explicit gate ids | given a route, when policy validation runs, then each capability has a nonempty gate set and every named gate exists |
| R-017 | Receipt freshness binds content, modes, index entries, and symlink targets rather than status text alone, and refuses to certify a tree holding state it cannot bind | given a dirty file whose bytes change while its porcelain status stays the same, when verified, then the receipt is stale; given a tree containing a submodule, when verified, then the receipt is refused and names the unbindable path (D-072) |
| R-018 | Concurrent repository changes cannot produce accepted gate evidence | given a fresh receipt, when an input changes after preflight or during a gate, then that gate result is marked stale and cannot satisfy an obligation |
| R-019 | Git acquisition represents old and new rename or copy paths, mode-only and type changes, conflicts, staged, unstaged, untracked, and submodule changes | given each supported record, when acquired, then no routing-relevant path or status is lost; unsupported records block selective routing |
| R-020 | Agent hints are additive data only | given any valid hint, when applied, then it cannot change facts, rule matches, comparison base, existing set members, a true boolean to false, or the computed minimum level downward |
| R-021 | Self-grading inputs force the canonical full route | given a change to router code or schema, capability catalog, gates, CI, installer or distribution controls, Git interpretation files, router tests, shared test support, `SKILL.md`, or the routing-owning pass references, then `force_full` is true |
| R-022 | The canonical full route is independent of changed-file applicability filters | given `force_full`, when gates are selected, then the validated full recipe runs at Level 3 and no selected gate is removed by `include_globs` |
| R-023 | Receipt identity is deterministic while observational metadata is not authoritative | given identical snapshots, policies, gates, calibration, and hints in any input order, then authoritative receipt bytes and hash match; timestamps do not enter that hash |
| R-024 | A malformed, truncated, or unrecognised git record is reported, never silently dropped | given garbage, a truncated header, a rename missing its destination, or an unknown status letter, when parsed, then a stable reason code is returned and the snapshot is not complete |
| R-025 | Staged and unstaged records are acquired by separate comparisons | given a staged change, when acquired, then it appears once as staged and not also as unstaged |
| R-026 | A path matching several classifier entries emits a fact for each | given a path matched by a broad entry and a specific entry, when classified, then both readings are present |
| R-027 | Git acquisition does not execute repository-configured code or update repository state | given a repository-local filesystem monitor that writes a sentinel, when every acquisition command runs, then no sentinel is written and the index and worktree identities are unchanged |
| R-028 | Snapshot completeness requires valid transport framing and a valid base identity | given a missing terminal NUL, an invalid raw header field, malformed untracked output, or an empty successful merge-base result, when acquired, then a stable problem code is present and `complete` is false |
| R-029 | Copy provenance and every mode transition survive real Git acquisition | given a copy from an unchanged source or a content-plus-mode change, when acquired, then the copy has both paths and the mode transition remains explicit |
| R-030 | Every `ChangeInput`, classifier entry, and emitted fact uses only closed enum values | given one invalid value for each enum field, when classification runs, then it raises a policy or input error and emits no fact |
| R-031 | Canonical fact order is independent of input order and Python hash seed | given duplicate inputs and two copies with one source, when classified under several hash seeds, then facts are deduplicated and every serialized field has the same order |
| R-032 | Classifier glob semantics are independent of the host operating system | given a Git path and pattern that differ only by case, when classified on Linux, macOS, and Windows, then every host returns the same result |
| R-033 | Capability count has one count-derived contract in scripts and tests | given a future catalog size, when runtime and contiguity checks run, then both derive the total from `CAPABILITY_COUNT`; V21 and V22 identity tests remain explicit |
| R-034 | Git acquisition blocks every known configured program and lazy fetch | given clean and process filters, a text converter, filesystem monitor, external diff command, and missing promisor object, when acquisition runs, then no sentinel appears, no fetch occurs, and repository identity is unchanged |
| R-035 | A loaded policy is immutable and cannot be bypassed | given a loaded policy, when every source container is mutated, then routing is unchanged; given a raw mapping, when `build_route` is called, then it refuses the value |
| R-036 | Policy match values and the full recipe satisfy their complete contracts | given a wrong match container, invalid predicate member, non-boolean mode flag, Level 0 full recipe, or incomplete canonical full set, when loading runs, then `PolicyError` is raised |
| R-037 | Raw parsing enforces Git status, score, mode, null-side, and object-width semantics | given each invalid combination and each boundary score, when parsed, then only documented records are accepted and every rejection has a stable problem code |
| R-038 | Route collections have canonical observable order | given facts in every order, when routed, then set serialization, obligation iteration, route representation, and later receipt bytes agree |
| R-039 | Hints contain only validated requirement additions | given an unknown key, pass, capability, gate, path, or reason, when hint validation runs, then it fails; computed evidence fields cannot be supplied by a hint |
| R-040 | Git path classification is case-sensitive without rewriting literal characters | given simulated host case folding and a POSIX filename containing backslash, when classified, then case and literal-character results stay in Git path semantics |
| R-041 | Every route predicate and retained hint evidence has a mutation guard | given deletion of path or mode matching, or replacement of unknown and unmapped unions with assignment, when tests run, then at least one focused test fails |
| R-042 | Policy loading has no internal capability catalog default | given a catalog extended by one id, when policy loading runs, then the caller-supplied catalog accepts it without another code edit; omitting catalog ids is an error |
| R-043 | Lazy fetch is disabled rather than tuned | given a blobless partial clone whose rename comparison needs a missing blob, when acquisition runs, then no fetch child starts, no object appears, and the snapshot is incomplete |
| R-044 | The acquisition boundary detects byte changes that preserve metadata | given a tracked file changed after its comparison with size and mtime restored, when the after-check runs, then `ADC-ROUTE-BOUNDARY-VIOLATED` is present and the snapshot is incomplete |
| R-045 | Policy authority proves loader provenance and the canonical full set | given a directly constructed policy record or a full recipe missing one canonical pass, capability, or gate, when validation or routing runs, then it is rejected |
| R-046 | Raw grammar is consistent across statuses and the repository object format | given a missing C or R score, an invalid status side, or mixed object widths across records, when parsed, then the payload is malformed and the snapshot is incomplete |
| R-047 | Hints preserve types and approved obligation bindings | given an out-of-range level, non-boolean flag, cross-capability gate pair, or proposed-only pair, when hint validation runs, then `HintError` is raised |
| R-048 | Route output is deeply immutable and full-recipe fields have discriminating mutation guards | given a Route built from a plain mapping or a mapping proxy backed by mutable data, when the caller mutates any source or nested field, then the Route cannot change; given deletion of one recipe field or reason, when tests run, then at least one focused test fails |
| R-049 | Policy authority cannot survive changed fields or an omitted canonical full-set input | given a loaded policy copied with changed authority fields, or a load without the canonical full set, when routing or loading runs, then no selective route is produced |
| R-050 | The closing acquisition boundary detects index, linked-worktree index, hard-link, and symlink replacement | given each replacement while weaker metadata is held constant, when acquisition closes, then the snapshot is incomplete |
| R-051 | One repository object format and real conflict grammar govern every acquisition source | given committed, staged, worktree, and conflict records, when acquired, then valid records survive and a cross-source width mismatch blocks |
| R-052 | Route immutability holds for direct, replaced, copied, built, and hinted values | given every construction path, when source or nested authority data is mutated, then the Route does not change |
| R-053 | Every stored authority mutation is replayable and caught by its configured suite | given each active row, when replay applies it alone, then its suite fails and the source is restored; a superseded row names its replacement |
| R-054 | Real configured programs and a real missing promisor object cannot execute or fetch during acquisition | given global filters and a blobless clone missing a required blob, when acquisition runs, then no program or lazy fetch starts |
| R-055 | Cost evidence names time, byte units, storage sharing, and represented state | given a cost record, when it is used for an architecture decision, then its command, repeated wall times, logical and allocated byte units, sharing mode, and represented state are explicit |
| R-056 | The tool's own run store is never a change the router must route | given a clean tree, when a receipt is written, then no emitted fact's path lies under `.anti-dark-code/`, and a real change under `.anti-dark-code/calibration/` is still collected |
| R-057 | Every routing rule names at least one obligation | given a rule with no obligations, when the policy loads, then it is refused, so no matched rule can select an empty gate set |
| R-058 | A shadow record is evidence only when every canonical gate decided, and its class follows the rules' terms and the router | given outcomes missing a gate or carrying an undecided one, when a record is built, then it is not measurable and carries no verdict; given two policies differing only in prose, then the class key is the same, and given a different router, then it is not |
| R-059 | The shadow measurement is evidence, never a gate, and a gate no CI job carries is unresolved | given the workflow, then the shadow job is absent from the required aggregator's needs; given a jobs payload in which a mapped job was renamed, then that gate reads unresolved and the record is not measurable |
| R-060 | A backfilled record replays today's router over a historical change set and says so | given a merge and its run, when backfilled, then the record carries provenance backfill and the class key of today's rules; given a merge with no run, then it is recorded as not measurable rather than dropped |
| R-061 | A backfilled record grades a pull request's own run attempts, never the merge that survived them | given a merged pull request on a merge-commit history with several run attempts, one failing an omitted gate, when backfilled, then one record exists per head and attempt, each with a non-empty change set against the first parent of the landing commit, each says its base was reconstructed, and the failing attempt is a miss |
| R-062 | Routing markdown a gate reads is verification authority in this repository | given a change to a top-level `design/routing/*.md` file alone, or to one below it, when routed under the repository calibration, then a verification-authority fact is emitted and the route forces full |
| R-063 | The criterion counts pull requests, and a miss on any attempt is the class's miss | given one pull request with many clean records, when the summary counts, then N advances by one; given one miss among them, then the class has a miss |

### 4.2 Assumed requirements

| ID | Assumption | How it gets verified |
|---|---|---|
| A-001 | Explicit gate ids are sufficient for the first policy, so coverage metadata can wait | build the first policy and check every obligation resolves to a gate |
| A-002 | Route computation stays under one second at this repository size | timed test in the suite |
| A-003 | Shadow comparison against the existing full run is enough to detect misses | count misses per route class over real changes |

### 4.3 Open questions

| ID | Question | Blocks what | Close by |
|---|---|---|---|
| Q-002 | Does the CI trusted-base pattern from `proposal-intake.yml` transfer to routing without modification | selective CI execution, out of slice 1 | read both existing workflows when selective CI is scheduled |
| Q-003 | Where do routing-miss tallies live long term, `.anti-dark-code/runs/` or `metrics/` | shadow reporting beyond slice 1 | after the first thirty shadow comparisons |

**Closed Q-001.** D-016 records the result. Ten proposed obligation names map without distortion to V01, V07, V08, V09, V12, V14, V17, and V18. Two methods are absent and need new ids: affected-unit testing (V21) and input fuzz testing (V22). `affected-unit` is not V11 because V11 selects affected checks but does not execute their assertions. `fuzz` is not V15 because V15 perturbs the environment while fuzzing perturbs input values. Distribution validation is V08 applied to a generated package boundary. Cross-platform and hostile-environment checks are V12 adaptations.

**Ledger rules.** Every requirement has an acceptance test stated as an observable condition. The catalog extension in SLICE-001 milestone M1 is limited to V21 and V22. Q-002 and Q-003 remain open and out of the first implementation slice.

## 5. Data Model

```
ENTITY: ChangeInput
Purpose: one status-aware record acquired from git before pure classification
Owned by: Git change reader
Fields:
  path              string, required
  old_path          string, required for rename or copy
  change_kind       enum add|modify|delete|rename|copy|mode|type-change|unmerged|unknown, required
  source            enum committed|staged|unstaged|untracked, required
  old_mode/new_mode strings, optional
  old_object/new_object strings, optional git object ids
  content_identity  string, required when bytes or a symlink target exist
  submodule_state   object, required for a gitlink or dirty submodule
Relations: several ChangeInputs may describe one path when index and worktree state differ.
Deletion rule: inputs are derived. The receipt retains their canonical identity and the facts derived from them.
```

```
ENTITY: RawParse
Purpose: the rows one git payload yielded, plus why anything else did not parse
Owned by: Git change reader
Fields:
  inputs     tuple of ChangeInput, required, possibly empty
  problems   tuple of stable reason codes, required, possibly empty
Relations: one RawParse per git payload. Problems union into ChangeSnapshot.
Deletion rule: derived, never stored beyond the snapshot that absorbs it.
```

```
ENTITY: ChangeFact
Purpose: one dimensioned statement about one changed path
Owned by: fact collector
Fields:
  path            string, required
  related_path    string, optional, used to link both sides of rename and copy records
  change_kind     enum add|modify|delete|rename|copy|mode|type-change|unmerged|unknown, required
  source          enum committed|staged|unstaged|untracked, required
  surface         enum docs|product|tests|schema|ci|release|skill-policy|site, required
  effect          enum prose|behavior|public-contract|persisted-state|verification-authority, required
  breadth         enum leaf|package|runtime|cross-runtime|repository, required
  sensitivity     enum normal|auth|privacy|billing|deletion|crypto|release, required
  confidence      enum verified|inferred|unknown, required
Relations: many ChangeFacts per routed change. One path emits one fact per
  matching classifier entry, and a rename or copy classifies both of its paths.
  A path matching no entry emits exactly one fact with confidence unknown.
Deletion rule: facts are derived, never stored beyond the receipt that quotes them.
```

**Why one fact per matching entry.** Classification does not stop at the first
matching glob. A broad entry such as `*.md` would otherwise mask a specific one
such as `anti-dark-code/SKILL.md`, and the authority reading would be gone
before any rule could see it. Keeping every match means each rule that would
fire does fire, and the monotonic union decides the rest. It also avoids
inventing a precedence order among sensitivities like `auth` and `billing`,
which are not ordered. See D-024.

```
ENTITY: Rule
Purpose: one reviewed mapping from matched facts to required work
Owned by: routing policy
Fields:
  id                string, required, unique
  match             object of positive path globs and single-fact predicates, required
  requires          object: passes, minimum_level, obligations,
                    independent_review, force_full
  obligations       object mapping capability id to a nonempty set of explicit gate ids
  review_status     enum proposed|approved, required
Relations: a Route names every Rule id it matched.
Deletion rule: removing a rule changes the policy hash and invalidates every receipt.
```

```
ENTITY: ValidatedPolicy
Purpose: immutable proof that classifier, rule, full-recipe, gate, pass, and capability contracts passed
Owned by: routing policy loader
Fields:
  classifier        canonical immutable classifier entries
  full_recipe       Level 3 recipe checked against the caller's canonical full set
  rules             canonical immutable rules
  capability_ids    caller-supplied catalog ids used during validation
Relations: build_route accepts this type and no raw policy mapping.
Deletion rule: derived from the hashed repository policy and rebuilt when that file or a bound catalog changes.
```

```
ENTITY: Receipt
Purpose: the auditable record binding one route to one worktree state
Owned by: receipt writer
Fields:
  run_id, repo_binding_identity, base_identity, head_identity,
  index identity, staged/unstaged/untracked content and mode identities,
  symlink targets and submodule state, changed files with status,
  routing_policy_sha256, gate_configuration_sha256, calibration_hashes,
  matched_rule_ids, emitted_facts, selected_passes, capability_to_gate_ids,
  selected_gate_ids,
  omitted_gates with reason codes, unmapped_paths, unknowns,
  independent_review_required, independent_review_recorded,
  force_full, operator_escalation with reason
Deletion rule: receipts are local run artifacts under `.anti-dark-code/runs/`, safe to delete.
```

**Model rules.**

- Identifiers are stable strings. Reason codes follow the existing `ADC-` prefix convention, for example `ADC-SKIP-004`.
- Every authoritative array is sorted by a documented canonical key before hashing. `normalized_json_hash` stabilizes object-key order but does not sort arrays.
- `run_id` is derived from the authoritative receipt hash. Timestamps and display-only environment details live outside that hash and cannot change routing authority.
- Receipt freshness uses object ids where git already has them and hashes current bytes, executable modes, and symlink targets where it does not. A porcelain-status digest is not sufficient because different dirty bytes can produce identical status text.
- The gate runner reads the receipt once, verifies that exact object, and carries its immutable authoritative route and verified worktree identity to execution. Every pre-gate identity must equal the verified identity, and every post-gate identity must equal its pre-gate identity; either mismatch preserves diagnostic output but cannot satisfy a capability.
- Enum values are closed sets. An unrecognized value is an error, not a passthrough.
- Canonical `ChangeFact` order includes `related_path` and every other serialized field after exact duplicate facts are removed.
- Git directory boundaries use forward slashes and classifier matching is case-sensitive on every host. The collector does not rewrite literal backslash characters.
- `ValidatedPolicy` owns deeply immutable nested values. A shallow dictionary copy is not a validated artifact.
- Obligation capability keys and every nested gate collection have canonical order before display or hashing.

## 6. Permissions and Access Model

- **Roles:** deterministic router, implementing agent, reviewing human.
- **Access matrix:**

| Role | Route minimum | Route maximum | Recorded exception |
|---|---|---|---|
| Deterministic router | establishes | establishes | none |
| Implementing agent | may raise | may raise | none |
| Reviewing human | may raise | may raise | may acknowledge missing evidence, but may not lower the route |

- **Enforcement point:** `build_route` is the single place requirements combine. Nothing downstream may reduce a route.
- **Admin surface:** there is no downgrade path in the router or receipt. An operator may run more work. If required evidence cannot be produced, the receipt remains incomplete and records the reason without authorizing selective execution.

## 7. Security Requirements

Tier 1 baseline applies. The relevant additions for this subsystem:

- [ ] The router never executes repository code. Git acquisition neutralizes filesystem monitors, content filters, external diff commands, text converters, and lazy fetch, then proves each boundary with a real hostile repository.
- [ ] Receipt contents pass through the existing redaction helpers before being printed.
- [ ] A receipt is data, not an instruction. Loading one never causes execution by itself.
- [ ] Policy files are validated against a schema before use. An invalid policy blocks routing and produces no selective receipt.

**Risk-flag depth, verification authority.** This subsystem can cause less verification to run. That forces full depth on three things: the self-grading rule (ADD guardrail 3), receipt integrity (R-008, R-009), and rollout discipline (section 11 shadow mode).

## 8. Privacy and Data Handling

- **Personal data inventory:** none. Receipts contain repository paths and hashes.
- **Retention:** local run artifacts under `.anti-dark-code/runs/`, owned by the repository, ignorable.
- **Sharing:** none. Receipts do not leave the machine unless the repository chooses to commit one.

## 9. Coding Standards

- **Language and typing:** Python 3.12+, type hints on every public function, standard library only.
- **Naming:** existing `adc.py` conventions. Functions are verbs, records are nouns.
- **Functions:** `read_change_inputs` owns Git I/O. `collect_change_facts` and `build_route` are pure and take passed data only.
- **Git records:** use NUL-delimited output and validate its framing. Do not parse human-formatted status text. Preserve both paths for rename and copy, consider unchanged copy sources, and preserve every mode transition even when content also changed.
- **Errors:** fail closed. A known unmapped fact or unreachable base produces the canonical full route. Unreadable Git output, an invalid policy, or an invalid full recipe exits 2 and produces no receipt. Never a silent default.
- **Logging:** one compact route summary line, matching the existing gate plan output style.
- **Comments:** say why. The monotonic union deserves a comment explaining what would break without it.
- **User-facing text:** reason codes are identifiers with a separate human sentence, so the code stays stable if the wording changes.
- **AI-generated code:** held to every rule above, and specifically excluded from grading its own routing changes.

## 10. Repository Organization

- **Router code:** the CLI adapter lives in `anti-dark-code/scripts/adc.py`. The pure router and status-aware Git reader live in `anti-dark-code/scripts/adc_route.py` from the start, so routing changes have one explicit self-grading surface beside `adc_efficiency.py` and `work_receipt.py`.
- **Policy template:** `anti-dark-code/assets/templates/calibration/routing-policy.json`.
- **Installed copy:** `.agents/skills/anti-dark-code/calibration/routing-policy.json`, repository owned.
- **Tests:** `anti-dark-code/tests/test_route.py`, plus the current shared helpers in `test_adc.py`. Any later `conftest.py` or shared fixture module joins the self-grading set automatically.
- **Design documents:** `design/routing/`. Note that `docs/` in this repository is the published website, not inert documentation.

## 11. Testing and Verification

**The standard.** A claim that a route is correct requires a passing test, a recorded shadow comparison, or an observed receipt. The router's own summary is a claim.

**Test types.** Unit tests on the pure functions, property tests on monotonicity, integration tests on receipt staleness, and a mutation or revert test proving that weakening a hard escalator fails the suite.

**Verification ledger.**

| Requirement | Check | Evidence lives |
|---|---|---|
| R-001 | property test, generated fact sets | `test_route.py` |
| R-002 | shuffled-input hash equality | `test_route.py` |
| R-003 | unmapped path forces full | `test_route.py` |
| R-004 | `SKILL.md` classification test | `test_route.py` |
| R-005 | Every self-grading path class routed through the real classifier with the rules approved, plus source and managed-install probes, an ordinary-path counterexample, and a load-time refusal | `SelfGradingAuthorityTests` in `test_route.py`; D-071, D-078, D-082; M68, M90, M92 |
| R-006 | change-kind coverage test | `test_route.py` |
| R-007 | unreachable base test | `test_route.py` |
| R-008 | worktree mutation invalidates receipt | `test_route.py` |
| R-009 | policy and gate hash change invalidates receipt | `test_route.py` |
| R-010 | two-rule union test | `test_route.py` |
| R-011 | hint monotonicity test | `test_route.py` |
| R-012 | obligation coverage test | `test_route.py` |
| R-013 | A routed gate command rejects a lower level and accepts an equal or higher level | `RouteLevelCliTests` and `CanonicalFullTests::test_level_may_raise_the_route_minimum`; exact nodes in `requirement-evidence.json` |
| R-014 | `calibration/gates.json` produces a fact | `test_route.py` |
| R-015 | generated positive-match monotonicity test | `test_route.py` |
| R-016 | policy schema and missing, duplicate, unknown, disabled, or unapproved gate tests | `test_route.py` |
| R-017 | Bytes, index, and symlink checks, plus a real submodule fixture proving the receipt is refused and an ordinary tree still verifies fresh | `SubmoduleContractTests` in `test_route.py`; D-072 |
| R-018 | One receipt read is verified before selection; its identity, validated policy, and gate configuration remain one in-memory authority context; two identities are compared before and after each real gate, the receipt-comparable one and a timestamp-keeping lifecycle one, so a change the gate itself restored is still caught; movement records `stale`, stops even under `--keep-going`, and satisfies no obligation | `GateLifecycleTests`, `StaleReceiptCliTests`, and `ReceiptIntegrityCliTests`; exact nodes in `requirement-evidence.json`; D-075, D-076 and D-077 |
| R-019 | Rename, copy, mode, type, conflict, and source-union checks, plus a gitlink record that parses and withdraws snapshot completeness | `RawParserTests` and `SubmoduleContractTests` in `test_route.py`; D-072 |
| R-020 | generated hint monotonicity over every route field | `test_route.py` |
| R-021 | The eleven self-grading path classes, in source and managed installed layouts, measured against the installed policy with every rule approved | `SelfGradingAuthorityTests` in `test_route.py`; exact nodes in `requirement-evidence.json`; D-071, D-082 |
| R-022 | Force-full execution takes exactly the canonical set, bypasses changed-file applicability globs, and refuses candidate selection at the executable boundary | `CanonicalFullTests::test_force_full_runs_the_canonical_set_despite_include_globs` and `CandidateRouteTests::test_a_candidate_selection_cannot_remove_a_gate`; exact nodes in `requirement-evidence.json` |
| R-023 | canonical order and timestamp-independence tests | `test_route.py` |
| R-024 | garbage, truncated header, orphan rename, unknown status letter | `test_route.py` |
| R-025 | real-repository staged change is not also unstaged | `test_route.py` |
| R-026 | broad glob cannot mask a specific glob | `test_route.py` |
| R-027 | repository-local filesystem-monitor sentinel remains absent | `test_route.py` |
| R-028 | terminal NUL, raw field shape, untracked framing, and nonempty-base table | `test_route.py` |
| R-029 | real unchanged-source copy and content-plus-mode repository cases | `test_route.py` |
| R-030 | invalid-value table over every input, classifier, and fact enum | `test_route.py` |
| R-031 | duplicate collapse and cross-seed full-field ordering | `test_route.py` |
| R-032 | cross-platform case-collision fixture | `test_route.py` |
| R-033 | contiguity test derives its bound from `CAPABILITY_COUNT` | `test_route.py` |
| R-034 | real filter, helper, repository-identity, and offline partial-clone table | `test_route.py` |
| R-035 | post-load nested-mutation table and raw-policy rejection | `test_route.py` |
| R-036 | complete match-value and full-recipe validation tables | `test_route.py` |
| R-037 | semantic raw-record grammar table | `test_route.py` |
| R-038 | order-sensitive route representation and serialization test | `test_route.py` |
| R-039 | invalid and computed-evidence hint table | `test_route.py` |
| R-040 | simulated case-folding test plus POSIX backslash repository case | `test_route.py` |
| R-041 | four focused mutation or revert tests | `test_route.py` |
| R-042 | mandatory catalog input and future-id test | `test_route.py` |
| R-043 | real blobless partial clone with missing rename blob and fetch trace | `test_route.py` |
| R-044 | same-size, same-mtime tracked rewrite after its worktree comparison | `test_route.py` |
| R-045 | direct record construction and one-at-a-time canonical full-set omissions | `test_route.py` |
| R-046 | status-side, required-score, and payload-wide object-format table | `test_route.py` |
| R-047 | typed hint values and approved capability-gate pair table | `test_route.py` |
| R-048 | nested Route mutation attempts and focused recipe-field mutations | `test_route.py` |
| R-049 | mandatory canonical full-set input plus changed-field policy-copy rejection | `test_route.py` |
| R-050 | index-byte, linked-worktree index, hard-link, and symlink boundary mutation table | `test_route.py` |
| R-051 | repository-wide object format plus real source-specific conflict grammar | named tests in `requirement-evidence.json`; M47 is caught and the plain raw conflict form is accepted |
| R-052 | direct, replaced, built, copied, and hinted Route immutability table | named tests in `requirement-evidence.json`; mutable proxy backing is copied |
| R-053 | data-driven replay of all 126 stored mutations | `mutants/`; 120 active and 6 superseded under D-094 and D-113. Round Twenty-One's two full serial `--write` replays at `fe350e9`, one on Windows and one on WSL2 Ubuntu, each processed all 126 rows with 0 not caught from a clean clone; their records were merged per platform, so every active row carries exact failed and skipped identities from both hosts at one commit (D-109); a read-only Windows parallel replay at the same head agrees with the Windows write row for row. M100 was re-anchored and M115 and M116 added under D-118, M117 and M118 under D-119, M119 to M122 under D-120, and M123 to M126 under D-121; all thirteen carry records from both hosts. M37, M46, and M48 are `caught elsewhere` only because the exact Windows skipped node is the exact Linux failed node (D-104). Source restoration is hash-verified by D-068 |
| R-054 | real configured-program and missing-promisor-object tests | named tests in `requirement-evidence.json`; the blobless counterfactual proves the fixture reaches the network without the guard |
| R-055 | repeatable cost record with wall time, byte units, storage sharing, and represented state | D-047 review evidence, linked in `requirement-evidence.json` |
| R-056 | receipt-level check that the store's own ignore file is not a fact, plus a counterexample that a calibration change under the store still is | `test_route_cli.py` |
| R-057 | load-time refusal of a rule with no obligations, including one that forces full | `test_route.py` |
| R-058 | record-level status table over decided, absent, and undecided outcomes, plus class-key equality under prose edits and inequality under a router change, unit and end to end | `test_route.py`, `test_route_cli.py` |
| R-059 | workflow contract check on the required aggregator's needs and the shadow job's conditions, plus a jobs-payload table over renamed jobs, missing steps, failed legs, and cancelled legs | `test_route.py` |
| R-060 | backfill of a real merge in a fixture repository, and of a merge with no run | `test_route_cli.py` |
| R-061 | backfill of a fixture pull request with several run attempts, one failing | proposed under D-128; `test_route_cli.py` when M5 is rebuilt |
| R-062 | classifier check on a routing markdown change under the repository calibration, at both depths and on the canary's own filename, plus the glob spelling itself | `test_route.py`; M139 and M140 |
| R-063 | summary count over a pull request with many clean records, and with one miss | proposed under D-128; `test_route_cli.py` when M4 lands |

**Test data rule.** ChangeInputs and fact sets are constructed in code for pure-function tests. A small temporary Git repository exercises the impure reader on every platform. A NUL-delimited parser fixture covers path bytes and statuses the host filesystem cannot create.

**Shadow rollout.** For every real change: compute the proposed route, run the proposed targeted gates, still run the canonical full recipe at Level 3 without changed-file glob filtering, and record whether an omitted gate found anything. A `routing_miss` is targeted verification green while omitted verification failed. Results stay separated by route class. A hundred successful documentation routes do not validate the leaf-code route.

Using the rule of three for perspective: zero misses in 30 comparable routes still permits a miss rate near 10 percent, zero in 100 near 3 percent, zero in 300 near 1 percent. These are not certification thresholds. They prevent "it worked several times" from becoming false confidence.

## 12. Tool and Agent Discipline

Modes and standing rules per the core skill. The additions specific to this subsystem:

- The router is read-only. It never writes outside `.anti-dark-code/runs/`.
- An agent may supply hints. An agent may not edit a receipt.
- An agent working on the router may not use the router to judge its own change. That case forces the full route by ADD guardrail 3.
- Stop and ask before: adding a rule to the policy, changing an escalator, or enabling any selective execution.

**Self-grading path classes.** The first policy names these as hard full-route triggers, not ordinary reviewed rules:

- `anti-dark-code/scripts/adc.py`, `adc_route.py`, and any imported helper that can change collection, hashing, validation, selection, execution, installation, or distribution
- the routing policy schema and template, installed `routing-policy.json`, `gates.json`, `verification-capabilities.json`, `SOURCE-SCOPE.json`, and managed-install manifest logic
- `anti-dark-code/SKILL.md` and the routing-owning pass 00, 10, and 14 references
- `.github/workflows/**`, `.github/CODEOWNERS`, `.gitattributes`, `.gitignore`, `.gitmodules`, and any future Python project or lock file
- `test_route.py`, shared test fixtures such as a future `conftest.py`, and any mutation, fuzz, or validator harness used to grade a router change

The path table has one test per class. A newly authoritative config that is not represented makes the table test fail closed until reviewed. D-097 tried to infer script authority from an `adc*` name and a quoted-loader scan. A dynamically assembled `importlib` load bypassed that scan. D-100 replaces the inference: every Python file directly under `anti-dark-code/scripts/` is verification authority by location, and `test_every_shipped_script_is_authority_by_location` holds the rule. D-118 narrows the classifier that implements it to that directory in both spellings, `anti-dark-code/scripts/*.py` and `**/anti-dark-code/scripts/*.py`, after D-107 measured the earlier `**/scripts/*.py` entry reaching every nested scripts directory of an installing repository; `test_nested_consumer_scripts_are_product_code_and_shipped_scripts_are_authority` holds the width. D-119 adds a collision guard to both route builders: a path whose case-folded spelling would match a canonical authority glob that the path itself does not match forces the full recipe with `ADC-ROUTE-AUTHORITY-CASE-COLLISION`, because a case-insensitive checkout writes such a path over the authority it imitates; the classifier stays case-sensitive as R-040 states. D-120 widens the fold set to the policy's own verification-authority entries and force-full rule paths, normalizes compatibility forms and strips format characters, and treats an NTFS short-name component or a trailing dot or space as an ambiguous spelling that forces full with `ADC-ROUTE-AMBIGUOUS-SPELLING`. D-121 makes the fold set every approved rule's paths that require anything beyond the empty route, excludes proposed rules per D-022, and folds each glob once per route.

## 13. Observability

- **Always recorded:** the compact route line, the matched rule ids, every omission with its reason code, and every unknown.
- **Never recorded:** environment values, secrets, or anything the existing redaction helpers would strip from gate output.
- **The numbers reviewed on a schedule:** routing misses per route class, and the count of unmapped paths, which measures how much of the repository the policy actually describes.

## 14. Operations and Deployment

- **Environments and release path:** per ADD section 12.
- **CI gates:** the existing `Tests` aggregator continues to require every job. The router adds no CI job in slice 1.
- **Migrations:** none. A missing `routing-policy.json` means no calibrated policy and no selective receipt. The caller uses the documented full verification path.
- **Configuration:** the policy is repository-owned calibration. The template ships with the core. Its root `full_recipe` object is required, names the repository's canonical Level 3 passes, capability-to-gate bindings, and gate ids, and validates before any rule does.

**Aggregator note.** The `required` job in `tests.yml` refuses unless every dependency reports exactly `success`, so a skipped job fails it. Selective CI execution therefore requires rewriting that aggregator to consult the trusted route, and that edit is itself a verification-authority change that forces the full route. Selective CI is scheduled strictly after selective local execution for this reason.

## 15. Cost Discipline

- The purpose of this subsystem is reducing model tokens spent reloading passes that nothing invalidated, and reducing wall-clock spent on gates nothing touched.
- Cost is measured, not asserted. The existing efficiency receipt machinery is the model for how honest measurement looks here.
- Engineering time is a cost. The cheapest-gate optimizer is deliberately not built, because explicit recipes are easier to trust while the system is young.

## 16. Risk Register and Unknowns

| ID | Risk or unknown | Impact if wrong | Verification or mitigation | Status |
|---|---|---|---|---|
| U-001 | The router silently drops a path class and nobody notices | a real change routes as low risk | R-014 plus the unmapped-path counter | Open |
| U-002 | Shadow mode is enabled but nobody reads the misses | false confidence accumulates | misses reviewed per route class at every audit | Watching |
| U-003 | A rule is added that is broader than intended | requirements quietly loosen for a whole path class | rules carry `review_status`, and policy changes force the full route | Watching |
| U-004 | Q-001 resolves to fewer than five new capabilities | the catalog extension is smaller than planned | D-016 limits the extension to affected-unit testing and input fuzz testing | Resolved |
| U-005 | Provisional routing encourages an agent to under-plan before implementing | work starts too narrow | the final route supersedes, and slice 1 builds no provisional path | Watching |
| U-006 | A content change retains the same porcelain status and passes a status-only freshness check | stale evidence executes against different bytes | R-017 binds content and refuses unbindable state (D-072); R-018 consumes one verified receipt and holds every routed gate to its verified, pre-gate, and post-gate identities (D-075) | Resolved |
| U-007 | A capability and a gate appear in parallel arrays with no provable relationship | an unrelated gate is treated as evidence | R-016 policy-local capability-to-gate binding | Open |
| U-008 | A Git status or old rename path disappears before routing | a verification-authority change receives a lower route | R-019 status table and R-021 self-grading path table, both measured against the classifier with the rules approved (D-071) | Watching |
| U-009 | A Git configuration path starts a program or network request before routing | repository code runs at the trust boundary | R-034 hostile execution-family table | Open |
| U-010 | A mutable or malformed policy bypasses its one validation pass | an unreviewed rule produces a cheap route | R-035 and R-036 | Open |
| U-011 | Route equality hides order differences later preserved by a receipt | authoritative bytes depend on fact order | R-038 | Open |
| U-012 | A copied policy retains loader provenance after authority fields change | an unreviewed recipe produces a cheap route | R-049 and D-042 | Open |
| U-013 | Index bytes or path topology change while content metadata stays equal | acquisition reports a changed repository as complete | R-050 and D-043 | Open |
| U-014 | Per-call width inference or one status-side table disagrees with repository Git output | valid conflicts block or mixed repository identity is accepted | R-051 and D-044 | Open |
| U-015 | A future round removes an id from the `untraced` list and maps it to a test that collects but does not exercise the clause | the traceability gate reports progress that did not happen, which is exactly how D-070 arose | the guard cannot check this; `REVIEWED_UNTRACED` in `test_route.py` is a review record, and shrinking it needs a named reviewer (D-071) | Open |
| U-016 | A gate restores both the bytes and the timestamp of a file it changed while running | a gate result is accepted against content that is not in the tree | out of scope for before-and-after sampling; recorded in D-077 rather than claimed as covered | Open |
| U-017 | The candidate-route copies of the union lines M02 through M05 and M40 hold are not covered by a mutation row | a shadow measurement is wrong without anything noticing | shadow-only by construction: a CandidateRoute reaches neither receipt authority nor executable gate selection (D-087) | Open |
| U-018 | A repository configures a filter driver whose name defeats the `-c` override in a way `--get` also misreports | repository code runs during acquisition | the neutralization is verified against effective configuration rather than assumed, and the worktree comparison is skipped when any driver survives it (D-085) | Watching |
| A-001 to A-003 | see section 4.2 | | | Open |

## 17. Definition of Done

**Per change:**

- [ ] Builds clean, suite passes on the existing three-platform matrix.
- [ ] Tests exist for the change and pass. Evidence linked per section 11.
- [ ] No new runtime dependency.
- [ ] Documents and DECISION-LOG.md updated if any decision changed.
- [ ] Deliberate self-review pass against this checklist.

D-080 withdraws the retrospective per-change claim before `ea8733c` because the evidence cannot be reconstructed. The replacement is a qualified slice-level result. From `ea8733c` forward, the exact commit trailer `EDD-Checklist: satisfied` records item 5; each commit still names the host and workflow evidence that supports the other items.

**Per release:**

- [ ] The full suite, distribution check, and hostile-environment matrix pass.
- [ ] A mutation or revert test proves a weakened escalator fails the suite.
- [ ] Shadow results reviewed per route class.
- [ ] Human approval recorded. Final approval rests with Daniel Boyd.

## 18. Change Control

- Documents start at v0.1 Draft. A full audit pass bumps the version and marks it Audited.
- Status lifecycle per the Conductor vocabulary.
- No silent edits. Decision changes travel through DECISION-LOG.md.

---

*End of Engineering Document. Sections filled: 18 of 18. Unknowns carried: 11.*
