# Shadow routing evidence

Load for explicit installation or review of a routing measurement campaign. Ordinary audits do not install CI jobs. The campaign measures proposed change-to-verification rules while CI continues to execute the full canonical recipe. It does not authorize selective gate execution.

## Contract and prerequisites

Use repository-owned calibration/routing-policy.json with rules proposed, calibration/gates.json with canonical_full_set, and .github/shadow-gate-map.json mapping canonical gates to actual CI jobs/steps. Begin from shipped templates and keep owner_confirmed_safe_to_execute false. Do not import another repository's calibration.

The non-required job in assets/templates/shadow-job.yml depends on the existing gate jobs through needs. It never becomes a prerequisite of a required check or changes which gates run. Installation modifies CI and needs authority for the reviewed workflow change.

Records carry base/merge/head identities, run/attempt, matched rule terms, candidate selected/omitted gates, classifier/router identity and CI outcomes. Class identity changes when meaning changes; changing approval alone does not change it. A saved artifact is an inbox claim until ingestion checks its provenance.

## Status meanings

| Status | Meaning |
| --- | --- |
| clean | Every canonical gate passed and the nonempty candidate omitted at least one. |
| miss | An omitted gate failed while selected gates passed; retain the negative evidence. |
| inconclusive | Selected failure or matching base failure prevents evidence for the candidate. |
| no_omission | Candidate omitted nothing. |
| selects_nothing | Candidate selected no gates; not evidence of a safe rule. |
| not_measurable | Missing, skipped, cancelled, unresolved or otherwise undecided canonical outcome. |

Only clean and miss count as evidence for/against a class. Silence never reads as clean. Keep all other dispositions visible.

## Commands and evidence locations

Subcommands of scripts/adc.py shadow are defined in scripts/adc_shadow.py:

- outcomes --map <map> --run <run> --attempt <n> --out <file> reduces CI jobs to canonical conclusions. --jobs supplies a saved payload; otherwise it may fetch API data.
- record --repo <repo> --base <base> --merge <merge> --head <head> --pr <number> --run <run> --attempt <n> --outcomes <file> --out <record> describes the tree CI verified.
- backfill --repo <repo> --map <map> --branch <ref> --out-dir <directory> revisits PR heads and attempts, including superseded attempts. Backfill provenance never adds live approval count.
- ingest --repo <repo> --map <map> --source <directory> --ledger <directory> --month <YYYY-MM> rechecks named CI outcomes, recomputes verdicts and, by default, recomputes class identity from preserved policy/router evidence. A landed canary is refused.
- summary --ledger <directory> --out <file> regenerates deterministic summaries, counting PRs per class rather than rewarding repeated attempts.
- dominance --repo <repo> --class-key <key> --out-dir <directory> probes a class no gate reads. Even its default temporarily deletes/replaces tracked files, restores them and writes evidence; it requires a clean tree and owner confirmation. The default skips gate execution and proves no behavioral conclusion. Use an authorized isolated copy, verify restoration, and review repository-code execution separately.

Offline ingestion skips API revalidation; skipping class recomputation is intended for fixtures without a clone. Neither shortcut supplies the omitted assurance. Review network and output scope before invoking campaign commands.

Keep committed evidence under metrics/shadow/ or the campaign repository's metrics/shadow/consumers/<owner>-<name>/. Preserve policy/gate/router evidence required to recompute classes, and keep inbox artifacts distinct from the ledger.

## Acceptance boundary

A class needs a canary branch canary/<rule>/<date>, never merged, deliberately breaking an omitted gate and recording miss, or the applicable reviewed dominance evidence. Provenance derives from branch evidence rather than a claimed label.

CI conclusions, not the local gate runner, supply campaign outcomes. Records enable owner review; they never approve a rule. Preserve negative attempts and explicit human adjudications without silent subtraction. Completion means measurement provenance and limits are recorded while the full CI recipe remains intact.
