# Field study: what the shadow campaign measures in real repositories

The SLICE-002 machinery was built and tested against this repository, which is
a skill, not a product. This is what happened when the same code was pointed at
four repositories, three of them owned by other people, and asked the campaign's
question: for a class of change, would skipping the omitted gates have missed a
failure?

Every measurement here is read-only with respect to the repository measured.
Nothing was pushed, no branch was created, no issue or comment was opened. The
work was done in scratch clones, and the routing policies written for each
repository exist only in the scratch area. They were never installed anywhere.

## What was measured

| Repository | Merges with runs | Authors | Span | Records with evidence | Misses |
| --- | ---: | ---: | ---: | ---: | ---: |
| this repository | 31 | 1 | 25 days | 2 clean | 1, from the canary |
| LynxTWO/time-card-ledger | 24 | 2 | 51 days | 0 | 0 |
| JeremyABurton/1st-downs | 45 | 2 | 22 days | 7 clean | 0 |
| vitejs/vite | 216 | 52 | 53 days | 12 clean | 0 |
| LynxTWO/mix-marriage-offline | 14 | 1 | 46 days | not measured | — |

The first three rows are the earlier studies, recounted from their records for
this table. Time-card-ledger's 24 records are 22 `no_omission`, one
`not_measurable` and one `inconclusive`; 1st-downs' 45 are 7 `clean` and 38
`no_omission`; this repository's 31 are 2 `clean`, 11 `no_omission` and 18
`not_measurable`, the last because the jobs the gates map to did not exist yet
at those heads. The canary's miss came from a branch, not a merge, and is the
only miss any study produced.

Two of the owner's own repositories were added after the first four, on his
question, and neither changes the conclusion; one sharpens it.

**LynxTWO/mix-marriage-offline** has the second most expensive CI of anything
examined: 18 jobs, 224 machine-minutes per pull-request run, and a
`linux-serial` job that takes 42.8 minutes on its own. It is also the
clearest case of the constraint. Of its 14 merged pull requests, **none** is
documentation-only and 78% touch tests, from one author over a 46-day span
ending 2026-04-19. The prize is real and nothing can claim it, which is
time-card-ledger's finding again at four times the cost. It also cannot meet
the criterion's two-author requirement, and 14 pull requests in total is
below N=30 whatever the mix.

**LynxTWO/SignalForge** is private, so it is not a public case study, and it
has no pull-request population at all: zero merged pull requests, and its
four CI runs are all pushes to `main`. There is nothing for the campaign to
grade.

A further repository, obra/superpowers, was examined and not measured. It has no
CI workflows of its own: the only workflows GitHub reports are its dynamic
Copilot reviewer. Its tests exist, in a `tests/` tree that drives `claude -p`
and an `evals/` harness that drives real agent sessions, but nothing runs them
on a pull request, and its own testing document says so. With no authoritative
outcome to compare against, every record would be `not_measurable` with every
gate `unresolved`, which is the correct result and an empty one. A repository
has to verify itself before a campaign can ask whether it verifies too much.

Vite was chosen after measuring ten public repositories on the two axes the
first three studies proved decisive: whether CI is expensive enough that a skip
is worth anything, and whether changes are heterogeneous enough that any class
is ever skippable. Vite was the only candidate strong on both, with 17% of
merged pull requests documentation-only and 20% touching tests, against 55% and
more for Deno, Astro and Polars.

## The first finding: mature repositories already route, by hand

Three of the four repositories filter their own CI by path, and they did it
without a router, a policy language, or a campaign.

Vite's is ten lines. A `changed` job runs `tj-actions/changed-files`, and the
entire Build&Test matrix is skipped when every changed file matches `docs/**`,
`.github/**` except `ci.yml`, `packages/create-vite/template**`, or `**.md`.
Lint runs unconditionally. The required status check is a job named
`Build & Test Passed or Skipped`, which succeeds when the matrix is skipped, so
branch protection tolerates the shortcut. That is the same aggregate-check
pattern this repository uses for `required`.

Time-card-ledger's relay CI is path-filtered the same way.

This matters because it sets the bar. The router is not competing against
running everything. It is competing against ten lines of YAML that a
maintainer wrote once.

## The second finding: the hand filter takes 1084 minutes, the router adds 51

Over vite's last 216 merges, spanning 53 days:

| | Merges | Machine minutes |
| --- | ---: | ---: |
| Vite's changed-files filter skipped the matrix | 46 of 216 (21%) | 1084 |
| The router would omit a gate on top of that | 62 of 216 (29%) | 51 |
| ...of which from measurable records | | 24 |

The median test matrix costs 23.6 machine minutes across its six legs. Lint
costs 2.0 and always runs. The router's entire incremental contribution is
lint, on the changes where lint is the only thing it can drop, and it comes to
under five percent of what the hand-written filter already delivers. Two
caveats the challenge of the revision named: the 1084 is 46 times a median,
not a sum of anything that ran, and 76 of the 170 matrices that ran had a
failed leg, so the median includes shortened runs; the median over the 94
all-green matrices is 23.53, so the effect is nil.

