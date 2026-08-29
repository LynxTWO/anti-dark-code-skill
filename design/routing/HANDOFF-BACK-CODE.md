# Handoff back to Claude: router pure layer review

- Date: 2026-08-29
- Agent: OpenAI Codex
- Branch: `design/assurance-router-specs`
- Review HEAD: `0619b60e92e597723e15004a7e46e5a0928e1369`
- Code and spec HEAD: `df1b338`
- Reviewed range: `537dff4..df1b338`
- Platform: Microsoft Windows 10.0.26220
- Python: 3.14.2
- Git: 2.50.1.windows.1
- Repository `core.fileMode`: `false`
- Suite: `179 passed, 13 skipped, 45 subtests passed in 115.54s`
- Router suite: `48 passed in 3.21s`, then `48 passed in 3.28s` after restoring all mutations
- Validation: `VALID (universal): 0 errors, 1 warning(s)`

## 1. Verification results

| Claim | Verdict | Evidence | Note |
|---|---|---|---|
| Q-01 | verified | `python -m pytest anti-dark-code/tests -q` returned `179 passed, 13 skipped, 45 subtests passed in 115.54s`. `python anti-dark-code/scripts/adc.py validate --mode universal` returned `0 errors, 1 warning(s)`. | The stated baseline is reproducible on this platform. |
| Q-02 | refuted | The requested six mutations were caught, but removing `set(facts)` returned `48 passed`. The current `test_ordering_is_deterministic_under_shuffled_input` also passes while cross-process ordering changes, and `test_every_fact_field_is_a_closed_enum_value` passes while invalid values escape. | The suite has live tests, but two named guarantees are narrower than their names and claims. |
| Q-03 | refuted | A real staged copy from an unchanged source was `A copy.txt` with `-C`, and `C100 source.txt copy.txt` only with `--find-copies-harder`. A real staged content-plus-mode record was `:100644 100755 ... M`, but the parser returned `change_kind='modify'`. | Copy provenance and some mode transitions do not survive real Git acquisition. |
| Q-04 | verified | `test_staged_change_is_not_counted_twice` ran in the passing suite. Code at `adc_route.py:227-236` uses `--cached` for index versus `HEAD` and no revision for worktree versus index. The `--cached` to `HEAD` mutation failed two tests. | The staged and unstaged comparisons are distinct. |
| Q-05 | verified | A real scratch repository returned `.agents/skills/probe/SKILL.md` and `.anti-dark-code/probe.json` as untracked add records. `test_skill_tree_paths_are_not_filtered_out` also passes. | The two tooling trees survive acquisition. |
| Q-06 | refuted | A raw record missing its final NUL, a six-field header, and `:bad bad bad bad M` each returned no problems and produced `complete=True`. A successful runner result of `b'\n'` for merge-base also produced `base_resolved=True`, `base=''`, and `complete=True`. | D-025 is sound, but the parser does not report every malformed transport or header. |
| Q-07 | refuted | Static inspection found no disk or network call in `collect_change_facts`, but identical arguments yielded two tuple orders under different `PYTHONHASHSEED` values. | The function has no I/O, but its returned value depends on process hash salt for tied sort keys. |
| Q-08 | refuted | Seeds 1 and 2 ordered source-side copy facts differently because `related_path` is absent from the key at `adc_route.py:341-342`. Removing duplicate collapse also survived all 48 tests. | Canonical ordering is incomplete and duplicate collapse lacks a direct test. |
| Q-09 | refuted | Pure classification tests prove both paths are classified when a copy record exists. Real Git acquisition turns the common unchanged-source copy into an add, so `old_path` never reaches classification. | Rename handling passed. Copy handling is not end-to-end complete. |
| Q-10 | refuted | A classifier entry with `surface='BOGUS'` emitted a verified fact carrying `BOGUS`. A `ChangeInput` with `change_kind='BOGUS_KIND'` and `source='BOGUS_SOURCE'` emitted both values unchanged. | The frozensets describe valid values but do not enforce them. |
| Q-11 | refuted | `adc.py` uses `CAPABILITY_COUNT`, but `test_route.py:62` derives the total with `range(1, 23)`. | The next capability still requires a second count edit. |
| Q-12 | refuted | A repository-local `core.fsmonitor=.git/hooks/fsmonitor-probe` script wrote a sentinel three times during one `read_change_inputs` call. The snapshot returned `complete=True`. | Starting Git is not a no-repository-code boundary when local Git configuration can name an executable. No network access was observed. |

