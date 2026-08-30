# Handoff back to Claude: round seven

Date: 2026-08-30. Agent: Codex. Branch: `design/assurance-router-specs`.
Reviewed commit: `cc15c8c1c3d22724ecade62aa5b7c1a3ffbf4b17`.
Platform: Microsoft Windows 11 Pro Insider Preview 10.0.26220, build 26220.
Python: 3.14.2. Git: 2.50.1.windows.1. `core.fileMode=false`.
Suite: `309 passed, 13 skipped, 45 subtests passed in 106.04s`.
Router suite: `178 passed in 12.35s`. Validation: `0 errors, 1 warning`.

## 1. Verification results

| Claim | Verdict | Evidence | Result |
|---|---|---|---|
| S-01 baseline | verified | verified | The full suite, router suite, and universal validation reproduced. The warning is the known `__pycache__` warning. |
| S-02 matrix replay | verified | verified | An isolated clone replayed all 37 stored rows. M01 through M35 were caught. M36 and M37 survived. The source was restored and the clone was clean. |
| S-03 repository mid-merge | verified | verified | The real Git conflict test passed. The acquired snapshot kept `src.py` and did not report `ADC-ROUTE-MALFORMED-RECORD`. |
| S-04 replaced policy refused | verified | verified | `dataclasses.replace` on a loaded policy is refused by `build_route`. Registry collection, equal-object forgery, and two equal loaded policies also behaved correctly. |
| S-05 index-only change detected | refuted | verified | An ordinary index update moves metadata and is detected. A same-size index rewrite with restored mtime is invisible. A linked-worktree index is not read at all. See P-02. |
| S-06 every Route path immutable | refuted | verified | The named test passes because `replace` changes only `minimum_level` and retains the old proxy. Direct construction and `replace(..., obligations={...})` both return mutable mappings. See P-03. |
| S-07 canonical full set required | refuted | verified | Omitting the argument raises `TypeError`, but passing `{}` or an empty shaped mapping accepts a Level 3 recipe with one pass and one obligation. See P-01. |
| S-08 clone evidence | partly verified | verified | The wrong staged answer reproduced, along with missing unstaged and untracked state. Five shared bare clones took 0.10 to 0.33 seconds and stored 38,477 logical bytes, not about 27 KB. See P-09. |
| S-09 no configured program or lazy fetch | partly verified | verified | Six focused tests passed for fsmonitor, external diff, local and effective filter discovery, the no-write check, and the lazy-fetch environment control. The lazy-fetch test asserts the environment variable, not real missing-object behavior. The universal program claim remains unknown. |
| S-10 parser matches real Git | partly verified | verified | Real conflict, SHA-256, symlink-mode, gitlink-mode, and type-change output parsed. The grammar still accepts malformed `U` rows and mixed repository widths across sources. See P-04 and P-05. |
| S-11 acquisition cost | refuted | verified | This repository took 0.341 to 0.379 seconds. The 345-file repository took 3.298 seconds cold and 0.698 to 0.739 seconds warm. An unconditional under-one-second claim does not reproduce. |
| S-12 no direct write or network API | verified | verified | Source scan found only `open(path, "rb")`, `Path.read_text`, and the known Git subprocess boundary. No direct write or network API is present. Git child behavior is separate under S-09. |

Receipts, the `route` subcommand, gate runner binding, and shadow comparator are not built. Their behavior is unassessed.

## 2. Mutation results

The original replay result reproduced:

```text
M01 through M35: caught
M36 fingerprint ignores path topology: SURVIVED
M37 lstat becomes stat: SURVIVED
37 mutants, 2 not caught: ['M36', 'M37']
```

I added M38 to `mutants/matrix.json`:

| ID | Change | Result |
|---|---|---|
| M38 | Replace the weak validated-policy registry with a plain dictionary that pins every loaded policy | `178 passed in 14.90s`, SURVIVED |

The current matrix has 38 unique ids, 35 caught rows, and 3 survivors. Every stored target occurs once in its named source.

M38 does not show an authority bypass. It shows that the suite does not hold the documented memory-lifetime property. Direct registry probes found that the current identity design is sound. A collected policy loses its weak entry, an equal forged policy is refused, and a second equal loaded policy remains accepted.

The replay harness itself failed three challenge probes:

1. A forced process-tree termination after mutation left `adc_route.py` mutated in the disposable clone.
2. `replay.py M38 --write` rewrote the 38-row scratch matrix as a one-row file.
3. A suite exit with `1 error in 0.01s`, and a silent exit 2, both returned `caught=False`. Both would be recorded as survivors even though the suite did not pass.

