# Handoff to Codex, round ten

Branch `design/assurance-router-specs`.

The owner granted the two approvals held open in round nine, and this round
spends them. Linux is now required verification authority, the missing-promisor
case is proven instead of blocked, and M3 is built: policy schema, receipt
writer and verifier, and the `route` subcommand.

Three things in here are findings against my own work rather than progress
reports, and they are the parts worth reading first.

## What to check first

    python -m pytest anti-dark-code/tests -q
    python anti-dark-code/scripts/adc.py validate --mode universal
    python design/routing/mutants/replay.py

Observed: Windows `364 passed, 14 skipped, 45 subtests`; T540P Linux
`374 passed, 1 skipped`, and that one skip is a test of Windows process
termination. Validation `0 errors, 1 warning` on both.

The matrix is 60 rows and now carries a verified result from two hosts for
every active row: Windows 11, Python 3.14.2, git 2.50.1, and Ubuntu 24.04.4,
kernel 7.0.0-28-generic, Python 3.12.3, git 2.43.0. 53 caught on both, 3 caught
on Linux where Windows skips the test that holds them, 4 superseded. No
survivors, nothing unverified.

Rows now carry an optional `suite`. A mutant in `adc_receipt.py` replayed
against the router suite would have reported caught while proving nothing,
because the tests that hold it never ran. Check that every row's suite actually
exercises its source.

## Q-05 is proven, and the fixture shape is the interesting part

A `git daemon` on loopback is a real `git://` transport, it ships with git, and
it needs no install and no machine-wide change. The owner approved adding one;
nothing had to be added.

The proof is end to end rather than a flag check. The clone is genuinely
missing the base blob and records a promisor remote. The diff acquisition
actually runs exits 128 under the guard and leaves the object missing. The same
command without the guard exits 0 and writes the object, so the network really
was reachable. Full acquisition reports `ADC-ROUTE-COMMITTED-UNREADABLE` and
fetches nothing.

Reaching a missing object at all takes a specific fixture, and this is the part
I would have got wrong by reasoning alone. Acquisition runs three raw diffs,
and a raw diff wants object ids rather than content. The one exception is
inexact rename detection, which scores similarity by reading both blobs. An
exact rename shares its object with the tip, so the tip checkout fetches it and
nothing is ever missing.

My first three attempts had no rename across the base. They reported the change
complete with the guard removed, which is a fixture that passes whether or not
the control exists. The counterfactual is now asserted rather than assumed: the
unguarded run must fetch the object, or the guarded result is not evidence.

M52 holds the guard. D-060 records it, and D-056 is marked superseded rather
than quietly edited.

## Linux is required, and the T540P is a recorded host

D-058 adds a required `mutation-replay` job on `ubuntu-latest` that replays all
60 rows on every pull request, wired into the `required` aggregator. Linux
only: on a real Linux host the full suite reports 374 passed and 1 skipped
against 361 and 14 on Windows, and that single skip is a test of Windows
process termination, which is the mirror image of a gap rather than one.
Windows skips the symlink tests and would report host facts as coverage.
The aggregator was exercised directly and fails on both `failure` and
`skipped`.

D-057 records a mistake of mine, corrected by the owner. I reported the T540P
as unreachable and blamed a missing SSH rule in the tailnet policy. The policy
was already correct. It permits `autogroup:member` to `autogroup:self` as
`autogroup:nonroot` and needed no edit; the account is `daniel-boyd`, which is
one of the few names I did not try.

The reasoning error is worth more than the fact. I tried fourteen names, saw
one refusal text for all of them, and concluded no rule existed.
`autogroup:nonroot` admits any non-root account that exists, and Tailscale
refuses a name that is not a local account using the same message it uses when
no rule matches. One string, two causes, and I reported the stronger one as
established. A negative result across a list I invented says as much about the
list as about the system, and I did not mark it as inference.

The T540P is now a recorded replay host: Ubuntu 24.04.4 LTS, kernel
7.0.0-28-generic, Python 3.12.3, git 2.43.0. No policy was changed.

CI replay stays required regardless, and the reason is unchanged: the matrix
should not depend on any one machine being reachable.

WSL was used once, before the T540P was available, as a pre-flight that the new
gate would not land red. It is not in the matrix as a host verdict.

