# Proportionality evaluation set v1

This set exercises `references/proportionality.md` with two prompts in
`cases.json`. Each case names the rules it targets, the pressures it applies,
and a yes/no rubric. The prompts describe a synthetic private-beta product;
no real repository, credential or person is involved.

Trials are behavioral: a fresh agent receives only the pinned skill path and
one case prompt, cannot run anything, and writes the plan it would send. A
reviewer scores the plan against the rubric and quotes the sentence that
earned each yes. Record the model identifier, date, skill state (git ref and
the SHA-256 of `SKILL.md` and the reference under test), and who scored.

Evidence files (`evidence-YYYY-MM-DD.json`) keep the trials that were run,
including the baseline trials against the skill state without the reference.
A baseline is the failing test that justified the text; keep it. The author
of the rules scoring their own trials is not independent review, and the file
says so. Do not publish a compliance percentage from three trials; report the
counts and the quotes.

Rerun the set when `references/proportionality.md`, the three pointer
sentences in `SKILL.md`, or the hooks in `references/tasks/investigate.md` and
`references/tasks/verify.md` change. A wording change that is not retested
inherits no result from an earlier evidence file.