See P-06 before treating matrix output as unattended evidence.

## 3. Findings

### P-01: Caller-supplied canonical data can define away the full set

Severity: blocking. Risk: high. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:1153` through `:1238`; `anti-dark-code/tests/test_route.py:1999`.

`full_set` is required by the Python signature, but it has no schema or trusted origin. The coverage checks iterate only what the caller supplies.

Concrete failing input: pass a valid minimal Level 3 policy with pass `07` and obligation `V09`, then call `load_policy(..., full_set={})`. Actual result: a `ValidatedPolicy` with only pass `07` is returned. The same happens with `{"passes": [], "obligations": {}}`. Expected result: untrusted or incomplete canonical input is refused before a policy gains authority.

Proposed fix: obtain the canonical set inside one reviewed loader, or accept a private authority object produced by that loader. Validate its complete schema and provenance. A caller mapping must not be able to narrow the ceiling it is meant to check.

### P-02: The boundary still misses index bytes and linked-worktree indexes

Severity: blocking. Risk: high. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:370` through `:375`.

The fingerprint records only size and mtime from `repo/.git/index`. It neither hashes index bytes nor asks Git for the administrative path. D-043 requires both.

Concrete failing inputs:

1. Write `AAAA` to the index, fingerprint it, replace it with `BBBB`, and restore the original mtime. Actual result: the fingerprints are equal. Expected result: different fingerprints and `ADC-ROUTE-BOUNDARY-VIOLATED` during acquisition.
2. Represent a linked worktree with a `.git` file and mutate the real administrative index. Actual result: the fingerprints are equal because `repo/.git/index` cannot exist below a file. Expected result: the resolved index change is detected.

Proposed fix: implement D-043 as written. Resolve `index` with `git rev-parse --git-path index`, verify the resolved administrative target, and include an index content digest plus metadata.

### P-03: Route immutability is still limited to selected call sites

Severity: major. Risk: high. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:685` through `:696`; `anti-dark-code/tests/test_route.py:1341` through `:1355`.

The frozen dataclass accepts a plain obligations mapping and has no `__post_init__`. The new test calls `dataclasses.replace(built, minimum_level=3)`, which retains the proxy already made by `build_route`. It never supplies a new mapping.

Concrete failing input: construct `Route(obligations={"V09": frozenset({"validate-core"})})`, or replace a Route with that mapping, then call `clear()`. Actual result: the mapping is emptied. Expected result: mutation is refused for every Route instance.

Proposed fix: implement D-045. Canonicalize nested fields in `__post_init__`, or make Route private behind reviewed constructors. Test direct construction and `replace` with a newly supplied obligations dictionary.

### P-04: The unmerged exemption accepts records Git cannot emit

Severity: major. Risk: medium. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:121` through `:140`; `anti-dark-code/tests/test_route.py:415` through `:429`.

`U` is absent from `_STATUS_SIDES`, so it takes the same early return as an unknown future status. That return occurs before score validation and has no source-specific grammar.

Concrete failing inputs: an unstaged `U100`, an unstaged `U` with both modes and objects null, and a committed `U`. Actual result: all three parse with no problem and one unmerged row. Expected result: `ADC-ROUTE-MALFORMED-RECORD` while retaining enough failure context to block a selective route.

Proposed fix: implement the source-specific grammar in D-044. Keep unknown future letters fail-closed, but do not use that exemption for known `U`. Add real staged and worktree conflict fixtures plus scored, both-null, and committed negative cases.

### P-05: Object width is still local to each acquisition call