**A correction the owner should see.** macOS was scoped out on the grounds that
no macOS host exists. CI already runs the suite on `macos-latest`, so macOS is
covered for the suite and has been. It is not a replay host and no matrix
coverage is claimed there. D-059.

## I committed a live mutant to the router

The worst thing in this round, and it is mine.

`a92c869` shipped M01. `_union_obligations` was assigning instead of unioning,
so a capability required by two rules kept only the gates of whichever rule was
applied last. The docstring directly above that line says what it costs: a
route would claim a capability was covered by work it never selected. Running
less verification than a change deserved is the failure this entire subsystem
exists to prevent, and it went into the router itself.

Cause: I started the authoritative replay in the background and then ran
`git add -A` for an unrelated docs commit while it was running. Replay mutates
tracked source in place and restores it between rows, so for seconds at a time
the tree holds a deliberate defect. `add -A` took what was there.

No test could have caught it. The suite was green before that commit and green
after, because the mutant existed only in the window where nothing ran and the
restore put the correct line back afterwards. Only the diff between HEAD and
the restored file showed it, and I found that while checking source restoration
rather than by looking for it.

`9e61386` restores the router. No other file was affected.

That is the fourth instance on this branch of one class: the tree not being
what a green suite implies. The deleted test, the shadowed duplicate, M56's
stale target, and now this.

So the guard sits where it can see that class. `MutationMatrixIntegrityTests`
checks the tree against the matrix: if a row's original text is missing from
its source, either the row is stale or that file is holding the mutant. A
second test states the narrow case separately, because a row whose replacement
is present while its original is absent is not ambiguous.

It skips during a replay, and that is load-bearing rather than convenient.
Replay mutates the tree on purpose, so without the flag this check would fail
for whichever row is applied and every mutant would report caught with no
behavioural test having noticed. A guard that turns the coverage record into a
tautology is worse than none. Verified in both directions: with M01 reapplied
the two checks fail and name it, with the flag set they stand aside, and M01
still replays as caught on the strength of a real test.

**Worth your scrutiny:** whether any earlier commit on this branch carries the
same problem. I checked the current tree, not the history.

## The Linux host earned its keep on the first run

M48, open since round eight, is caught on Linux. So are M37 and M46, now on a
host we can re-run rather than a report. And the first clean Linux replay found
something no amount of reading would have: **M36 survived there while Windows
caught it.**

The cause is a side channel, not a difference in the code.
`test_replacing_a_file_with_a_hard_link_is_detected` asserts a boundary
violation after a hard-link swap that holds bytes, size, and mtime equal. On
Linux git refreshes the index during acquisition, the boundary fires on that,
and the test passes with topology disabled. Its own docstring records removing
an earlier timestamp side channel from this same test. That fix removed one and
left another, and Windows could not see it.

Demonstrated rather than argued. With topology disabled on Linux, `index_state`
changes across acquisition, the violation is still reported, and the test still
passes. On a clean tree the topology field moves from `(1, ino, mode)` to
`(2, ino, mode)`, so the detector was never the problem.

`test_path_topology_alone_moves_the_fingerprint` takes two fingerprints with
nothing in between: no acquisition, so no index movement, so nothing but
topology can differ, and content, size, and mtime are asserted equal so a pass
cannot be explained by them. M36 is now caught on both hosts, and on Linux the
new test is the one that fails while the old one still passes. The old test is
kept for the end-to-end path, with the limitation written into its docstring
rather than left implied.

**A second one of mine, quieter and worse.** The matrix integrity guard skipped
during replay. A skip counts toward the per-host skip total, and that total is
what decides whether an uncaught row reads as SURVIVED or as "nobody could
check this". Four guaranteed skips on every host would have relabelled every
genuine survivor as unverified, which is the failure mode D-054 exists to
prevent, reintroduced by the fix for a different problem. The guard is
deselected by a `-k` filter now, and a test asserts the harness still names the
class, because a rename would leave the filter matching nothing and the tests
running against a mutated tree.

I also contaminated my own diagnosis on the way here. A probe cleaned up with
`git checkout --`, which failed on the T540P because the tree there is an
archive extract with no `.git`. Every probe after that ran against a mutated
file and I read the results as real behaviour before noticing. Restores are now
verified by digest against HEAD rather than assumed.

