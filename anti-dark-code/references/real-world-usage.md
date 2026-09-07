# Observe real work

Load for explicit usage collection or trigger feedback. This optional collector observes existing host records without model calls, replaying work, changing model settings, or uploading data. It is off until the owner enables it. Other hosts remain unsupported until a tested source adapter exists.

## Enable locally

Choose a new private directory outside source logs and repositories. Configure only host directories the owner authorized. From the package checkout:

```sh
python3 anti-dark-code/scripts/adc.py usage init --directory <private-ledger> --source codex=<sessions-root> --opt-in
python3 anti-dark-code/scripts/adc.py usage collect --directory <private-ledger>
python3 anti-dark-code/scripts/adc.py usage summary --directory <private-ledger>
```

Add `--source claude=<projects-root>` only for authorized Claude Code logs. A scheduled local `usage collect` command can run every five minutes after that authorization. Preserve existing hooks; scheduling grants no permission to run repository gates or model calls. Configuration contains local paths; keep the entire directory private. The generated ignore file is an accident barrier, not an export review.

The ledger records usage timestamp, hashed technical identities, exact observed model/effort, attribution source, host version where present, counters, and fixed diagnostics. It discards prompt/output bodies; it does not tokenize them to fill missing counts. Startup may read older lines for model context, but excludes pre-opt-in usage. Incremental offsets and response identity prevent copied logs or repeated ticks from adding the same tokens twice. Claude streaming updates replace earlier counters for that response.

Collection has a bounded read budget. Inspect `last_collection`, `backlog` and diagnostics before describing coverage. Finish the backlog with later ticks; a partial line waits for completion. Changed adapter code rebuilds context from the configured sources while deduplicating known responses. Unsupported legacy usage, compaction/fallback iterations, unreadable sources, oversized lines and malformed data leave gaps. Arithmetic or conflicting response counters roll back the tick, preserving its previous offsets; inspect the original locally before retrying. No result proves all account usage was observed.

`usage disable --directory <private-ledger>` stops reads and retains history. Remove the scheduler separately. No automatic retention deletion is configured.

## Account for models honestly

Codex 0.153.0 per-response records are the tested starting contract. Compatibility cumulative notifications are ignored. Context model attribution is labeled `turn-context`; it does not attest to the serving model. Linked reroute or usage metadata has its own attribution. Missing model/effort/cache/reasoning fields remain null. Native host tokens are not a provider invoice.

Codex input includes cache subsets; output includes reasoning. Claude normalized input adds uncached input, cache creation and cache read, only when all are present. Never add subsets twice. Claude totals are derived under their named semantics. Summaries expose known subtotals and missing-event counts, separated by provider, exact model, attribution, effort, semantics, role, host version, task class and outcome. Retries, subagents and approval reviews remain in observed usage when their logs are available.

Subscription cost, included quota and savings remain unknown. Dated API rates do not convert a subscription price into quota. Compare natural tasks only as observational strata, with differences in scope and quality stated. Controlled savings still require [comparable receipts](16-community-feedback-and-efficiency.md); do not replay successful real tasks merely to manufacture a baseline.

## Label normal reviews

During an already-needed review, take the hashed task ID from the recent summary and record what was observed:

```sh
python3 anti-dark-code/scripts/adc.py usage feedback --directory <private-ledger> --task-id <hash> --used yes --expected yes --invocation implicit --quality passed --task-class audit
```

`used` means the skill actually guided this task. Merely reading its files, mentioning it or reviewing the skill is insufficient. `expected` is the reviewer's separate judgment of whether the description should have activated it for that request. Leave either unknown without evidence. Quality reflects the task's existing acceptance checks; the label grants no gate approval.

Label non-activations too: `used no`, with expected yes for a miss or no for a correct non-trigger. A sample containing only activations cannot measure recall. Do not add a classifier call or collect request text for this purpose. The skill cannot observe every missed invocation by itself.

Only labeled implicit cases with established task boundaries enter the confusion matrix. Explicit invocations, unknown labels, and Claude request units lacking a reliable user-task boundary are excluded. Codex root-turn grouping includes linked child work, not just the parent. Precision is TP/(TP+FP); recall is TP/(TP+FN); empty denominators stay null. Report sample counts, selection bias, exclusions and description changes. These are feedback-sample scores, not population accuracy or automatic learning. Review accumulated misses before proposing a description change.
