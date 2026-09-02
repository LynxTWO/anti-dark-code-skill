# SLICE-001 owner walkthrough

Budget: 30 minutes, most of it waiting on one test run. Run from the repository root in PowerShell.

This script reviews evidence and asks you six questions. It does not approve a routing rule, enable selective execution, or mark the slice `Done`. Nothing here writes to a tracked file; step 4 writes one receipt into the ignored run store.

**If any command's output does not match what is written here, stop and record the difference.** A mismatch is a finding, not a formality — this project has repeatedly found that a document said something the tree did not. You are the last check on that.

## 0. Get onto the reviewed tree (2 minutes)

```powershell
git fetch origin
git switch --detach origin/codex/round-sixteen-verify
git log -1 --format="%h %s"
git status --short
```

`--detach` on purpose. A plain `git checkout` of that branch exits 128 if any worktree already holds it, which is likely: the agents that produced this work keep their own worktrees. Detaching reads the same commit without claiming the branch.

Expected: `git status --short` prints nothing, or only untracked `.anti-dark-code/`, which is the local run store.

If it shows tracked modifications, stop. Every number below describes a clean tree, and three provenance tests in `test_adc.py` compare the working tree against `git archive HEAD` and will fail on any difference.

## 1. Read the rules you are being asked not to approve (4 minutes)

The whole slice rests on one decision: every routing rule ships unapproved, so the router always returns the full recipe and can save nothing. Read the rules themselves before ratifying that.

```powershell
python -c "import json,pathlib; d=json.loads(pathlib.Path('.agents/skills/anti-dark-code/calibration/routing-policy.json').read_text()); [print('{:22} {:9} -> level {}, force_full={}'.format(r['id'], r['review_status'], r['requires'].get('minimum_level'), r['requires'].get('force_full', False))) for r in d['rules']]"
```

Expected, all six `proposed`:

```text
docs-only              proposed  -> level 0, force_full=False
product-code           proposed  -> level 2, force_full=False
schema-contract        proposed  -> level 2, force_full=False
verification-authority proposed  -> level 3, force_full=True
skill-policy           proposed  -> level 3, force_full=True
mode-change            proposed  -> level 2, force_full=False
```

Read `docs-only` hardest. It is the cheapest route the policy offers, and approving it would be the first thing that ever lets this repository run less than everything.

Then read D-064 itself, which is the decision you are ratifying:

```powershell
python -c "import pathlib,re; t=pathlib.Path('design/routing/DECISION-LOG.md').read_text(encoding='utf-8'); m=re.search(r'## D-064.*?(?=\n## D-)', t, re.S); print(m.group(0))"
```

```powershell
python -c "import json,pathlib; d=json.loads(pathlib.Path('.agents/skills/anti-dark-code/calibration/gates.json').read_text()); print('owner_confirmed_safe_to_execute =', d['execution_policy']['owner_confirmed_safe_to_execute']); print('gates carrying an executable command =', [g['id'] for g in d['gates'] if g.get('argv')])"
```

Expected: `False` and `[]`. No gate carries a command, so nothing local can execute even if a rule were approved.

> **Question 1.** Every rule stays `proposed` until a separate evidence campaign justifies approving one, rule by rule. Is that still the right boundary for SLICE-001? **yes / no**

## 2. Check the two execution-authority boundaries (3 minutes)

```powershell
python -m pytest -q anti-dark-code/tests/test_route.py::CandidateRouteTests::test_a_candidate_selection_cannot_remove_a_gate anti-dark-code/tests/test_route.py::CandidateRouteTests::test_a_candidate_route_is_refused_by_the_receipt_writer anti-dark-code/tests/test_route.py::CanonicalFullTests::test_force_full_runs_the_canonical_set_despite_include_globs
```

Expected: `3 passed`. The middle one is the receipt-writer refusal named in question 2; without it that question asks you to ratify a boundary nothing here demonstrates.

