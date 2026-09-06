# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.09.05-unified.10`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: Documentation is not evidence that code does a thing

- Scope: repo-agnostic
- Lesson: A content-signal scan that reads every text file treats a design note, a steering file, or a user guide as proof that the product has the behavior the note mentions. Prose describes intentions, risks, other systems, and things that were ruled out; source and configuration describe what runs. A planner that selects a capability because documentation mentions billing or simulation is planning verification for code that may not exist. Record where each piece of signal evidence came from, and let a signal whose only backing is documentation reach the planner as a question, not an observation.
- Evidence: With 2026.09.05-unified.10 installed, the deterministic profile of a media processing desktop repository reported 23 of 30 signals present, including financial entitlement and simulation, and every citation for those two was a Markdown steering or audit document rather than a source file. The automatic plan selected 21 of 22 capabilities on that basis, against a human-reviewed plan of 10. The profiler already classifies files by extension for counting, so the class of each evidence path was available and simply not recorded.
- Limits: Some repositories keep truth in prose on purpose, such as a specification repository or a policy corpus; there the documentation class is the source class and the rule should be applied with that mapping. Configuration files sit between the two and are treated as code-side evidence here because they change runtime behavior.
- Proposed target: scripts/adc.py
- Proposed change: Record `evidence_classes` (source, config, structure, prose) and a `documentation_only` flag on every signal; in the planner, a non-core capability whose matched signals are all documentation-only becomes `candidate` with a reason that names them, instead of `selected`. Document the flag in `references/14-deterministic-verification.md`.
