# Pull Request

<!--
This template reflects the anti-dark-code maintenance harness. Fill in every section that applies. Leave sections blank or write "n/a" with a one-line reason if they do not apply to this change.

Short is fine. Honest is required. Do not smooth over uncertainty.
-->

## What changed

<!-- Plain English. What is different after this PR merges? One to three sentences. -->

## Why it changed

<!-- The reason, not the mechanism. Tie to an issue, incident, ticket, or decision if one exists. -->

## What is still unclear

<!-- Anything you could not confirm. Link to or quote the relevant `docs/unknowns/` entry. If you added a new unknown, say which file. "Nothing unclear" is a valid answer if it is true. -->

## Risk change

<!-- Did this change move risk up or down, or leave it flat? If up, say how, and say what mitigation is in place. -->

## Approval status

<!-- For changes that touch protected areas (auth, access control, secrets, crypto, billing, deletion or retention, migrations, security controls, concurrency or locking, privileged CI or CD, release tooling, support tools with production reach, or repo-specific high-risk areas named in the steering files):

- Approver:
- Approval evidence (link, comment, or written record):

Otherwise: "Not applicable - no protected area touched." -->

## Docs updated

<!-- Check all that apply and link the touched file(s). If none of these apply, say "Not applicable" with a one-line reason. -->

- [ ] Steering file (`AGENTS.md` or siblings)
- [ ] System map (`docs/architecture/system-map.md` or `service-map.md`)
- [ ] Coverage ledger (`docs/architecture/coverage-ledger.md`)
- [ ] Repo slices (`docs/architecture/repo-slices.md`)
- [ ] Logging audit (`docs/security/logging-audit.md`)
- [ ] Relevant unknowns file(s) under `docs/unknowns/`
- [ ] Runbook
- [ ] ADR
- [ ] README
- [ ] Service or module manifest
- [ ] Rollback note
- [ ] Observability note
- [ ] Release-path note
- [ ] Localization or transcreation boundary note

## Tests or checks run

<!-- Name what ran and where. "Unit tests pass locally" is less useful than "`pnpm test packages/auth` green; `lint` green; no new warnings." -->

## Deterministic verification

<!-- Name exact commands or gate ids. Link the failure packet for any known failure. Do not paste full green logs. -->

- Confidence level run: <0 | 1 | 2 | 3>
- Gate command or ids:
- Result: <pass | fail | not run>
- Full local artifact path:
- Failure packet, if any:
- Checks deliberately skipped and why:

## Test and baseline changes

<!-- If tests, fixtures, snapshots, mutation settings, timeouts, mocks, architecture exceptions, or coverage thresholds changed, name the behavior contract that changed and why the old expectation was wrong or incomplete. -->

- [ ] No test or baseline behavior changed, or the explanation below is complete.
- [ ] No test was skipped, assertion removed, timeout inflated, mock broadened, or snapshot re-recorded merely to obtain green.

Explanation:

## Replay and regression memory

<!-- For a reproduced failure, name the seed, trace, fixture, property, or regression test that now preserves it. -->

## Sensitive-data self-check

<!-- Confirm none of these appear anywhere this PR touches (code, logs, comments, tests, docs, examples, screenshots, commit messages):

- passwords, tokens, API keys, session IDs, cookies, signed URLs
- secrets, encryption keys, certificates, connection strings
- raw personal data beyond the minimum safe example
- decrypted payloads, full request or response bodies with sensitive data
- real user or customer data copied from production

Acknowledge: -->

- [ ] Confirmed. No sensitive data added to any surface listed above.

## Protected comment continuity

<!-- If this PR deleted, moved, or materially rewrote any anti-dark-code comment that captured rationale, invariants, trust boundaries, failure modes, ordering or idempotency assumptions, language boundaries, or repair warnings:

- [ ] A replacement comment was added near the surviving code, OR
- [ ] An intentional removal note is recorded below, explaining why the comment is no longer needed.

If neither applies, the protected comment should be restored before merging. -->

Removal or replacement notes:

<!-- Free-form notes here, if any. -->

## TODO continuity

<!-- If this PR planted any `TODO(adc:` lines, confirm each is paired with a backlog or unknowns row. If this PR cleared any `TODO(adc:` lines, confirm the matching row was closed in the same change. -->

- [ ] Planted TODOs reference a backlog or unknowns row, or n/a.
- [ ] Cleared TODOs closed their matching row, or n/a.

## Follow-up work

<!-- Anything this PR leaves on the floor. Link issues or planned next passes. -->
