# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.08.20-unified.6`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: A new producer is born under the audit, or its pass is not evidence

- Scope: repo-agnostic
- Lesson: Where an audit certifies gate evidence as a set, adding a new gate is not done when the gate passes; it is done when the audit validates the gate's record inside the set and the gate participates in the audit's freshness protocol. Three obligations arrive together with any new producer: the audit gains validation of the new record's shape and counts, the producer invalidates any standing audit before writing new evidence, and the record obeys the evidence canon of the existing family, encodings and line discipline included, because the audit will hold the newcomer to the same law as the incumbents. A new gate that skips any of the three reports passes the release decision cannot use.
- Evidence: A seventh gate was added to a six-gate sweep whose audit certifies the evidence set. The audit was extended to validate the new record and the gate was given the standing-audit invalidation the incumbent producers already had. On the first full sweep the audit rejected the new record for carriage-return line endings, because the platform's JSON serializer does not emit the family's canonical form; the writer was normalized and the next sweep produced the first audit certifying the newcomer inside the set. A second incident then proved the deeper rule: an independent review found the same gate had skipped the family's writer lease, its invalidation order, its atomic publish, and its receipt-bound task cleanup, because the author had enumerated obligations from the one failure already observed instead of reading an incumbent producer end to end. The repair replicated the incumbent's full evidence discipline and proved the exclusion by a contention run and a create-new-weakening mutation.
- Limits: Two incidents in one family. The specific canon, line endings and strict UTF-8 and leases, is one family's law; the general rule is that the audit's existing record requirements bind new producers from their first write, and that the obligation list comes from reading an incumbent end to end, not from memory or from the failures that happened to surface.
- Proposed target: references/14-deterministic-verification.md
- Proposed change: In the gate-authoring guidance, add the new-producer checklist: audit-side validation of the new record, producer-side invalidation of stale audits, and conformance to the family's evidence canon, all landing in the same change as the gate itself.
