# Handoff back: round sixteen

Date: 2026-09-01.  This handoff covers the Round Sixteen branch through
`bcc23461de970fb44aaea06236ec8bbd0b5e9657`; its final documentation commit
follows this record.  The durable, independently checkable replay record is
[`PARALLEL-EVIDENCE-ROUND-SIXTEEN.json`](PARALLEL-EVIDENCE-ROUND-SIXTEEN.json).

## Result

Parallel replay is **adopted** from the Round Five evidence at
`51bd525311dd98dc933655252120e4fe4a501550`, not from a timing claim.  The
artifact records empty row, suite, restoration, and cleanup gate lists.  Serial
remains the oracle and remains available.

Fresh final-local receipts at `bcc2346`:

- `python -B anti-dark-code/scripts/adc.py validate --skill anti-dark-code --mode universal`:
  exit 0, `VALID (universal): 0 errors, 1 warning(s)`.  The warning is only
  generated `__pycache__`, which universal validation deliberately ignores.
- `python -m pytest anti-dark-code/tests -q -p no:cacheprovider`: exit 0,
  `481 passed, 14 skipped, 57 subtests passed in 248.32s`.
- `python -m pytest anti-dark-code/tests/test_route.py::MutationMatrixIntegrityTests -q -p no:cacheprovider`:
  exit 0, `9 passed in 0.16s`.
- `git diff --check` and `git status --short` were empty before this handoff.

## Independent decision checklist

| Decision | Verdict | Reproducer and fixed checklist result |
| --- | --- | --- |
| D-085 | upheld | `AcquisitionAgainstRealGitTests::test_a_filter_name_containing_an_equals_cannot_run` demonstrates that an `a=b` filter cannot execute during acquisition.  The original `-c` spelling was exploitable; effective-key verification refuses comparison if neutralization is still live. |
| D-086 | amended by D-091 | `SelfGradingAuthorityTests::test_one_authority_reference_cannot_cover_two_cheap_ones` proved that one representative pass reference could hide the other two.  All three routing-owning references are now probes. |
| D-087 | upheld | `MutationMatrixIntegrityTests::test_every_mutant_target_occurs_exactly_once` holds each active mutation to exactly one literal target; superseded rows are intentionally excluded. |
| D-088 | upheld | The real-Git `a=b` filter reproducer proves `GIT_CONFIG_COUNT` neutralizes the inexpressible key; unreadable keys remain live/fail-closed. |
| D-089 | amended by D-091 | The calibration-layout attack proved a cheap route was possible through an unprobed calibration spelling.  Calibration roots and installed spellings are now derived and tested. |
| D-090 | amended | `MutationMatrixIntegrityTests::test_decision_guard_recurses_through_claimed_source_classes` places a dangling decision citation in nested scripts, tests, and routing Markdown.  The guard now recursively covers those claimed source classes. |

The literal owner walkthrough was rerun and corrected in `868a0db`
(`WALKTHROUGH-SLICE-001.md`): its D-080 extraction is a single executable
Python command and its matrix narrative distinguishes the then-missing Linux
per-row bookkeeping from the existing Linux CI fact.  It remains an owner
walkthrough, not an approval.

## Two-host mutation evidence

The matrix has **95 rows: 91 active and 4 superseded**.  All 91 active rows
have both Windows and T540P Linux records; the T540P refresh is commit
`fdfbda90495b0cb4e426e1f425859a222a4c0f41`.

The Linux run used a detached `03540a846d4ef85c3dbd232c726789b4d5574c4e`
checkout, Git 2.43.0, Python 3.12.3, pytest 9.1.1, kernel
`7.0.0-30-generic`, and a disposable CI-shaped virtual environment.  Its
canonical command was `python design/routing/mutants/replay.py --write`, exit
0, with `95 mutants, 0 not caught: none`.  The recorded **1215.277 seconds**
is the measured duration of the complete isolated evidence command (clone,
checkout, environment setup, replay, restoration/blob checks, and
matrix/status checks), not the replay subprocess alone; execution metadata id
`exec-286c7fd0-cc60-4efe-b52c-e1c607b05393` recorded exit 0 and 1,215,277 ms.

