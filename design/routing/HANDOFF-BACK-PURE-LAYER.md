# Handoff back to Claude: pure layer review

Date: 2026-08-29. Agent: Codex. Branch: `design/assurance-router-specs`.
Commit reviewed: `34081af41eda6b8976a8064f8f307a98f4263e62`.
Platform: Microsoft Windows 10.0.26220. Python: 3.14.2. Git: 2.50.1.windows.1.
`core.fileMode=false`.

Full suite: `245 passed, 13 skipped, 45 subtests passed in 118.78s`.
Router suite: `114 passed in 6.71s`.
Validation: `VALID (universal): 0 errors, 1 warning(s)`.

The pure layer is not ready for receipt or CLI work. Five blocking defects remain. Receipt writing, the `route` subcommand, gate runner binding, and shadow comparison do not exist, so I could not assess them.

## 1. Verification results

| Claim | Verdict | Evidence | Note |
|---|---|---|---|
| P-01 | verified | The three baseline commands reproduced the stated counts. | The validation warning was the expected generated `__pycache__` warning. |
| P-02 | verified | Inspection found union, maximum, and logical OR only. An expanded nine-fact pool exercised 2,304 one-fact extensions across every match dimension. | Every `Route` field stayed equal or increased under the comparison used by R-001. |
| P-03 | refuted | Reversing two facts reversed `list(route.obligations)` from `['V01', 'V02']` to `['V02', 'V01']`. | Mapping equality hides an observable order difference. Receipt byte stability is not assessable because receipts are not built. See K-07. |
| P-04 | refuted | Existing values are additive, including a route with nonempty unknown and unmapped sets. A hint also added pass `not-a-pass`, capability `V99`, gate `not-a-gate`, and reason `not-a-reason`. | `matched_rule_ids` is protected, but other computed and catalog-bound fields accept invented values. See K-08, K-12, and K-13. |
| P-05 | refuted | A policy with `full_recipe.minimum_level = 0` loaded. An unrouted fact then produced `force_full = true` at Level 0. | The recipe is selected, but validation does not establish that it is the canonical Level 3 recipe. See K-04. |
| P-06 | verified | A classified `tests/behavior` fact matched no approved rule and returned full with `ADC-ROUTE-UNROUTED-FACT`. | Unrouted and unmapped both force full and have different reason codes. |
| P-07 | verified | The router tests reject unknown, disabled, unapproved, and duplicate gate configuration ids. | This verdict covers duplicate gate definitions. Duplicate names inside one obligation list collapse to a set and are not rejected. |
| P-08 | refuted | `paths: "*.md"`, `mode_changed: "false"`, and a Level 0 full recipe all loaded. A default load also rejected V23 because it guesses V01 through V22. | Key validation exists, but match value shape and the full-recipe contract are incomplete. See K-02, K-04, and K-06. |
| P-09 | verified | A policy with every rule proposed loaded, matched no rule, and forced full. | This agrees with D-022. |
| P-10 | refuted | `A100`, `R999`, mode `777777`, and mixed 40/64 object widths parsed with no problem and a complete snapshot. The capability default also contains a new count literal. | H-02 and H-08 are not closed at their stated boundaries. See K-05 and K-06. |
| P-11 | refuted | A real repository clean filter ran during `read_change_inputs`, wrote `filter-side-effect.txt` into the repository, and the snapshot still returned complete. | The filesystem-monitor probe is too narrow. See K-01. |
| P-12 | refuted | The same clean filter caused a disk write. Git lazy fetch is also not disabled, so offline behavior is not established. | No direct Python file write was found. The Git subprocess can start configured programs and those programs control their side effects. See K-01. |

Evidence labels in this table apply to the claim within the tested boundary. The lazy-fetch part of P-12 is inferred from the missing control and Git's documented behavior. No network request was made during this review.

## 2. Mutation results

These four mutations are beyond the thirteen listed in the incoming handoff. Each mutation was made in an external clone, tested, and restored.

| Mutation | Tests that failed | Verdict |
|---|---|---|
| Replace hint `unknowns` union with assignment | none, router suite stayed `114 passed` | SURVIVED, K-12 |
| Replace hint `unmapped_paths` union with assignment | none, router suite stayed `114 passed` | SURVIVED, K-13 |
| Delete the `paths` predicate from `_fact_matches` | none, router suite stayed `114 passed` | SURVIVED, K-10 |
| Delete the `mode_changed` predicate from `_fact_matches` | none, router suite stayed `114 passed` | SURVIVED, K-11 |

## 3. Findings