## 2. Mutation results

Each mutation was applied alone to an external clone. The router suite ran after each change. The source was restored and the final external-clone run returned 48 passes.

| Mutation applied | Tests that failed | Verdict |
|---|---|---|
| Delete the mode-only branch | `RawParserTests.test_mode_only_change_is_not_reported_as_modify` | caught |
| Return `RawParse` without parser problems | Four malformed-record parser tests and `AcquisitionTests.test_parser_problems_reach_the_snapshot` | caught |
| Stop after the first classifier match | `test_a_broad_glob_cannot_mask_a_specific_one`, `test_skill_md_is_never_only_inert_documentation` | caught |
| Remove `-C` from `_DIFF_FLAGS` | `AcquisitionTests.test_acquisition_requests_rename_and_copy_detection` | caught |
| Replace staged `--cached` with `HEAD` | `test_snapshot_unions_all_four_sources`, `test_staged_and_unstaged_use_different_comparisons` | caught |
| Stop classifying the source side of rename and copy | `test_copy_emits_facts_for_both_sides`, `test_related_path_links_both_sides_of_a_rename`, `test_rename_emits_facts_for_both_sides` | caught |
| Replace `set(facts)` with `facts` | none, `48 passed in 3.20s` | **SURVIVED** |

## 3. Findings

### H-01, blocking: Git acquisition executes repository-configured code

- File and line: `anti-dark-code/scripts/adc_route.py:12`, `anti-dark-code/scripts/adc_route.py:179-189`.
- What is wrong: `_default_runner` starts Git without neutralizing `core.fsmonitor`. A candidate repository can configure Git to start a repository-controlled filesystem-monitor program during acquisition. This contradicts the module boundary and can execute before routing decides what evidence is required.
- Concrete input and expected output: configure `core.fsmonitor` to a script that writes a sentinel, then call `read_change_inputs(repo, "HEAD")`. Observed: three sentinel lines and `complete=True`. Expected: no sentinel, no repository-controlled process, and an unchanged index and worktree.
- Proposed fix: invoke every Git command with `-c core.fsmonitor=false`, set `GIT_OPTIONAL_LOCKS=0`, and add a real hostile-repository test. Audit each future Git option for another executable configuration path before adding it.

### H-02, blocking: malformed acquisition can produce a complete snapshot

- File and line: `anti-dark-code/scripts/adc_route.py:73-80`, `anti-dark-code/scripts/adc_route.py:107-112`, `anti-dark-code/scripts/adc_route.py:149-155`, `anti-dark-code/scripts/adc_route.py:204-212`.
- What is wrong: `_split_z` discards empty fields and does not prove a terminal NUL. `parse_raw_z` accepts extra fields and does not validate modes or object ids. Untracked framing is unchecked. A whitespace-only successful merge-base result is treated as resolved. D-025 can only fail closed when these cases enter `problems`.
- Concrete input and expected output: `b':100644 100644 ' + b'1'*40 + b' ' + b'2'*40 + b' M\0file.py'` returned one input, no problems, and `complete=True`. `b':bad bad bad bad M\0file.py\0'` did the same. Expected: no accepted row for each malformed record, a stable framing or header problem code, and `complete=False`.
- Proposed fix: require a terminal NUL for every nonempty `-z` payload; preserve record boundaries while parsing; validate the supported mode, object, and status grammar; validate untracked framing; require one nonempty merge-base id; and test each failure through `ChangeSnapshot.complete`.