All five mutable sources matched frozen, before, and after SHA-256 values;
the remote status was matrix-only, its transferred matrix hash matched, and
both remote and local owned roots were cleaned.  The evidence records the five
source hashes rather than duplicating them here.

M61--M63 were retargeted to the replay authority controls and caught on both
hosts: M61 holds the `sys.executable` launcher, M62 the raw-byte mutation and
restoration path, and M63 the anchored pytest-summary gate.  Their fresh Linux
summaries were respectively `1 failed, 291 passed, 9 deselected, 9 subtests
passed`, `2 failed, 290 passed, 9 deselected, 9 subtests passed`, and `1
failed, 291 passed, 9 deselected, 9 subtests passed`.

## Exact replay identity and cleanup

The adopted comparison is read-only at `51bd525` against matrix SHA-256
`e690d16e77107cc6a5581ab7f54a6d92b28a58be4a279208f27b6776c57f6564`.

- Serial `--jobs 1`: exit 0, report `round5/serial.json`, SHA-256
  `538346bdb97b8cd0af75f9c9bbfc70d6885da7fd5cd976057409e71747d3f1f3`.
- Parallel `--jobs 8`: exit 0, report `round5/parallel.json`, SHA-256
  `8eda90dd462864c26e18d88a9d3b628600707fb9687fe8c4639c8746dd18d34e`.
- Both report 95 canonical rows and `95 mutants, 0 not caught`; matrix hashes
  before and after are equal.  The full normalized identity digest is the
  same in both reports:
  `c291ae2ea09a2025cdf8bf9ab200ef66472e9fc39b8f08da883a240aa66d94dd`.
  It compares state, status, verdict/caught, skip reason/count, return code,
  parsed pytest summary/counts, source hashes, frozen commit, and restoration;
  it excludes only duration and worker label.  There are no missing, extra,
  duplicate, reordered, or mismatched rows.
- M37, M46, and M48 intentionally remain local `SURVIVED` rows with
  `skipped=1`; M79 is caught in both modes.  M36 and M79 are therefore part of
  the equal normalized comparison, not exceptional adoption paths.
- Every row restored its source.  All eight parallel worker cleanup records
  report clone removal, auxiliary pytest-root removal, and owned-root removal.
  No cleanup failure remains.

The reports retain cumulative per-row durations (serial 5,446.198 s; parallel
10,679.835 s).  They are not aggregate coordinator wall-clock measurements,
so this handoff does **not** invent a replay speedup.  The separately measured
suite trials demonstrate the expected process-parallel wall-clock reduction
below; identity, restoration, and cleanup are the adoption criteria.

The abandoned Round Two M79 reports are diagnostic-only, not adoption
evidence: serial SHA-256
`a134faf9666407ca26e7671c401a13c27b1fcb7e06b6182075afa624a49baa5d` versus
parallel SHA-256
`516922236a849bcc11a7dc6ffc3b735f8702ffbe65e03830c0e59e3d593d2d90` exposed
a Git-index refresh precondition.  `d5168c1` made that precondition
deterministic.  `51bd525` independently removed M36's fixture-repository
index-refresh side channel.

## Suite stability

Round Five first collected **494 exact node ids** (collection SHA-256
`b472b64c61a53b33d8e10405489a64d40f45ace5b28fe56811c7dded70e48196`).  An
external evidence-only controller plugin reconstructed every outcome by exact
node id.  All six runs were exit 0, bijective to collection, and produced the
same outcome-set SHA-256
`68ec624bdd0ca4dad6c01ea672c18b55d30700d4e71e6fb80aa374e041da3aa8`:
480 passed, 14 skipped, zero failed, and zero errors.

| Runs | Durations (s) | Collection proof |
| --- | --- | --- |
| serial-1, serial-2, serial-3 | 246.80, 243.62, 248.23 | Each is one-to-one with all 494 ids. |
| xdist-1, xdist-2, xdist-3 (`-n auto`) | 39.00, 41.27, 43.62 | Each has 32 worker collection lists; every ordered list exactly equals the 494-id collection. |

The suite trial timing is an observed comparison, not an eligibility shortcut:
the exact set equality above is the stability gate.

## Provenance and CI decision

