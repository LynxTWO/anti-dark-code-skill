# Handoff back to Codex: round seventeen

Date: 2026-09-02. Agent: Claude. Base: `92e028e`, the head of `codex/round-sixteen-verify`, PR #26. Branch: `claude/round-seventeen-verify`, draft PR #27. Implementation head: `3856f11`; the evidence and documentation commits follow it and change no mutation source.

## 1. Terminal outcome

- **Round sixteen's numbers reproduce exactly**, its two digests recompute from its artifact, and its owner walkthrough is true: every command ran as written on a fresh clone at `92e028e` and every stated expectation held.
- **Five defects and one false claim** were found, all measured against running code. The most serious was in round sixteen's own evidence: its Linux replay recorded a survivor its summary did not report, and the CI job that has been described as failing on any survivor could not have failed on that one. Two more were found by this round's own evidence run failing: the parallel workers' collection tree climbed into the machine-wide temp directory, and the coordinator discarded the reason they reported.
- SLICE-001 remains `Proposed`. No routing rule was approved, selective execution stays disabled, and the last box is still the owner's.
- M97, M98, and M99 are new and carry a Windows record only until the next T540P run. The Linux CI replay has caught all three on every run of the branch.

## 2. Round sixteen, reproduced before its conclusions were read

Windows 11, Python 3.14.2, Git 2.50.1, in a fresh worktree at `92e028e`.

| Claim | Result |
| --- | --- |
| Suite `486 passed, 14 skipped, 62 subtests` | `486 passed, 14 skipped, 62 subtests passed in 34.67s`, CI-shaped (`-n auto -p no:cacheprovider`), 35 s wall |
| Universal validation 0 errors, 1 warning | `0 errors, 0 warning(s)` on the pristine tree with `-B`; the one warning appears only after pytest writes `__pycache__`, exactly as the walkthrough says |
| Integrity, traceability, workflow contracts 12 passed | `12 passed in 0.38s` |
| Matrix 96 rows, 91 active, 5 superseded, both hosts on every active row | 96/91/5; 91 Linux `caught`; 88 Windows `caught` and 3 Windows `SURVIVED` under one skip (M37, M46, M48); SHA-256 `d7e88dcc…` |
| Artifact gates empty, boundaries false | Schema v3, execution commit `f3d08a4`, `adopted`, four empty gate lists, three false boundaries |
| Serial/parallel identity digest `13b75072…` | Recomputed from the artifact's own rows over the 18 identity fields in canonical order: both modes reproduce it as `json.dumps(rows, sort_keys=True, separators=(",", ":"))`; zero field mismatches across 96 ids. The method was not recorded in the artifact; it is recorded here |
| Outcome-set digest `e57dd443…` and 500 exact node ids | One fresh xdist trial with the tracked plugin: 500 ids, collection SHA-256 equal to `13e8c402…`, 32 workers each collecting the identical list, outcomes equal to the canonical 486/14 sets, exit 0. The digest is the compact sorted JSON of the `{node id: outcome}` map |
| Frozen evidence carries to the final head | The five mutable sources, `matrix.json`, and `tests.yml` are byte-identical between `f3d08a4` and `92e028e` |
| CI green at the exact head | Run `33591194855` at `92e028e`, all nine jobs `success`; the mutation job log ends `96 mutants, 0 not caught: none` with the three `caught elsewhere (here: caught)` lines and no `(here: SURVIVED)` line |
| All 39 commits carry the EDD trailer | 39 of 39, checked with `%(trailers:key=EDD-Checklist)` |
| Four document contradictions fixed in `429f0d7` | Fixed. One residue: D-073's own section still said `Status: Provisional` while the index and D-083 said superseded; corrected to `Superseded by D-083` |

## 3. What round seventeen found

### D-095: a local survivor could not fail the replay, or CI

`replay()` merged the local result into the row's stored results before deciding anything, and `derive_verdict` read "caught anywhere" as caught. A row the other host had once caught therefore could not fail a replay on this host: the local `SURVIVED` became `caught elsewhere`, left the not-caught list, and the exit stayed 0.

