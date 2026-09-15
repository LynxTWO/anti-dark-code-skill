# Five product principles

Use for user-facing design, broad improvement and readiness alongside the
[quality tests](quality-tests.md). These principles expose review obligations;
they do not prescribe features for every product or replace the owner's contract.
The [core](../SKILL.md) preserves authority, privacy and scoped evidence.

| Principle | Observable obligations when relevant | Counterexample to challenge |
| --- | --- | --- |
| Make truth easier | Status matches authoritative state; material prices, limits and consequences appear before decisions; uncertain automated results are described accurately. | A failed save announces success, or a recommendation implies evidence it does not have. |
| Make repair normal | People can correct mistakes, retain drafts, retry safely, undo where appropriate, recover access and appeal consequential errors. | Retry duplicates a charge, or a recoverable input error destroys completed work. |
| Make dignity default | Core interactions support relevant input/access needs, meaningful choices and readable remedies. Collect only needed data; refusal and enforcement use neutral language. | A keyboard user cannot finish; declining an offer becomes a judgment about their character. |
| Make ownership unavoidable | Identify whose data, work or opportunities are affected and who owns system errors. Provide appropriate correction, retrieval, deletion and review of automated decisions. | An export omits promised data, another user can edit it, or nobody can correct a system decision. |
| Make manipulation unnecessary | Defaults, rewards, recommendations and exit paths support informed choices. Optional collection respects refusal; costs and cancellation are clear; no fabricated urgency. | Analytics starts despite refusal, cancellation adds arbitrary hurdles, or rewards make dishonest use easier. |

Trace the affected person's journey, not only operator permissions. For personal
data record purpose, authoritative store, access, duration, correction, export,
removal and any justified retention limit. Include copies, backups, diagnostics
and third parties when present. Account for existing consent; changing a label
cannot change the authorized purpose. An export needs a declared scope and
destination. A removal operation needs a bounded target and interruption policy.

Data minimization, recovery, accountability, privacy and retention can conflict.
State the tradeoff, affected people, required decision owner and testable rule.
Do not invent a universal retention period, destroy records to satisfy a slogan,
or preserve sensitive history forever for unspecified accountability. Legal
obligations require appropriate current sources and qualified review where needed.

Use existing verification methods: stateful journeys (V02), contracts (V03),
invariants (V07), semantic snapshots (V13), and fault injection (V15). Keep stable
capability IDs. Verify actual outcomes: a declined optional feature stays off,
an error retains the draft, repeated retry does not duplicate the operation,
and authorized correction changes only the intended record.

Automation can check named controls, state and selected accessibility rules.
Manual keyboard and assistive-technology checks, real user comprehension, and
unobserved provider state retain their own coverage limits. A static scan cannot
certify fairness or accessibility. Preserve clean controls and record false
accusations and unnecessary edits as evaluation failures.

Apply only relevant obligations. A local converter without accounts does not need
an account-deletion service. A clear price is not itself manipulation. Required
information can be justified if its purpose and consequences are understandable
and the person retains a dignified refusal or exit path.
