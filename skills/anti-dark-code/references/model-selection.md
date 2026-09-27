# Model selection and usage comparisons

`scripts/adc_model_policy.py` is a local, pure recommendation helper. It
does not call a model, tools, a network, a subprocess, or mutate host settings.
It answers a narrow question: given the models and controls that the active
host says are live, which already-authorized model route is appropriate for
the next real task? It does not replay work, add a classifier call, or measure
usage by running extra tasks.

Use the active host's actual model-selection control only when it is exposed
and existing user authority explicitly permits a switch. Under that authority,
perform the selected route through the host control without a separate
classifier call, then record both the requested model/effort and the model the
host reports after the work. Preserve a user-selected parent model when switch
authority is absent. An unsupported host has no route: keep the current model
and record `host-selection-unavailable`. A request is not proof that the host
served it.

## Conservative routing

The helper filters the caller's live candidates first. A candidate must be
available now, included by the caller as eligible, and support every required tool, modality,
context marker, and exact requested effort supplied by the caller. Catalog
metadata never proves current host availability or controls. `ultra` and
`max` are different values; the helper does not translate effort names.

For a task with a meaningful, directly checkable acceptance oracle, the
starting heuristic is:

| Task | Tier |
| --- | --- |
| Narrow, bounded, directly checkable work | economy |
| Routine, scoped implementation or exploration | standard |
| Security, destructive, publication, ambiguous, or other consequential work | strong |

The shipped snapshot maps Luna to economy, Terra to standard, and Sol/Astra
to strong. These are dated startup heuristics, not measured competence or a
quality guarantee. The selector preserves the current strong model for strong
work. If requirements, current constraints, quality tier, cost rank, or the
acceptance oracle are unknown, it keeps the current model with a reason.

After a real acceptance check fails, pass a concise evidence locator through
`failure_evidence` and set `verification_failed`. The helper permits one route
to a stronger eligible tier meeting the task's minimum and returns `attempts_to_record: 2`; retain
the failed artifacts and count both attempts. Persist `escalation_count: 1`
after using that route; subsequent calls cannot escalate again. It never retries successful work
for comparison and does not repeatedly escalate. No eligible stronger model
means keep the current route.

## CLI

The CLI only writes one JSON recommendation to standard output:

```text
python anti-dark-code/scripts/adc_model_policy.py --catalog anti-dark-code/assets/model-policy.json --available gpt-5.6-luna --available gpt-5.6-terra --current gpt-5.6-terra --task bounded --can-select --switch-authorized --has-oracle
```

`--available` may be repeated. `--task` is `bounded`, `routine`, or
`consequential`; `--requires-control`, `--required-effort`,
`--verification-failed`, and `--failure-evidence` make the caller's limits
explicit. The CLI's bare available IDs carry no controls, so a requested
control requires a caller integration that supplies live capability metadata
to the pure function. `--request '<JSON object>'` accepts that live metadata,
including model controls and exact supported efforts, with a 64 KiB input cap;
malformed or oversized JSON produces `request-json-invalid`. A `keep-current`
response is a conservative result, not a failure to be worked around.

## Dated catalog and account usage

[`assets/model-policy.json`](../assets/model-policy.json) is a 2026-09-07
documentation snapshot for five exact OpenAI IDs. It has a configurable,
default 30-day freshness limit. It includes Standard API per-million-token
rates and relative ranks with the [official API pricing page](https://developers.openai.com/api/docs/pricing)
as its source. The generic schema accepts any provider/model ID with caller
supplied metadata; it contains no OpenAI-only selection code.

Pricing does not measure actual subscription quota, remaining account usage,
quality, or invoice dollars. API and host/credit rates are separate products;
cache writes, speed tiers, long context, tool charges, discounts, and billing
mode need their own documented contract before estimating money. Record
observed host/provider/model/effort usage and task outcomes as observational
data. Do not claim causal savings without comparable passing work under the
existing controlled-pair contract.
