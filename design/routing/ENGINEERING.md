# Assurance Router Engineering Document (EDD)

Version: 0.1 Draft. Date: 2026-08-28. Authors: Daniel Boyd, Claude Opus 5. Status: In interview.
Companion documents: ARCHITECTURE.md, DECISION-LOG.md, SLICE-001-route-shadow.md.

Rules for placing pieces. Where a section depends on an architecture decision, it references the ADD section number instead of restating it.

---

## 1. One-Page Overview

- **Build philosophy in one line:** the router establishes a minimum, judgment may raise it, and only a reviewed rule backed by deterministic evidence may permit less work.
- **The three goals that outrank the rest:** correctness of the monotonic property, auditability of every omission, and honest measurement before any shortcut is allowed to govern anything.
- **The verification standard:** tests, logs, diffs, and observed behavior. An agent saying the route was right is not evidence. Shadow mode exists because this subsystem cannot be trusted on its own account.
- **Current build boundary:** SLICE-001, per ADD section 15.

## 2. Engineering Principles

1. An unknown means the shortcut has not been earned. It does not mean the code is bad.
2. Combination is union and maximum. Never averaging, never subtraction. Thirty README lines cannot cancel one authentication schema change.
3. A skipped check is an explained decision with a stable reason code, never an absence.
4. The classifier does not grade itself. A change to routing must be judged by the previously trusted router.
5. Deterministic tooling establishes the minimum. Agent judgment may raise it. Only a human may approve a recorded exception, and the reason lands in the receipt.
6. Purity where it matters: fact collection and route building are pure functions, so they can be tested exhaustively without a repository.
7. No new runtime dependency. The hostile-environment matrix is the cost of every import.

## 3. System Goals

| Goal | Target | How measured |
|---|---|---|
| Correct | adding a changed file never lowers a route | property test over generated fact sets |
| Auditable | every omitted gate carries a reason code and matched rule id | receipt schema validation |
| Fast | route computation under one second on this repository | timed test |
| Deterministic | identical facts produce byte-identical receipts regardless of input order | repeated-run hash comparison |
| Honest | routing misses are counted per route class, not in aggregate | shadow ledger |
| Tamper-evident | a changed worktree, policy, or gate set invalidates a receipt | staleness tests |

## 4. Requirements Ledger

### 4.1 Confirmed requirements

| ID | Requirement | Acceptance test |
|---|---|---|
| R-001 | Adding a changed file never lowers any component of the route | given a route for facts F, when a fact is added, then level, passes, and obligations are all supersets or equal |
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

### 4.2 Assumed requirements

| ID | Assumption | How it gets verified |
|---|---|---|
| A-001 | Explicit gate ids are sufficient for the first policy, so coverage metadata can wait | build the first policy and check every obligation resolves to a gate |
| A-002 | Route computation stays under one second at this repository size | timed test in the suite |
| A-003 | Shadow comparison against the existing full run is enough to detect misses | count misses per route class over real changes |

### 4.3 Open questions

| ID | Question | Blocks what | Close by |
|---|---|---|---|
| Q-001 | Which of the five new capability ids (V21 to V25) are genuinely distinct rather than variations of existing ones | the capability catalog extension | a spike reading all 20 existing capability definitions before writing V21 to V25 |
| Q-002 | Does the CI trusted-base pattern from `proposal-intake.yml` transfer to routing without modification | selective CI execution, out of slice 1 | read both existing workflows when selective CI is scheduled |
| Q-003 | Where do routing-miss tallies live long term, `.anti-dark-code/runs/` or `metrics/` | shadow reporting beyond slice 1 | after the first thirty shadow comparisons |

**Ledger rules.** Every requirement has an acceptance test stated as an observable condition. Q-001 must close before the catalog is extended, and its closing spike is scheduled in SLICE-001 milestone M1.

## 5. Data Model

