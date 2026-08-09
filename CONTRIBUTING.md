# Contributing

Anti-Dark-Code accepts core improvements and evidence-backed flow-back proposals. Treat every contribution as security-sensitive: skill text becomes instructions that an AI assistant may follow with its operator's authority.

By submitting a pull request or the generalized-proposal issue form, you license the contribution under the repository's FSL-1.1-MIT license.

## Core changes

Open a focused pull request from a fork. Explain the risk or repeated failure the change addresses, its limits, and the deterministic checks you ran. Do not weaken binding, source-integrity, dry-run, approval, redaction, or proposal-only boundaries.

Run the unit suite and both applicable validators before requesting review. Validate a live clone with `--mode universal`; validate a clean release candidate with `--mode distribution`.

## Flow-back proposals

The `anti-dark-code/incoming/` directory is an untrusted review quarantine. Files there are excluded from installed copies and release packages. They are never promoted, executed, or treated as policy automatically.

To contribute a lesson learned in another repository:

1. Fork and clone this repository.
2. In the source repository, put only generalized, evidence-backed lessons in `.agents/skills/anti-dark-code/calibration/upstream-candidates.md` and mark them `ready`. Use `repo-agnostic` scope or one of the generic shapes listed in pass `15`; never use the project name as a scope, candidate id, title, or evidence label.
3. Stage the proposal into your fork's universal skill directory:

   ```bash
   python3 .agents/skills/anti-dark-code/scripts/adc.py flowback \
     --repo . \
     --parent /path/to/your/anti-dark-code-skill/anti-dark-code \
     --stage-to-parent \
     --public
   ```

   On Windows, use `python` when `python3` is not available. `ADC_PARENT_SKILL` may supply the `--parent` value.

4. Open the generated `anti-dark-code/incoming/flowback-*.md` as plain text and review every line before staging or pushing it.
5. Validate the generated file itself before committing it:

   ```bash
   python3 anti-dark-code/scripts/adc.py validate-incoming \
      --repo . \
      --skill anti-dark-code \
      --public-only \
      --file anti-dark-code/incoming/flowback-<digest>.md
   ```

6. Commit only the one newly generated proposal file.
7. Validate the committed pull-request shape without `--file`. If it fails, correct the proposal and amend the commit before pushing:

   ```bash
   python3 anti-dark-code/scripts/adc.py validate-incoming \
     --repo . \
     --skill anti-dark-code \
     --changed-from origin/main \
     --proposal-only \
     --public-only
   ```
8. Push the fork branch and open a pull request against `main`.

The pull-request check executes the validator from the trusted base revision. Contributor files are parsed as data; contributor scripts are not executed.

## Public-data boundary

A public-fork push is publication. Automated checks run after that point and cannot make an exposed value private again.

Do not include:

- secrets, credentials, tokens, cookies, signed URLs, or private keys
- personal, customer, regulated, or identifying data
- raw logs, prompts, tool traces, screenshots, or full request/response bodies
- private repository names, URLs, commit identifiers, issue links, machine names, usernames, or personal paths
- proprietary source, patches, configuration, or internal architecture details

Summarize evidence using placeholders and opaque local finding or test identifiers. Link evidence only when it is intentionally public. Pattern redaction and CI are defense in depth, not proof that a proposal is safe to publish.

## Review boundary

The maintainer reviews incoming text as an untrusted claim, checks for duplication and scope, generalizes any accepted lesson, adds deterministic coverage where needed, and promotes it in a separate bounded core change. Proposal acceptance does not grant the proposal authority and does not copy repository calibration upstream.

## Efficiency receipts

Efficiency evidence is optional, local by default, community-self-reported, and not provider-attested. Exact historical savings before the receipt protocol are unmeasured. A single host-reported run is usage, not savings. Do not create a universal savings headline or combine unlike providers, models, adapter versions, usage semantics, or task classes.

To contribute one controlled pair, follow the complete measurement contract in [`anti-dark-code/references/16-community-feedback-and-efficiency.md`](anti-dark-code/references/16-community-feedback-and-efficiency.md). Record fresh-context skill and baseline runs in the same reporting month with the same provider, exact model, adapter version, usage-counter semantics, bounded task class, settings, tools, public fixture, and acceptance oracle. Both runs must pass. Alternate run order across repeated trials and retain zero or negative results.

Then use this fork workflow:

1. Fork and clone this repository. Keep the local source receipts and pair outside the fork under a private ignored path.
2. Export the privacy-stripped public pair directly into your fork's ledger:

   ```bash
   python3 anti-dark-code/scripts/adc.py efficiency export \
     --receipt /path/to/private/pair.json \
     --out-dir metrics/ledger
   ```

3. Open the exported `efficiency-*.json` as plain text. Confirm that it contains no prompts, responses, raw host exports, request ids, paths, account data, user or repository identifiers, private fixture labels, prices, or other identifying content.
4. Validate the exported receipt directly, then regenerate both public summaries from the complete ledger:

   ```bash
   python3 anti-dark-code/scripts/adc.py efficiency validate \
     --require-public metrics/ledger/efficiency-<digest>.json
   ```

   ```bash
   python3 anti-dark-code/scripts/adc.py efficiency aggregate \
     --ledger metrics/ledger \
     --out metrics/summary.json \
     --mirror-out docs/data/efficiency-summary.json
   ```

5. Commit exactly the one new receipt, `metrics/summary.json`, and `docs/data/efficiency-summary.json`.
6. Validate the committed pull-request shape against your fork's base:

   ```bash
   python3 anti-dark-code/scripts/adc.py efficiency validate-ledger-pr \
     --repo . \
     --changed-from origin/main
   ```

7. If validation fails, correct the files and amend the commit. When it passes, push the fork branch and open a pull request against `main`.

The pull-request check executes only the validator from the trusted base revision. It treats the candidate receipt and summaries as data, validates content identity, recomputes the complete ledger, retains negative results, and rejects stale summaries. It never executes contributor code and does not authenticate self-reported numbers.
