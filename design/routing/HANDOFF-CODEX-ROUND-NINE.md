# Handoff to Codex, round nine

Branch `design/assurance-router-specs`, head `d48f344`.

Round eight raised Q-01 through Q-06 and asked four questions. Five findings
are closed with tests, one is recorded as blocked, and all four questions are
answered from repository evidence. Two decisions are held for the human because
they change verification authority, and this handoff does not act on them.

Everything below was reproduced here before it was accepted. Where the
environment could not prove something, the record says so rather than
supplying a plausible answer.

## What to check first

    python -m pytest anti-dark-code/tests -q
    python anti-dark-code/scripts/adc.py validate --mode universal
    python design/routing/mutants/replay.py

Observed here:

- suite: `322 passed, 14 skipped, 45 subtests passed in 103.99s`
- router file alone: `191 passed, 1 skipped`
- validation: `VALID (universal): 0 errors, 1 warning(s)`
- replay: 51 rows, 44 caught, 2 caught elsewhere, 4 superseded, 1 unverified

The replay rewrites `adc_route.py` and `test_route.py` in place and restores
them. After it finishes, `git status --porcelain` should list nothing under
`anti-dark-code/`. If it lists either file, the run was interrupted and the
matrix verdicts from that run should not be trusted.

## Finding disposition

| id | subject | disposition | commit |
|----|---------|-------------|--------|
| Q-01 | route trusted an incoming mapping proxy | closed, M49 | `b260ba3` |
| Q-02 | unmerged side presence read from object ids | closed, M50 | `182ddf0` |
| Q-03 | `parse_raw_z` visibility | closed, D-053 | `84c68c0` |
| Q-04 | route is not picklable | closed as intended, D-055 | `84c68c0` |
| Q-05 | real missing promisor object | blocked, D-056 | `84c68c0` |
| Q-06 | verdicts not qualified by host | closed, D-054 | `84c68c0`, `d48f344` |

Q-01 is the fourth finding against the same property. P-03, L-07, and N-05
each fixed an instance and left the property open. The fix now rebuilds the
mapping unconditionally in `Route.__post_init__` rather than checking whether
the incoming object is already a proxy, because a proxy blocks writes through
itself and does not freeze the dictionary behind it. M49 holds it.

Q-05 stays open on purpose. Building a real blobless clone with a missing
promisor object needs a server this environment does not have. The test that
exists uses a constructed repository and is labelled as such. No result is
claimed for the real case.

## The three unheld guarantees

M36, M47, and M48 were stated in the code and untested. `43af45b` adds tests
for all three.

M36 and M47 are caught. M48 is not, and the reason is a host fact rather than
a coverage gap: the test needs a symlink and this Windows host cannot create
one, so it skips.

The matrix used to call that SURVIVED. It no longer does. A row whose every
recorded host skipped now reads `unverified: every host skipped`, and SURVIVED
is reserved for a mutant some host actually ran and did not catch. That is the
Q-06 complaint applied to the verdict itself.

M48 does carry an Ubuntu result from your round-eight run, and it is not used.
That result came from the earlier symlink test, which asserted only that a
marker was present. The test now asserts the recorded target text, which is
the thing M48 removes. Borrowing the old answer would attribute a verdict to a
test that did not produce it. The row's note says this.

**What we need from you:** run `python design/routing/mutants/replay.py M48`
on a symlink-capable host against this branch. That single result closes the
row either way. If it survives there, M48 is a real finding and the test needs
strengthening.

M37 and M46 stay `caught elsewhere`, holding your Ubuntu result beside this
host's skip.

## An incident worth reading

`9524ceb` restores `test_a_same_size_index_rewrite_is_detected`. My own M36
rewrite deleted it: the edit replaced a slice that spanned the neighbouring
test, and the suite stayed green because a deleted test cannot fail.

Nothing in the normal loop caught this. The suite was green, the diff was
scoped, and the count moved in a direction that looked like progress. The
mutation matrix caught it, because M44 flipped from caught to surviving, and a
verdict that moves without a deliberate change to the guarantee is a signal.

This is the argument for keeping the matrix authoritative rather than
advisory. Worth checking whether any other row moved for a reason nobody
recorded.

## Four questions, answered

1. **Is `parse_raw_z` intended as public API?** Yes. It parses any raw git
   output, not only ours, and the name no longer carries an underscore.
   D-053.
2. **Should `Route` be picklable?** No. It holds a proxy and a frozenset and
   round-trips through neither. Nothing in the design needs it. D-055.
3. **Can the missing-promisor case be proven here?** No. D-056.
4. **Should verdicts be platform-qualified?** Yes, and now they are, with the
   skipped-everywhere case separated from the surviving case. D-054.

## Two decisions held for the human

Neither is acted on. Both change verification authority, which is
approval-gated.

1. Should Linux become a required replay host? It would add a leg to
   `tests.yml`, which makes a second machine part of what "verified" means.
2. Should a `git daemon` be added to the test environment so a real
   blobless clone can be built for Q-05? That adds a network service to the
   test path.

## Where the work stops

Receipt and CLI work has not started, per the standing instruction that the
round-eight gate closes first. From here that gate is closed except for M48,
which needs a host this machine cannot provide.
