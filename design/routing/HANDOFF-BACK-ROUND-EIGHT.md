# Handoff back to Claude: round eight

Date: 2026-08-30. Agent: Codex. Branch: `design/assurance-router-specs`. Baseline commit: `516d6ff4b22c7b18721415ffedcf6e762de14ac4`. Review changes are uncommitted.

Platform: Windows 11 Pro Insider Preview 10.0.26220, 64-bit. Test Python: 3.12.3. Shell default Python: 3.14.2. Windows Git: 2.50.1. `core.fileMode=false`. Windows symlink creation failed with WinError 1314. Ubuntu under WSL2 supplied real symlink evidence with Python 3.12.3 and Git 2.43.0.

Suite: `319 passed, 14 skipped, 45 subtests passed in 111.81s`. Router suite: `188 passed, 1 skipped in 16.78s`. Universal validation: `0 errors, 1 warning` for generated Python artifacts.

## 1. Verification results

| Claim | Verdict | Evidence | Note |
|---|---|---|---|
| T-01 baseline results | verified | Full suite, router suite, and universal validation reproduced under Python 3.12.3. | The shell default is Python 3.14.2, so the commands used `py -3.12`. |
| T-02 46-row replay | verified | The first 46 rows reproduced 40 caught, 3 superseded, and M36, M37, M46 surviving on Windows. | The matrix now has 48 rows after M47 and M48. Its Windows result is 40 caught, 3 superseded, 5 surviving. |
| T-03 empty canonical full set refused | verified | The suite covers `{}`, missing fields, empty arrays, empty obligations, unknown ids, and missing canonical members. | This verdict is limited to the supplied full-set contract. The future CLI source and binding are not built. |
| T-04 Route obligations immutable under all construction | refuted | A direct Route and a replaced Route accepted a mapping proxy backed by mutable data. Later backing mutations changed each Route. | `__post_init__` trusts an existing proxy instead of copying it. See Q-01. |
| T-05 unmerged grammar corrected | partly refuted | Scored, committed, and all-null-mode `U` rows are refused. Production flags accepted a real conflict under Ubuntu. Plain `git diff --raw -z --no-abbrev` emitted a real `U` row with both object ids zero and one real mode, which the parser rejects. | Copy detection changes that Git output and hid the broader parser form. See Q-02. |
| T-06 one snapshot cannot mix widths | verified | Current code rejected a single 64-character row beside a resolved 40-character merge base. An unresolved base plus a malformed first row remained incomplete. | M47 removes the merge-base seed and survives. The behavior is right but unheld. See Q-03. |
| T-07 index bytes and linked index | verified | The same-size index rewrite and linked-worktree tests passed. The 48-row replay caught M44 and M45. | No contrary case was found. |
| T-08 symlink target recorded and not followed | verified for current code, unheld for target text | The real Ubuntu symlink test passed. M37 and M46 failed that test. M48 omitted target text and the same test still passed. | Windows cannot create the link. See Q-04 and the rulings. |
| T-09 replay failure handling | verified | A collection-breaking mutant produced pytest exit 2 and `INCONCLUSIVE`; the source was restored. A simulated `KeyboardInterrupt` propagated after restoration. Filtered `--write` returned 2, restored the source, and left the matrix hash unchanged. | The probe used disposable directories and left no tracked file. |
| T-10 no configured program and no lazy fetch | partly verified | Real fsmonitor, external diff, local filter, and effective filter tests pass. The runner sets `GIT_NO_LAZY_FETCH=1`. | There is no real missing-promisor-object test. The source says that case could not be built. The universal configured-program claim also remains unknown. See Q-05. |
| T-11 parser accepts real Git forms | partly refuted | Real Ubuntu probes accepted SHA-256 objects, a file-to-symlink type change, a gitlink add, and the production-flag conflict forms. | The plain raw conflict form in Q-02 is real Git output and is rejected. "Every record" is too broad. |
| T-12 no direct disk write or network API | verified | AST scan: 1 production candidate file, 0 direct write findings, 0 network imports, and one read-only `open(..., "rb")`. A known-positive scan of `test_route.py` found 40 write calls. | Git child behavior is separate under T-10. |

Receipts, the `route` subcommand, gate runner binding, and shadow comparator remain unbuilt and unassessed.

## 2. Mutation results

The checked-in replay completed all 48 rows and rewrote their host-local results:

```text
40 caught
3 superseded: M32, M34, M35
5 Windows survivors: M36, M37, M46, M47, M48
```

The original 46-row claim therefore reproduced as 40 caught, 3 superseded, and 3 Windows survivors.

Two rows were added:

- M47 removes the merge-base width seed. It survived the router suite. With one 64-character row beside a resolved 40-character base, the mutant accepted the row and reported a complete snapshot.
- M48 removes symlink target text but retains the type marker. It survived on Windows and also survived the real Ubuntu symlink test.

Platform challenge results:

- M37 failed the existing Ubuntu symlink test.
- M46 failed the existing Ubuntu symlink test.
- M48 passed the same Ubuntu test.
- A corrected hard-link probe held bytes, size, and mtime equal. Current code detected the swap and M36 did not.

The `INCONCLUSIVE` path fired for a disposable test mutant that broke pytest collection. It reported `pytest exit 2: 1 error`, restored the source, and returned 1.

## 3. Findings

### Q-01: Route trusts a proxy backed by mutable authority data

- **Severity:** high
- **File and line:** `anti-dark-code/scripts/adc_route.py:752`, especially `:757` through `:760`.
- **What is wrong:** `__post_init__` copies plain mappings but skips an existing `MappingProxyType`. A proxy prevents writes through the proxy. It does not freeze its backing dictionary or nested values.
- **Concrete failing input:** construct `Route(obligations=MappingProxyType({"V09": {"validate-core"}}))`, retain the backing dictionary, then clear the nested set or add `V99`. The Route changes. `dataclasses.replace` has the same result when given a proxy.
- **Expected output:** later source mutation cannot change the Route.
- **Actual output:** direct Route changed from `{"V09": {"validate-core"}}` to `{"V09": set(), "V99": {"foreign-gate"}}`; the replaced Route became empty.
- **Proposed fix:** always copy obligation keys and convert gate collections to fresh `frozenset` values before wrapping. Add direct and replaced proxy-backed cases.

### Q-02: unmerged grammar confuses null object ids with absent sides

- **Severity:** medium
- **File and line:** `anti-dark-code/scripts/adc_route.py:126` through `:135`; contrary test at `anti-dark-code/tests/test_route.py:442`.
- **What is wrong:** the `U` branch refuses both zero object ids even when one mode says a side exists. Ubuntu Git 2.43 emitted that form during a real conflict for plain raw worktree diff.
- **Concrete failing input:** `:000000 100644 <40 zeros> <40 zeros> U\0f.txt\0` from `git diff --raw -z --no-abbrev`.
- **Expected output:** one `unmerged` row with no malformed problem, because the new mode is real.
- **Actual output:** no `U` row and `ADC-ROUTE-MALFORMED-RECORD`.
- **Proposed fix:** use modes to decide whether a side exists. Refuse both-null modes, scores, and committed `U`; accept a real mode with a null worktree object id. Add the real plain-raw and production-flag cases.

### Q-03: M47 removes repository-width binding without failing the suite

- **Severity:** high
- **File and line:** implementation at `anti-dark-code/scripts/adc_route.py:540`; current guard at `anti-dark-code/tests/test_route.py:604` through `:616`.
- **What is wrong:** the test proves disagreement between two changed sources, not disagreement between one source and the resolved merge base. M47 removes the base seed and still passes all 188 router tests.
- **Concrete failing input:** resolved base `"a" * 40` and one committed raw row whose two object ids are 64 characters.
- **Expected output:** `ADC-ROUTE-MALFORMED-RECORD`, zero accepted rows, incomplete snapshot.
- **Actual output under M47:** one accepted 64-character row, no problems, complete snapshot.
- **Proposed fix:** add that single-source fixture and require it to fail M47.

### Q-04: M48 removes symlink target text without failing on Linux

- **Severity:** high
- **File and line:** implementation at `anti-dark-code/scripts/adc_route.py:441` through `:447`; test at `anti-dark-code/tests/test_route.py:994` through `:1013`.
- **What is wrong:** the test checks only that the stored value contains `symlink:`. It never checks the target returned by `os.readlink`.
- **Concrete failing input:** M48 changes the stored value from `symlink:{target}:{topology}` to `symlink:{topology}`.
- **Expected output:** the symlink test fails because target identity was lost.
- **Actual output:** the Ubuntu test reports `OK`.
- **Proposed fix:** assert the recorded target text, then retarget a same-length link and prove the fingerprint changes.

### Q-05: R-054 names a real partial-clone test that does not exist

- **Severity:** high
- **File and line:** `design/routing/ENGINEERING.md`, verification ledger R-054; `anti-dark-code/tests/test_route.py:1021` through `:1047`.
- **What is wrong:** the test docstring says a true blobless clone could not be built and the test only inspects `GIT_NO_LAZY_FETCH`. The former R-054 text claimed a real missing-object no-execution table.
- **Concrete failing input:** a blobless promisor clone whose rename or copy comparison needs a missing blob.
- **Expected output:** no fetch child, no new object, an unreadable source problem, and an incomplete snapshot.
- **Actual output:** we do not know yet. No such test runs.
- **Proposed fix:** build the real case on a transport that honors partial-clone filtering, or keep R-043 open and retain the downgraded R-054 evidence text.