### H-03, blocking: unchanged-source copies lose their source path

- File and line: `anti-dark-code/scripts/adc_route.py:157-161`, `anti-dark-code/scripts/adc_route.py:224-236`.
- What is wrong: `_DIFF_FLAGS` contains `-C` but not `--find-copies-harder`. Git considers an unchanged source only with the latter flag. The destination is therefore acquired as add, so source sensitivity cannot reach classification.
- Concrete input and expected output: commit `source.txt`, create identical `copy.txt`, stage it, and acquire from `HEAD`. Observed raw result with current flags: `A copy.txt`; observed snapshot: `('copy.txt', None, 'add', 'staged')`. Expected: `C100 source.txt copy.txt` and a copy input with both paths.
- Proposed fix: add `--find-copies-harder` to every raw diff, retain `-C`, and add a real repository test that copies an unchanged sensitive source to an ordinary destination. Set copy-detection limits explicitly and treat a detection-limit warning as incomplete. This closes the demonstrated identical-copy case; Git similarity remains a heuristic for changed copies.

### H-04, blocking: a mode transition disappears when content also changes

- File and line: `anti-dark-code/scripts/adc_route.py:129-132`.
- What is wrong: a modify becomes mode only when old and new object ids are equal. A record that changes bytes and executable mode has unequal object ids, so the mode signal disappears. An unstaged mode transition also uses a zero worktree object id and cannot satisfy the equality test.
- Concrete input and expected output: stage new content in `tool.sh` and set its index mode from `100644` to `100755`. Real Git emitted `:100644 100755 <old> <new> M tool.sh`; acquisition returned `change_kind='modify'`. Expected: the mode transition remains explicit, either as `change_kind='mode'` or a separate `mode_changed=True` signal that rules cannot miss.
- Proposed fix: represent `old_mode != new_mode` independently of object equality. Prefer an explicit mode-change field so a combined content and mode change retains both facts. Add pure mode, content-plus-mode, and unstaged mode fixtures.

### H-05, blocking: closed enums are declarations, not enforced contracts

- File and line: `anti-dark-code/scripts/adc_route.py:33-69`, `anti-dark-code/scripts/adc_route.py:282-303`, `anti-dark-code/scripts/adc_route.py:315-343`.
- What is wrong: classifier values, `ChangeInput.change_kind`, and `ChangeInput.source` pass into `ChangeFact` without validation. A policy typo can silently change rule matching.
- Concrete input and expected output: classifier `{'surfaces':[{'glob':'*.py','surface':'BOGUS','effect':'behavior'}]}` emitted a verified fact with `surface='BOGUS'`. An input with `BOGUS_KIND` and `BOGUS_SOURCE` also emitted both. Expected: a policy or input error and no fact.
- Proposed fix: validate every entry against `SURFACES`, `EFFECTS`, `BREADTHS`, `SENSITIVITIES`, `CONFIDENCES`, `CHANGE_KINDS`, and `CHANGE_SOURCES` before fact creation. Add one negative case per field.

### H-06, major: canonical fact order omits `related_path`

- File and line: `anti-dark-code/scripts/adc_route.py:338-343`.
- What is wrong: `set(facts)` is sorted by eight fields, but `ChangeFact` has nine. Two source-side facts for copies from one source tie on the current key and retain hash-table order.
- Concrete input and expected output: classify `src.py -> a.py` and `src.py -> b.py` copies. Under seed 1 the two source facts were ordered `b.py, a.py`; under seed 2 they were `a.py, b.py`. Expected: one order under every seed.
- Proposed fix: include `related_path or ""` in the key, preferably by defining one canonical function that names every serialized field. Run a subprocess test over several hash seeds.

### H-07, major: classifier case semantics change with the host OS

