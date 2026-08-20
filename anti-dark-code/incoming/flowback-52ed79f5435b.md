# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.08.18-unified.5.1`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: Revert-mutation proofs need a committed baseline

- Scope: repo-agnostic
- Lesson: A revert-mutation proof restores the code by version-control checkout, and
- Evidence: Three mutation proofs on a new, uncommitted unit each produced the expected
- Limits: One incident. The closing-green-run discipline is the load-bearing half and is
- Proposed target: references/11-remediation-loop.md
- Proposed change: In the guard-and-mutation guidance, require either a committed

## ADC-LOCAL-002: Whole-record equality over collection members is a hidden reference comparison

- Scope: repo-shape:managed-desktop
- Lesson: In runtimes where a record or value type delegates member equality to the
- Evidence: A cross-version stability assertion compared two normalized payload records
- Limits: One incident, in one runtime family. The general shape, default equality
- Proposed target: references/14-deterministic-verification.md
- Proposed change: Add a caution to the gate-authoring guidance: equality assertions over

## ADC-LOCAL-003: An implicit restore is a silent mutation of audited dependency state

- Scope: repo-agnostic
- Lesson: Where dependency lock files are audited evidence, a routine build that
- Evidence: A test build without the no-restore flag rewrote five lock files, removing
- Limits: One incident, one package manager. The general mechanism, a build tool
- Proposed target: references/10-maintenance-harness.md
- Proposed change: Add audited dependency state to the harness prerequisites: name the

## ADC-LOCAL-004: A remediation must fix exactly the set the gate names

- Scope: repo-agnostic
- Lesson: When a gate names the artifacts that violate a rule, the fix must target that
- Evidence: A whitespace gate failed naming one markdown file lacking a final newline.
- Limits: One incident. The narrow rule, fix only what the gate names, trades off
- Proposed target: references/11-remediation-loop.md
- Proposed change: In the fix-application guidance, require the fix set to equal the

## ADC-LOCAL-005: A mutation proof that hangs is a defect in the code, not the proof

- Scope: repo-agnostic
- Lesson: A revert-mutation proof expects red; a third outcome exists: the suite never
- Evidence: Neutralizing a process-tree kill did not turn the harness red; the suite
- Limits: One incident. Bounding a cleanup wait needs a bound chosen honestly: long
- Proposed target: references/11-remediation-loop.md
- Proposed change: In the guard-and-mutation guidance, name the hang as the third

## ADC-LOCAL-006: A surviving mutant demands a diagnosis, and the diagnosis is a finding

- Scope: repo-agnostic
- Lesson: When a mutation survives, the possibilities are a missing test or an
- Evidence: Two mutations of a filesystem probe both survived a corpus that
- Limits: One incident. Distinguishing equivalent mutants from missing tests requires
- Proposed target: references/11-remediation-loop.md
- Proposed change: In the guard-and-mutation guidance, add the surviving-mutant rule:
