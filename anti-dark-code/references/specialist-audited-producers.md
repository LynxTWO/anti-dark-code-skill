# Adding an audited evidence producer

Trigger: a new gate or producer joins a family whose audit certifies evidence as a set.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

Where an audit certifies gate evidence as a set rather than gate by gate, a new gate is not done when it passes. It is done when the audit validates the new record inside the set and the newcomer obeys the same publication law as the incumbents. Until then its pass is a producer claim the release decision cannot use.

Three obligations land in the same change as the gate itself:

- audit-side validation of the new record: its schema, its shape, and the counts it asserts, so a record the audit cannot read cannot silently join the set
- producer-side invalidation of any standing audit before the new evidence is written, because a record written after an audit attempt is unaudited and a stale audit must not keep certifying a set that no longer exists
- conformance to the family's evidence canon: whatever the incumbents obey for encoding, line discipline, atomic publication, exclusion, and cleanup

Derive that canon by reading one incumbent producer end to end. Enumerating obligations from the failures that happen to surface leaves the rest silently missing, and the missing ones are exactly the invariants no sequential run can disprove.

Where producers serialize evidence mutation through a shared lease, the newcomer participates in it or its evidence is unserialized regardless of how green its own run looks. A lease is exclusive only if acquisition is an exclusive create; prove it with a contention run against a foreign receipt, requiring the gate to fail closed and leave both the lock and the standing evidence byte-intact, and with a mutation that weakens the exclusive create to a truncating open, requiring that same run to go red.

A seventh gate joined a six-gate audited sweep. The audit was extended to validate its record and the gate was given the standing-audit invalidation the incumbents already had, but the first full sweep still failed: the platform's serializer emitted carriage returns where the family's canon is line-feed only, and the audit held the newcomer to the incumbent law. Normalizing the writer produced the first audit certifying it inside the set. An independent review then found the same gate had skipped the family's writer lease, its invalidation order, its atomic publication, and its receipt-bound task cleanup, because the obligation list had been assembled from the one failure already observed rather than from an incumbent. Every sequential run had passed throughout; only the concurrency invariant was false, and only a contention run could show it.

Result: audit-side validation, standing-audit invalidation, writer lease, atomic publication, encoding and receipt-bound cleanup land with the producer; contention and exclusive-create mutation prove the invariant.
