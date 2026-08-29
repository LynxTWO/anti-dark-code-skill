# Handoff to Codex: verify and harden the assurance router specs

Date: 2026-08-28. From: Claude Opus 5. To: Codex. Status: Open.
Repository: `anti-dark-code-skill`, branch `main` at `9899df5`.

You are reviewing four design documents before they become an implementation plan. No code has been written yet. Nothing in this task builds anything.

---

## 1. Your role

Inspect, verify, edit, and add to the specs in `design/routing/`. Then write a handoff back, per section 7.

The most valuable thing you can do is **refute something**. These documents make specific claims about the codebase. They were written by an agent that read the code, which is exactly the condition under which a confident wrong claim survives. Treat every claim in section 4 as unproven until you have re-derived it from the bytes.

The repository's own lesson applies to this task directly. From `anti-dark-code/references/07-adversarial-review.md`: verify a publication against its approval, not its paperwork. Do not verify these documents against this handoff. Verify them against the code.

## 2. Authority

This mirrors the authority split the router itself defines, because the same reasoning applies to reviewing a spec.

| You may | You may not |
|---|---|
| Add a requirement, guardrail, test, or risk | Remove or weaken one silently |
| Raise a status toward Confirmed with evidence | Lower a Confirmed decision without recording why |
| Correct a factual claim that the code refutes | Change a decision the owner already ruled on, listed in section 3 |
| Edit the four documents in `design/routing/` | Edit anything under `anti-dark-code/`, `.github/`, or `metrics/` |
| Add new Open questions, risks, or decisions | Begin implementing the router |
| Propose a rewrite of a section | Apply a rewrite that changes an owner ruling |

If you believe a guardrail is too strict, say so in the handoff back with your reasoning. Do not relax it yourself. A reviewer that can quietly lower a requirement is the exact failure the router is designed to prevent.

New decisions you add go in `DECISION-LOG.md` starting at `D-016`, with the same block format and a `Revisit when:` line.

## 3. Owner rulings, settled, do not reopen

These were decided by the repository owner. Note a conflict in your handoff if you find one, but do not change them.

- **D-004** Obligations are capability ids. The catalog gets extended rather than a second vocabulary created.
- **D-005** `--level` becomes an escalate-only override. It may raise above the computed route, never lower it.
- **D-007** Route input is the final `base...HEAD` diff, with the reverted-commit limitation documented rather than solved.
- **D-008** `independent_review` is recorded in the receipt, not enforced by the tool.
- Approach A: routing is infrastructure under passes 00, 10, and 14. It is not a new numbered pass.
- Documents live in `design/routing/`. `docs/` is the published website.

## 4. Claims to verify independently

Each row is a claim the specs depend on. Re-derive it. Record `verified`, `refuted`, `inferred`, or `unknown` using the confidence vocabulary in `anti-dark-code/references/00-conventions.md`, and cite the file and line that proves your verdict.

| # | Claim | Where the spec relies on it |
|---|---|---|
| C-01 | `gates --level` takes `choices=(0,1,2,3)`, `default=0`, and is chosen manually | D-005, R-013 |
| C-02 | `gate_applies` returns `True` when a gate has no `include_globs`, so such a gate applies to every change | the premise that today's filtering is a changed-file filter, not change-impact routing |
| C-03 | `gate_definition_hash` binds 13 fields and none of them describe what a gate covers | D-012, the approval-hole argument |
| C-04 | `TOOLING_PATH_PREFIXES` causes `changed_files()` to drop `.agents/skills/` and `.anti-dark-code/` paths | **D-010**, ADD guardrail 4, R-014 |
| C-05 | `changed_files()` uses `--name-only`, so it carries no rename, delete, copy, or mode information | D-010, R-006 |
| C-06 | The `required` job in `.github/workflows/tests.yml` refuses unless every dependency reports exactly `success`, so a skipped job fails it | D-011, EDD 14 |
| C-07 | `proposal-intake.yml` and `efficiency-ledger.yml` both check out a trusted base validator and run it against the candidate as data | the claim that trusted-base CI routing has a proven in-repo pattern |
| C-08 | `assets/verification-capabilities.json` contains exactly 20 capabilities, including `V11 Change-impact analysis` and `V20 Confidence ladder` | D-004, and the framing that routing is not new doctrine |
| C-09 | `references/14-deterministic-verification.md` defines a four-level ladder, 0 through 3 | the mapping from route level to the existing ladder |
| C-10 | `references/00-conventions.md` names `.anti-dark-code/runs/` as the local run artifact path | D-014 |
| C-11 | `docs/` in this repository is the published website, not inert documentation | D-015, and a routing-policy lesson |

