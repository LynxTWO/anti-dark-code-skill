## Summary

Describe the smallest behavior or guidance change and why it is needed.

## Contribution type

- [ ] Shared-core change
- [ ] Flow-back proposal only
- [ ] Public efficiency receipt only
- [ ] Documentation or repository maintenance

## Evidence and limits

- Evidence:
- Limits or unverified boundaries:
- Deterministic checks run:

## Public proposal attestation

Complete these when adding a file under `anti-dark-code/incoming/`:

- [ ] This PR adds exactly one generated `flowback-*.md` file and no unrelated changes.
- [ ] I opened the proposal as plain text and reviewed every line before pushing it.
- [ ] The proposal contains no secrets, personal or customer data, private paths, private repository identifiers, raw logs, screenshots, prompts, tool traces, or proprietary source.
- [ ] The lesson is repo-agnostic or uses an approved generic repo-shape, names its evidence and limits, and remains a proposal rather than executable policy.
- [ ] I ran `validate-incoming` with `--proposal-only --public-only`.

Use `N/A` for this section when the pull request does not add an incoming proposal.

## Efficiency-receipt attestation

Complete these when adding a file under `metrics/ledger/`:

- [ ] This PR adds exactly one exported `efficiency-*.json` receipt and updates only the two generated summaries.
- [ ] I explicitly opted into measurement and reviewed the public JSON before pushing it.
- [ ] The receipt contains only allowlisted study/measurement metadata, integrity fields, and numeric counters: no prompts, responses, raw exports, request ids, paths, account data, user or repository identifiers, or prices.
- [ ] A controlled pair uses the same provider, exact model, adapter version, usage-counter semantics, task class, reporting month, settings, tools, fixture, acceptance oracle, and fresh-context contract; both conditions passed.
- [ ] I retained zero and negative results, labeled the evidence community-self-reported, and made no universal savings claim.
- [ ] I regenerated both summaries from the complete ledger and ran `efficiency validate-ledger-pr`.

Use `N/A` for this section when the pull request does not add an efficiency receipt.
