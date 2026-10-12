# Product evaluation set v1

This versioned set separates fixture behavior from assistant behavior. The broken
and clean Pocket Notes apps share an explicit contract in `cases.json`. Expected
outcomes are frozen independently of a future assistant's response. The author
of these fixtures is not a blind participant or independent model evaluator.

`verify_fixtures.py` executes browser checks against both versions. Passing it
means the planted failures and clean controls behave as specified, not that the
broken app meets its product contract or an assistant finds every problem.
Browser automation does not establish screen-reader or participant usability.

`documentation-cases.json` adds isolated instruction trials for concise audience modes, stale notes, canonical ownership and cited scratch evidence. Give the trial raw prompts and artifacts, hiding the rubric. Record the exact skill source, outputs, executed checks and scorer. One independent pass is a smoke trial; older evidence does not qualify changed instructions or establish readability with human participants.

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
