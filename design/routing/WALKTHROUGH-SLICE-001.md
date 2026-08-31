# SLICE-001 owner walkthrough

Budget: 25 minutes. Run from the repository root on the round-fourteen branch. This script reviews evidence and decisions. It does not approve a routing rule, enable selective execution, or mark the slice `Done`.

## 1. Confirm the review target (2 minutes)

```powershell
git branch --show-current
git log -1 --oneline
git status --short
```

Expected: the round-fourteen branch, its latest handoff commit, and no tracked change. `.anti-dark-code/` may appear as an untracked local run store.

Look at the branch and status first so later receipts and test output are tied to the intended tree.

## 2. Read the shipped authority state (5 minutes)

```powershell
python -c "import json,pathlib; d=json.loads(pathlib.Path('.agents/skills/anti-dark-code/calibration/routing-policy.json').read_text()); print('\n'.join('{}: {}'.format(r['id'],r['review_status']) for r in d['rules']))"
python -c "import json,pathlib; d=json.loads(pathlib.Path('.agents/skills/anti-dark-code/calibration/gates.json').read_text()); print('owner_confirmed_safe_to_execute=',d['execution_policy']['owner_confirmed_safe_to_execute']); print('gates_with_argv=',[g['id'] for g in d['gates'] if g.get('argv')])"
```

Expected:

```text
docs-only: proposed
product-code: proposed
schema-contract: proposed
verification-authority: proposed
skill-policy: proposed
mode-change: proposed
owner_confirmed_safe_to_execute= False
gates_with_argv= []
```

Look for any rule that is not `proposed`. D-064 is the reason every authoritative route is still canonical-full. The gate file names reviewed CI capabilities but supplies no executable command and does not authorize local execution.

Owner question 1: Is D-064 still the correct SLICE-001 boundary, with every rule left `proposed` until a separate evidence campaign and rule-by-rule approval change? Answer yes or no. A no answer blocks slice approval; it does not authorize editing a rule during this walkthrough.

## 3. Exercise the two execution-authority boundaries (5 minutes)

```powershell
python -m pytest -q anti-dark-code/tests/test_route.py::CandidateRouteTests::test_a_candidate_selection_cannot_remove_a_gate anti-dark-code/tests/test_route.py::CanonicalFullTests::test_force_full_runs_the_canonical_set_despite_include_globs
git grep -n "CandidateRoute cannot select executable gates" -- anti-dark-code/scripts/adc.py
git grep -n "canonical set is named directly" -- anti-dark-code/scripts/adc.py
```

Expected: `2 passed`. The first source lookup reaches the candidate refusal. The second reaches the force-full branch that selects canonical ids before applicability filtering.

Look for two separate properties: proposed candidate data cannot enter executable selection, and force-full selection does not use changed-file globs to remove a canonical gate.

Owner question 2: Does this preserve the intended shadow-only boundary, with candidate routes useful for measurement but never acceptable to receipts or executable selection? Answer yes or no.

## 4. Mint and verify one real receipt (5 minutes)

```powershell
python anti-dark-code/scripts/adc.py route --repo . --base origin/main --write
```

Expected: one `ROUTE` line with Level 3, passes `07,10,11,14`, gates `distribution,full-suite,hostile-environment,mutation-replay,validate-core`, `force_full=true`, and `complete=true`. Then verify the newest receipt:

```powershell
$receipt = (Get-ChildItem .anti-dark-code/runs/*.json | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
python anti-dark-code/scripts/adc.py route --repo . --verify $receipt
```

Expected: `FRESH` followed by the receipt id.

Look at the selected rules field. It should be `rules=-` because every shipped rule is proposed. The full result comes from the validated root recipe, not from a proposed rule.

## 5. Check the closure evidence without replaying history (5 minutes)

```powershell
python -m pytest anti-dark-code/tests -q
python -m pytest anti-dark-code/tests/test_route.py -q -k MutationMatrixIntegrity
python design/routing/mutants/replay.py M92
python anti-dark-code/scripts/adc.py validate --skill anti-dark-code --mode universal
gh run view 33402328694 --json headSha,conclusion
```

Expected on the recorded Windows host: `425 passed, 14 skipped, 48 subtests passed`; six matrix-integrity tests pass; M92 is caught; universal validation reports 0 errors and one generated-artifact warning; and run `33402328694` reports `SUCCESS` at `157f10a1b2f0bc1c65e3e1ea92ed49d37316c987`.

The required run predates the round-fourteen portability delta. That delta has Windows suite evidence and Linux and Windows M92 evidence, not a new macOS run. D-080 also withdraws the claim that every historical branch commit satisfied the per-change checklist. Read those qualifications in section 9 rather than treating the checkboxes as broader claims.

Owner question 3: Are the platform and historical EDD qualifications in D-080 and SLICE-001 section 9 acceptable as the honest evidence boundary? Answer yes or no.

## 6. Review the three durable decisions (3 minutes)

Read D-082 through D-084 in `design/routing/DECISION-LOG.md`.

- D-082 checks both `anti-dark-code/...` and `.agents/skills/anti-dark-code/...` authority spellings. Owner question 4: Does that cover the managed layout the installer supports? Answer yes or no.
- D-083 confirms typed `ReceiptError` refusal for an unreadable fingerprint and mints no identity. Owner question 5: Is that the durable unreadable-state model for this slice? Answer yes or no.
- D-084 keeps a gate stale if it writes in the verified worktree, even if it restores the bytes. A future writing gate must use an isolated checkout. Owner question 6: Is that strictness correct for the gates you expect to approve? Answer yes or no.

## 7. Record the human gate

- [ ] Questions 1 through 6 have recorded yes answers, or each no answer has a named follow-up.
- [ ] No routing-policy rule changed during this walkthrough.
- [ ] Selective local and CI execution remain disabled.
- [ ] Daniel Boyd approves the SLICE-001 walkthrough.

Only the owner may check the last box. After that approval, a separate follow-up may mark SLICE-001 `Done` and update the ADD boundary to SLICE-002.
