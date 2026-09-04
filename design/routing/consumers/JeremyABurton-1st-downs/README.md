# 1st-downs: the campaign's first consumer

A proposal for one pull request in `JeremyABurton/1st-downs`, per D-135. The
four files beside this one are what that pull request adds, with one job. The
calibration is authored for 1st-downs from the read-only field study of
2026-09-03, in which all 45 of its pull requests were measurable, seven were
`clean` for the `docs-only` class, and none was a miss. It is a proposal:
its owners edit it before it lands, and nothing here is copied from this
repository's own calibration.

## Why 1st-downs

It is the only repository the field study measured that can meet the
criterion's fourth condition, two distinct authors. This repository has one.
Its CI costs 34 seconds, so no time is saved by anything; the product is the
graded record (D-130), and this is where it is first measured rather than
argued.

## The pull request, step by step

1. **Upgrade the skill.** 1st-downs carries `2026.08.22-unified.8`, which
   predates `adc_shadow.py`. The installer refuses a source that is not at a
   release tag, so this waits on the release that ships the shadow reference
   and templates, named in CHANGELOG under `Unreleased` today.
2. **Calibration.** Copy `gates.json` and `routing-policy.json` from this
   directory into `.agents/skills/anti-dark-code/calibration/`, beside the
   files already there. If a `gates.json` or `routing-policy.json` already
   exists, merge by hand: keep their gates, add the canonical full set, keep
   every rule `proposed`, keep `owner_confirmed_safe_to_execute` false.
3. **Gate map.** Copy `shadow-gate-map.json` to `.github/shadow-gate-map.json`.
   Both gates are steps of the one job `test`: `Run pnpm test` and
   `Run pnpm replay`, which is what GitHub names a bare `run:` step.
4. **The job.** Paste `shadow-job.yml` into `.github/workflows/ci.yml` under
   `jobs:`, after `test`. Its `needs: [test]` is already filled. Do not add it
   to any required check, and do not make `test` depend on it.
5. **Open the pull request.** Its own run produces the first live record as an
   artifact named `shadow-<head>-1`. Download it and check it reads
   `provenance: live`; whatever its status, it is the first record.

## After it lands

Records are ingested here, never there. From a clone of 1st-downs:

    python -B anti-dark-code/scripts/adc.py shadow ingest \
      --repo <clone> --repository JeremyABurton/1st-downs \
      --map <clone>/.github/shadow-gate-map.json \
      --source <downloaded artifacts> \
      --ledger metrics/shadow/consumers/JeremyABurton-1st-downs/ledger \
      --month <yyyy-mm> --main origin/main \
      --write-pull-requests metrics/shadow/consumers/JeremyABurton-1st-downs/pull-requests.json

then `shadow summary` with the same `--ledger` and an `--out` beside it. The
backfill over its 45 pull requests' run history runs the same way, into the
same ledger, with `provenance: backfill`, and never counts toward N.

## What this proposal does not do

- It approves no rule. Every rule is `proposed`; a proposed rule never runs
  less than everything.
- It executes nothing. `owner_confirmed_safe_to_execute` is false.
- It changes no required check and no existing job.
- It writes nothing to 1st-downs beyond the four files and the job.
