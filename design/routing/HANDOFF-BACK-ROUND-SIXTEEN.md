# Handoff back: round sixteen

Date: 2026-09-02. This handoff covers the Round Sixteen implementation and
frozen evidence head through `f3d08a45d4f0b2fb9f1e62b97014187dd2853977`;
documentation and final-CI receipt commits follow it. The durable evidence
record is [`PARALLEL-EVIDENCE-ROUND-SIXTEEN.json`](PARALLEL-EVIDENCE-ROUND-SIXTEEN.json).

## Result

Parallel replay is **adopted from current-head evidence**, not from timing or
the superseded Round Five record. Serial remains the oracle and is available as
`--jobs 1`. The final matrix has **96 rows: 91 active and 5 superseded**; all 91
active rows carry both Windows and T540P Linux records.

The frozen `f3d08a4` evidence gates are empty:

- row mismatches: none;
- suite outcome-set mismatches: none;
- restoration failures: none;
- cleanup failures: none.

Fresh pre-documentation baseline receipts at that head were:

- universal validation: exit 0, `VALID (universal): 0 errors, 1 warning(s)`;
  the warning names ignored generated `__pycache__` entries;
- serial full suite: exit 0, `486 passed, 14 skipped, 62 subtests passed in
  263.07s` (263.549 seconds wall clock);
- mutation-matrix integrity: exit 0, `9 passed in 0.21s`;
- clean status and matrix SHA-256
  `d7e88dcc2a8f3d3e4158a505cf13a77584b821c4fb54ecb0833e6ba2ab9e18ba`.

Final post-documentation local gates and final-head CI are recorded below when
they exist. A pending field is not evidence.

## Fixed adversarial checklist

The review stayed on the handoff's fixed attack list; these are measurements,
not a second open-ended design round.

| Decision | Verdict | Measurement |
| --- | --- | --- |
| D-085 | upheld | A deterministic 297-name real-Git corpus accepted 296 configurations; all 296 acquisitions were complete, all 296 ran the worktree comparison, and repository filter markers executed zero times. The direct nonzero-query control returned the injected live key rather than treating query failure as absence. |
| D-086 | amended by D-091 and D-093 | Installed-layout derivation is still required, but one path per class was not enough: distinct routing-owning references and broader authority classes could still be partitioned cheaply. D-091 added every pass-owning reference and D-093 added the canonical classifier contract. |
| D-087 | upheld | Every then-active row had exactly one literal target, 91 distinct effective `(source, mutant SHA-256)` values, no no-op replacement, and no effective collision. Superseded rows invoked no suite; the final matrix integrity gate remains 9/9 after M96 and D-094. |
| D-088 | upheld | The corpus included 96 names whose first `--get` through command-line overrides returned nonzero; numbered environment configuration recovered all 96, including leading `=`, without filter execution. `_live_filter_programs()` also treated an injected `None` query result as live/fail-closed. |
| D-089 | amended by D-091 and D-093 | Calibration-root derivation closes the measured fallback-layout hole, but it did not establish coverage of every distinct authority file or class. Those broader claims now belong to D-091 and D-093. |
| D-090 | amended | A nested-script/test/routing-Markdown attack bypassed the original top-level list. `test_every_referenced_decision_exists` now recursively derives all claimed Python and routing-Markdown sources, and the final integrity suite passes. |
| D-091 | upheld within its scope | Exact cheap classification of either omitted routing-owning reference is rejected. It remains a path-set guarantee; D-093 supplies the separate class contract. |
| D-092 | upheld | A tagged fixture containing a real `.pytest_cache/.gitignore` and cache payload keeps the same managed file set, provenance digest, and `git-tag` classification. Authoritative commands still use `-p no:cacheprovider` to keep evidence runs sterile. |
| D-093 | broken, repaired, then confirmed | The first class-contract implementation could be disabled by deleting every authority-labelled entry and retaining only a cheap exact classifier. `7b0dc2d` now requires the full canonical class set for every nonempty classifier paired with any non-force-full rule; empty and all-force-full policies retain their safe compatibility. |
| D-094 | upheld | The frozen T540P run measured M92 surviving because D-093 made its old path-loop reversion inert. M96 attacks the stronger load-time contract and was caught on both hosts, so superseding M92 records rather than hides the changed guarantee. |

The retained attack generator, harness tests, and measurement have SHA-256
values respectively
`62a91547f3fefda1232e61efe1797dda6854b2d55ac747ce838d7742514ed359`,
`37f5f7019f77ce1d2210360b6d9f40967e911ecfb43bdf49526c752250bbccbc`,
and `9df495a3cfcac922823264c8dca008d3f96e2249310d7a6750d850ef567d0788`.
Eight unneutralized positive controls executed 14 marker writes while production
neutralization executed none, proving the fixture could observe the attack.

