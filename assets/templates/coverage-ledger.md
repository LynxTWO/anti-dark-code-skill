# Coverage Ledger

Tracks which areas of the repo have been reviewed under the anti-dark-code workflow, at what confidence, and what the next pass should be.

Do not claim full coverage unless the evidence in this ledger supports the claim.

For canonical status values, classification labels, and risk levels, see `references/00-conventions.md`.

## Ledger

| Area / Slice | Paths | Risk | Status | Label | Evidence | Verification guard | Capability ids | Invalidated by | Owner | Next pass |
|---|---|---|---|---|---|---|---|---|---|---|
| <e.g., auth service> | `services/auth/**` | high | mapped | owned-risky | `docs/architecture/system-map.md` auth section | auth contract suite | V03, V08, V15 | auth schema or middleware change | <team> | 03 critical-path comments |
| <e.g., billing worker> | `workers/billing/**` | high | unscanned | owned-risky | none yet | none | V03, V07, V15 | any change | <team> | 02 architecture map |
| <e.g., vendored SDK mirror> | `third_party/vendor-sdk/**` | low | excluded | third-party mirror | N/A | upstream checksum | V13 | mirror update | upstream | none; document in map |

## Notes

- Add nested ledgers when one flat table would hide detail (e.g., per-package ledgers under a monorepo ledger).
- Record exclusions explicitly. An area without a row is worse than an area with an honest `excluded` row.
- When a risky slice changes, move the row, do not quietly rewrite history. Keep a dated changelog at the bottom if the ledger sees heavy churn.

## Changelog

- <YYYY-MM-DD> - <what changed, why>