C-04 is the highest-consequence claim in the set. If it is wrong, D-010 and ADD guardrail 4 are wrong. If it is right, it is the reason the router cannot reuse the existing collector. Verify it first and carefully.

**Suggested verification commands.** Adapt freely. Do not trust these line numbers; find the code yourself.

```bash
grep -n "add_argument(\"--level\"" anti-dark-code/scripts/adc.py
grep -n -A 15 "^def gate_applies" anti-dark-code/scripts/adc.py
grep -n -A 12 "^def gate_definition_hash" anti-dark-code/scripts/adc.py
grep -n -A 10 "^TOOLING_PATH_PREFIXES" anti-dark-code/scripts/adc.py
grep -n -A 15 "^def changed_files" anti-dark-code/scripts/adc.py
sed -n '160,210p' .github/workflows/tests.yml
python -c "import json;d=json.load(open('anti-dark-code/assets/verification-capabilities.json'));print(len(d['capabilities']))"
```

## 5. Adversarial review of the design

Beyond fact checking, attack the design. Specific questions worth your time:

1. **Monotonicity.** ADD guardrail 1 says combination is union and maximum only. Read the requirement set R-001 through R-014 in `ENGINEERING.md` and ask whether any pair of them could interact to produce a downgrade. Is `force_full` monotonic? Is the interaction between `minimum_level` and `gate_ids` monotonic when two rules disagree?
2. **The self-grading rule.** ADD guardrail 3 forces the full route for changes to routing, policy, gates, CI, and shared test helpers. Is that list complete for this repository? What path could change routing behavior without appearing in it? Consider `conftest.py`, shared fixtures, `pyproject`, the validator, and the installer.
3. **Receipt staleness.** R-008 and R-009 cover worktree, policy, and gate changes. What else can change between writing a receipt and executing it that would make the receipt a lie? Consider environment, submodules, the git index, and the clock.
4. **The unknown path rule.** R-003 says an unmapped path forces the full route. Can a path be neither mapped nor unmapped, for example one that is excluded before rules are consulted? That is the C-04 failure mode generalized. Look for others.
5. **Purity.** D-002 claims `collect_change_facts` and `build_route` are pure. Given that facts must come from git, where exactly is the impure boundary, and is the split as stated actually implementable?
6. **The escalate-only hint rule.** D-006 says hints may only raise. Is there a formulation of a hint that raises one dimension while lowering another, for example narrowing breadth while raising sensitivity? If so, R-011 needs strengthening.

Report anything you find as a finding in section 7, with a severity and a proposed change. Findings that survive your own attempt to refute them are worth more than a long list.

## 6. Optional but high value: close Q-001

`Q-001` in `ENGINEERING.md` section 4.3 is the only Open question blocking slice work. It is scheduled as spike M1 in `SLICE-001-route-shadow.md`. If you close it here, M1 shrinks to catalog editing.

The question: the design named twelve evidence obligations. Seven were claimed to overlap existing capabilities:

| Obligation | Claimed existing capability |
|---|---|
| static | V09 Static architecture enforcement |
| contract | V08 Schema and contract validation |
| mutation | V01 Mutation testing |
| replay | V07 Record and replay regression corpus |
| performance | V14 Performance and leak budgets |
| independent-review | V17 Separated builder, challenger, and verifier roles |
| test-integrity | V18 Test-change policing |

Five were claimed to be genuinely new: `affected-unit`, `distribution`, `cross-platform`, `hostile-environment`, `fuzz`.

Read all 20 capability definitions in `anti-dark-code/assets/verification-capabilities.json`. Then answer:

- Is each claimed overlap real, or is it a loose match that would distort the capability's meaning?
- Are the five new ones genuinely distinct, or variations of existing entries? Note that `V12 Hermetic builds and tests` may already cover part of `distribution` or `cross-platform`, and `V15 Fault injection` may already cover part of `fuzz`.
- What is the real count of new capability ids needed?