The first holds that shadow data measuring a proposed rule can never enter executable gate selection. The second holds that a forced-full route runs the canonical set even when every gate's `include_globs` would have excluded the changed file.

> **Question 2.** Candidate routes exist to measure what a proposed rule would have skipped, and are refused by both the receipt writer and gate selection. Is that the boundary you want? **yes / no**

## 3. Mint and verify one real receipt (4 minutes)

```powershell
python anti-dark-code/scripts/adc.py route --repo . --base origin/main --write
```

Expected: one `ROUTE` line reading `level=3`, `passes=07,10,11,14`, `gates=distribution,full-suite,hostile-environment,mutation-replay,validate-core`, `force_full=true`, `complete=true`, and **`rules=-`**.

`rules=-` is the point. No rule matched, because none is approved. The full result comes from the validated root recipe, not from any rule.

```powershell
$receipt = (Get-ChildItem .anti-dark-code/runs/*.json | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
python anti-dark-code/scripts/adc.py route --repo . --verify $receipt
```

Expected: `FRESH` and the receipt id.

Now make it stale, which is the property the receipt exists for:

```powershell
"scratch" | Out-File -Encoding utf8 walkthrough-scratch.txt
python anti-dark-code/scripts/adc.py route --repo . --verify $receipt
Remove-Item walkthrough-scratch.txt
python anti-dark-code/scripts/adc.py route --repo . --verify $receipt
```

Expected: `STALE` with `ADC-STALE-004 worktree_identity`, then `FRESH` again once the file is gone. If the middle command says `FRESH`, stop: the receipt is not binding the worktree.

## 4. Run the evidence (10 minutes, mostly waiting)

```powershell
python -m pytest anti-dark-code/tests -q -p no:cacheprovider
```

**The pass count is host-dependent, so read the failure count, not the total.** Expected: `0 failed`. The final Round Sixteen Windows evidence host reported `486 passed, 14 skipped, 62 subtests passed`; another host may run tests this host skips. A different total is not a finding. A failure is.

Roughly three minutes.

`-p no:cacheprovider` keeps this evidence run free of host-generated cache state. D-092 now excludes `.pytest_cache` from install provenance, so the old false digest drift is fixed; retaining the flag makes this command match the authoritative Round Sixteen evidence environment.

```powershell
python anti-dark-code/scripts/adc.py validate --skill anti-dark-code --mode universal
```

Expected: `VALID (universal): 0 errors, 1 warning(s)`. The single warning lists generated `__pycache__` files and appears only because you just ran pytest.

```powershell
python -c "import json,pathlib; rows=json.loads(pathlib.Path('design/routing/mutants/matrix.json').read_text()); act=[r for r in rows if not r.get('superseded_by')]; both=[r for r in act if {x['platform'] for x in r.get('results',[])} >= {'Linux','Windows'}]; print('rows', len(rows), '| active', len(act), '| recorded on both hosts', len(both)); print('awaiting host records:', [r['id'] for r in act if r not in both])"
```

Expected:

```text
rows 96 | active 91 | recorded on both hosts 91
awaiting host records: []
```

All 91 active rows now carry both authoritative Windows and T540P Linux records. M92 is one of five superseded rows: the frozen Linux replay measured it surviving after D-093 made its old path-loop attack redundant, and D-094 records why the stronger M96 authority-contract mutant replaces it. M96 was caught on both hosts.

```powershell
python -c "import json,pathlib; d=json.loads(pathlib.Path('design/routing/PARALLEL-EVIDENCE-ROUND-SIXTEEN.json').read_text()); print('execution_commit =', d['execution_commit']); print('matrix_sha256 =', d['matrix_sha256']); print('adoption =', d['adoption']); print('gates =', d['gates'])"
gh pr checks codex/round-sixteen-verify
```

Expected from the first command: execution commit `f3d08a45d4f0b2fb9f1e62b97014187dd2853977`, matrix SHA-256 `d7e88dcc2a8f3d3e4158a505cf13a77584b821c4fb54ecb0833e6ba2ab9e18ba`, adoption `adopted`, and four empty gate lists. Expected from the second: every required PR check passes on the final Round Sixteen branch head. If CI is pending, wait; if a check fails, stop.

