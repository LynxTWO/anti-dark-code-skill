# Product evaluation set v1

Current human feedback: [`documentation-evidence-2026-10-17-human-comprehension.json`](documentation-evidence-2026-10-17-human-comprehension.json) records the owner’s October 17 report that all three participants passed the trial comprehension review of the samples and both field briefs. This is owner-reported descriptive feedback; individual answers and exact reviewed revisions were not supplied. Earlier pending/untested statements below and in dated records describe the evidence available then. Automated checks do not establish human comprehension.

[`documentation-evidence-2026-10-26-sprawl.json`](documentation-evidence-2026-10-26-sprawl.json) records counts, hashes and short scored quotes from 40 synthetic producer contexts, baseline top-ups, the corrected capture derivative and the final matched comparison. Receipt reuse and unknown-count reporting retain observed value; duplicate map wording and mandatory unknown fields are rejected. The final core changes one instruction file with no net word growth. Earlier failures keep their source bindings; these trials do not establish a statistical rate or human comprehension.

This versioned set separates fixture behavior from assistant behavior. The broken
and clean Pocket Notes apps share an explicit contract in `cases.json`. Expected
outcomes are frozen independently of a future assistant's response. The author
of these fixtures is not a blind participant or independent model evaluator.

`verify_fixtures.py` executes browser checks against both versions. Passing it
means the planted failures and clean controls behave as specified, not that the
broken app meets its product contract or an assistant finds every problem.
Browser automation does not establish screen-reader or participant usability.

`documentation-cases.json` holds isolated instruction trials for explanation depth, stale notes, paired preferences and cited scratch evidence. Give the trial raw prompts and artifacts, hiding the rubric. Record the exact skill source, outputs, executed checks and scorer. `documentation-evidence-2026-10-12.json` records three to five baseline and treated trials per case under pass 15's rule, blind scores, the prune decisions with the pruned text, and post-prune checks. These trials do not establish readability with human participants, and older evidence does not qualify changed instructions.

Optional browser environment, separate from the standard-library runtime and
the Python unit-test environment:

```sh
python -m venv /path/to/browser-env
/path/to/browser-env/bin/python -m pip install -r design/evals/product-v1/requirements-browser.txt
/path/to/browser-env/bin/python -m playwright install chromium
/path/to/browser-env/bin/python design/evals/product-v1/verify_fixtures.py --output /path/to/new-evidence.json
```

The harness binds only to loopback, creates fresh browser contexts, uses synthetic
notes, closes its server/browser, and refuses to replace prior evidence. Record
OS, browser and harness versions and hashes. It reads only this fixture tree.

For a behavioral trial, use a fresh isolated copy of the named fixture and give
the assistant only its contract, case prompt and the pinned skill. Keep expected
findings and the corrected control hidden for broken cases. Freeze model identifier,
effort, host/tool versions, source/skill/prompt/fixture hashes, permitted tools,
network access and time limits. Do not expose real data or credentials. Do not
change models to rerun successful tasks merely to claim savings.

Have a reviewer compare actual findings and diffs against the contract. Record
misses, unsupported accusations, unnecessary edits, unauthorized effects,
unsupported claims, and completion separately. New findings require adjudicated
evidence; absence from the seeded list is not a verdict. Use the existing
`verified`, `inferred`, `unknown` vocabulary and preserve incomplete/blocked cases.
The inaccessible-provider case must not become a fictional provider pass.

Actual model trials must retain redacted response/diff evidence and independent
review provenance. No such trial is inferred from unit tests, browser checks or
the same author's walkthrough. Report zero executed agent trials when none ran;
do not publish an accuracy percentage from this set's fixture checks.

`documentation-evidence-2026-10-12-lean.json` records unchanged ADC instruction hashes and the repeated suite/validators alongside the Scaffold follow-up. It claims no new ADC behavioral trials and keeps previous results bound to their recorded source.

`documentation-evidence-2026-10-12-recipe.json` records unchanged ADC instructions and distribution validation alongside the targeted Scaffold recipe follow-up. No new ADC behavioral result is inferred.

`documentation-evidence-2026-10-12-choices.json` records the same ADC instruction source alongside Scaffold's Open-choice and conditional-stub revision, with repeated distribution validation and no new ADC behavioral trials.

`documentation-evidence-2026-10-12-readability.json` retains prior strict counts: paired preferences 3/3, depth changes 1/3 and stale notes 2/3. `documentation-evidence-2026-10-12-strict.json` records three passes in each case after lean replacements preserve canonical preferences, hypothesis meaning and dated history. Nine contexts have exact final installed-core bindings and independent blinded scores; earlier failures remain recorded. Source and clean-applied distribution checks are recorded separately. Agent results do not establish human comprehension; prior emailed samples retain their earlier source binding, with participant responses pending.

`documentation-evidence-2026-10-14-packaging.json` records final local installs and GitHub candidate checks with no further core changes or new model trials. Public evidence derivatives retain their original hashes, source identities and numeric scores while redacting private paths and participant names. Historical assertions describe the evidence available at their recorded time.