### K-01, blocking: Git acquisition runs content filters and can write to the repository

File and line: `anti-dark-code/scripts/adc_route.py:203`, `:212`, and `:254`.

What is wrong: the isolation list disables filesystem monitors and external diff commands, but it does not disable `filter.<driver>.clean` or `filter.<driver>.process`. Git applies clean conversion while comparing a worktree file. The child process receives the caller environment. A helper can write files, start a network client, or read inherited values before routing decides what may execute.

Concrete failing input: a scratch repository had `.gitattributes` set to `*.txt filter=evil`, local config set `filter.evil.clean=.git/hooks/filter-probe` and `filter.evil.required=true`, and a modified `tracked.txt`. The helper wrote `filter-side-effect.txt` in the worktree. `read_change_inputs(repo, "HEAD")` returned `complete=True`, `problems=()`, and the side-effect file existed.

Expected output: no repository-configured program starts and no file changes. If the boundary cannot neutralize a driver, acquisition returns incomplete with a stable reason code.

Proposed fix: either use an acquisition path that never performs worktree conversion, or discover every effective filter driver without executing it and override `clean`, `smudge`, and `process` to no command with `required=false`. Add `--no-textconv`, `--no-lazy-fetch`, and `GIT_NO_LAZY_FETCH=1`. Add real clean-filter and process-filter sentinels plus an offline partial-clone case. Do not claim isolation from a fixed list without those cases.

### K-02, blocking: policy match values are not validated

File and line: `anti-dark-code/scripts/adc_route.py:506` and `:791`.

What is wrong: `load_policy` validates match keys but not their value types or enum members. `_fact_matches` then treats a string path pattern as an iterable of one-character patterns and coerces `mode_changed` with `bool()`.

Concrete failing input: an approved cheap rule with `match: {"paths": "*.md"}` loads. Its `*` character matches `src/auth.py`, so the unrelated path receives the cheap rule. `match: {"mode_changed": "false"}` also loads and is interpreted as true.

Expected output: `load_policy` raises `PolicyError` before routing.

Proposed fix: require every plural predicate to be a nonempty list of strings, validate each member against its closed fact set, require `paths` entries to be nonempty strings, and require `mode_changed` to be an actual boolean. Reject unknown fields at every policy object level.

### K-03, blocking: validation returns an aliased mutable policy

File and line: `anti-dark-code/scripts/adc_route.py:729`, `:804`, and `:542`.

What is wrong: `load_policy` returns `dict(data)`, a shallow copy. Nested rules, recipes, and classifier entries remain shared with the caller. `build_route` also accepts any mapping, so its type does not distinguish reviewed data from raw data.

Concrete failing input: load a policy whose rule is proposed, mutate the original nested rule to approved, then call `build_route` with the loaded result. The proposed rule now matches and returns a cheap route.

Expected output: post-load mutation cannot change the loaded policy, and `build_route` refuses a raw policy value.

Proposed fix: parse into a frozen `ValidatedPolicy` made from immutable nested records and canonical tuples. Make `build_route` accept only that type. Tests should mutate every original nested container after load and confirm the route is unchanged.

### K-04, blocking: a full recipe can validate as Level 0

File and line: `anti-dark-code/scripts/adc_route.py:712`, `:769`, and `:598`.

What is wrong: the generic level validator permits 0 through 3 for the full recipe. It also does not prove that the recipe contains the repository's full pass and capability set. This contradicts D-020 and ADD guardrail 10.

Concrete failing input: a full recipe with `minimum_level: 0`, no passes, and one valid obligation loads. An unrouted fact returns `force_full=True` and `minimum_level=0`.

Expected output: policy load fails because the full recipe is not Level 3 and does not establish the declared full set.

Proposed fix: validate the root recipe separately. Require Level 3 and compare its pass, capability, and approved gate coverage with caller-supplied canonical full-set inputs.

### K-05, blocking: the raw parser checks character shape but not Git's record grammar

File and line: `anti-dark-code/scripts/adc_route.py:52` and `:136`.

What is wrong: any six octal digits are accepted as a mode, each object id may independently be 40 or 64 digits, and any uppercase status may carry zero to three digits. Git's raw format gives scores specific meanings and ties them to status letters. The parser accepts records Git cannot emit and marks them complete.

Concrete failing input: otherwise well-framed raw records with status `A100`, status `R999`, mode `777777`, or mixed 40 and 64 digit object ids all returned inputs with `problems=()`.

Expected output: each record is rejected with `ADC-ROUTE-MALFORMED-RECORD`, making its snapshot incomplete.

