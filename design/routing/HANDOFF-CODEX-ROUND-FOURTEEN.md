# Handoff to Codex: round fourteen

Date: 2026-08-31. Starting point: the head of `claude/round-thirteen-audit`.

## Objective

**Close SLICE-001.** M1 through M4 are implemented. What remains is Task 13, the section 9 evidence list, and the section 11 definition of done — plus one human gate that is not yours to close.

This is a convergence round. The loop has run thirteen times and the slice is still `Proposed`. The goal is to reach a state where the only thing standing between SLICE-001 and `Done` is Daniel Boyd's walkthrough, and to make that walkthrough cheap to perform.

Read first:

1. `design/routing/HANDOFF-BACK-ROUND-THIRTEEN.md`
2. `design/routing/SLICE-001-route-shadow.md`, sections 9 and 11
3. `design/routing/plans/2026-08-28-assurance-router-slice-001.md`, Task 13
4. `design/routing/DECISION-LOG.md`, D-071 through D-077

### What a failed round looks like

- The slice is still `Proposed` and no new evidence item is ticked.
- An unmet section 9 item was ticked without the evidence it names.
- macOS was claimed without an observed run.
- A round was spent reviewing round thirteen instead of closing items.

## 1. Two rows, one host

M88 and M89 carry Windows results only. Replay all 89 rows on T540P under the D-068 rules and restore the two-host property. Do this first; it is small.

## 2. Task 13, run for real

Run every command Task 13 names and record the actual counts and the receipt path. Do not paraphrase them, and do not reuse round thirteen's numbers.

Exercise both error paths and record what happened: an unreachable base, and a corrupted `routing-policy.json` restored afterwards. Confirm no receipt is written on refusal.

## 3. Section 9, item by item

Four items are unticked. Each needs closing or an explicit, recorded narrowing. Do not tick one without its evidence.

- **"Automated tests covering every acceptance criterion, passing on Linux, macOS, and Windows."** macOS has never been observed in fourteen rounds. Either obtain one real macOS run, or amend this item to say what is actually true — Linux and Windows observed, macOS configured in CI only — and record the amendment as a decision. **Do not tick it as written.** A false tick here is worse than an open box.
- **"EDD section 17 per-change checklist satisfied for every change in the slice."** Work out whether this is achievable retrospectively across thirteen rounds. If it is not, say so and narrow it to the changes from a stated commit forward.
- **"The clean distribution archive check passes with the new template included."** Runnable now. Run it.
- **"K-01 through K-13, L-01 through L-09, and N-01 through N-08 closed with failing-before and passing-after evidence."** Enumerate them, state which are closed, and be honest about which are not.

## 4. Small open items

- **R-022's map understates its coverage.** `test_a_candidate_selection_cannot_remove_a_gate` holds a clause R-022 names but is not mapped to it. Fix the map.
- **D-071 portability.** The guard probes literal source-layout paths. Either state a measured installed-layout invariant or narrow the clause explicitly. Round twelve confirmed the gap; two rounds have now deferred it.
- **D-073 is provisional.** Confirm alternative 1 or replace it.
- **D-077 strictness.** A gate that moves an mtime inside the repository is now stale. If that is wrong for a real gate, reverse it; M88 holds it either way.
- **The 64-commit historical scan** has not been rerun for three rounds. Automate it or retire it explicitly.

## 5. Prepare the human gate

Section 11's last box is "Human walkthrough completed and approved by Daniel Boyd." That is the owner's, not yours. Your job is to make it cheap.

Write `design/routing/WALKTHROUGH-SLICE-001.md`: a short, ordered script the owner can follow at a terminal in under thirty minutes. Commands to run, what each should print, what to look at and why it matters, and the specific questions the owner is being asked to approve — above all D-064, since approving a routing rule is the decision this whole slice defers.

It is a reading script, not a summary of the work. Assume the reader has not read the decision log.

## Traceability gate

- `untraced` is empty. Round thirteen emptied it after closing R-018 properly, having found round twelve emptied it while R-018's implementation was narrower than its clause. Before you rely on it, pick one requirement and disprove its coverage the way round thirteen did: run the real code against the case the clause names.
- Any new node goes in only when it exists and collects.
- `REVIEWED_UNTRACED` shrinks only with a named reviewer and a recorded reason.

## Non-negotiable boundaries

- Do not approve any routing-policy rule. That is the owner's call and it is the point of the walkthrough.
- Do not enable selective local or CI execution.
- Do not mark SLICE-001 `Done`. The last box is the owner's.
- Do not claim a macOS result without an observed run.
- Do not make a candidate route acceptable to the receipt verifier or gate selector.

## Deliverables

1. Every active matrix row recorded on both hosts.
2. Task 13 run with real recorded numbers, both error paths exercised.
3. Section 9 items closed or explicitly narrowed with a decision, none falsely ticked.
4. Section 11 in a state where only the human walkthrough box remains.
5. `design/routing/WALKTHROUGH-SLICE-001.md`.
6. `design/routing/HANDOFF-BACK-ROUND-FOURTEEN.md` naming exactly what still blocks `Done`.

If everything else closes and macOS is the only thing standing in the way, say so plainly in one line at the top of the handoff. That is a decision for the owner to make in an afternoon, and it should not take a fifteenth round to surface.