Round sixteen's own record is the evidence. Its Linux write replay at `0a26531` has `local_survivor_ids: ["M92"]` in its report and `96 mutants, 0 not caught: none`, exit 0, in its summary. Codex noticed M92 through the `(here: SURVIVED)` note and superseded it under D-094, which was the right call for that row; the mechanism stayed. The `Mutation replay (Linux)` job runs the same function, so the claim in `HANDOFF-CODEX-ROUND-SIXTEEN.md` that it "fails on any survivor", written by Claude in round fifteen, was false for the 88 rows Windows had once caught.

Reproduced here: with the one test holding M57 renamed in an uncommitted edit, `replay.py M57 --jobs 1` printed `caught elsewhere (here: SURVIVED)` and `1 mutants, 0 not caught: none`, exit 0.

Fix: an unskipped `SURVIVED` result is `SURVIVED` before catches are counted, and the summary discloses rows that survived here only under skipped tests. M37, M46, and M48 keep `caught elsewhere`. Linux skips nothing, so every Linux survivor now fails CI. Windows skips the symlink test on every row, so a Windows-only survivor is disclosed, not blocked; that limit is stated in D-095. M97 holds the branch.

### D-096: serial and parallel replay disagreed on a dirty tree

Parallel replay clones HEAD; serial replay tests the disk. The coordinator preflight froze only the matrix, the harness, and the mutation targets. With the same uncommitted edit to `test_receipt.py`, which no row mutates:

    --jobs 1: M57 SURVIVED here, 19 passed, exit 0, commit 92e028e
    --jobs 2: M57 caught, 1 failed, 19 passed, exit 0, commit 92e028e

Nothing in either report said the two runs described different trees. Fix: the coordinator refuses any tree `git status --porcelain` reports as different from HEAD, untracked files included, before a clone exists. Serial replay is unchanged; the trade for it is put to the owner in the round-eighteen handoff. M98 holds the refusal.

A limitation found on the way, recorded in D-096 and not fixed: a Windows checkout made under `core.autocrlf=true` cannot coordinate a parallel replay, because the frozen-source comparison reads CRLF worktree bytes against LF blobs. Authoritative replays run from a clone made with `core.autocrlf=false`, which is what the workers already use.

### D-097: the helper-naming promise had no test

ENGINEERING section 12 promises that a newly imported helper not represented in the path table "makes the table test fail closed until reviewed". Nothing derived the loaded set; the classifier reaches a helper only through the `**/scripts/adc*.py` name. Measured with every rule approved in memory: `anti-dark-code/scripts/receipt_store.py`, a name `adc.py` could load tomorrow, routed as Level 2 product code with `force_full` false in both the source and `.claude` installed spellings. A table test now requires every script under `scripts/` to be authority by name or a reviewed standalone script that `adc.py` never names. `work_receipt.py` is the one such script, and it is not a self-grading class: `adc.py` never names it.

### D-098: a worker's collection tree climbed out of its clone

Found by this round's own evidence run, not by reading. The first full `--jobs 8` replay at `3856f11` completed exactly four rows per worker and then returned 59 rows inconclusive, all inside the window in which a serial replay ran in another clone. Rerunning failed rows through the worker path alone, with a second serial run started 100 seconds later, reproduced it with the error visible:

    ERROR collecting test session
    FileNotFoundError: [WinError 2] ... 'J:\TEMP\tmpo1xr2yol'
    Interrupted: 1 error during collection
    1 error in 4.25s            (pytest exit 2, about five seconds per row)

Without `--rootdir`, pytest roots a session at the common ancestor of the invocation directory and the absolute suite path. The coordinator clone sat in a scratch directory beneath `J:\TEMP`, this host's temp directory, so that ancestor was the machine-wide temp directory, and every worker scanned it at every row's start. Round sixteen's identical run never saw this because its coordinator lived on `C:` and its temp on `J:`, which share no ancestor; CI never sees it because the ancestor is `/`, which pytest refuses as a rootdir. The evidence was layout-dependent without anyone knowing. Fix: the worker command carries `--rootdir=<clone>`. M99 holds it.