Proposed fix: validate the allowed Git modes, require one object width per record and repository, enforce null-side consistency, require 0 through 100 scores for C and R, allow the documented optional score only where Git permits it, and reject scores on other statuses.

### K-06, major: policy loading reintroduces a capability count literal

File and line: `anti-dark-code/scripts/adc_route.py:747`.

What is wrong: omitting `capability_ids` creates V01 through V22 with `range(1, 23)`. That is another executable source of truth after D-029 removed the earlier copies.

Concrete failing input: a policy naming V23 fails under the default. The same policy loads when the caller passes V01 through V23.

Expected output: policy loading never guesses the catalog boundary.

Proposed fix: make the catalog-derived capability set mandatory. If a convenience wrapper is needed, derive it from the catalog through the existing source of truth.

### K-07, major: obligation mapping order depends on fact order

File and line: `anti-dark-code/scripts/adc_route.py:570` and `:610`.

What is wrong: set fields compare equally across permutations, but the obligation dictionary keeps first-insertion order. Dataclass equality does not expose this difference. Iteration, representation, and a serializer without key sorting do.

Concrete failing input: one fact adds V01 and another adds V02. Routing `(a, b)` yields key order `['V01', 'V02']`; routing `(b, a)` yields `['V02', 'V01']`.

Expected output: all observable route collections have one canonical order.

Proposed fix: construct obligations in sorted capability order and sort gate ids at the serialization boundary. Add an order-sensitive route test before receipt work.

### K-08, major: hints accept invented catalog and evidence values

File and line: `anti-dark-code/scripts/adc_route.py:623`.

What is wrong: `apply_hints` accepts raw strings without a schema or policy context. It protects `matched_rule_ids`, but it lets a caller add arbitrary passes, capabilities, gates, unmapped paths, and reason codes.

Concrete failing input: applying `{"passes": ["not-a-pass"], "obligations": {"V99": ["not-a-gate"]}, "unknowns": ["not-a-reason"]}` to an empty route returns all three invented values.

Expected output: invalid hints fail before a route or receipt exists. Agent input cannot write computed evidence fields.

Proposed fix: define a validated hint type. Limit hints to requirement fields, validate them against the loaded policy and catalogs, and reserve `matched_rule_ids`, `unmapped_paths`, and `unknowns` for deterministic code.

### K-09, major: slash replacement changes a legal Git pathname

File and line: `anti-dark-code/scripts/adc_route.py:401` and `:511`.

What is wrong: replacing every backslash with slash treats a literal POSIX filename character as a separator. Git `-z` output is verbatim. Host path conventions must not rewrite repository path bytes.

Concrete failing input: the pure collector classifies path `docs\\auth.py` against glob `docs/auth.py`. It returns a verified docs fact instead of an unknown fact. This input is inferred to be reachable from a POSIX repository, where backslash is a legal filename character.

Expected output: the literal backslash path does not match the slash pattern.

Proposed fix: define policy patterns in Git's forward-slash path space and do not rewrite input characters. Add a real POSIX repository fixture for a backslash filename and skip that fixture on Windows.

### K-10, major: removing path matching leaves every router test green

File and line: `anti-dark-code/tests/test_route.py:1052`.

What is wrong: the monotonic pool and route tests do not include a rule selected by `paths`. Deleting the entire path predicate from `_fact_matches` left all 114 tests green.

Concrete failing input: the mutation removed lines 511 through 515 of `adc_route.py`; expected at least one router test failure, actual result `114 passed`.

Proposed fix: add an approved rule whose only discriminator is `paths`, plus positive, negative, case, and literal-backslash cases. Include that fact in the expanded monotonic pool.

### K-11, major: removing mode matching leaves every router test green

File and line: `anti-dark-code/tests/test_route.py:1052`.

What is wrong: no route rule in the tests depends on `mode_changed`. Deleting that predicate left all 114 tests green.

Concrete failing input: the mutation removed lines 523 through 524 of `adc_route.py`; expected at least one router test failure, actual result `114 passed`.

Proposed fix: add true and false mode rules and facts. Include the true case in the expanded monotonic pool.

### K-12, minor: hint unknown-reason retention has no mutation guard

File and line: `anti-dark-code/tests/test_route.py:995`.

What is wrong: the hostile hint test starts from a route whose `unknowns` set is empty. Replacing union with assignment therefore remains invisible.

Concrete failing input: mutate line 647 to use only the hint values. The router suite still reports `114 passed`.

Proposed fix: apply hostile hints to a route with an existing reason and assert that exact reason remains.

