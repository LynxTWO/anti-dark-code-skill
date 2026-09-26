# Falsifiable verifiers and canonical output

Trigger: a test, detector, closure check, equality comparison, or canonical-output claim may accept evidence that cannot expose the defect.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

An assertion that no execution can fail is worse than a missing assertion, because it reports coverage that does not exist. Treat one as a finding, not a style nit.

The recurring shapes, in the order they tend to surface:

- a field written as a fixed literal by a producer and pinned to that same literal by a checker
- an assertion comparing a value to itself, or to a constant it was already compared against
- a claimed property with no probe behind it
- a boolean literal asserted in place of a captured outcome
- a checker pinned to a document string that later becomes false
- a tolerance or threshold wider than the reachable range, or a matcher that accepts every candidate

The test for the class is the falsifying input: name the concrete, producible input or state that would make the check fail. A check whose author cannot name one gets rewritten or removed. In the sharpest form of this defect the producer can emit only one value and the checker requires exactly that value, which makes the acceptance criterion permanently unsatisfiable and would reject an honest recording of a genuine result.

Sweep the whole verification surface once the class is named, and re-sweep after remediating it.

The exception is a deliberate restatement of a property already proven elsewhere. Such a restatement must cite the probe that proves it, at the restatement. Deterministic gates share this rule; see the local cautions in [the exact gate contract](specialist-exact-gate-contract.md).

## Effects slower than the test window

A change whose observable effect takes longer than any test or engine window (a decay, a cooldown, a clamped catch-up pass, a multi-day horizon) leaves every gate green. That reads as "nothing changed" when nothing could have been seen, so a byte-identical suite does not prove the change is inert. Gather two kinds of evidence and say which one carries the claim:

- assert the intermediate values the change actually moves, so the cause is checked inside the window;
- where chaining is affordable, run one long-horizon probe past the window's clamp and diff it against the parent to observe the effect at least once.

Where the long run is not affordable, the intermediate assertions are the whole proof; state that.

## Canonical output

Ordering keyed on a parsed or normalized value is not total over raw representations. Two distinct raw spellings can parse equal (a timestamp with a different offset, a number with trailing zeros, a case-folded key), so a shuffle-stability test can pass while output order inside the equal class still follows input order. Tie-break canonical comparators on the raw representation after the parsed comparison, or reject equivalent-but-distinct representations at the input boundary, and never let the choice fall through silently. Every determinism suite includes a fixture pair of distinct raw representations of one parsed value and requires byte-identical canonical output across shuffles.

## Equality and handoffs

Collection-bearing equality and child-context handoff follow the cautions in [the exact gate contract](specialist-exact-gate-contract.md). For falsifiability, retain a structurally equal, reference-distinct fixture, and prove the handoff fails when its artifact is missing.

Detector thresholds need clean and known-bad fixtures, a documented separating rationale, and a positive fixture that crosses the threshold. Review threshold changes as behavior changes.

Result: every check has a concrete producible falsifier, slow effects are shown through their cause or a long-horizon probe, negative fixtures exercise comparisons and missing handoffs, and canonical-output tests include equal parsed values with distinct raw forms.
