# Handoff back: round eighteen

Date: 2026-09-02. Base: `17520c13a7daad9bcd58664931c6c3bc95f85b4d`,
the reviewed head of `claude/round-seventeen-verify`. Branch:
`codex/round-eighteen-verify`.

## 1. Outcome

- D-095 through D-099 were attacked through running code. One held in its
  stated parallel scope, one needed narrower evidence, and three were broken.
  D-100 through D-104 record the resulting contracts.
- The matrix has 106 rows, 101 active and 5 superseded. Every active row now
  carries Windows and T540P Linux records. M97, M98, and M99 are caught on both
  hosts.
- The full T540P serial `--write` replay processed all 106 rows with zero not
  caught. It began from a clean `core.autocrlf=false` clone at `c846660` and
  changed only `matrix.json` at publication.
- Dirty read-only serial replay remains available and labels both status
  endpoints. `--write` now requires a clean start and a clean check immediately
  before matrix publication. This is option 2 from the handoff.
- R-032 survived an independent real-classifier challenge on Windows and
  T540P. Its canonical two-host output digest is
  `2a7b70cc3c5c0d6fed7103418e55fe6653bde876217f7aad0c118eb3d49e1e2c`.
- No routing rule was approved. Selective execution remains disabled. The
  slice is not `Done`.

## 2. D-095 through D-099 attack verdicts

| Decision | Verdict | Measurement | Successor |
|---|---|---|---|
| D-095 | Amended | A clean T540P clone removed the only test holding M57, then ran `M57 --jobs 2`: 19 passed, 0 skipped, local `SURVIVED`, exit 1, restored source, clean endpoint. The zero-skip branch held. Two direct result sets then showed the gap: a relevant Windows skip and an unrelated Windows skip both became `caught elsewhere` because only the count was stored. | D-104 stores exact failed and skipped node ids. A skipped survivor is carried only by an exact intersection. M105 and M106 hold the attribution and collector. |
| D-096 | Upheld for parallel; serial amended | Editing the coordinator after its clean preflight did not change a clone already created from the frozen commit. The clone matched the committed blob, not the dirty working file. Separately, one dirty test edit made M57 survive serially while parallel caught it from HEAD. | D-103 labels dirty read-only serial work and makes both `--write` checks fail closed. M103 and M104 hold the checks. |
| D-097 | Broken | `adc.py` could construct `work_receipt.py` from string fragments and load it through `importlib` while the quoted-name scan found nothing. | D-100 classifies every Python file directly under `anti-dark-code/scripts/` as authority by location. M100 holds it. |
| D-098 | Broken | `--rootdir=<clone>` blocked a parent `conftest.py`, but `PYTEST_ADDOPTS=-p external_adc_plugin` plus an external `PYTHONPATH` still loaded code from the coordinator and passed the clone-owned test. | D-101 removes caller pytest controls and paths, disables automatic plugins, and names the tracked outcome plugin explicitly. M101 holds it. |
| D-099 | Broken | A 3,062-character worker error surfaced 2,000 raw characters and retained newline, carriage return, ANSI escape, and bidirectional format controls. It could print a forged replay line. | D-102 renders controls before applying the 2,000-character limit. M102 holds it. A source-flow scan found zero shell candidates across five production error-flow functions, one known-positive candidate, and exactly one parallel-write guard. |

The D-096 clone race did not expose a parallel mismatch after clone creation.
That result does not extend to serial replay, which reads the disk. The two
contracts remain separate.

## 3. Dirty serial replay choice

Sixty `git status --porcelain` samples were taken in a disposable clone.

| Tree | Minimum | Median | p95 | Maximum | Returned state |
|---|---:|---:|---:|---:|---|
| clean | 25.872 ms | 27.411 ms | 59.052 ms | 63.075 ms | 0 paths, 0 bytes |
| seven-path dirty | 28.321 ms | 29.191 ms | 32.652 ms | 54.117 ms | 7 paths, 317 bytes |

The three-row serial replay took 173.03 seconds. The prior full serial records
took 1,524 seconds on T540P and 6,585.939 seconds on Windows.

The measured options were:

1. Refuse every dirty serial run. One start check costs about 29 ms on the
   measured dirty tree, but round-robin documentation work must stop or move to
   another clone. This option still needs a final check to close the mid-run
   race.
2. Record both endpoint statuses, allow labelled dirty read-only replay, and
   require clean execution endpoints for `--write`. Two median checks cost
   about 58 ms, below 0.004 percent of the shorter full replay.
3. Leave serial unchanged. This saves the status calls but preserves the
   measured false-HEAD record: the dirty serial M57 result and the parallel HEAD
   result disagree with no label explaining why.

Codex selected option 2. D-103 is the decision. A report records exact porcelain
rows before and after replay. The final `--write` guard runs before publication;
the post-run status therefore names the published `matrix.json` as the sole
expected dirty path.

