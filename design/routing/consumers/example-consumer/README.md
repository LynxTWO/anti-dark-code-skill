# Illustrative historical consumer configuration

This directory preserves the shape of an earlier ADC campaign proposal (D-135). It is an anonymized illustration, not calibration bound to an existing repository, a current installation request, or evidence of owner approval. Historical measurements elsewhere concern anonymized source cases; they are not measurements of this example.

The adjacent files show how a two-gate campaign can describe a test step and a replay step. Job names, paths, commands and gate mappings are examples. Do not copy them as ready-to-run calibration or infer that another repository has these jobs.

## What the example contains

- `gates.json`: two illustrative gates, disabled and proposed, with global execution confirmation false. The canonical full-set mapping shows the historical shape; it must be derived again from the target repository's actual obligations.
- `routing-policy.json`: illustrative classifier entries and proposed rules. A proposed rule does not authorize omitting checks.
- `shadow-gate-map.json`: example step names within one `test` job; they are not verified against any current workflow.
- `shadow-job.yml`: a workflow fragment based on the shared template, with example job dependencies. It is not an executable installation plan for another repository.

## Adapting the shape

Start with the target repository's source, current CI and owned calibration. Derive its real canonical gate set, commands, environment and source bindings; preserve existing records and review any merge. Use the shared operator and verification guidance to prepare a concrete proposal. Only that repository's current authority can cover installation, calibration writes or execution. No historical permission is carried by these files.

A reviewed campaign keeps evidence outside the consumer when that is its chosen arrangement. The following syntax is illustrative and unexecuted; replace every placeholder using reviewed evidence before proposing a command:

```text
python -B anti-dark-code/scripts/adc.py shadow ingest \
  --repo <clone> --repository <owner>/<repository> \
  --map <clone>/.github/shadow-gate-map.json \
  --source <downloaded-artifacts> \
  --ledger <reviewed-ledger-directory> \
  --month <yyyy-mm> --main <reviewed-main-ref> \
  --write-pull-requests <reviewed-pull-request-record>
```

Ingest and backfill records retain their actual provenance. A backfill does not count toward the live sample threshold. The example does not approve a rule, enable a gate, change a required check, or authorize a write to any repository.