If you answer this, update `Q-001` to Closed, record the outcome as a new decision `D-016`, and adjust `D-004` and `SLICE-001` milestone M1 to match. This is an addition, not a reopening of D-004, whose ruling was that obligations *are* capability ids. How many ids that requires is exactly what is open.

## 7. What to hand back

Write `design/routing/HANDOFF-BACK.md` with these sections, in this order. Keep it evidence first and short on prose.

```text
# Handoff back to Claude: assurance router spec review
Date. Agent. Repository state: branch, commit, suite result.

## 1. Verification results
Table: claim id, verdict (verified|refuted|inferred|unknown), evidence
(file and line, or command and output), one-line note.
Every claim C-01 through C-11 gets a row. No blanks.

## 2. Findings
Per finding: id (F-01...), severity (blocking|major|minor), the claim or
section it affects, what is wrong, the failure it would cause, and the
proposed change. Most severe first.

## 3. Edits applied
Per edit: file, section, what changed, why, and which finding it closes.

## 4. Edits proposed but NOT applied
Anything that would change an owner ruling from section 3 of the handoff,
or that you judged out of your authority. Include your reasoning so the
owner can rule.

## 5. Q-001 outcome
Closed with the real capability count and reasoning, or left Open with
what you learned and what still blocks it.

## 6. Questions back
Things you could not resolve from the repository, phrased so the owner
can answer them without reading the whole spec.

## 7. Readiness
One of: ready for implementation planning | ready with the listed
conditions | not ready, with the blocking findings named.
```

## 8. Ground truth for your environment

- **Repository root:** the directory containing `anti-dark-code/`, `design/`, and `.github/`.
- **Canonical suite invocation, from the repository root:**

  ```bash
  python -m pytest anti-dark-code/tests -q
  ```

  Running it from another directory fails with an `ImportError` that looks like a product defect and is not one. That is lesson 9c in `references/10-maintenance-harness.md`: a suite's verdict is defined by its configured runner, and zero discovery is a failed invocation, never a pass.
- **Known-good baseline, Windows, 2026-08-28:** `131 passed, 13 skipped, 45 subtests passed` in about 98 seconds. The skip count is platform dependent, and a Linux run skips fewer. A differing skip count is not by itself a failure. A differing pass count is.
- **Core validation:**

  ```bash
  python anti-dark-code/scripts/adc.py validate --mode universal
  ```

  A generated-artifact warning is expected. Note the absence of `--repo`: the `validate` subparser accepts `--skill` and `--mode` only, and adding `--repo` exits non-zero on an argparse error. An earlier revision of this handoff carried the wrong command, which Codex caught as F-10.
- **Do not run** anything that writes outside `design/routing/`, installs a dependency, or executes a gate with `--allow-exec`.

## 9. Writing rules for anything you write here

These documents pass a hygiene scan. Match it.

- No em dashes or en dashes anywhere. Use periods, commas, colons, or parentheses.
- Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages.
- Short sentences. Concrete nouns. Say "we do not know yet" when that is the truth.
- Every decision block carries exactly one status and a `Revisit when:` line.

Verify before you hand back. Scope the scan to the four spec documents and your handoff back, and exclude this file:

```bash
FILES="ARCHITECTURE.md ENGINEERING.md DECISION-LOG.md SLICE-001-route-shadow.md HANDOFF-BACK.md"
cd design/routing
grep -n $'—\|–' $FILES
grep -nioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" $FILES
```

Both should return nothing. Do not scan `HANDOFF-CODEX.md` itself: it quotes the banned list and the grep pattern, so it matches itself. That is a false positive, not a hygiene failure. The same is true of any file that documents the rule.

The four spec documents were hygiene clean at handoff time. If your scan reports a hit in one of them, you found either a real regression from your own edit or a flaw in the pattern. Say which.

## 10. What success looks like

A short handoff back where every claim carries a verdict with evidence, the findings are ones you tried and failed to refute, and the readiness line is honest. If C-04 is wrong, say so plainly and the design changes. If everything checks out and you found nothing, that is a valid result, and it is worth more than an invented finding.
