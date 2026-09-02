# SLICE-001 owner walkthrough

Budget: 30 minutes, most of it waiting on one test run. Run from the repository root in PowerShell.

This script reviews evidence and asks you seven questions. It does not approve a routing rule, enable selective execution, or mark the slice `Done`. Nothing here writes to a tracked file; step 4 writes one receipt into the ignored run store.

**If any command's output does not match what is written here, stop and record the difference.** A mismatch is a finding, not a formality — this project has repeatedly found that a document said something the tree did not. You are the last check on that.

## 0. Get onto the reviewed tree (2 minutes)

```powershell
$reviewedHead = git rev-parse HEAD
git switch --detach $reviewedHead
git log -1 --format="%h %s"
git status --short
```

Start from a fresh clone of `claude/round-twenty-verify`. The variable freezes
the head that supplied this walkthrough, and `--detach` keeps every later
command on that exact commit. Do not fetch or switch to a newer commit during
the walkthrough.

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

> **Question 1.** Every rule stays `proposed` until a separate evidence campaign justifies approving one, rule by rule. Is that still the right boundary for SLICE-001? **yes**

## 2. Check the two execution-authority boundaries (3 minutes)

```powershell
python -m pytest -q anti-dark-code/tests/test_route.py::CandidateRouteTests::test_a_candidate_selection_cannot_remove_a_gate anti-dark-code/tests/test_route.py::CandidateRouteTests::test_a_candidate_route_is_refused_by_the_receipt_writer anti-dark-code/tests/test_route.py::CanonicalFullTests::test_force_full_runs_the_canonical_set_despite_include_globs
```

Expected: `3 passed`. The middle one is the receipt-writer refusal named in question 2; without it that question asks you to ratify a boundary nothing here demonstrates.

The first holds that shadow data measuring a proposed rule can never enter executable gate selection. The second holds that a forced-full route runs the canonical set even when every gate's `include_globs` would have excluded the changed file.

> **Question 2.** Candidate routes exist to measure what a proposed rule would have skipped, and are refused by both the receipt writer and gate selection. Is that the boundary you want? **yes, with U-017 named as the accepted residual**

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

