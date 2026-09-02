# Handoff back to Codex: round fifteen

Date: 2026-08-31. Agent: Claude. Base: `57e941f`, the head of `codex/round-fourteen-convergence`. Branch: `claude/round-fifteen-verify`, draft PR #25.

**This file was missing.** The round-sixteen handoff told its reader to begin here, and it had never been written. Codex found that within minutes of starting, alongside D-088 and D-089 being cited by eleven places and existing in none. Both are recorded in D-090, and both are round fifteen's own defects rather than findings about round fourteen.

## 1. Terminal outcome

- **Round fourteen's numbers reproduce exactly**: `425 passed, 14 skipped, 48 subtests`; 92 rows, 88 active, every active row on both hosts; run `33402328694` real, green, and at the sha it names. Round fourteen did not falsely tick anything, and its two `[~]` marks were the right call.
- **One inherited defect was serious**: repository code could execute during acquisition. D-085 and D-088 close it.
- **Round fifteen introduced five defects of its own.** A self-audit found them, and Codex found two more that the self-audit did not. They are listed in section 4, because a round that only reports what it fixed is not reporting.
- SLICE-001 remains `Proposed`. No routing rule was approved and selective execution stays disabled.

## 2. What round fifteen changed

### D-085 and D-088: repository code could execute during acquisition

`_filter_overrides` neutralized content filters by emitting `-c filter.<name>.clean=`, and git splits a `-c` argument on the **first** `=`. A driver named `a=b` produced `-c filter.a=b.clean=`, which git read as the key `filter.a`, leaving `filter."a=b".clean` live. A repository reaches such a driver from its own `.gitattributes`, and `check-attr` resolves it.

Measured against the real `read_change_inputs`, payload writing outside the worktree so the boundary fingerprint could not see it:

    driver 'plain'   executed=False  complete=True
    driver 'a=b'     executed=True   complete=True  problems=()

Repository code ran, and the snapshot still called itself complete, so a selective route would also have been authorised. Both halves of R-034 and R-054 failed at once.

D-085 verifies the neutralization with `config --get` rather than assuming it, and skips the worktree comparison entirely when a driver survives — refusing to route afterwards would already have started the program. D-088 then removes the cost of that refusal by neutralizing through `GIT_CONFIG_COUNT`, which carries key and value separately so no name is inexpressible, with D-085's refusal kept as the fallback.

### D-086 and D-089: the self-grading guard, corrected a fourth and fifth time

D-086 extended the guard from source-layout paths to the four layouts the installer writes, after finding that `.claude/skills/anti-dark-code/SKILL.md` — a file `install_skill` writes by default — routed at Level 0 under a policy that loaded clean.

D-089 closes the fifth hole. The derivation only expanded paths starting `anti-dark-code/`, and the two calibration entries were already spelled `.agents/skills/...`, so they gained nothing. `.anti-dark-code/calibration/routing-policy.json`, which is what `calibration_dir()` returns for any repository without a managed install, routed at Level 0 in every shape. D-086's own Consequences section had named that residual and dismissed it as "calibration rather than a skill tree". Calibration is the authority.

### D-087: a mutation target must match exactly one place

`replay.py` rewrites the first occurrence only. Five active rows matched two places and reported `caught` while testing one. The uniqueness guard now fails any active row matching more than once.

### D-090: a decision id cited in code must exist

Added after Codex found D-088 and D-089 cited in eleven places and recorded in none.

## 3. Verification

Windows 11, Python 3.14.2, Git 2.50.1.

- Round fourteen baseline reproduced: `425 passed, 14 skipped, 48 subtests passed`.
- Final: `436 passed, 14 skipped, 48 subtests passed`.
- Full replay at this head: **95 mutants, 0 not caught.** Sources restored to exact pre-run hashes.
- Matrix: 95 rows, 91 active, 4 superseded. 83 active rows carry Windows and Linux; 8 carry Windows only and await a T540P run; 3 are `caught elsewhere` where Windows skips the symlink test.
- Universal validation: 0 errors, 1 expected generated-artifact warning.
- CI run `33434352766` at `9dd7a3b`: green on ubuntu 3.12 and 3.13, macOS, windows, both hostile-environment legs, the clean distribution archive, and the Linux mutation replay.

Run `pytest` with `-p no:cacheprovider`. Without it pytest writes `anti-dark-code/.pytest_cache` inside the managed tree, changes its digest, and fails three provenance tests in `test_adc.py`. That cost an hour and a wrong diagnosis.

## 4. Round fifteen's own defects

Every one of these was in work this round produced, and none was found by its author unaided.

1. **A duplicated loop made mutation row M91 ambiguous**, one commit after the guard that catches ambiguity. Fixed by removing the duplication.
2. **The first filter verification used `--get-regexp`**, which lists the file value beside the empty override, so every ordinary driver read as live. It would have refused acquisition in any repository using git-lfs.
3. **D-087 claimed six ambiguous rows and blamed the previous round.** Five, and the sixth was this round's own commit.
4. **SLICE-001 and ENGINEERING claimed a two-host record for eight rows that carried no results at all**, because the retarget deleted five and three were new.
5. **The walkthrough was called true twice and was not**, including a matrix claim that those eight rows had Windows verdicts when they had none.
6. **D-088 and D-089 were cited in eleven places and never written** — found by Codex, not by the audit.
7. **`HANDOFF-BACK-ROUND-FIFTEEN.md` did not exist** while the next handoff instructed its reader to start there — also found by Codex.

Items 6 and 7 survived a full suite, a validation run, a 95-row replay, and a five-agent adversarial audit. D-090 closes item 6 as a class. Nothing yet closes item 7.

## 5. What round sixteen should do

`design/routing/HANDOFF-CODEX-ROUND-SIXTEEN.md` has the detail. In short: verify all of the above independently, restore the Linux per-row record for the eight rows, and evaluate parallel execution against a verdict-identity bar. Nothing in this repository is parallel; the owner's host has 32 cores and uses one, and the replay holds the shared tree for forty minutes.

Do not treat this handoff as acceptance of its own contracts. Its author has been wrong about that specifically, twice.
