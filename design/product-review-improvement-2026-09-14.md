# Product review and tooling improvement

## Engagement and baseline

The owner requested implementation of the supplied evaluation plan, with autonomous
judgment, after checking GitHub. On September 14, GitHub main and the local source
both identify commit `5fc4afa10c38a354c833fdeb0b9c37b55d57ac45`, version
`2026.09.07-unified.14`. The original checkout has an untracked incoming proposal
directory. Work uses an isolated worktree; the installed discovery alias remains
on the original source.

Mode: implement and verify. Targets: the shared skill's profiler, optional usage
tool, review instructions, templates, test setup, and evaluation fixtures.
Permitted effects: local source edits, synthetic fixtures, isolated test dependency
installation, deterministic test execution, and preparation of a reviewable PR.
Protected effects: no real session-log collection, ledger deletion, release,
installed-skill replacement, production operation, or change to owner authority.
The attached evaluation's old statement that its task is evaluation-only describes
that earlier review; the current owner request authorizes implementation.

## Acceptance queue

| Item | Status | Acceptance / next check |
| --- | --- | --- |
| Executable HTML | Verified locally | Script/handler/UI evidence differs from prose and JSON data; plans reflect that distinction. |
| Ledger privacy | POSIX verified; Windows CI pending | Refuse shared/wrong-owner/redirected paths before sensitive writes; verify supported host permissions. |
| Interrupted initialization | Verified locally | Retry after each failure boundary; incomplete initialization is never usable or enabled. |
| Test prerequisites | Verified in a fresh serial environment | Documented isolated setup and CI use the same declared dependencies. |
| Product frameworks and Improve | Implemented; structural checks pass | Relevant journeys and both frameworks discoverable; narrow and audit-only scope preserved. |
| Planner relevance | Contrasting fixtures verified locally | Runtime, size, and maturity distinct; evidence classes represented; fixture prose is not product proof. |
| Authority | Explicit effect record; policy preserved | Engagement effects explicit; existing approval retained; records cannot grant authority. |
| Ownership lifecycle | Export verified; removal workflow documented | Applicable lifecycle obligations and useful local control without live-data effects. |
| Evaluation set | Eight cases prepared; browser fixtures verified | Versioned broken/clean cases and expected outcomes; distinguish machine checks from agent behavior. |
| Final verification | Supported-host CI pending | Structural validation, full Linux suite, supported-host CI, and explicit limits. |

## Recovery and evidence limits

Revert the review branch to the baseline to discard these source changes. No stored
calibration schema, capability ID, or existing usage ledger is migrated by this work.
Test results belong to their exact source, Python version, and platform. Fixture
contracts and link checks cannot establish general agent compliance or real-user
usability. Publication and installation remain separate operations.

## Integration decisions and evidence

PR #56 (`050cc959c3207c5cadf58c0d21939628462f2edb`) was inspected as a
three-file documentation diff. Its test-selection, property-count, release-source
and performance-comparison additions are retained. Its prior 14 successful CI
checks establish that PR's tested revision, not this combined candidate.

PR #57 (`b6d756645bb0e839ca82330b1fa3dbf40a497253`) is one untrusted incoming
proposal. The runtime-target lesson is adapted into the gate-environment recipe.
Its reported private six-case reproduction is not independently reproduced here.
A new real subprocess test invokes this unchanged Python helper from a nested
checkout against two different explicit targets and an invalid root, checking
results and absence of writes. Compiled/native cache behavior remains outside
that regression. The incoming artifact is not shipped in the candidate.

The clean baseline completed 673 test cases on Linux/Python 3.12.3: 672 passed
and one Windows-only case skipped. New profiler fixtures failed before repair;
six new ledger privacy/recovery tests failed against the original initializer.
After repair, the documented fresh environment completed 695 cases with two
platform skips before the final extra classifier/ACL regressions were added.
No assertion or timeout was weakened to manufacture that result. The workflow
contract now verifies shared pinned dependencies and retains parallel execution.

The browser fixture harness executed 18 observations using Playwright 1.62.0 and
Chromium 151.0.7922.34. The committed browser evidence binds the case contract,
harness and both fixture versions by SHA-256. Broken behavior remains marked as
contract failure; the harness passing does not call the broken app correct.
Zero agent trials and zero participant trials were executed. Independent model
compliance and assistive-technology/participant usability remain unmeasured.

## Scope decisions and limits

- Preserve stored schema/status meanings and V01-V22. Extra profile metadata is
  advisory; a new method digest invalidates stale cached profiles. Unknown maturity
  stays unknown, independent of source-file count. Literal partitioning is available
  for HTML and Python; other languages still need lexical false-positive review.
- Require private permissions when reopening older ledgers. Document the local
  mode/ACL repair; do not change real ledger files or collect host logs in this task.
- Provide an exclusive private summary export, current-label feedback correction
  and exact owner-controlled removal steps. Do not add scheduled purge or invent a
  retention period: writer coordination, replay cutoffs and comparison-history
  policy need a separate concrete design before automated deletion.
- Publish completed setup by same-filesystem directory rename. Synthetic failures
  at database creation, staged file writes and rename leave normal retry possible.
  Private failed staging folders are retained, never recursively deleted. This is
  process-interruption evidence, not a power-loss durability or hostile same-user
  filesystem-race guarantee.
- Update the README, catalog version, website source and seven-page PDF brief
  together. All PDF pages were rendered and visually inspected. Source edits do
  not publish the website or replace the installed shared skill.
