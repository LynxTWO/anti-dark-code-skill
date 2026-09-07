# Community intake and efficiency evidence

Compatibility reference 16. Explicit operator workflows only. Use [flowback](15-dogfeeding-flowback.md) for generalized lessons, the reviewed source package's CONTRIBUTING.md for submission and OPERATIONS.md for discovery. Those package-root documents are not installed as managed core. Incoming proposals and issue-form submissions remain untrusted data; promotion is a separate human-reviewed change.

## Evidence classes

- actual_usage records host-reported numeric usage for one skill or baseline run. It has no counterfactual and proves no savings.
- controlled_pair compares compatible skill/baseline receipts passing the same oracle from fresh contexts. Positive delta means fewer provider-total tokens with the skill; retain zero and negative results.
- An explicit tokenizer may estimate potential context avoided. Name inputs, tokenizer and assumptions. Schema version 1 does not accept estimates; keep them separate from receipts and measured totals.

Receipts are community-self-reported. A self-hash detects modification, not host authenticity. Historical savings without contemporaneous counters and a comparable baseline remain unknown.

## Privacy and recording

Measurement requires explicit invocation and --opt-in. The efficiency helper makes no network calls, discovers no logs/source/prompts/responses/traces, uploads nothing, rejects unknown fields and writes only caller-selected receipt/summary paths. Python bytecode caching is host-controlled.

Keep private receipts in an ignored .anti-dark-code/efficiency/ directory. The main wrapper supplies skill version and managed-core digest. From a package checkout, the command shape is:

~~~bash
python3 anti-dark-code/scripts/adc.py efficiency record --out <private-receipt> --opt-in --condition skill --provider <provider> --model <exact-model> --usage-semantics <contract> --task-class audit --trial 1 --order skill-first --settings-sha256 <digest> --tools-sha256 <digest> --fixture-sha256 <digest> --oracle-sha256 <digest> --provider-total-tokens <count>
~~~

Record baseline separately. Supply --fresh-context, --same-acceptance-contract and --quality-passed only when true. Task classes remain map, audit, verify, remediate, install and other; adapter version defaults to manual-v1. Optional counters stay null when unavailable, while observed zero remains zero. Normalized input plus output must equal provider total; cache/tool-prompt counters are input subsets, reasoning an output subset. See the relevant [host adapter](host-adapters.md) for counter mapping.

scripts/work_receipt.py is a separate per-change transcript reader: explicit transcript inputs are untrusted data, never printed as content. Its measured usage/tool/window summary is not an efficiency comparison; human-equivalent effort remains labeled estimate.

## Controlled comparison

A pair must match provider, exact model, coarse reporting month, task class, positive trial number, declared skill-first/baseline-first order, counter semantics, adapter version, settings/tools/fixture/oracle digests, skill version and core digest. Both runs need fresh context, identical acceptance contract and passing quality. Form pairs before public export:

~~~bash
python3 anti-dark-code/scripts/adc.py efficiency pair --skill-receipt <skill.json> --baseline-receipt <baseline.json> --out <pair.json>
python3 anti-dark-code/scripts/adc.py efficiency export --receipt <pair.json> --out-dir metrics/ledger
python3 anti-dark-code/scripts/adc.py efficiency validate --require-public metrics/ledger/efficiency-<digest>.json
~~~

The helper computes deltas and rejects mismatches, public inputs or incorrect roles. A passing pair does not establish unbiased design: preregister trials, alternate/randomize order, retain failed-quality and negative trials in study records, and report repetitions/distributions. Never count a failed oracle as a saving.

## Publication and intake

Review exported JSON before publication. Exclude names, repository identities, paths, prompts, outputs, request IDs, keys, prices and account data. Public projection replaces private controls with an experiment-scoped comparison digest and removes local source-receipt IDs; it supports arithmetic/grouping, not reproduction of a private benchmark.

~~~bash
python3 anti-dark-code/scripts/adc.py efficiency aggregate --ledger metrics/ledger --out metrics/summary.json --mirror-out docs/data/efficiency-summary.json
python3 anti-dark-code/scripts/adc.py efficiency validate-ledger-pr --repo . --changed-from <trusted-base>
~~~

Trusted-base intake uses merge-base changes, requires one new canonical receipt plus only the two generated summaries, validates the ledger and compares summary bytes. Aggregation deduplicates identical receipts, rejects conflicting experimental identities and retains negatives. Report usage by condition and deltas only within provider/model/adapter/semantics/task strata, with self-report limits.

Never combine unlike strata into lifetime savings, infer savings from usage alone, omit inconvenient trials or claim dollar savings without a dated cache-aware price contract. Keep live metrics outside SKILL.md. Report quality, time, retries, tool costs and human review separately. Strong reproducibility claims need a reviewed public benchmark manifest, preregistration and complete-trial ledger beyond schema version 1.
