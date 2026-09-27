# Five quality tests

Load for building, broad improvement, user-facing behavior or readiness. These
tests concern the software's quality. Apply the separate [product principles](product-principles.md)
to how it treats people. The [core](../SKILL.md) controls evidence and authority.
Use [Improve](tasks/improve.md) only when implementation is requested.

Establish a compact [product contract](../assets/templates/product-contract.md) in
the existing map or work record. For each relevant journey record user, intended
outcome, prerequisites, actual steps, decision information, authoritative state,
affected people, failure/recovery/exit paths and observable acceptance criteria.
Name constraints and a realistic counterexample. Unknown user needs remain
assumptions to test; do not invent interviews, legal conclusions or usage data.

| Test | Questions and useful evidence |
| --- | --- |
| Does this hold up? | Does the result solve the stated problem under its constraints? Trace claims to state and enforcement. Challenge assumptions, thresholds and alternatives. Separate source, configuration and observed outcomes. |
| Can the user understand it and use it? | Walk the complete core task, including setup, missing prerequisites, mistakes, recovery and exit. Verify understandable controls, relevant keyboard/assistive-technology operation, and observable completion. |
| Would a person say this or expect this behavior? | Review copy at the point of use: onboarding, consent, errors, status and limitations. Preserve meaning and authored voice. Explain the next useful action without shame or unjustified certainty. Apply [writing hygiene](06-writing-hygiene.md). |
| Where does this break? | Exercise ordinary misunderstandings as well as hostile inputs. Include refusal, interruption, partial writes, stale data, inaccessible controls and unavailable dependencies where relevant. Preserve work and distinguish retry from duplicate action. |
| Does this earn the user's time and reward it? | Does effort advance the intended outcome? Compare a simpler coherent solution. Check setup burden, needless repetition, hidden work, misleading rewards and incentives to game the system. State who gains and who bears the cost. |

For consequential alternatives record expected benefit, complexity, compatibility,
migration burden and regression risk. A wider repair is justified when a small
patch preserves the cause. A stylistic preference alone does not justify churn.

Classify findings separately from confidence and severity:

- **Defect:** demonstrated failure against an applicable contract or principle.
- **Justified improvement:** supported benefit with a named cost or tradeoff.
- **Hypothesis:** plausible benefit or harm needing discriminating evidence.
- **Preference:** an aesthetic or personal choice without a demonstrated outcome.

A deliberate coercive design may violate an applicable product principle while
matching its implementation specification. Explain the concrete mechanism and
affected decision, rather than accusing a product from vocabulary alone.

Return supported changes, preserved strengths, unanswered questions, alternatives
rejected with reasons, checks performed and limits. A simulated walkthrough is
design evidence, not participant research; a green unit suite is not usability
validation. Technical and human outcomes keep separate coverage dispositions.