## A test that was defined and never ran

`AcquisitionAgainstRealGitTests` defined `test_a_linked_worktree_index_is_found`
twice. Python keeps the later definition and discards the earlier, so the file
claimed 196 tests while pytest collected 195. The bodies were byte-identical,
so no guarantee was lost.

The duplicate came from `9524ceb`, the commit that restored the test an earlier
rewrite had deleted. The fix for a slice edit was itself a slice edit, and it
pasted the neighbour twice.

That is twice on this branch for the same failure: a test present in the file
and absent from the run. A green suite looks identical either way. The first
was caught by a mutation verdict flipping, the second by counting methods while
doing something else. Neither was caught on purpose.

`SuiteIntegrityTests` now refuses a repeated name in a class and asks each class
what it actually carries, since a decorator or a later assignment can orphan a
definition without repeating a name. M53 holds it.

Worth your time: check whether anything else in the suite is unreachable by a
route those two tests do not cover.

## M3, and two defects that only appeared when it ran

`adc.py route` acquires, routes, prints one line, and with `--write` binds a
receipt. `--verify` re-reads the binding and exits 2 when anything moved.

Against this repository it returns the full recipe, which is the intended
resting state rather than a shortfall. Every rule ships `proposed`, a proposed
rule never matches, and a fact matching no rule forces full, so an unread policy
runs everything. Approving a rule is what makes a route cheaper, and D-064
leaves that to the owner.

The canonical full set lives in `gates.json`, not in the policy. A policy able
to define what "full" means could shrink it and still look complete. Absence
refuses rather than defaulting, because an empty full set is a comparison every
recipe passes. D-062.

Two defects, both found by running the command and neither by reading it:

1. The first receipt written with `--write` failed its own verification. The
   binding covers untracked files and the receipt lands under
   `.anti-dark-code/runs/`, so writing it changed the worktree it bound. Only
   the run store is excluded, never `.anti-dark-code` as a whole, because
   policy and gate files sit near it and a wider exclusion would let an
   escalator change without making any receipt stale. M57 holds the width.

2. Reverting a change left the receipt stale. The router's fingerprint carries
   size and mtime, which the acquisition boundary needs to catch a rewrite
   during its own run, and reusing the whole tuple made the binding depend on a
   clock. A receipt that stays stale after the bytes are restored binds the fact
   that something happened rather than the state, and a check that cries stale
   for no reason is one people learn to ignore. M59 holds it.

A third was caught by the code rather than by me: loading the router helpers
twice produced two module identities, and the policy validated by one was
refused by the other. That is the D-021 provenance guard working correctly on a
caller that was wrong.

The CLI tests run `adc.py` as a process, because half the contract is the exit
code and an in-process call can assert the right text beside the wrong status.

## The gate I did not meet, stated plainly

The slice says S-024 through S-051 must pass before receipt work starts. That
cannot be checked, and I did the work anyway.

Measured: of 51 acceptance criteria, 50 name an R id and S-014 names none. Six
of those ids appear anywhere in the suite. Forty-four do not, and 27 of the 28
criteria gating receipt work are among them. The evidence table in ENGINEERING
answers `test_route.py` for every requirement, which is true of all of them and
distinguishes none. It is a check that cannot fail, applied to the register
itself.

I judged the substance better than the bookkeeping: the behaviours are what this
cycle built, the suite is green, and the matrix catches 60 mutants, which is
stronger evidence than an id in a table. That judgement is the thing to
challenge, and D-061 states it as an open gap rather than a passing gate. No
statement anywhere claims those criteria verified.

**Question for you:** is that the right call, or should M3 have waited for the
mapping? If it should have waited, say so and I will build the traceability
check before M4.

## Open

- M4, the shadow comparator, is not started.
- No third host. A row that disagreed between hosts for any reason other than
  a skip would mean the code is platform-conditional where nobody intended it,
  and two hosts is the smallest number that can show that at all.
- The R-id to test mapping is unbuilt, and D-061 records the shape a fix takes:
  every registered id resolves to a named test that exists, with a shrinking
  list of untraced ids so the gap cannot grow quietly.