### Q-06: replay verdicts flatten platform skips

- **Severity:** medium
- **File and line:** `design/routing/mutants/replay.py:36` through `:58`; matrix rows M37 and M46.
- **What is wrong:** Windows says both mutants survive because the symlink test skips. Ubuntu says both are caught. A single unqualified `verdict` cannot represent both facts.
- **Concrete failing input:** replay M37 or M46 on Windows, then run the existing symlink test with the same mutant under Ubuntu.
- **Expected output:** platform-qualified results, or an inconclusive host result when the only relevant test skipped.
- **Actual output:** generic `SURVIVED` on Windows and a test failure under Ubuntu.
- **Proposed fix:** record platform, Python, Git, and skip state per replay result, or run required platform legs before assigning one repository-wide verdict.

## 4. Rulings

### M36

Keep path topology. The corrected hard-link probe gives it a discriminating purpose. It remains unheld by the checked-in suite and blocks the pure-layer gate until that probe becomes a test.

### M37

Keep `lstat`. The existing symlink test fails M37 under Ubuntu. Reclassify it as caught on the supported symlink-capable path, not as a repository-wide survivor. Windows alone cannot provide this evidence.

### M46

Keep the symlink branch. The existing Ubuntu test fails M46. The Windows survivor label is caused by a skip. M48 shows that target-text identity still needs its own assertion.

### D-048

Confirm the narrowed ruling. The measured bare shared clone cannot represent staged, unstaged, or untracked state and can answer the staged question wrongly. That capability gap rules out the tested bare forms. It does not rule out a representation with a complete index and worktree snapshot. The 38,477-byte figure is now attached to the cited 345-file repository, and cold timing remains separate from warm timing.

## 5. Edits applied

- Added M47 and M48 plus challenge and platform evidence to `design/routing/mutants/matrix.json`.
- Added this handoff.
- Updated the current gates and version to 0.9 in `ARCHITECTURE.md`, `ENGINEERING.md`, and `SLICE-001-route-shadow.md`.
- Added the round-eight gate to the implementation plan.
- Added D-049 through D-052 to `DECISION-LOG.md`.
- Did not edit `adc_route.py`, `adc.py`, `test_route.py`, `.github/`, or `metrics/`.

## 6. Execution evidence

```text
py -3.12 -m pytest anti-dark-code/tests -q
319 passed, 14 skipped, 45 subtests passed in 111.81s

py -3.12 -m pytest anti-dark-code/tests/test_route.py -q
188 passed, 1 skipped in 16.78s

python -B anti-dark-code/scripts/adc.py validate --mode universal
VALID (universal): 0 errors, 1 warning(s)

python design/routing/mutants/replay.py --write
48 mutants, 5 not caught: ['M36', 'M37', 'M46', 'M47', 'M48']

Ubuntu real symlink baseline
Ran 1 test ... OK

Ubuntu M37 and M46 challenge
M37 caught
M46 caught

Ubuntu M48 challenge
M48 SURVIVED

collection-breaking replay probe
INCONCLUSIVE: pytest exit 2: 1 error in 0.27s
source restored: true

interrupt replay probe
interrupt propagated: true
source restored: true

filtered write probe
return: 2
source restored: true
matrix unchanged: true
```

Disposable probes used temporary directories. Scratch removal succeeded. Final status contains only permitted paths under `design/routing/`.

## 7. Questions back

1. Is `parse_raw_z` public for all raw Git output, or private to `_DIFF_FLAGS`? Q-02 needs a code fix for the first contract and a narrower document contract for the second.
2. Should the mutation record become platform-qualified now, or should Linux be the required replay host for filesystem topology rows?
3. Is Route expected to support `pickle` or `deepcopy`? Both currently raise `TypeError` because `mappingproxy` is not picklable. `copy.copy` retains immutability.
4. Which environment will own the real missing-promisor-object case for R-043?

## 8. Readiness

**Do not proceed.** Q-01 is a live deep-immutability failure. M36, M47, and M48 remain unheld. Q-05 leaves a network and configured-execution boundary without the real test its ledger named. Q-02 also refutes the broad raw-parser claim.

Pass 07 ran on the pure router and mutation harness. Four high and two medium findings are open. No approval-gated implementation file was edited. Human review is required before the builder changes verification-authority code or tests. The next pass should be pass 11, with one safe-fix batch per finding and focused red-green evidence before another round.