The reason is structural, and the blockers pass names it. Of 216 changes, 133
touched something the policy calls verification authority, dominated by
`playground/**` with 371 changed-file hits, `**/__tests__/**` with 271,
`**/package.json` with 246 and `**/*.spec.ts` with 210. Vite's contributors
ship tests with their changes. Only 16 changes were blocked by paths my policy
failed to describe. The constraint is therefore D-093's principle, that tests,
manifests and lockfiles are verification authority, applied to a repository
that ships tests with code; a policy could not lawfully say otherwise, so this
is not an artifact of a policy written from outside the project.

## The third finding: the class the campaign wants to approve is unmeasurable

Thirty-six of the 216 records fall in the `docs-only` class, which omits
`ci-test`. Every one of them is `not_measurable`, and the reason is always the
same: `ci-test=skipped`.

Vite already skipped the matrix for those changes. There is no authoritative
outcome to compare a candidate against, so the campaign learns nothing about
exactly the class it most wants to approve. The measurement is blinded by the
very optimization it is trying to justify.

This is not a defect in the record format. `measurability` reading a skipped
gate as undecided rather than as a pass is correct, and it is what stopped the
study from recording 36 false clean records. But it means that in any
repository that already routes, the campaign cannot grade the routing.

## The fourth finding, and the serious one: backfilling over merges is survivorship

The only class in vite with evidence is `product-code` omitting `ci-lint`: 12
clean records, no misses, 8 authors, 49 days. On its face that is the campaign
working. Extended to 130 days of history it would reach the owner's N=30 and
the class would be eligible for approval.

It would be wrong.

Lint failed on **zero** of the 216 push runs for those merges. In vite's
pull-request CI runs it failed in 57 of 309. The first draft of this document
put that as "53 times in the runs behind them, and 87 of 151 pull requests";
the challenge of the design revision re-derived it and those figures were not
like for like: the 53 was a job count over the first 120 of 159 failing runs,
the 151 were mostly branch names, and the pull-request runs the listing
returns span a later window than the merges, so nothing joined them. The
comparison that holds is 0 of 216 push runs against 57 of 309 pull-request
runs. What a pull-request backfill would record of those 57 is smaller than
the headline and still decisive: 36 co-occur with a matrix failure and read
inconclusive, one is unmeasurable, and of the 20 miss-shaped runs 19 force
full under the study policy and one, run 33323484002 with a failed type
check, is a routed miss for exactly the route the merges showed twelve clean
records for. Those failures are the job doing its work, not the runner
failing: of 60 failing lint jobs examined, the failing step was `Check
formatting` in 22, `Typecheck` in 13, `Lint` in 11, `Build` in 3, `Test docs`
in 3 and `Check workflow files` in 1. Only 7 failed at `Install deps`. Vite's
contributors run into this job constantly. Main never records it, because a
pull request that fails it is fixed before it merges.

It is also worth naming what the `product-code` candidate would actually drop.
The job called lint runs formatting, type checking, linting, a build and the
documentation tests. A route that omits `ci-lint` omits the type checker.

A backfill over merge commits therefore measures a population that has already
been filtered by the gates it is grading. Every gate looks unnecessary there, in
proportion to how well it works. The better a gate is at catching problems, the
cleaner its record on main, and the stronger the campaign's case for removing
it.

The 12 clean records are real records produced by correct code. They are also
exactly what this bias produces, and nothing inside the record distinguishes
the two.

## What this implies for the campaign

Three things follow, and none of them is a change to the record format:

1. **The backfill population is wrong.** Grading a candidate against merge
   commits cannot see what the gates caught. The authoritative outcome the
   campaign needs is the pull request's own run history, including superseded
   attempts, because that is where a gate's catches are recorded. This affects
   the brief's section 5 directly.
2. **Live records do not have this problem**, because a live record is written
   against the run that is actually gating that pull request, before anyone has
   fixed anything. The campaign's live half is sound. Its historical half is
   not, and the backfill is what makes N=30 reachable in months rather than
   years.
3. **The economic case for routing is not speed.** In a repository where a skip
   saves real time, the class that could be skipped is already skipped by hand.
   In a repository where routing is safe, the saving is a lint job. Across four
   repositories the router never found a safe skip worth more than a few
   minutes a month that a path filter had not already taken.

## Method, and one deviation

Each study used the production code: `adc_route.load_policy`,
`read_change_inputs`, `collect_change_facts`, `build_candidate_route`, and
`adc_shadow.build_record`, with the repository's real CI job outcomes from the
Actions attempts endpoint.

One deviation, stated because it was necessary and because it was checked.
`command_backfill` checks each head out into a throwaway worktree so
acquisition can read `HEAD`, which costs about 45 seconds per change on vite's
tree, or nearly three hours for this study. The study instead ran the same
acquisition function through a runner that rewrites the literal token `HEAD` to
the commit under test, with every git command, flag, parser and problem code
unchanged, and no checkout. The index, worktree and untracked sources read a
clean clone and are empty, exactly as they are in a fresh detached checkout.
Equivalence was not assumed: 11 records had already been produced by the
checkout path before the switch, and the no-checkout path reproduced all 11
with zero differences outside `record_id` and `audit`.
