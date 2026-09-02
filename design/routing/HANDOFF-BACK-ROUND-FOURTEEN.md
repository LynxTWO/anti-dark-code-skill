Only the human walkthrough remains before SLICE-001 can be marked Done.

# Handoff back: round fourteen

Date: 2026-08-31. Branch: `codex/round-fourteen-convergence`. Base: `157f10a1b2f0bc1c65e3e1ea92ed49d37316c987` from draft PR 23.

## 1. Outcome

SLICE-001 remains `Proposed`. No routing rule was approved, no selective execution was enabled, and the ADD boundary was not moved. Section 9 and section 11 now close or qualify every evidence item except the owner walkthrough.

The owner script is `design/routing/WALKTHROUGH-SLICE-001.md`. It is a 25-minute terminal sequence with six yes-or-no questions. D-064 is first: every rule remains `proposed`, and any future rule approval is a separate change.

## 2. Linux replay came first

The disposable T540P clone ran Linux `7.0.0-30-generic`, Python 3.12.3, pytest 9.1.1, and Git 2.43.0. The exact incoming base replay reported:

```text
91 mutants, 0 not caught: none
```

Four rows were superseded. M37, M46, and M48 were caught on Linux and remain `caught elsewhere` because Windows skips their symlink coverage. Pre-run and post-run SHA-256 values matched for `adc.py`, `adc_receipt.py`, `adc_route.py`, `test_route.py`, and `replay.py`.

The replay corrected an incoming record error. M68, M90, and M91 had no host result, while the handoff described M90 and M91 as Windows-only. Linux caught M68, M88, M89, M90, and M91. Windows then caught the genuinely missing M68, M90, and M91 rows. The 91-row record had both hosts before convergence work began.

D-082 adds installed-layout protection and M92. M92 was caught on both hosts:

```text
Linux:   1 failed, 243 passed, 6 deselected in 10.08s
Windows: 1 failed, 242 passed, 1 skipped, 6 deselected in 45.37s
```

The final matrix has 92 rows, 88 active and 4 superseded, with no missing host and no survivor. The disposable clone and virtual environment at `/tmp/adc-round-fourteen-replay.uJz21xD6` were deleted after their absolute paths were verified. That deletion is unrecoverable and removed only the disposable replay tree.

## 3. Task 13 actual

The written plan used the removed `route --changed-from` flag. The current interface is `route --base`; the plan and slice now say so.

At checkpoint `ea8733c`, the actual route command returned Level 3, passes `07,10,11,14`, the five canonical gates, no matched rule, `force_full=true`, and `complete=true`. Receipt `59f3951317c0e7bc897bc5b137fc05f9b29766170d4cd4f47795f62725632137.json` verified `FRESH`. An earlier Task 13 probe verified stale after an untracked edit and fresh after removal. Later documentation commits correctly stale the checkpoint receipt.

The two actual refusal probes were:

- unreachable base: exit 0, Level 3, `complete=false`, `ADC-ROUTE-BASE-UNREACHABLE`;
- invalid policy JSON: exit 2 with `REFUSED`, no new receipt, followed by byte-for-byte restoration.

The current Windows suite reported `425 passed, 14 skipped, 48 subtests passed`. Universal validation reported 0 errors and one expected generated-artifact warning. Required run `33402328694` passed Linux, macOS, Windows, Python 3.13, distribution, hostile-environment, mutation replay, and the `Tests` aggregator at PR 23 commit `157f10a1b2f0bc1c65e3e1ea92ed49d37316c987`. The post-run branch delta has Windows suite evidence and Linux and Windows M92 evidence; it does not claim a new macOS run.

## 4. Evidence closures

- D-080 withdraws the unreconstructible historical per-change EDD claim. The earlier range has a qualified slice-level result. Commit `ea8733c` is the forward anchor, and it and every later commit carry `EDD-Checklist: satisfied`.
- The K, L, and N section 9 bullet is now a 30-row ledger. Twelve ids retain direct passing-after verdicts, N-08 closes under D-079, and 17 name the successor finding and requirement that carries their substance.
- D-081 retires the standing historical live-mutant scan after round thirteen reproduced 164 commits, 58 matrix-bearing commits, 2,994 first-pass pairs, 7,423 second-pass pairs, the single `a92c869` and M01 live-mutant state, and 12 drift pairs. `MutationMatrixIntegrityTests` and the required integration workflow are the maintained successors; the CI limitation on intermediate branch commits is explicit.
- D-082 closes D-071 portability. The load guard derives `.agents/skills/anti-dark-code/...` aliases from source paths. The regression test failed before the change, passes after it, and M92 holds the exact reversion.
- D-083 confirms D-073 alternative 1. An unreadable fingerprint raises typed `ReceiptError`, returns a clean refusal, and mints no digest.
- D-084 keeps D-077 strictness. The current gate configuration has no executable `argv` and owner execution confirmation is false. A future writing gate must use an isolated checkout.
- R-022 now maps both exact nodes. The independent challenge built a candidate selecting only `validate-core` against the five canonical ids and called the real selector; it raised `CandidateRoute cannot select executable gates`.
- All 51 S-ids name an R-id. Forty-nine use collected tests. S-014 and corrected S-050 use R-053 mutation replay.

## 5. Commits

The six implementation commits before this handoff are:

1. `d5a1aaf` `routing: replay round-thirteen matrix on Linux`
2. `1a53206` `routing: complete the round-thirteen two-host record`
3. `f4cdaeb` `routing: protect installed self-grading paths`
4. `6986cc4` `routing: record portable guard mutation`
5. `ea8733c` `routing: map candidate gate-removal coverage`
6. `53bc5ab` `routing: close slice evidence for owner review`

The first two preserve the requested replay order. The next two close the three-round D-071 portability gap with red-green evidence and a two-host mutant. The last two anchor forward EDD review, correct traceability, close the documents, and prepare the owner gate.

## 6. Boundaries preserved

- Every routing-policy rule is still `proposed`.
- `owner_confirmed_safe_to_execute` is still false, and no gate carries `argv`.
- Candidate data is refused by receipt construction, verification, and executable gate selection.
- SLICE-001 is not `Done`; its human checkbox is empty.
- Selective local and CI execution remain disabled.

Run `design/routing/WALKTHROUGH-SLICE-001.md`. If the owner records the six decisions and approves the last checkbox, a separate follow-up may mark the slice `Done` and move the ADD boundary to SLICE-002.
