# Handoff back: the policy store, the dominance probe, and the release

Date: 2026-09-04. From: Opus 5, which implemented `HANDOFF-OPUS-SLICE-002-R3.md` and stopped at its stop point. For: the owner, then Jeremy for M11, then Sonnet 5 for the periodic ingest and summary.

## 1. Terminal outcome

M8, M9 and M10 are built, tested and committed. M11, 1st-downs' pull request, is deliberately not opened: the handoff's stop point is after the release is checked and before that pull request, which the owner and Jeremy open.

Two decisions were recorded rather than made silently, and one of them is the owner's own answer to a question this build raised.

- **D-136** corrects D-133 on where a record's router is found. Read literally, "the router at the record's head" refused all 55 backfilled records, because a backfill names today's router by D-127's decision and its head is a historical commit whose router never built it. The router is now read from the head for a live or canary record and from the working tree for a backfill, with the digest checked either way.
- **D-137** records the owner's decision, taken as "three now, two later", after the dominance probe met this repository and could not run.

## 2. What was built

| Item | Commit | What holds it |
| --- | --- | --- |
| M8, the policy store and class recomputation | `f8e5c3d` | four `ShadowLedgerCliTests`; M152 to M155 |
| M9, the prose sweep and the dominance probe | `e153bfc` | `SuiteReadsNoRepositoryProseTests`, five `ShadowDominanceCliTests`; M156 to M158; M147 re-anchored |
| M10, the consumer test and the release | `b8ee128`, `4bb7e49` | the consumer ledger test; `release-check` |

Full suite at the head: 566 passed, 14 skipped, 77 subtests. `validate --mode universal`: 0 errors, the one expected pycache warning. Every mutation row was measured to fail its named suite before commit, with the source restored and hash-verified; M152 to M158 carry `pending` for the next authoritative two-host replay.

## 3. The re-ingest, and what it refused

The handoff asked for the existing ledger to be re-ingested under the new check and for the refusals to be reported. It took three runs to get an honest answer, and the first two failures were mine.

1. **All 65 records refused**, with a Python error rather than a verdict: a module holding dataclasses must be registered in `sys.modules` before it is executed, or `dataclasses` cannot resolve its own fields. Fixed.
2. **All 55 backfill records refused**, correctly by the letter of D-133 and wrongly by its intent: they had no policy sidecar, because they were written before sidecars existed. Re-running the backfill wrote them.
3. **All 55 backfill records refused again**, this time `router-unrecoverable`. This was the real finding, and it is D-136.

After D-136, the ledger re-ingests whole: **70 records, zero refusals**, every class recomputed against the policy that built it, in twelve classes. The six D-131 inbox records and both canaries recovered from their heads' calibration exactly as the handoff predicted. The two sidecars the entire ledger rests on are two files, each named by the digest of its own content.

## 4. The dominance probe, and why it has not run here

The probe is built and exercised: a fixture class no gate reads comes back **dominated**, a fixture class an omitted gate reads comes back **NOT dominated**, both refusals fire, and the tree is hash-verified as restored after each probe.

It cannot run in this repository, and the reason is not a defect. Every gate here carries `argv: None`, and the calibration says why in its own note: *"Gate ids mirror the jobs in `.github/workflows/tests.yml`. The router names gates; it does not run them."* `owner_confirmed_safe_to_execute` is false for the same reason. So the probe refuses twice and there is nothing local to execute.

The owner was given three options and chose the third now and the second later, which D-137 records: this repository's `docs-only` class is approvable by neither path, that is written down rather than engineered around, and dominance as a CI act belongs to SLICE-003's design. The first repository to exercise either path is a consumer whose gates are real commands, which is 1st-downs.

One consequence to state plainly: M9 removed the construction PR #38's canary used, deliberately, so that class now has neither a live canary nor a dominance record. PR #38 stays open as the record of the key it belongs to.

## 5. The release

`2026.09.04-unified.9`. VERSION, the CHANGELOG section, the capability catalog and the README carry it; the public brief and the site carry it, the new date, and a section on the campaign written to the brief's own standard, including the canary that came back a miss and the survivorship measurement. The PDF is regenerated from the updated HTML and its provenance names the renderer that made it, which changed with this release from a Linux snap Chromium to Chrome 152 on Windows; the normalized digest is only reproducible on the toolchain the record names, which is why it names it.

`release-check` against a local candidate tag: **`RELEASE OK`**, core reproduced, distribution valid, no undescribed files. It first reported three, and the notes now describe what each change was rather than merely listing it: the calibration templates' `canonical_full_set` block and their starting classifier and proposed rules, and the catalog's V21 and V22.

**The tag itself is not created.** A release tag should point at `main`, and this branch is not merged. After the merge, tag the merge commit `v2026.09.04-unified.9` and re-run `release-check` against it; the candidate run above is the evidence that it will pass.

Two things are deliberately absent from the brief: the four spots that would show a real receipt, decision and record rather than describe them, proposed and never chosen; and the Alongside Superpowers section, which waits in `brief/drafts/` until its author has seen it.

## 6. Open, and for whom

- **The owner and Jeremy.** M11: 1st-downs' pull request, exactly as `design/routing/consumers/JeremyABurton-1st-downs/README.md` walks it, after the tag exists, because the installer refuses an untagged source.
- **The owner.** Whether the brief's four document-showing spots and the superpowers section land in a later release.
- **Sonnet 5.** The periodic ingest and summary, here and for 1st-downs once it has records.
- **The next authoritative replay.** M152 to M158 carry `pending` and no host records.
- **Measured, not assumed, and still open:** whether a fork pull request's read-only token can upload the artifact. Unchanged since the first handoff.

## 7. Boundaries, unchanged

Nothing selective executes. `required`'s needs are untouched. No rule is approved. No classifier entry was narrowed beyond D-129's. Nothing was written to any repository but this one, and the dominance probe refuses to run a gate without the owner's confirmation, which this repository does not give.