### K-13, minor: hint unmapped-path retention has no mutation guard

File and line: `anti-dark-code/tests/test_route.py:995`.

What is wrong: the hostile hint test also starts with no unmapped path. Replacing union with assignment remains invisible.

Concrete failing input: mutate line 646 to use only the hint values. The router suite still reports `114 passed`.

Proposed fix: apply hostile hints to a route built from an unknown-confidence fact and assert that its path remains.

## 4. Rulings on the three divergences

### D-026: endorse with changes

The principle is right and the shipped list is incomplete. The clean-filter probe refutes the current isolation claim. Git documents that a `filter` attribute selects configured `clean` and `process` commands, and that `process` takes precedence. Git also documents `GIT_NO_LAZY_FETCH` as the control that prevents an on-demand promisor fetch. See [Git attributes](https://git-scm.com/docs/gitattributes) and [Git environment variables](https://git-scm.com/docs/git).

The boundary must cover `filter.<driver>.clean`, `filter.<driver>.process`, lazy fetch, external diff, text conversion, filesystem monitors, and optional locks. Add a hostile case for each execution family. If a future command adds another configurable program path, it joins the list before shipping.

### D-027: endorse with changes

Keep unlimited copy detection for now. A several-thousand-path rename exceeding one second is acceptable because the bounded alternative silently loses provenance. I found no public structured exhaustion signal cheaper than retaining stderr. If a limit returns, the runner should retain stdout, stderr, and return code, pin diagnostic locale, and turn the tested exhaustion warning into an incomplete snapshot. Until that exists, `diff.renameLimit=0` is the safer setting.

The decision also needs stronger parser language. Git documents which statuses carry scores and that C and R always carry them. The present regular expression does not implement that grammar. See [Git raw diff format](https://git-scm.com/docs/diff-format.html).

### D-028: endorse with changes

There is a host-independent behavioral test. Patch `os.path.normcase` to lowercase during classification, then assert that `README.md` does not match `readme.md`. A regression to `fnmatch.fnmatch` fails under that simulated host behavior, while `fnmatch.fnmatchcase` passes. This tests the result, not a function call.

Remove backslash replacement. Git paths are not host filesystem paths at this layer. On POSIX, a literal backslash must remain a literal character. Keep policy globs in forward-slash Git path form.

## 5. Edits applied

Documents only:

- `design/routing/ARCHITECTURE.md`
- `design/routing/ENGINEERING.md`
- `design/routing/DECISION-LOG.md`
- `design/routing/SLICE-001-route-shadow.md`
- `design/routing/plans/2026-08-28-assurance-router-slice-001.md`
- `design/routing/HANDOFF-BACK-PURE-LAYER.md`

No implementation, test, workflow, or metrics file was edited.

## 6. Execution evidence

```text
python -m pytest anti-dark-code/tests/test_route.py -q
114 passed in 6.71s

python -m pytest anti-dark-code/tests -q
245 passed, 13 skipped, 45 subtests passed in 118.78s

python anti-dark-code/scripts/adc.py validate --mode universal
VALID (universal): 0 errors, 1 warning(s)

python audit_properties.py
rich_monotonic_checks=2304
hint_retains_unmapped=True
hint_retains_unknowns=True
unrouted_force_full=True reason=True
all_proposed_force_full=True matches=[]
hint_invented_passes=['not-a-pass']
hint_invented_obligations={'V99': frozenset({'not-a-gate'})}
hint_invented_unknowns=['not-a-reason']

clean-filter repository probe
complete=True problems=() side_effect_in_repo=True

four mutation runs
114 passed after each mutation
```

The mutation clone and hostile repositories were under `C:\DEV\skills\anti-dark-code-pure-review-20260829`, outside the repository, and were removed after evidence was recorded. Final `git status --short` contained only `design/routing/` edits.

## 7. Questions back

1. Will you accept D-030 through D-035 as the remediation contract, or should any remain open questions?
2. Should policy validation reject all unrecognized object fields, or only match and requirement fields?
3. Is trusted global Git filter configuration allowed to execute, or must acquisition suppress every external filter regardless of configuration origin?
4. Is `Route` identity defined by semantic set equality alone, or must iteration and representation also be canonical before receipt serialization?

## 8. Readiness

Do not proceed. K-01 through K-05 are blocking findings in acquisition, policy trust, full-route validation, and parser completeness. K-06 through K-13 should also close before receipt work because receipts would otherwise preserve noncanonical or weakly tested route data. Receipt writing, the CLI, gate binding, and shadow comparison remain unassessed because they are not built.
