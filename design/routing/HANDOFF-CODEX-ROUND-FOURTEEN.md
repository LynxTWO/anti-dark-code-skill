# Handoff to Codex: round fourteen

Date: 2026-08-31. Starting point: the head of `claude/round-thirteen-audit`, draft PR #23.

## Objective

**Close SLICE-001.** M1 through M4 are implemented. What remains is the section 9 evidence list, the section 11 definition of done, and one human gate that is not yours to close.

Thirteen rounds in, the slice is still `Proposed`. The goal is to reach a state where the only thing between SLICE-001 and `Done` is Daniel Boyd's walkthrough, and to make that walkthrough cheap to perform.

Round thirteen audited every unticked item, so this handoff names the actual state rather than asking you to find it. **Three of the four are closeable now, and one is already proven by CI.**

Read first:

1. `design/routing/HANDOFF-BACK-ROUND-THIRTEEN.md`
2. `design/routing/SLICE-001-route-shadow.md`, sections 9 and 11
3. `design/routing/DECISION-LOG.md`, D-071 through D-079
4. `design/routing/plans/2026-08-28-assurance-router-slice-001.md`, Task 13

### What a failed round looks like

- The slice is still `Proposed` and no evidence item moved.
- An item was ticked without the evidence it names.
- A round was spent reviewing round thirteen instead of closing items.

## 1. Restore the two-host record

M88 through M91 carry Windows results only, and M68 was retargeted after the guard was rewritten so its Linux record is stale. Replay all 91 rows on T540P under the D-068 rules. Do this first; it is small and it is the strongest evidence this project has.

## 2. Section 9, item by item, with the state already established

### "Automated tests ... passing on Linux, macOS, and Windows" — closeable now

macOS has been observed. `.github/workflows/tests.yml:27` runs `[ubuntu-latest, macos-latest, windows-latest]`, and run `33345218999` at `8f46a76` reported `success  macos-latest / Python 3.12`. The project spent fourteen rounds saying "no observed macOS result" without reading the job list.

The catch is real, though: `tests.yml` fires on `pull_request` and `push: main` only, so **5 of the slice's 90 commits ever ran the matrix**, and `codex/round-twelve-m4` never ran CI at all. PR #23 now puts the round-thirteen head through the full matrix.

Tick this against **PR #23's run id and sha**, not against `33345218999`, which predates roughly 1,400 lines of router and test change. Do not tick the "every acceptance criterion" half from a CI run: no job proves S-001..S-051 coverage. Split the bullet.

### "The clean distribution archive check passes" — closeable now

The `distribution` job at `tests.yml:72-98` is exactly that check: it extracts `git archive HEAD` and validates the tree with `--mode distribution`. It passed in the same run. Tick it against PR #23's run.

### "K-01 through K-13, L-01 through L-09, N-01 through N-08" — needs a disposition table

The 30 ids are the numbered findings of the round-four, five and six reviews, defined in `HANDOFF-BACK-PURE-LAYER.md:46-184`, `HANDOFF-BACK-ROUND-FIVE.md:72-173`, and `HANDOFF-BACK-ROUND-SIX.md:46-128`. Failing-before evidence exists for all 30.

Passing-after evidence **recorded against the named id**: 12 of 30 — K-02, K-06, K-07, K-09, K-10, K-11, K-12, K-13, L-05, L-08, N-02, N-06.

Explicitly not closed at their last per-id verdict: 17. Their substance was carried forward under new ids and mostly closed by rounds eight to ten, but no document ties that closure back to the original id.

**N-08 was never addressed at all** until round thirteen. D-079 closes it: the global-filter test configured a *local* filter and was cited as evidence for R-054's global clause.

Replace the bullet with a per-id table naming, for each of the 30, either the round that verified it closed or the successor id and requirement that now carries it. That is bookkeeping, not investigation — the audit trail exists.

### "EDD section 17 per-change checklist satisfied for every change" — narrow it, do not tick it

Not retrospectively satisfiable, and the slice supplies its own counterexamples. `a92c869` shipped a live mutant with a green suite either side; `a4949a8` records a test present in the file and absent from the run, twice. Item 1 of the checklist has no CI record for 85 of 90 commits and no push can create one retroactively.