### D-099: the coordinator threw away the worker's reason

Every one of those 59 rows was reported as `worker result schema does not match the required evidence fields`, because the coordinator's exact field-set check ran before it read the worker's `error` field, and `error` is not in the set. The real cause appeared only after the rows were rerun by hand. An inconclusive worker row is now reported as `worker row <status>: <its own error>`; completed rows are validated exactly as before.

### A false evidence claim

SLICE-001 ticked "from `ea8733c` forward, every commit carries `EDD-Checklist: satisfied`". Seven of the 49 commits in that range carry no trailer: the round-fifteen commits `30c577c` through `bf9aba3`, all Claude's. D-080 says such commits violate it. The line now records the violation and the evidence those commits do have, rather than rewriting history or leaving the tick.

### Checked and found sound

- Every currently authoritative path forces the full route with every rule approved: the installed spellings of exact globs, nested `.gitattributes` and `.gitignore`, `agents/openai.yaml`, a root `conftest.py`, and the routing JSON under `design/routing/` are all unmapped, and an unmapped path forces full.
- `ENGINEERING.md` and `SLICE-001` take the Level 0 docs route, but the traceability test couples ENGINEERING's requirement tables to `requirement-evidence.json`, which is unmapped and forces full, so a Markdown-only edit cannot shrink the traced set; it fails the test instead.
- The D-093 classifier contract, the D-091 pass-reference probes, and the D-092 provenance exclusion held against every variant tried.
- PR #26 is not a draft while #21 through #25 are. Convention only.

## 4. Verification

- After the changes, CI-shaped suite: `491 passed, 14 skipped, 64 subtests passed` (five new tests, two new subtests). Universal validation: 0 errors, the one expected warning after pytest.
- The first commit's own tree, extracted with `git archive`, passes the integrity, traceability, guard, and replay-evidence classes: `48 passed`.
- D-090's guard caught this round citing D-095 through D-097 before they were written; the decisions were written before the code was committed.
- Windows parallel replay, `--jobs 8`, read-only, from a `core.autocrlf=false` clone beneath the host temp directory. The first run, at `3856f11`, returned 59 rows inconclusive and is retained as the D-098 measurement (report SHA-256 `81e6d43b4cd2a170ebac0c71b210acf066ed2237cf0814762b07ed6f4d35bba4`). The run at the fixed head `4b24122`: exit 0, `99 mutants, 0 not caught: none`, 94 completed and 5 superseded rows, every row restored, all eight clones and roots removed, 879 s wall, report SHA-256 `70da49098da9aa02361552c4edb9f925afcfd7ddc18ba241cd985c09b58c0024`, matrix digest unchanged. The serial oracle run of M97, M98, and M99 in another clone started 108 seconds into it and churned the host temp directory until 347 seconds, the condition that broke the first run; every row completed. Every stored Windows verdict, skip count, and failed count matched; the passed and subtest counts moved only by the tests this round added. The disclosure line named M37, M46, and M48.
- Serial oracle for the three new rows at `4b24122`: exit 0, `3 mutants, 0 not caught`, 239 s, report SHA-256 `98e037635ce5a6d0e65116c451b7784bfc7965ba398bce2dd5ede9166abdb0cb`, agreeing with the parallel result row for row. Their Windows records in the matrix are transcribed from this serial report, because `--write` is serial-only and the matrix is written from serial observations.
- CI on PR #27: run `33608219799` at `3856f11` and run `33610038786` at `4b24122`, all nine jobs `success` in each; the second's mutation job ran 9m08s and ended `99 mutants, 0 not caught: none` with M97, M98, and M99 caught. The final documentation head's exact-head run is recorded below once observed.
- The owner walkthrough at the documentation head, and that head's exact CI run, are recorded in section 4a by the receipt commit that follows it. The receipt commit's own exact-head run belongs on PR #27, for the reason round sixteen gave: embedding it would move the head again.

## 4a. Receipt at the documentation head