The traceability challenge selected **R-021** rather than trusting the empty
`untraced` list. Exact cheap classifiers for mutation harnesses, repository
metadata, source-scope provenance, workflows, and project manifests loaded and
routed below full despite representative-path tests; D-093 is the resulting
requirement-level repair.

## Two-host mutation evidence

### T540P Linux first

The authoritative Linux write replay used a clean detached checkout at
`0a26531b7a32e9dd126d932b94b4c47ecfb00752`, Python 3.12.3, Git 2.43.0,
kernel `7.0.0-30-generic`, disabled pytest cache and bytecode, and a disposable
CI-shaped virtual environment. It began `2026-09-01T18:45:44-04:00`, ended
`19:11:08-04:00`, and took **1,524 seconds**, including clone/setup/checks.

`python design/routing/mutants/replay.py --write --report <external>` exited 0
with `96 mutants, 0 not caught: none`. The report SHA-256 is
`3b2cd5e60582fc670523b6a0d66b13831f0d7cd0797546a9f886243d4b6034ce`;
its generated matrix SHA-256 is
`cfcb3f8fa2da32400d1661445bfebed8d5b50c0cfedb4c93c538be0a751685ff`.
All 96 rows restored and all five mutable source hashes matched frozen/before/
after bytes. Remote status was matrix-only and the owned remote root was
removed after transfer.

At this frozen point the report held 92 completed and 4 superseded rows. M92's
local survivor was the D-094 finding, not a replay failure to paper over: its
old attack had become redundant, while M96 caught the stronger guarantee.

### Windows and final record

After D-094 superseded M92, the authoritative Windows write replay used clean
commit `ff95c8c4e5a7a5a4179b70b3a90f02259d03408a`, Python 3.14.2, Git
2.50.1.windows.1, disabled pytest cache and bytecode, and source bytes equal to
the commit blobs. It began `2026-09-01T19:17:44.3443460-04:00`, ended
`21:08:45.2058977-04:00`, and took **6,660.666 seconds (1h51m)**.

The same `--write --report` shape exited 0 with `96 mutants, 0 not caught:
none`. Report SHA-256 is
`6e613b1530ad5da5bea111f4b9ade3ce86aabd2f71f3662bcb59310588edd564`;
the generated matrix SHA-256 was
`8441237dc1d06a2013c97e8f9ca776854fcf6ce02a9253bcac2987e79bd8c63d`.
The later M96 note-only annotation changed the committed matrix digest to
`d7e88dcc2a8f3d3e4158a505cf13a77584b821c4fb54ecb0833e6ba2ab9e18ba`;
it did not change result data and did not justify repeating the expensive
replay.

M61, M62, M63, and M96 are active and caught on both hosts. Their final Windows
summaries are respectively `1 failed, 299 passed, 1 skipped, 9 deselected, 14
subtests passed`, `2 failed, 298 passed, 1 skipped, 9 deselected, 14 subtests
passed`, `1 failed, 299 passed, 1 skipped, 9 deselected, 14 subtests passed`,
and `13 failed, 292 passed, 1 skipped, 9 deselected, 9 subtests passed`.

## Exact replay identity and cleanup

Both comparison runs were read-only at exact commit `f3d08a4` and matrix digest
`d7e88dcc2a8f3d3e4158a505cf13a77584b821c4fb54ecb0833e6ba2ab9e18ba`:

- serial `--jobs 1`: exit 0, **6,585.939 seconds (1h49m46s)**, report SHA-256
  `5934573d24fcec957ae74f64797936dcc12ba48c25c20c666a1e3b5c096beefe`;
- parallel `--jobs 8`: exit 0, **1,903.084 seconds (31m43s)**, report SHA-256
  `73c3016cec363d05eee0a21297f7451f5685752aebe50656606a6a8cd323b223`.

Both contain 96 canonical rows in the same order, 91 completed and 5
superseded, with zero duplicate, missing, extra, reordered, or mismatched rows.
The normalized identity digest is identical:
`13b75072ae9c54045f84ae97cc59c9a8676aceac3c05702e415934e3340d2ecc`.
Identity includes state, status, verdict/caught, skip reason/count, pytest
return and parsed counts, source, before/after hashes, post-restore state,
frozen commit, restoration, and host. It excludes elapsed timing, worker label,
and parallel transport fields (`matrix_index`, `clone_retired`).