```
ENTITY: ChangeFact
Purpose: one dimensioned statement about one changed path
Owned by: fact collector
Fields:
  path            string, required
  change_kind     enum add|modify|delete|rename|copy|mode, required
  old_path        string, optional, required when change_kind is rename or copy
  staged_state    enum staged|unstaged|untracked|committed, required
  surface         enum docs|product|tests|schema|ci|release|skill-policy|site, required
  effect          enum prose|behavior|public-contract|persisted-state|verification-authority, required
  breadth         enum leaf|package|runtime|cross-runtime|repository, required
  sensitivity     enum normal|auth|privacy|billing|deletion|crypto|release, required
  confidence      enum verified|inferred|unknown, required
Relations: many ChangeFacts per routed change. One path may emit several facts.
Deletion rule: facts are derived, never stored beyond the receipt that quotes them.
```

```
ENTITY: Rule
Purpose: one reviewed mapping from matched facts to required work
Owned by: routing policy
Fields:
  id                string, required, unique
  match             object of path globs and fact predicates, required
  requires          object: passes, minimum_level, gate_ids, obligations,
                    independent_review, force_full
  review_status     enum proposed|approved, required
Relations: a Route names every Rule id it matched.
Deletion rule: removing a rule changes the policy hash and invalidates every receipt.
```

```
ENTITY: Receipt
Purpose: the auditable record binding one route to one worktree state
Owned by: receipt writer
Fields:
  run_id, repo_binding_identity, base_identity, head_identity,
  staged/unstaged/untracked identity, changed_files with status,
  routing_policy_sha256, gate_configuration_sha256, calibration_hashes,
  matched_rule_ids, emitted_facts, selected_passes, selected_gate_ids,
  omitted_gates with reason codes, unmapped_paths, unknowns,
  independent_review_required, independent_review_recorded,
  force_full, operator_override with reason
Deletion rule: receipts are local run artifacts under `.anti-dark-code/runs/`, safe to delete.
```

**Model rules.**

- Identifiers are stable strings. Reason codes follow the existing `ADC-` prefix convention, for example `ADC-SKIP-004`.
- Every hash uses the existing `normalized_json_hash` helper so ordering never changes a digest.
- Enum values are closed sets. An unrecognized value is an error, not a passthrough.

## 6. Permissions and Access Model

- **Roles:** deterministic router, implementing agent, reviewing human.
- **Access matrix:**

| Role | Route minimum | Route maximum | Recorded exception |
|---|---|---|---|
| Deterministic router | establishes | establishes | none |
| Implementing agent | may raise | may raise | none |
| Reviewing human | may raise | may raise | may approve, with a reason in the receipt |

- **Enforcement point:** `build_route` is the single place requirements combine. Nothing downstream may reduce a route.
- **Admin surface:** the operator override is the only downgrade path, and it writes its reason into the receipt.

## 7. Security Requirements

Tier 1 baseline applies. The relevant additions for this subsystem:

- [ ] The router never executes repository code. It reads git metadata and JSON only.
- [ ] Receipt contents pass through the existing redaction helpers before being printed.
- [ ] A receipt is data, not an instruction. Loading one never causes execution by itself.
- [ ] Policy files are validated against a schema before use, and an invalid policy fails closed to the full route.

**Risk-flag depth, verification authority.** This subsystem can cause less verification to run. That forces full depth on three things: the self-grading rule (ADD guardrail 3), receipt integrity (R-008, R-009), and rollout discipline (section 11 shadow mode).

## 8. Privacy and Data Handling

- **Personal data inventory:** none. Receipts contain repository paths and hashes.
- **Retention:** local run artifacts under `.anti-dark-code/runs/`, owned by the repository, ignorable.
- **Sharing:** none. Receipts do not leave the machine unless the repository chooses to commit one.

## 9. Coding Standards

- **Language and typing:** Python 3.12+, type hints on every public function, standard library only.
- **Naming:** existing `adc.py` conventions. Functions are verbs, records are nouns.
- **Functions:** `collect_change_facts` and `build_route` are pure and take no I/O handles.
- **Errors:** fail closed. Any error path produces the full route or exits non-zero. Never a silent default.
- **Logging:** one compact route summary line, matching the existing gate plan output style.
- **Comments:** say why. The monotonic union deserves a comment explaining what would break without it.
- **User-facing text:** reason codes are identifiers with a separate human sentence, so the code stays stable if the wording changes.
- **AI-generated code:** held to every rule above, and specifically excluded from grading its own routing changes.