The documentation head is `eba8ea9`. Required run [`33611787880`](https://github.com/LynxTWO/anti-dark-code-skill/actions/runs/33611787880) at exactly that commit passed every job; the mutation job ended `99 mutants, 0 not caught: none` with M97, M98, and M99 caught.

| Job | Result | Duration |
| --- | --- | ---: |
| Ubuntu / Python 3.12 | success | 36s |
| Ubuntu / Python 3.13 | success | 38s |
| Windows / Python 3.12 | success | 1m36s |
| macOS / Python 3.12 | success | 51s |
| Hostile environment (C locale) | success | 32s |
| Hostile environment (international paths) | success | 36s |
| Clean distribution archive | success | 6s |
| Mutation replay (Linux) | success | 8m50s |
| Aggregate `Tests` | success | 2s |

The owner walkthrough was run as written, in PowerShell, on a fresh GitHub clone detached at `eba8ea9`. Every stated expectation held: the six proposed rules; `False` and `[]`; `3 passed`; the `ROUTE` line with `rules=-`; `FRESH`, `STALE` with `ADC-STALE-004 worktree_identity`, `FRESH`; `491 passed, 14 skipped, 64 subtests passed` and no failure; `VALID (universal): 0 errors, 1 warning(s)`; `rows 99 | active 94 | recorded on both hosts 91` with `awaiting host records: ['M97', 'M98', 'M99']`; both artifacts' expected values; D-080, section 9, and fifteen decision headings printed; and the end state `?? .anti-dark-code/`. One difference, which the document anticipates: when its `gh pr checks` step ran, eight checks had passed and the mutation job was still pending, so the walkthrough says to wait; the completed run above is the receipt. The boxes in section 6 remain unchecked. This round does not approve on the owner's behalf.

This receipt commit follows `eba8ea9` and therefore triggers one more exact-head run. Embedding that run here would move the head again; its receipt belongs on PR #27.

## 5. Round seventeen's own defects

- The handoff-to-Codex claim that CI fails on any survivor was Claude's, from round fifteen. This round found it by measurement, not by rereading.
- The round-fifteen commits without the EDD trailer were Claude's.
- The round's first evidence run was launched from a layout no earlier round had used, and it failed. The failure was real and became D-098 and D-099, but the round spent an hour on its own evidence before that evidence could be trusted, and the first report's diagnostics had to be recovered by hand.
- The round cited D-095 through D-097 in code before writing them. D-090's guard refused the tree until they existed, which is the guard working, and is also the third round in a row to trip it.

## 6. What round eighteen should do

`design/routing/HANDOFF-CODEX-ROUND-EIGHTEEN.md` has the detail. In short: attack D-095 through D-099, record M97, M98, and M99 on T540P, and present the serial-replay trade to the owner with measurements rather than deciding it.

## 7. Runtime

Round sixteen reported 28h48m whole-goal elapsed against about five hours of evidence commands. This round, on the same Windows host: about 1h30m from its first command to this receipt commit, of which the authoritative evidence commands took about 45 minutes.

| Command | Wall time |
| --- | ---: |
| baseline CI-shaped suite at `92e028e` | 35s |
| owner walkthrough at `92e028e`, all steps | about 6m |
| xdist stability trial with the tracked plugin | 26s |
| first full parallel replay at `3856f11`, failed under churn | 7m17s |
| serial oracle runs, three in all | 7m26s |
| worker-path diagnostic rerun of five rows | 2m01s |
| full parallel replay at `4b24122` under the same churn | 14m39s |
| suite and validation runs after each change, three in all | about 1m30s |
| owner walkthrough at `eba8ea9`, all steps | about 6m |

Three CI runs of nine to ten minutes each overlapped other work. The gap between forty-five minutes of evidence and ninety of elapsed time was reading round sixteen's record, attacking it, writing five decisions and their tests, one evidence run that failed and had to be diagnosed, and the documents. The largest single cost was the failed run: launched from a layout no earlier round had used, it needed a diagnostic rerun before its cause could be named, which is what D-099 now removes.

Do not treat this handoff as acceptance of its own contracts. Its author has now twice recorded a claim about the replay gate that the code did not hold.