- File and line: `anti-dark-code/scripts/adc_route.py:294`.
- What is wrong: `fnmatch.fnmatch` applies `os.path.normcase`. Windows matches paths case-insensitively while Linux and macOS use case-sensitive matching. Identical Git path and policy data can therefore yield different facts and receipts.
- Concrete input and expected output: on Windows, path `AUTH/login.py` matched pattern `auth/*` and received sensitivity `auth`. The same call does not match on a case-sensitive host. Expected: one documented result on every supported platform; D-028 selects case-sensitive Git-path semantics, so this case should be unmapped.
- Proposed fix: normalize separators to `/`, use `fnmatch.fnmatchcase`, and add the same case-collision fixture to every platform job.

### H-08, minor: capability count still has a second derived literal

- File and line: `anti-dark-code/tests/test_route.py:60-62`.
- What is wrong: the runtime count uses `CAPABILITY_COUNT`, but the contiguity test uses `range(1, 23)`. The drift scanner searches specifically for old 20 forms and does not flag this new count contract.
- Concrete input and expected output: add V23 and change `CAPABILITY_COUNT` to 23. The contiguity test still expects V01 through V22 until manually edited. Expected: the range derives from `adc.CAPABILITY_COUNT`; explicit V21 and V22 identity tests remain.
- Proposed fix: load `adc`, use `range(1, adc.CAPABILITY_COUNT + 1)`, and replace the previous-number regex with a structural count-contract check.

### H-09, minor: duplicate-collapse mutation survives the router suite

- File and line: `anti-dark-code/tests/test_route.py:504-507`, with production behavior at `anti-dark-code/scripts/adc_route.py:338-340`.
- What is wrong: the suite claims duplicate facts collapse, but no test submits duplicate rows. Removing the production `set` left all 48 tests green.
- Concrete input and expected output: submit the same mapped `ChangeInput` twice. Under the survivor there are two equal facts. Expected: one fact and a test failure when deduplication is removed.
- Proposed fix: add an explicit duplicate-input assertion and retain the survivor in the mutation matrix.

## 4. Ruling on the two deviations

### D-024: endorse with changes

Keeping every matching classifier entry is the right choice. It prevents a broad glob from hiding a specific authority reading and works with positive, single-fact monotonic rules. The implementation must add four conditions before this is complete:

1. Validate every classifier and input enum before emitting facts.
2. Use case-sensitive, slash-normalized Git-path matching on every host.
3. Deduplicate facts and sort by all serialized fields, including `related_path`.
4. Enforce D-024's positive, single-fact rule restriction when policy loading and `build_route` arrive.

These additions do not reopen the all-matches decision. They make each emitted fact valid and canonical.

### D-025: endorse with changes

`RawParse(inputs, problems)` and the `ChangeSnapshot.complete` predicate are the right fail-closed shape. The implementation does not yet report every incomplete view. It must validate terminal NUL framing, raw field shapes, untracked framing, and a nonempty merge-base identity. It must also keep stable reason codes for each failure class and prove that every future caller consults `complete` before a selective receipt can exist.

## 5. Edits applied

Only design documents were edited. No Python, JSON, test, workflow, or application file changed.

| File | Section | Change | Reason |
|---|---|---|---|
| `design/routing/ARCHITECTURE.md` | 5, 6, 9, 13, 14 | Corrected the D-025 reference and added the Git execution boundary, parser framing, copy, mode, enum, glob, and canonical-order guardrails. | The previous architecture claimed boundaries that the probes refuted. |
| `design/routing/ENGINEERING.md` | 4, 5, 7, 9, 11 | Added R-027 through R-033 and their test ledger entries. | Each finding now has an observable closure condition. |
| `design/routing/DECISION-LOG.md` | index, D-026 through D-029 | Added proposed decisions for Git configuration isolation, acquisition fidelity, canonical facts, and the capability count source. | Settled D-024 and D-025 remain intact; the new findings get new ids. |
| `design/routing/SLICE-001-route-shadow.md` | 3, 8, 11 | Marked M2 review blocked and added S-024 through S-030. | `build_route` must not begin on an unsound snapshot and fact layer. |
| `design/routing/plans/2026-08-28-assurance-router-slice-001.md` | review gate, Tasks 1 through 4 | Added the round-three gate and task-specific correction notes. | The historical code blocks omit several required controls. |

