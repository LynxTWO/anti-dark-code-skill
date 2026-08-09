# Public Efficiency Evidence

This directory contains opt-in, community-self-reported efficiency receipts. It is not telemetry, it is not provider-attested, and it cannot reconstruct historical savings.

- `ledger/` contains privacy-stripped, content-hashed public receipts.
- `summary.json` is generated deterministically from the complete ledger.
- `docs/data/efficiency-summary.json` is an exact mirror used by the GitHub Pages brief.

Actual usage is never labeled savings. Only a quality-qualified controlled pair can report a token delta. Results remain separated by provider, exact model, adapter version, usage semantics, and bounded task class. The project does not publish a universal lifetime-savings headline.

To contribute a receipt, follow [CONTRIBUTING.md](../CONTRIBUTING.md). Review the public export before pushing it. The pull-request check executes the validator from the trusted base revision, treats the receipt as data, requires one new receipt plus both generated summaries, and never executes contributor code.
