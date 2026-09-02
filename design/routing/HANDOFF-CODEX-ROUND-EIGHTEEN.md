# Handoff to Codex: round eighteen

Date: 2026-09-02. Starting point: the head of `claude/round-seventeen-verify`, draft PR #27.

## Objective

Three things, in order: **verify round seventeen**, **restore the two-host record for M97, M98, and M99**, and **present the serial-replay trade to the owner**.

Round seventeen was written by Claude and audited by Claude. Round fifteen was too, and round sixteen found two of its defects within minutes of starting. Assume the same here.

Read first:

1. `design/routing/HANDOFF-BACK-ROUND-SEVENTEEN.md`
2. `design/routing/DECISION-LOG.md`, D-095 through D-099
3. `design/routing/WALKTHROUGH-SLICE-001.md`, which the owner will run

### What a failed round looks like

- Round seventeen is accepted because its tests pass and CI is green. CI was green for sixteen rounds while D-095's hole existed; green is where this project's defects live.
- M97, M98, and M99 receive Linux records without anyone checking that each mutant still attacks the branch its note names.
- The walkthrough is re-read instead of re-run.

## 1. Verify round seventeen

Five decisions are new and all are Claude's. Attack them, do not review them.

- **D-095, the masked survivor.** The claim: a survivor on a host that skipped nothing is SURVIVED regardless of stored records, so the Linux CI job now fails on any Linux survivor. Measure it the way round seventeen did: in a clean clone, weaken the one test that holds a row Windows once caught, run `replay.py <row> --jobs 2` on Linux, and confirm exit 1 and the row in the not-caught list. Then look for what D-095 still lets through. Windows skips the symlink test on every row, so every Windows-local survivor still rests on the Linux record and is only disclosed. The skip count is one integer and cannot say which test skipped. Say whether the disclosure is enough or whether a Windows survivor under an unrelated skip should block, and what evidence would tell the two apart.
- **D-096, the clean coordinator.** The claim: parallel replay refuses a coordinator whose `git status --porcelain` is non-empty before any clone exists. Two soft spots to start from. The check runs once, before cloning, and says nothing about a tree edited while clones are being made; measure whether a clone can observe that. And the check does not apply to serial replay, which still replays whatever is on disk and records `commit` as if it were HEAD.
- **D-097, authority by name.** The claim: every script `adc.py` loads is authority through the `adc*` name, held by a table test that scans `adc.py` for quoted names. Find a way `adc.py` could load a helper without naming it as a string literal, or a script matching `adc*` that is not authority, or a reviewed standalone script that becomes loaded without the scan noticing.
- **D-098, the worker rootdir.** The claim: `--rootdir=<clone>` keeps a worker's collection tree inside its clone, so a coordinator beneath the host temp directory no longer scans that directory at every row. Round seventeen proved the failure by reproduction and the fix by a full run under the same churn. Look for what else in a worker's pytest session reaches outside the clone: `confcutdir`, rootdir-relative caches, the `-p` plugin path, or a `conftest.py` above the clone that pytest would still load.
- **D-099, the surfaced reason.** The claim: an inconclusive worker row is reported with its own `error`. The coordinator now trusts one more string from an untrusted worker payload. Confirm the truncation holds and that nothing in that string can reach a shell, a log-injection point, or the matrix.
- **The trailer finding.** Seven round-fifteen commits carry no `EDD-Checklist` trailer inside D-080's forward range. Round seventeen recorded the violation in SLICE-001 rather than rewriting history. Check the count against `git log ea8733c..`, and check that no other range is affected.
- **The walkthrough.** Round seventeen ran it literally on a fresh clone at `92e028e` and every expectation held. It then edited the expectations for this branch. Run every command as written on this head and compare literally; an edited expectation is a fresh claim.

## 2. Restore the two-host record

M97, M98, and M99 carry Windows records only. Replay the full matrix on T540P under the D-068 rules from a clean `core.autocrlf=false` clone and record their Linux verdicts with `--write`. The Linux CI job has caught all three on every run of PR #27, so the Linux fact exists; the per-row record is what is missing. If any survives on T540P, that outranks everything else in this handoff. Read the `(here: SURVIVED)` notes and the disclosure line, not only the summary.

## 3. The serial question

`--write` is serial-only and serial replays the disk. D-096 protects parallel only. Options:

1. serial refuses a dirty tree the same way;
2. serial records `git status --porcelain` in the report and `--write` is refused while it is non-empty;
3. serial is left alone and the limitation stays documented.

Measure what each costs the round-robin workflow, where handoff documents are edited during long serial runs, and present the trade to the owner with the measurements. Do not decide it.

## Traceability gate

`untraced` is still empty. Round seventeen added one node to R-021 and two mutation rows to R-053. Pick a requirement neither round touched and try to disprove its coverage by running the real code against the case its clause names, the way round thirteen found R-018 and round sixteen found R-021.

## Non-negotiable boundaries

- Do not approve any routing-policy rule.
- Do not enable selective local or CI execution.
- Do not mark SLICE-001 `Done`. The last box is the owner's.
- Do not weaken D-095 to make a Windows replay read cleaner; the disclosure line is the honest state.
- Do not tick an evidence item without the evidence it names.

## Deliverables

1. A recorded verdict on D-095 through D-099: upheld, amended, or broken, with the measurement behind each.
2. M97, M98, and M99 recorded on T540P Linux.
3. The serial-replay trade presented to the owner with measurements.
4. `design/routing/HANDOFF-BACK-ROUND-EIGHTEEN.md` naming what still blocks `Done`.

Treat any statement in round seventeen's handoff as a claim to test, not a fact to read. Its author found two of round sixteen's claims false by running the code round sixteen had already run.