## 6. Execution evidence

Commands ran from the repository root unless a scratch path is named.

```text
> git status --short --branch
## design/assurance-router-specs

> python -m pytest anti-dark-code/tests/test_route.py -q -rs
48 passed in 3.21s

> python -m pytest anti-dark-code/tests -q
179 passed, 13 skipped, 45 subtests passed in 115.54s (0:01:55)

> python anti-dark-code/scripts/adc.py validate --mode universal
VALID (universal): 0 errors, 1 warning(s)
```

Real Git copy probe:

```text
> git diff --raw --no-abbrev -M -C --cached
:000000 100644 000... 2f47... A copy.txt
> git diff --raw --no-abbrev -M -C --find-copies-harder --cached
:100644 100644 2f47... 2f47... C100 source.txt copy.txt
> read_change_inputs(...)
snapshot_staged= [('copy.txt', None, 'add', 'staged')]
```

Real Git combined mode probe:

```text
> git diff --raw --no-abbrev --cached
:100644 100755 be6a... 98b7... M tool.sh
> read_change_inputs(...)
[('tool.sh', 'modify', '100644', '100755', ... , 'staged')]
```

Malformed and enum probes:

```text
missing_final_nul ... problems= () complete= True
extra_header_field ... problems= () complete= True
invalid_columns ... problems= () complete= True
blank merge-base: base='' base_resolved=True problems=() complete=True
invalid_enum= ChangeFact(... surface='BOGUS' ... confidence='verified')
invalid input= ChangeFact(... change_kind='BOGUS_KIND', source='BOGUS_SOURCE' ...)
```

Cross-seed ordering probe:

```text
distinct_orders= 2
seed 1: ... ["src.py","b.py"],["src.py","a.py"]
seed 2: ... ["src.py","a.py"],["src.py","b.py"]
```

Repository-code probe:

```text
core.fsmonitor=.git/hooks/fsmonitor-probe
read_change_inputs(...): complete=True problems=() inputs=0
sentinel:
invoked
invoked
invoked
```

Mutation summary:

```text
requested mutations: 6 caught, 0 survived
additional duplicate-collapse mutation: 0 failed, 48 passed, SURVIVED
restored external clone: 48 passed in 3.28s
```

The external tree was resolved as `C:\DEV\skills\anti-dark-code-review-20260829`, checked against the approved prefix, moved to the Windows Recycle Bin, and then returned `Test-Path=False`. It is recoverable from the Recycle Bin until that bin is emptied.

Final repository status contains only these six `design/routing/` paths: the five edited specifications or plan files and this new handoff. No implementation file is modified.

## 7. Questions back

1. Please confirm or revise proposed D-026 through D-029 before remediation starts.
2. For a combined content and mode transition, should `ChangeInput` gain `mode_changed: bool`, or should `change_kind='mode'` dominate modify? I recommend the explicit field because it preserves both signals.
3. After the five blocking findings close, should the same review rerun before `build_route`, or should the remediation commit include `build_route`? I recommend a pure-layer recheck first.

## 8. Readiness

**Do not proceed, with blocking findings H-01, H-02, H-03, H-04, and H-05.**

The pure layer is not sound enough to feed `build_route`. Close repository-configured execution, incomplete snapshots, unchanged-source copy loss, mode-signal loss, and enum passthrough first. Then rerun the real Git, hostile-repository, cross-seed, mutation, full-suite, and universal-validation checks.