M37, M46, and M48 are the same Windows-local `SURVIVED`, `skipped=1` rows in
both modes and remain `caught elsewhere` from Linux. Every row restored. All
eight cleanup records prove clone removal, auxiliary pytest-root removal, and
owned-root removal with no error. Coordinator wall-clock speedup was **3.46x**;
that is useful operational evidence, not the adoption criterion.

## Suite stability

The tracked controller plugin
`design.routing.mutants.exact_nodeid_plugin` collected **500 exact node ids**
with digest
`13e8c4023e8d139ff4b5e0f6fb5fdb02d0afe34bc12cd0b5deed7531ff58480a`.
All six trials were exit 0, bijective to collection, and produced the same
outcome-set digest
`e57dd443dd8525aa12944f11d77020015e599a17c1baa09b18225e7339a97bf6`:
486 passed, 14 skipped, zero failed/error/missing.

| Runs | Wall durations (s) | Exact collection proof |
| --- | --- | --- |
| serial-1, serial-2, serial-3 | 270.657, 270.461, 269.624 | Each controller map contains every one of the 500 ids exactly once. |
| xdist-1, xdist-2, xdist-3 (`-n auto`) | 51.521, 51.633, 52.492 | Each has 32 ordered worker collection lists; every list equals the frozen 500-id collection. |

The node-id and outcome sets, not the faster times, satisfy the stability gate.

## CI decision and current status

Local evidence supports the already-staged CI settings: both suite-running
jobs install `pytest-xdist`, complete full-suite commands use `-n auto`, and
the Linux mutation job runs the entire matrix with `--jobs 2`. It has no row
selector and no `--write`; the workflow contract test rejects either weakening.

CI is **pending until the Round Sixteen PR exists and every required job passes
on its final head**. The final run URL, head SHA, and job conclusions belong
here only after observation.

## Owner walkthrough and remaining blockers

`WALKTHROUGH-SLICE-001.md` now detaches the Round Sixteen branch, expects
96/91/91 and no missing host records, checks the current evidence artifact and
PR, and reads D-085 through D-094. Its boxes remain unchecked; this work does
not approve on the owner's behalf.

- No routing-policy rule was approved. All six shipped rules remain proposed.
- Selective local and CI execution remain prohibited.
- SLICE-001 is not `Done`; Daniel Boyd must run the literal walkthrough, record
  any difference, answer questions 1--6, and personally approve the final box.
- `_repo_fingerprint` remains a **provisional implementation pending the owner
  decision**. This round did not silently convert it into policy approval.
- Parallel adoption changes execution mechanics only; it grants no routing,
  evidence-label, or owner-approval authority.

## Runtime postmortem and warning proposal

The owner-observed **21h01m** was total wall clock from goal start at that
checkpoint, not any replay. At evidence-artifact construction the goal manager
reported **101,016 seconds (28h03m36s)** total elapsed; the final goal total is
recorded after CI.

The final authoritative evidence commands themselves total **17,905.033
seconds (4.974 hours)**:

| Gate | Wall time |
| --- | ---: |
| Linux two-host write | 25m24s |
| Windows two-host write | 1h51m01s |
| baseline full suite | 4m24s |
| read-only serial replay | 1h49m46s |
| read-only parallel replay | 31m43s |
| three serial stability trials | 13m31s |
| three xdist stability trials | 2m36s |
| collection and universal validation | 1.4s |

The difference between roughly five hours of final gates and whole-goal
elapsed is implementation, adversarial diagnosis, independent review,
discarded evidence, restarts after real findings, remote coordination,
documentation, and waiting. A clean Round Sixteen-shaped path is now forecast
at **5.5--7 hours**, including final review and CI but excluding queue outages.

Before launching a costly mutation gate, the skill should show:

1. active mutant count and whether the repository mandates a full affected
   suite per mutant;
2. a measured suite sample and worker count;
3. an estimated range based on
   `active_mutants × suite_seconds ÷ effective_workers`, widened for clone,
   setup, cleanup, and host variance;
4. explicit confirmation when the upper estimate exceeds a threshold such as
   30 minutes; and
5. completed/total progress plus a revised ETA while running.

That warning changes consent and observability, not evidence strength. Full
per-mutant execution remains an exceptional repository contract, not the
default cost of using Anti-Dark-Code on an ordinary repository.

## Round Sixteen commit ledger through the evidence head

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
- `2f9a827` docs: hand back round sixteen
- `b3ea5ae` fix: guard self-grading authority classes
- `7b0dc2d` fix: fail closed for cheap classifiers
- `0a26531` evidence: track exact suite outcome collector
- `ff95c8c` evidence: refresh Linux record and supersede M92
- `f3d08a4` evidence: complete final two-host mutation record