Record a decision amending it to: satisfied from a named commit forward; for the earlier range the per-change claim is withdrawn as unreconstructible, and what is claimed instead is the slice-level statement that HEAD passes the three-platform matrix, adds no runtime dependency, and replays the matrix clean. Then make the forward half true by giving item 5 an artifact — a commit trailer or a git note — so a later round can check it rather than assert it.

## 3. Section 11 and the small corrections

- **Acceptance criteria.** 51 S-ids, all naming an R-id, none orphaned. 49 map to requirements carrying collected test nodes. Two, S-014 and S-050, rest on R-053, which carries mutation evidence rather than tests — a sanctioned class in the repo's own checker. **S-050's cell mislabels it as "R-053 test"; S-014 words it correctly as "R-053 mutation replay".** Fix S-050, then tick with the qualifier that 2 of 51 rest on replay evidence.
- **"Nothing is able to skip a check."** True today and measurably so, but the claim is unconditional while its truth rests entirely on D-064's deferral. Restate it as the conditional it is: under the shipped proposed-only policy, every route forces the full recipe, `gates --route` selects the canonical set by id, and candidate data is refused at both boundaries.
- **R-022's map understates its coverage.** `test_a_candidate_selection_cannot_remove_a_gate` holds a clause R-022 names but is not mapped to it.
- **The 64-commit historical scan.** Round thirteen reran it: 164 commits, 58 carrying a matrix, 2,994 active row/commit pairs in pass one and 7,423 in pass two, confirming `a92c869`/M01 as the sole live-mutant state and exactly 12 drift pairs, matching round ten. The ~100 commits added since produced nothing new. **Retire the standing rerun** with a decision naming `MutationMatrixIntegrityTests` plus the required CI gate as its successor. Note honestly that the CI guard fires only on `pull_request` and `push: main`, so it never sees intermediate branch commits — but a mutant fixed before merge ships nothing.
- **D-071 portability** is still open across three rounds. `SELF_GRADING_PATHS` probes literal source-layout paths and cannot state an installed-layout invariant. Close it or narrow it explicitly.
- **D-073 is provisional.** Confirm alternative 1 or replace it.
- **D-077 strictness.** A gate that moves an mtime inside the repository is now stale. If that is wrong for a real gate, reverse it; M88 holds it either way.

## 4. Prepare the human gate

Write `design/routing/WALKTHROUGH-SLICE-001.md`: an ordered script the owner can follow at a terminal in under thirty minutes. Commands to run, what each should print, what to look at and why it matters, and the specific questions the owner is being asked to approve — above all D-064, since approving a routing rule is the decision this whole slice defers.

It is a reading script, not a summary of the work. Assume the reader has not read the decision log.

## Traceability gate

`untraced` is empty. Round twelve emptied it while R-018 was narrower than its clause; round thirteen emptied it again after closing R-018, R-005 and R-021 properly. **Before you rely on it, pick one requirement and try to disprove its coverage the way round thirteen did**: run the real code against the case the clause names, rather than reading the test.

Any new node goes in only when it exists and collects. `REVIEWED_UNTRACED` shrinks only with a named reviewer and a recorded reason.

## Non-negotiable boundaries

- Do not approve any routing-policy rule. That is the owner's call and the point of the walkthrough.
- Do not enable selective local or CI execution.
- Do not mark SLICE-001 `Done`. The last box is the owner's.
- Do not tick an evidence item without the evidence it names.
- Do not make a candidate route acceptable to the receipt verifier or gate selector.

## Deliverables

1. Every active matrix row recorded on both hosts.
2. Task 13 run with real recorded numbers, both error paths exercised.
3. Section 9 items closed against named run ids, or narrowed by decision. None falsely ticked.
4. Section 11 in a state where only the human walkthrough box remains.
5. `design/routing/WALKTHROUGH-SLICE-001.md`.
6. `design/routing/HANDOFF-BACK-ROUND-FOURTEEN.md` naming exactly what still blocks `Done`.

If everything closes and only the walkthrough remains, say that in one line at the top. That is the sentence this project has been working toward for fourteen rounds.