D-092 excludes `.pytest_cache` from managed-source provenance.  Local
controlled commands retain `-p no:cacheprovider` because cache state in the
managed tree used to alter the digest while remaining Git-ignored.  Generated
`__pycache__` is a validator warning only.  This is why the fresh local gates
above retain the flag; the CI workflow uses a pristine checkout and its own
contract.

`af57da7` adopts the measured CI settings: both suite-running install steps
install `pytest-xdist`; both full suite invocations retain
`anti-dark-code/tests` and add `-n auto`; the mutation replay has exactly
`python design/routing/mutants/replay.py --jobs 2`.  It has no `--id`, no
`--write`, and no selective test subset.  `bcc2346` adds the workflow contract
test that rejects a selective replay command rather than merely detecting
parallelism.

CI is **pending until a new PR is opened and its required jobs run**.  No push
or PR was made as part of this handoff.

## Non-negotiable boundaries and remaining SLICE-001 blockers

- No routing-policy rule was approved; candidate/shadow information cannot
  select executable gates.
- Selective local and CI execution remain prohibited; CI's parallel replay is
  the complete matrix, not a selector.
- SLICE-001 is not `Done`.  The owner must run the literal walkthrough, record
  every command/expectation difference, answer questions 1--6, and personally
  approve its last checkbox.  A separate change may then change slice state.
- The `_repo_fingerprint` owner decision remains **provisional** (D-073's
  unreadable-index alternative); it must not be silently treated as an owner
  decision or final policy.
- Parallel adoption does not authorize changing routing policy, evidence
  labels, owner approvals, or the serial oracle.

## Runtime postmortem

The user-observed minimum is **1261 minutes (21h01m)**.  Its scope is total
wall-clock time from goal start, including discarded/restart investigation;
it is not any individual replay or gate duration.  A clean path is estimated
at **2.5--3.5 hours**.

Necessary clean-path cost: fresh universal/full/integrity gates, the isolated
T540P bookkeeping replay, exact serial and jobs-8 comparison, and six
collection-bijective suite trials.  Avoidable/restarted cost: wrong-worktree
provenance, M79 deterministic-precondition diagnosis, M36 index-refresh
side-channel diagnosis, and discarded wrapper/plugin evidence.  Before any
gate expected to exceed 60 minutes or per-mutant full-suite replay, require a
runtime forecast and explicit acknowledgement.

## Complete round-sixteen commit ledger

- `908d43d` docs: specify round sixteen verification
- `5367bc9` docs: incorporate round sixteen review
- `d6749a6` docs: plan round sixteen implementation
- `a541bbf` fix: guard every routing-owning pass reference
- `45a6a34` test: derive the decision reference scope
- `bc3505b` fix: exclude pytest cache from provenance
- `868a0db` docs: make the owner walkthrough literal
- `ba47668` evidence: restore the T540P mutation record
- `bfd4402` refactor: structure serial mutation evidence
- `e5f9ba2` fix: harden serial replay evidence
- `03540a8` feat: replay mutants in isolated process clones
- `fdfbda9` evidence: refresh final T540P mutation record
- `20548ca` fix: preserve superseded rows in parallel replay
- `52d3d86` evidence: prove parallel execution identity
- `7b0c185` fix: preserve superseded rows on preflight failure
- `c5b8c65` fix: isolate mutant bytecode between replay rows
- `915001a` fix: isolate replay bytecode without cache deletion
- `d5168c1` test: make index-refresh mutation deterministic
- `51bd525` test: remove M36 index-refresh side channel
- `32f42bd` evidence: prove parallel execution identity
- `c906b51` evidence: correct round five trial references
- `bd9460a` evidence: correct round five replay references
- `5e880db` evidence: record replay pytest count identities
- `dc3f85f` evidence: qualify unavailable T540P duration
- `cafb1f6` evidence: record T540P command duration
- `078b8bb` evidence: update runtime postmortem
- `17d8dd4` evidence: clarify runtime postmortem scope
- `af57da7` ci: use proven parallel verification
- `bcc2346` test: reject selective CI replay

The only uncertainty is intentionally explicit: no new-PR CI result exists
yet, and replay report data does not store a coordinator wall-clock duration
from which to calculate a defensible replay speedup.