Severity: major. Risk: medium. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:189` through `:204` and `:490` through `:498`.

Each `parse_raw_z` call starts with `width=None`. Acquisition calls the parser separately for committed, staged, and unstaged payloads. D-044 requires one repository object format.

Concrete failing input: a 40-digit merge base, a 64-digit committed record, and a 40-digit staged record from one runner. Actual result: `complete=True`, no problems, and both widths in one snapshot. Expected result: `ADC-ROUTE-MALFORMED-RECORD` and `complete=False`.

Proposed fix: acquire `extensions.objectFormat` or an equivalent Git-owned format once, validate merge-base width, and pass the required width into every parser call.

### P-06: Replay can leave a mutant, truncate the matrix, or misclassify a broken suite

Severity: major. Risk: high. Evidence: verified.
File: `design/routing/mutants/replay.py:31` through `:79`.

`run_suite` searches the final text line for `failed` instead of checking the process status. It has no timeout. A hard termination cannot run the restore `finally`. Named `--write` filters the rows before overwriting the matrix. The harness also uses `python` rather than `sys.executable` and checks only that the old text is present, not that it occurs once.

Concrete failing inputs and results:

- Kill the replay process tree after M36 is applied. Actual result: the M36 source edit remains.
- Run a named row with `--write`. Actual result: the scratch matrix contains only that row.
- Make the suite print `1 error in 0.01s` and exit 1, or exit 2 without output. Actual result: `caught=False`, so the broken run looks like a survivor.

Expected result: a nonzero suite status catches the mutant only when the failure is a test assertion, infrastructure failures are distinct, every run has a timeout, and a named write updates matching rows inside the complete matrix. The harness must verify the preimage, restoration, and clean status. Hard-kill recovery needs an isolated disposable checkout or a startup recovery record because `finally` cannot handle process termination.

### P-07: The fingerprint identifies a symlink, then follows it for content

Severity: major. Risk: medium. Evidence: inferred from verified source behavior.
File: `anti-dark-code/scripts/adc_route.py:397` through `:417`; `design/routing/DECISION-LOG.md:1175` through `:1187`.

The code calls `lstat`, then opens the path normally. A normal open follows a symlink. D-043 instead requires the symlink target text without following it. The same loop attempts to open any listed special-file type, so a tracked path replaced by a FIFO can block on POSIX.

Concrete failing input: replace a tracked regular path with a symlink to readable data outside the repository. Actual result by source semantics: the external target bytes are read and hashed. Expected result: hash the link target text and never read through it. This Windows host could not create the symlink because it lacks the required privilege, so the real filesystem result is unknown here.

Proposed fix: branch on `lstat().st_mode`. Use `os.readlink` for symlinks, stream only regular files, record gitlink and other supported types explicitly, and refuse unsupported special files without opening them.

### P-08: Policy-registry lifetime is not held by the test suite

Severity: minor. Risk: low. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:959` through `:981`; `design/routing/mutants/matrix.json` M38.

M38 replaces the weak registry with a plain dictionary. All 178 router tests pass, so a long-lived process could retain every loaded policy without a failure.

Expected result: after the final external reference is deleted and collection runs, the registry entry disappears. Proposed fix: add a small lifecycle test. Keep the current identity-keyed weak-value design.

### P-09: D-048 repeats a wrong storage number and rules beyond its evidence

Severity: minor. Risk: medium. Evidence: verified.
File: `design/routing/DECISION-LOG.md:1296` through `:1332`.

D-047 records 38,477 logical bytes for the cited shared clone. D-048 says about 27 KB. Five new runs again stored 38,477 logical bytes. Their wall times varied from 0.10 to 0.33 seconds, so a narrow 145 to 155 ms range is not portable evidence.

The capability probe does support rejecting a bare or ordinary full clone. The origin had one committed, staged, unstaged, and untracked change. The bare clone kept the committed row, reported all three tracked files as staged deletions, and reported unstaged and untracked acquisition unreadable. It does not rule on an isolated snapshot that explicitly carries candidate index and worktree state. D-047 already leaves that design open.

Proposed fix: align the D-048 cost record with D-047 and narrow the capability ruling to the clone forms tested. Keep a complete index and worktree snapshot as an open architecture question.

## 4. Rulings

### M36

Keep the topology fields. Evidence: verified. A corrected fixture gives two separate tracked files identical bytes and identical fixed mtimes, then replaces one path with a hard link to the other without calling `utime` after linking. The current fingerprint changes. M36 produces equal before and after fingerprints. Add this fixture to the suite. The existing test passes for a different metadata change and does not hold topology.

### M37

Keep `lstat` under D-043, but keep M37 marked as surviving until a test fails it. Evidence: inferred. A Linux fixture can make two equal target names refer to the same hard-linked inode, retarget a same-length symlink, and restore link metadata. `stat` sees the same target identity while `lstat` sees the changed link. This host could not create a symlink, so we do not know yet whether that fixture needs platform-specific adjustment.

### Registry identity

Keep `WeakValueDictionary[int, ValidatedPolicy]` and the `is policy` check. Evidence: verified. A live object cannot share its id with another live object. Once the registered object is collected, its weak entry is removed. Reuse of that integer therefore finds no old value, and the identity comparison is a second guard. Two equal loaded policies remain separate registrations. M38 calls for a lifecycle test, not a provenance redesign.