**Do not run `design/routing/mutants/replay.py` here.** It rewrites tracked source files and restores them; a replay belongs in a disposable clone.

Read the two qualifications you are being asked to accept, rather than taking this document's word for them:

```powershell
python -c "import pathlib,re; t=pathlib.Path('design/routing/DECISION-LOG.md').read_text(encoding='utf-8'); print(re.search(r'## D-080.*?(?=\n## D-)', t, re.S).group(0))"
python -c "import pathlib; t=pathlib.Path('design/routing/SLICE-001-route-shadow.md').read_text(encoding='utf-8'); s=t.split('## 9. Verification evidence required')[1].split('### K, L')[0]; print(s.strip())"
```

The first prints D-080, which withdraws the claim that every historical commit satisfied the EDD per-change checklist and anchors the forward record at `ea8733c`. The second prints section 9, where every evidence line carries either a tick with the run or command that earned it, or a `[~]` saying what is still missing. Read the `[~]` lines specifically: those are the boundaries this question is about.

> **Question 3.** Are those two qualifications the honest boundary — platform coverage named to the run that proves it rather than claimed for every commit, and the historical per-change claim withdrawn rather than ticked? **yes / no**

## 5. Read the decisions Round Sixteen verified or amended (5 minutes)

```powershell
python -c "import pathlib,re; t=pathlib.Path('design/routing/DECISION-LOG.md').read_text(encoding='utf-8'); [print(re.search(r'## '+d+r'.*?(?=\n## D-|\Z)', t, re.S).group(0)) for d in ('D-085','D-086','D-087','D-088','D-089','D-090','D-091','D-092','D-093','D-094')]"
```

- **D-085** stops repository code executing during acquisition. A content filter whose name contains `=` escaped the neutralization and ran; the neutralization is now verified against effective configuration instead of assumed.
- **D-086/D-089/D-091** make the self-grading guard cover installed layouts, calibration layouts, and every routing-owning pass reference rather than one representative.
- **D-087** makes a mutation row match exactly one place, after six rows were found testing one of two identical sites while reporting both covered.
- **D-088** neutralizes filter names through numbered environment configuration while retaining D-085's fail-closed verification.
- **D-090** requires every decision id cited in scripts, tests, or routing Markdown to resolve to a real decision heading.
- **D-092** excludes host-generated `.pytest_cache` from install provenance.
- **D-093** replaces path sampling with a canonical classifier contract for every self-grading authority class. The Round Sixteen attack found the sixth guard hole before this fix.
- **D-094** supersedes M92 with M96 because D-093 made M92's old replacement semantically inert; it does not disguise the measured Linux survivor.

> **Question 4.** D-085 refuses to compare the worktree at all when a filter cannot be neutralized, so such a repository always takes the full recipe. Is refusing the right trade against executing its code? **yes / no**
>
> **Question 5.** A gate that writes anywhere inside the repository is stale even if it restores the bytes. Is that correct for the gates you expect to approve? **yes / no**
>
> **Question 6.** D-093 requires every canonical self-grading authority classifier and D-086 covers `.agents`, `.claude`, `.codex` and `.gemini` installations. Does that match both the authority classes and layouts you intend to support? **yes / no**

## 6. Record the gate

- [ ] Every command above produced the expected output, or each difference is written down.
- [ ] Questions 1 through 6 answered, with a named follow-up for any `no`.
- [ ] No routing-policy rule changed during this walkthrough.
- [ ] Selective local and CI execution remain disabled.
- [ ] Daniel Boyd approves the SLICE-001 walkthrough.

Only you may check the last box. After that, a separate change may mark SLICE-001 `Done` and move the architecture boundary to SLICE-002.

If you answered `no` anywhere, the slice does not close today. That is a normal outcome and a cheaper one than approving a boundary you do not want.
