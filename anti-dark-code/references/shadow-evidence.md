# Shadow Evidence

A measurement a maintainer installs once, not a pass an agent runs. Load this
reference only when installing the campaign in a repository, or when
ingesting and summarising its records.

## What it measures

The routing policy in a repository's calibration proposes rules: a change of
this shape would need only these gates. Every rule ships `proposed`, and a
proposed rule never runs less than everything. Shadow evidence is how a rule
earns the right to be reviewed for approval: on every pull request, CI runs
the full recipe as it always has, and a non-required job records what the
proposed rules would have skipped and whether anything they skipped failed.

A record is evidence, never a gate. The job is absent from the required
check's dependencies, changes no other job, and blocks nothing. Nothing in
this reference executes selectively.

## What a record says

Each record carries the change (base, merge, head, run, attempt), the route
class (which rules matched, which gates the candidate selected, which it
omitted), the conclusion of every gate as CI reported it, and one status:

- `clean`: every gate passed and at least one was omitted. One unit of
  evidence for the class.
- `miss`: an omitted gate failed while every selected gate passed. The
  candidate would have skipped a failure. Never removed.
- `inconclusive`: a selected gate failed too, so the candidate would have
  caught it anyway; or the base's own run already failed the same gate.
- `no_omission`: the candidate omitted nothing, because the change touched
  something the policy calls verification authority.
- `not_measurable`: a gate did not decide, because it was skipped,
  cancelled, absent, or not yet mapped. Silence never reads as clean.

Records are grouped into classes by a key over the matched rules' terms, the
classifier, the canonical gate set, and the router's own digest. Approving a
rule does not change the key; changing what the rule means does.

## What a repository needs

1. The skill at a version that ships `scripts/adc_shadow.py`.
2. Its own calibration: `routing-policy.json` with every rule `proposed`,
   and `gates.json` whose `canonical_full_set` names the gates its CI runs.
3. `.github/shadow-gate-map.json`, naming which CI job and step carries each
   canonical gate. A gate no job carries reads `unresolved`, and the record
   is not measurable, so a renamed job announces itself in the next record.
4. The `shadow` job from `assets/templates/shadow-job.yml`, added to the
   workflow that runs the gates, with `needs` naming those gate jobs.

The calibration is authored for the repository by its owners. It is never
copied from another repository.

## Install

1. Upgrade the skill with the installer, from a release tag that ships
   `adc_shadow.py`.
2. Write `gates.json` and `routing-policy.json` under the calibration
   directory. Start from `assets/templates/calibration/` and name your own
   gates; keep every rule `proposed` and `owner_confirmed_safe_to_execute`
   false.
3. Copy `assets/templates/shadow-gate-map.json` to
   `.github/shadow-gate-map.json` and name your jobs and steps.
4. Copy the job from `assets/templates/shadow-job.yml` into your workflow.
   Set `needs` to your gate jobs. Do not add it to your required check.
5. Open a pull request. The job uploads `shadow-<head>-<attempt>.json` as an
   artifact, with the policy and gates it used beside it.

## Commands

All are subcommands of `adc.py shadow`.

- `outcomes --map --run --attempt --out`: reduce a run attempt's jobs to one
  conclusion per canonical gate. The job runs this.
- `record --repo --base --merge --head --pr --run --attempt --outcomes --out`:
  build one record for the tree CI verified. The job runs this.
- `backfill --repo --map --branch --out-dir`: replay today's router over
  every pull request's own run history, superseded attempts included, one
  record per head and attempt. A merge commit is never the population, because
  a merge already passed the checks that gated it and cannot show what they
  caught. Backfilled records carry `provenance: backfill` and never count
  toward approval.
- `ingest --repo --map --source --ledger --month`: verify records and append
  them to the ledger. Ingest re-reads every record's outcomes from the run it
  names and recomputes the verdict; a record whose status does not follow is
  refused. A canary that has landed is refused. Nothing is believed because
  it was uploaded.
- `summary --ledger --out`: regenerate the summary from the ledger bytes. It
  counts pull requests per class, not records; a miss on any attempt is the
  class's miss. It is byte-identical on a second run.

Proposed and not yet built, recorded in the design: ingest recomputing the
class itself with the policy kept by digest beside the ledger, and
`dominance`, an approval-time probe for a class no gate reads. Until they
land, the class is verified by its own consistency and the outcomes, not by
recomputation against the policy.

## Where evidence lives

The artifact is an inbox, not a ledger. Records are ingested by a person into
a committed ledger, either in the repository under `metrics/shadow/`, or, for
a repository whose campaign is run from the skill's own repository, under
that repository's `metrics/shadow/consumers/<owner>-<name>/`. In the second
arrangement nothing is written to the measured repository beyond the job,
the map, and its calibration.

## Canaries

Before a class's clean count means anything, the ledger must hold one
canary for it: a pull request on a branch named `canary/<rule>/<date>`, never
merged, whose change of that class deliberately breaks an omitted gate, and
whose record reads `miss`. That is how the comparator is shown to see
failures. Provenance is derived from the branch name, never asserted.

## Boundaries

- The job is never a required check and never a gate.
- No rule is approved by a record. Records make an approval review possible.
- The local gate runner is never a source of outcomes; only CI's own
  conclusions are.
- A record is produced by the deterministic step alone. Adjudication is a
  person's act, signed, and never subtracted silently.