### D-048

The bare and ordinary full clone rejection is correct. Evidence: verified. Those clones do not represent the candidate index or worktree and return a false staged answer. `--shared` also points into the candidate object store.

The general rejection of every isolated representation is not established. Evidence: unknown. No probe tested an OS-level or purpose-built snapshot containing index bytes, tracked worktree state, untracked names and bytes, modes, symlink targets, and gitlinks. Keep live acquisition as the current path only after P-02 and P-07 close. Keep the broader isolated snapshot question open as D-047 already states.

## 5. Edits applied

- Added M38 to `design/routing/mutants/matrix.json` with its replay result.
- Added this handoff.
- No implementation, test, CI, metrics, architecture, engineering, slice, plan, or decision file was edited.

## 6. Execution evidence

Baseline:

```text
python -B -m pytest anti-dark-code/tests/test_route.py -q
178 passed in 12.35s

python -B -m pytest anti-dark-code/tests -q
309 passed, 13 skipped, 45 subtests passed in 106.04s

python -B anti-dark-code/scripts/adc.py validate --mode universal
VALID (universal): 0 errors, 1 warning(s)
```

Focused real-Git and contract tests:

```text
6 passed, 172 deselected in 4.68s
4 passed, 174 deselected in 0.77s
real_mode_records=[new-link add 120000, submodule add 160000, type-entry type-change 100644/120000]
real_mode_problems=()
real_sha256_snapshot=True, problems=(), staged_width=64
```

Authority, parser, and boundary probes:

```text
narrow_full_set_accepted={} passes=['07']
narrow_full_set_accepted={passes: [], obligations: {}} passes=['07']
direct_route_obligations_mutable=True
replaced_route_obligations_mutable=True
unmerged_probe unstaged U100 problems=() inputs=1
unmerged_probe unstaged both-null U problems=() inputs=1
unmerged_probe committed U problems=() inputs=1
mixed_width_snapshot complete=True problems=() widths=[64, 40]
same_size_index_rewrite_invisible=True
linked_worktree_index_invisible=True
weak_registry_collected=True
equal_forged_policy_refused=True
live_registered_policy_accepted=True
```

Topology, clone, cost, and harness probes:

```text
hardlink_original_detects=True
hardlink_m36_misses=True
symlink_probe_unavailable=WinError 1314
origin_sources=[committed, staged, unstaged, untracked]
bare_clone_sources=[committed modify, three staged deletes]
bare_clone_problems=[ADC-ROUTE-UNSTAGED-UNREADABLE, ADC-ROUTE-UNTRACKED-UNREADABLE]
shared_clone_seconds=0.33,0.10,0.10,0.10,0.11
shared_clone_logical_bytes=38477 each
acquisition_current_seconds=0.360,0.379,0.344,0.341,0.344
acquisition_345_file_seconds=3.298,0.698,0.740,0.713,0.733
collection_error_result=(False, '1 error in 0.01s')
silent_crash_result=(False, 'no output')
hard_kill_left_mutant=True
named_write_rows_after=1
```

Matrix structure after M38:

```text
rows=38 unique=38
verdicts={'caught': 35, 'SURVIVED': 3}
duplicate_targets=[]
missing_fields=[]
```

All mutation and hostile harness runs used disposable clones outside the repository. The main implementation and tests were never edited. The local execution safety policy refused recursive removal of `C:\DEV\skills\anti-dark-code-round-seven-review-20260830`, so that external scratch directory remains for manual cleanup. No scratch entered the repository. Repository status contains only the two authorized `design/routing/` changes.

## 7. Questions back

1. Which reviewed repository-owned source should produce the canonical full set, so a caller cannot narrow it?
2. Can Linux CI own the M37 symlink fixture and the P-07 no-follow fixture?
3. Should replay use a disposable checkout for every row, or a persistent transactional worker with startup recovery? Hard termination cannot be made safe by `finally` alone.
4. Should the next builder close D-043, D-044, and D-045 before any receipt code starts? Their confirmed decisions are still not implemented.

## 8. Readiness

Do not proceed to receipts or the CLI. P-01 and P-02 are blocking. The pure layer still accepts caller-defined full authority and can report changed index authority as unchanged. Close P-01 through P-09, make M36 through M38 fail from the stored matrix, then repeat this gate.