## 10. Repository Organization

- **Router code:** `anti-dark-code/scripts/adc.py`, alongside the existing subcommands, unless it grows past roughly four hundred lines, at which point it earns `adc_route.py` beside `adc_efficiency.py` and `work_receipt.py`.
- **Policy template:** `anti-dark-code/assets/templates/calibration/routing-policy.json`.
- **Installed copy:** `.agents/skills/anti-dark-code/calibration/routing-policy.json`, repository owned.
- **Tests:** `anti-dark-code/tests/test_route.py`, matching the existing per-area test file convention.
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
| R-005 | escalator table test, one case per path class | `test_route.py` |
| R-006 | change-kind coverage test | `test_route.py` |
| R-007 | unreachable base test | `test_route.py` |
| R-008 | worktree mutation invalidates receipt | `test_route.py` |
| R-009 | policy and gate hash change invalidates receipt | `test_route.py` |
| R-010 | two-rule union test | `test_route.py` |
| R-011 | hint monotonicity test | `test_route.py` |
| R-012 | obligation coverage test | `test_route.py` |
| R-013 | `--level` downgrade refused | `test_route.py` |
| R-014 | `calibration/gates.json` produces a fact | `test_route.py` |

**Test data rule.** Fact sets are constructed in code, not read from a fixture repository, so the pure functions stay testable on every platform without git.

**Shadow rollout.** For every real change: compute the proposed route, run the proposed targeted gates, still run the current full verification, and record whether an omitted gate found anything. A `routing_miss` is targeted verification green while omitted verification failed. Results stay separated by route class. A hundred successful documentation routes do not validate the leaf-code route.

Using the rule of three for perspective: zero misses in 30 comparable routes still permits a miss rate near 10 percent, zero in 100 near 3 percent, zero in 300 near 1 percent. These are not certification thresholds. They prevent "it worked several times" from becoming false confidence.

## 12. Tool and Agent Discipline

Modes and standing rules per the core skill. The additions specific to this subsystem:

- The router is read-only. It never writes outside `.anti-dark-code/runs/`.
- An agent may supply hints. An agent may not edit a receipt.
- An agent working on the router may not use the router to judge its own change. That case forces the full route by ADD guardrail 3.
- Stop and ask before: adding a rule to the policy, changing an escalator, or enabling any selective execution.

## 13. Observability

- **Always recorded:** the compact route line, the matched rule ids, every omission with its reason code, and every unknown.
- **Never recorded:** environment values, secrets, or anything the existing redaction helpers would strip from gate output.
- **The numbers reviewed on a schedule:** routing misses per route class, and the count of unmapped paths, which measures how much of the repository the policy actually describes.

## 14. Operations and Deployment

- **Environments and release path:** per ADD section 12.
- **CI gates:** the existing `Tests` aggregator continues to require every job. The router adds no CI job in slice 1.
- **Migrations:** none. A missing `routing-policy.json` means no calibrated policy, which means the full route.
- **Configuration:** the policy is repository-owned calibration. The template ships with the core.

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
| U-004 | Q-001 resolves to fewer than five new capabilities | the catalog extension is smaller than planned | close Q-001 before writing V21 to V25 | Open |
| U-005 | Provisional routing encourages an agent to under-plan before implementing | work starts too narrow | the final route supersedes, and slice 1 builds no provisional path | Watching |
| A-001 to A-003 | see section 4.2 | | | Open |

## 17. Definition of Done

**Per change:**

- [ ] Builds clean, suite passes on the existing three-platform matrix.
- [ ] Tests exist for the change and pass. Evidence linked per section 11.
- [ ] No new runtime dependency.
- [ ] Documents and DECISION-LOG.md updated if any decision changed.
- [ ] Deliberate self-review pass against this checklist.

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

*End of Engineering Document. Sections filled: 18 of 18. Unknowns carried: 8.*