## 4. Authoritative host records

### Windows exact-node refresh

A clean `core.autocrlf=false` clone at `da15c0d` replayed M37, M46, M48, and
M100 through M106 serially. Both endpoint statuses were empty and the clone
remained clean. The ten row durations sum to 583.643 seconds. Report SHA-256:
`24e1d6f869ac466a017e52910bff2e5e8c253100bdf7111de6de6e3fe1988376`.

M37, M46, and M48 survived on Windows under the exact skipped node
`AcquisitionAgainstRealGitTests::test_a_symlink_is_identified_not_followed`.
M100 through M106 were caught. The records were committed at `c846660` before
the Linux replay.

### T540P full `--write`

The committed branch was transferred as a complete Git bundle with SHA-256
`f9fb53ab6f6352d5c78dcb654a555fdd9e28d73fb12d914437a8750c6d57a856`.
T540P cloned it with `core.autocrlf=false` at exact head `c846660`.

System Python no longer had pytest. The first wrapper logged that import failure
but, because that wrapper lacked `set -e`, continued into a fast all-inconclusive
run. Replay wrote no matrix, the clone stayed clean, and that packet was
discarded. The accepted run used an external venv with pytest 9.1.1 and checked
the import, commit, line-ending setting, and clean status before its first row.

Accepted result:

- host: Linux `7.0.0-30-generic`, Python 3.12.3, pytest 9.1.1, Git 2.43.0;
- command: `<external-venv>/bin/python replay.py --write --report <external>`;
- exit 0, 106 rows, 101 completed, 5 superseded, 0 not caught;
- summed row duration: 1,469.339 seconds;
- before status: empty; after status: only modified `matrix.json`;
- every completed row restored its mutation source;
- M97: caught by two exact tests, M98: caught, M99: caught;
- M37, M46, and M48: exact Linux failed node equals the exact Windows skipped
  node, so all three derive `caught elsewhere`;
- report SHA-256:
  `3563d8fe04ed6dd5dc0b57a6c8b08ad66a18e1fc28d5a777b560a4df2a159032`;
- published matrix SHA-256:
  `0d6f375a8563c4f0fd995c49d322cb155550d3a060dd44b7cb06ee002c792dcb`.

`SERIAL-EVIDENCE-ROUND-EIGHTEEN.json` carries the compact machine-readable
record. The matrix import matched the remote digest byte for byte, and all nine
matrix-integrity tests passed after import. A later writing pass changed only
the stale `awaiting` notes on M97 through M106. The final annotated matrix
SHA-256 is
`d1eb1f3c8790da323c322e683e7e36a5e73306d2081c53bc2ca3e003b2635301`;
the host result objects are unchanged.

## 5. Untouched requirement challenge

R-032 was selected because rounds seventeen and eighteen touched R-021 and
R-053. The real classifier ran five exact-case and case-only probes on Windows
and T540P Linux. Exact case matched. Directory, suffix, bracket-class, and
Unicode case changes all produced an `unknown` fact. The canonical output was
byte-identical across hosts.

Verdict: upheld. `docs/review/adversarial-pass.md` records the challenge.
`docs/unknowns/adversarial-pass.md` records that it created no open unknown.

## 6. Forward-range trailer check

At `d2e8b99`, `git log ea8733c..` contained 58 commits. Fifty-one carried
`EDD-Checklist: satisfied`; the same seven round-fifteen commits did not. Every
round-eighteen commit through that head carries the trailer. The historical
violation remains recorded under D-080 and was not rewritten.

## 7. Owner walkthrough and remaining block

`WALKTHROUGH-SLICE-001.md` now freezes the head from which it is read, expects
106 rows and 101 active two-host records, reads D-100 through D-104, and checks
the Round Eighteen evidence artifact. Its branch check names
`codex/round-eighteen-verify`.

Immediately before the documentation receipt, the full local suite reported
`498 passed, 14 skipped, 64 subtests passed` in 208.69 seconds. Universal
validation reported 0 errors and the one expected generated-artifact warning.
`git diff --check` was clean.

The literal own-head run must occur after this handoff is committed, because a
commit that embeds its own resulting hash cannot exist. Do not commit after the
run. The final response for this round must name the immutable head, local
command results, and exact-head PR checks.

SLICE-001 still needs Daniel Boyd to answer the six questions and check the
last approval box. No technical result in this round answers those questions
for him. The slice remains open.

## 8. Commits before the final documentation receipt

- `da15c0d` - replay evidence boundaries, tests, decisions, and M100-M106;
- `c846660` - exact Windows skip-sensitive and new-row records; and
- `d2e8b99` - full T540P Linux `--write` records.

Every commit carries `EDD-Checklist: satisfied`.