**The pass count is host-dependent, so read the failure count, not the total.** Expected: `0 failed`. Another host may run tests this host skips. A different total is not a finding. A failure is.

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
rows 114 | active 108 | recorded on both hosts 108
awaiting host records: []
```

Every record on both hosts was refreshed by Round Twenty's two full serial
writes at `0ace58f`, one on Windows and one on WSL2 Ubuntu, so each
carries exact failed and skipped test identities from one commit (D-109).
M37, M46, and M48 are `caught elsewhere`: Windows skipped the exact test
that failed for each mutant on Linux. M08 and M92 are two of six superseded
rows: D-113 records why M114 replaces M08, whose catch on three hosts was
the host's git-lfs driver, and D-094 why M96 replaces M92's inert path-loop
attack.

```powershell
python -c "import json,pathlib; d=json.loads(pathlib.Path('design/routing/PARALLEL-EVIDENCE-ROUND-SIXTEEN.json').read_text()); print('execution_commit =', d['execution_commit']); print('matrix_sha256 =', d['matrix_sha256']); print('adoption =', d['adoption']); print('gates =', d['gates'])"
```

Expected: execution commit `f3d08a45d4f0b2fb9f1e62b97014187dd2853977`, matrix SHA-256 `d7e88dcc2a8f3d3e4158a505cf13a77584b821c4fb54ecb0833e6ba2ab9e18ba`, adoption `adopted`, and four empty gate lists. This is the historical Round Sixteen adoption artifact. Its matrix digest is not the current digest.

```powershell
python -c "import json,pathlib; d=json.loads(pathlib.Path('design/routing/PARALLEL-EVIDENCE-ROUND-SEVENTEEN.json').read_text()); print('execution_commit =', d['execution_commit']); print('summary =', d['parallel']['summary']); print('report_sha256 =', d['parallel']['report_sha256']); print('serial rows =', [(r['id'], r['verdict']) for r in d['serial_oracle']['rows']]); print('first run =', d['first_run_before_d098']['status_counts']); print('boundaries =', d['boundaries'])"
```

Expected: execution commit `4b24122a6051109461d4d82826af34a6a84fca68`, summary `99 mutants, 0 not caught: none`, report SHA-256 `70da49098da9aa02361552c4edb9f925afcfd7ddc18ba241cd985c09b58c0024`, serial rows `M97`, `M98`, and `M99` all `caught`, a first run recorded with 59 inconclusive rows, and boundaries with every flag `False` and the matrix written from serial observations only. That first run is the D-098 measurement, kept rather than discarded: the same command failed before the fix under the same churn.

```powershell
python -c "import hashlib,json,pathlib,subprocess; d=json.loads(pathlib.Path('design/routing/SERIAL-EVIDENCE-ROUND-EIGHTEEN.json').read_text()); x=d['t540p_full_write_replay']; h=hashlib.sha256(subprocess.run(['git','cat-file','blob','08d0576f1bd50a0d302bb6ac3d953733bed65899:design/routing/mutants/matrix.json'],capture_output=True,check=True).stdout).hexdigest(); print('round-eighteen matrix blob matches its artifact =', h==x['final_annotated_matrix_sha256']); print('execution commit =', d['linux_execution_commit']); print('rows/completed/superseded =', x['rows'], x['completed'], x['superseded']); print('not caught =', x['not_caught']); print('M97-M99 =', x['m97_m99']); print('boundaries =', d['boundaries'])"
gh pr checks claude/round-twenty-verify
```

Expected from the first command: `True`, execution commit
`c8466606b00677200756967adb0acf30bddd057f`, `106 101 5`, an empty
`not caught` list, M97 through M99 all `caught`, and every protected boundary
`False` except the statement that the matrix came from full serial Linux
results. The digest is taken from the committed blob at the Round Eighteen
head, not from the checkout: a default Windows clone checks the file out
with CRLF line endings and the working-tree bytes differ from the blob
(D-108). Expected from the second command: every required PR check passes on
this walkthrough's exact head. If CI is pending, wait. If a check fails,
stop.

```powershell
python -c "import hashlib,json,pathlib,subprocess; d=json.loads(pathlib.Path('design/routing/SERIAL-EVIDENCE-ROUND-NINETEEN.json').read_text()); s=d['serial_write']; h=hashlib.sha256(subprocess.run(['git','cat-file','blob','ce71481a04cf14438c421738e7b008a72ad03d77:design/routing/mutants/matrix.json'],capture_output=True,check=True).stdout).hexdigest(); print('implementation_commit =', d['implementation_commit']); print('serial summary =', s['summary']); print('report_sha256 =', s['report_sha256']); print('committed matrix blob matches the serial write =', h==s['matrix_sha256_after']); print('windows records without exact ids before =', d['record_currency_before']['windows_records_without_exact_ids']); print('first test M107 =', d['first_test_record']['m107']); print('boundaries =', d['boundaries'])"
```

Expected: implementation commit `39d745d5720ef629231a4c17563be818399141f5`, serial summary `109 mutants, 0 not caught: none`, report SHA-256 `18073613eb138403a78d29153f73ec27eb0543e85a547b76c2393862ee4f3adf`, `True` for the matrix blob at `ce71481`, the commit that carried that write (the current head's matrix is Round Twenty's merge, so a check against `HEAD` would be false, D-108), `91` Windows records without exact identities before the refresh, first-test M107 `SURVIVED`, and boundaries with every flag `False`, the matrix written by the serial write only, and the Linux records not refreshed this round. The `SURVIVED` is the D-110 measurement, kept rather than discarded.

```powershell
python -c "import hashlib,json,pathlib,subprocess; d=json.loads(pathlib.Path('design/routing/SERIAL-EVIDENCE-ROUND-TWENTY.json').read_text()); w=d['windows_serial_write']; l=d['linux_serial_write']; m=d['merge']; h=hashlib.sha256(subprocess.run(['git','cat-file','blob','e73a7d715d8a21c23b940780da122f236d61b465:design/routing/mutants/matrix.json'],capture_output=True,check=True).stdout).hexdigest(); print('implementation_commit =', d['implementation_commit']); print('windows =', w['summary'], '|', w['report_sha256']); print('linux =', l['summary'], '|', l['report_sha256']); print('both hosts =', m['active_rows_recorded_on_both_hosts'], 'of', m['active_rows'], '| exact ids =', m['every_record_carries_exact_ids']); print('committed matrix blob matches the merged write =', h == m['matrix_sha256_after']); print('D-116 condition 1 =', d['stopping_rule_condition_one']); print('boundaries =', d['boundaries'])"
```

Expected: implementation commit `0ace58f2cc95f29ed96a17c407de95690806e89d`, Windows
`114 mutants, 0 not caught: none` with report SHA-256
`a2467a4239bd84bf2aa76797a17c9c0103228846901654da8becc41a562d6c93`, Linux
`114 mutants, 0 not caught: none` with report SHA-256
`a5350416a9fbfef94093f29915a2bf0e6fff65dfc787c676584d4229aa6e7b4a`, `108 of 108` with exact ids
`True`, `True` for the matrix blob at `e73a7d7`, the commit that carried the
merge (D-108: the commit the artifact names, not `HEAD`), condition 1 of D-116 holding at
the implementation commit, and boundaries with every flag `False` except the
statement that the Linux records were refreshed this round. The two serial
writes ran in separate clean clones on two hosts and were merged per platform;
the Windows parallel replay at the same head is read-only evidence that
agrees with the Windows write row for row.

**Do not run `design/routing/mutants/replay.py` here.** It rewrites tracked source files and restores them; a replay belongs in a disposable clone.

Read the two qualifications you are being asked to accept, rather than taking this document's word for them:

```powershell
python -c "import pathlib,re; t=pathlib.Path('design/routing/DECISION-LOG.md').read_text(encoding='utf-8'); print(re.search(r'## D-080.*?(?=\n## D-)', t, re.S).group(0))"
python -c "import pathlib; t=pathlib.Path('design/routing/SLICE-001-route-shadow.md').read_text(encoding='utf-8'); s=t.split('## 9. Verification evidence required')[1].split('### K, L')[0]; print(s.strip())"
```

The first prints D-080, which withdraws the claim that every historical commit satisfied the EDD per-change checklist and anchors the forward record at `ea8733c`. The second prints section 9, where every evidence line carries either a tick with the run or command that earned it, or a `[~]` saying what is still missing. Read the platform-coverage line and the remaining `[~]` historical line specifically: those are the boundaries this question is about.

> **Question 3.** Are those two qualifications the honest boundary — platform coverage named to the run that proves it rather than claimed for every commit, and the historical per-change claim withdrawn rather than ticked? **yes**

## 5. Read the decisions Rounds Sixteen through Twenty verified or amended (8 minutes)

```powershell
python -c "import pathlib,re; t=pathlib.Path('design/routing/DECISION-LOG.md').read_text(encoding='utf-8'); [print(re.search(r'## '+d+r'.*?(?=\n## D-|\Z)', t, re.S).group(0)) for d in ('D-085','D-086','D-087','D-088','D-089','D-090','D-091','D-092','D-093','D-094','D-095','D-096','D-097','D-098','D-099','D-100','D-101','D-102','D-103','D-104','D-105','D-106','D-107','D-108','D-109','D-110','D-111','D-112','D-113','D-114','D-115','D-116','D-117')]"
```

- **D-085** stops repository code executing during acquisition. A content filter whose name contains `=` escaped the neutralization and ran; the neutralization is now verified against effective configuration instead of assumed.
- **D-086/D-089/D-091** make the self-grading guard cover installed layouts, calibration layouts, and every routing-owning pass reference rather than one representative.
- **D-087** makes a mutation row match exactly one place, after six rows were found testing one of two identical sites while reporting both covered.
- **D-088** neutralizes filter names through numbered environment configuration while retaining D-085's fail-closed verification.
- **D-090** requires every decision id cited in scripts, tests, or routing Markdown to resolve to a real decision heading.
- **D-092** excludes host-generated `.pytest_cache` from install provenance.
- **D-093** replaces path sampling with a canonical classifier contract for every self-grading authority class. The Round Sixteen attack found the sixth guard hole before this fix.
- **D-094** supersedes M92 with M96 because D-093 made M92's old replacement semantically inert; it does not disguise the measured Linux survivor.
- **D-095** makes a survivor on a host that skipped nothing a survivor everywhere. Before it, a stored catch from the other host turned a fresh local survivor into `caught elsewhere` and kept the replay, and the Linux CI job, at exit 0; the Round Sixteen Linux replay that measured M92 surviving exited 0 for exactly that reason.
- **D-096** makes a parallel replay refuse a coordinator tree that differs from HEAD, because its clones are built from HEAD while the serial path tests the disk. One uncommitted test edit had made M57 survive serially and be caught in parallel.
- **D-097** attempted to make the helper-naming convention executable. Round Eighteen broke its quoted-loader scan and replaced it with D-100.
- **D-098** roots each parallel worker's pytest at its own clone. Rooted at the common ancestor of the coordinator and the clone, which on this host was the machine-wide temp directory, 59 rows died in collection the moment another process removed a temp entry.
- **D-099** makes the coordinator report an inconclusive worker row's own reason instead of a sentence about field names, which is all the first run of D-098's failure had to show.
- **D-100** classifies every shipped Python script as verification authority by its directory, not its name or a loader scan.
- **D-101** removes caller pytest options and plugin paths, disables automatic plugins, and gives replay an explicit tracked outcome plugin.
- **D-102** renders control and format characters as visible escapes before a worker diagnostic reaches the terminal.
- **D-103** labels dirty read-only serial replay and requires a clean start plus a clean pre-publication check for `--write`.
- **D-104** requires an exact skipped-node and failed-node intersection before another host can carry a skipped survivor.
- **D-105** closes the two layers beneath D-101: the interpreter's user site, where a caller's `PYTHONUSERBASE` executed code inside a worker, and pytest's configuration search, where an ancestor `pytest.ini` reached a worker. Every suite run now disables the user site and pins an empty run-owned configuration file.
- **D-106** applies D-102's renderer to the serial console, which had printed a forged replay line from a broken suite's text.
- **D-107** is yours to decide: D-100's canonical entry forces the full route for every nested `scripts/*.py` in any installing repository, wider than its own statement. Three options are recorded.
- **D-108** makes this walkthrough's Round Eighteen check hash the committed blob; hashing the checkout failed on a default Windows clone.
- **D-109** records that 91 Windows records predated D-100 through D-104 and refreshes every Windows record from a full serial write at this round's implementation head.
- **D-110** landed in round twenty: a row no host caught is `SURVIVED` under skips, with the skipped tests named, and the `unverified` label is retired.
- **D-111** drops the interpreter flags that change what a test means. `PYTHONWARNINGS=error` had failed a passing probe and `PYTHONOPTIMIZE=2` had stripped an assertion inside a worker.
- **D-112** gives every git the suite runs an empty run-owned global configuration and no system configuration. A `core.hooksPath` from outside the clone had run a hook during a fixture-shaped commit.
- **D-113** records that M08's catch on three hosts was each host's global git-lfs driver, not a test, and supersedes it with M114, which holds the environment neutralization and is caught by fixture-local tests on any host.
- **D-114** declares the evidence JSON under `design/routing/` LF on every checkout, the second root cause of the D-108 failure.
- **D-115** amends D-106: every console field that comes from `matrix.json` passes through the renderer, after a row name forged a coloured summary line.
- **D-116** is yours to decide: the stopping rule for the harness line. It names three conditions at one commit under which no further agent round opens, and what reopens the line. This round's evidence says whether they hold at its head.
- **D-117** makes a contract assertion install the state the harness must replace before asserting. The suite runs inside the harness under replay, so the `PYTHONNOUSERSITE` assertion passed on the inherited value and M107 survived on WSL2 at `2f86f14` while Windows caught it, which is D-116's first reopen condition observed in the round that proposed it.

> **Question 4.** D-085 refuses to compare the worktree at all when a filter cannot be neutralized, so such a repository always takes the full recipe. Is refusing the right trade against executing its code? **yes**
>
> **Question 5.** A gate that writes anywhere inside the repository is stale even if it restores the bytes. Is that correct for the gates you expect to approve? **yes**
>
> **Question 6.** D-093 requires every canonical self-grading authority classifier and D-086 covers `.agents`, `.claude`, `.codex` and `.gemini` installations. Does that match both the authority classes and layouts you intend to support? **yes, with D-107 option 2 written down as the named follow-up, done as a separate change after the walkthrough rather than during it.**
>
> **Question 7.** D-116 closes the harness line when both hosts' serial writes report zero not caught with exact-identity records at one commit, a fresh-context challenger finds only channels the harness cannot own, and this walkthrough passes on a fresh default clone of that commit. Is that the endpoint you want, with `PATH`, the interpreter's system site-packages, and the operating system left as the environment you provide? **yes**

## 6. Record the gate

- [X] Every command above produced the expected output, or each difference is written down.
- [X] Questions 1 through 7 answered, with a named follow-up for any `no`.
- [X] No routing-policy rule changed during this walkthrough.
- [X] Selective local and CI execution remain disabled.
- [X] Daniel Boyd approves the SLICE-001 walkthrough.

Only you may check the last box. After that, a separate change may mark SLICE-001 `Done` and move the architecture boundary to SLICE-002.

If you answered `no` anywhere, the slice does not close today. That is a normal outcome and a cheaper one than approving a boundary you do not want.

### Record of the run

Run on 2026-09-02 by Daniel Boyd from a fresh default clone, `core.autocrlf=true`, detached at `3e04422`, on Windows 11 with Python 3.14. The differences written down under the first box:

- The suite reported `516 passed, 1 skipped, 67 subtests passed` and zero failures. The CI-shaped host behind section 4a of `HANDOFF-BACK-ROUND-TWENTY.md` reports `503 passed, 14 skipped`; this host runs tests that one skips.
- The first pass used the round-nineteen copy of this document for the PR check and the Round Nineteen artifact check, so the check named the round-nineteen branch and the artifact command hashed `HEAD` and printed `False`. This copy's commands name `claude/round-twenty-verify`, which showed nine successful checks at `3e04422`, and `ce71481`, whose blob prints `True`.

Answers: 1 yes; 2 yes, with U-017 as the accepted residual; 3 yes; 4 yes; 5 yes; 6 yes, with D-107 option 2 as the named follow-up in a separate change; 7 yes. Approving no rule, enabling no execution, and marking nothing `Done` were the conditions of this run, and they held.
