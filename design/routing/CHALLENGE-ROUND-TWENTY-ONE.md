# Round twenty-one adversarial challenge of D-118

Challenger: a fresh-context agent with no memory of writing D-118, dispatched on 2026-09-02 against commit `69302743231fea27f830ccc22ad68b267eb5f29f` of `claude/round-twenty-one-verify`, working in its own `core.autocrlf=false` clone, a default clone, a clone of the parent commit `de5ef1d`, and one clone per mutant, all under `J:\TEMP\claude\r21-challenger\`. Windows 11, Python 3.14.2, pytest 9.0.2, git 2.50.1, `core.ignorecase=true`, `core.symlinks=false`. It wrote no fixes and touched no repository checkout. Its report is reproduced below with one framing note from the author: the harness refused the agent's report-file write, so the report arrived as the agent's final message and is saved here verbatim apart from that note. The two BROKEN verdicts are repaired by D-119 and by the source-half contract test with M117, in the commit that follows this one.

## Verdicts

| Item | Verdict | One line |
|---|---|---|
| 1. Spellings escaping both globs | **BROKEN** | A case variant of the directory name (`ANTI-DARK-CODE/scripts/adc_route.py`, `.agents/skills/ANTI-DARK-CODE/scripts/adc_route.py`) routes as cheap product code L2 in all 36 shapes; the parent commit forced it full. Git can carry that path, and pulling such a commit onto this NTFS clone overwrote the genuine `anti-dark-code/scripts/adc_route.py` on disk. Backslashes, `./`, `..`, nested, fifth prefix are authority or unmapped; `//` is cheap but unreachable from git; renamed-directory copies are cheap as D-118 discloses. |
| 2. Installer | UPHELD | `install --apply --hosts all` wrote 80 files, all under `.agents/skills/anti-dark-code/` plus `.claude/skills/anti-dark-code/SKILL.md`; every written `scripts/*.py` matches `**/anti-dark-code/scripts/*.py`. Target dir is a literal in `install_skill`; no CLI option names it; `HOST_SKILL_TREE_PREFIXES == INSTALLED_SKILL_PREFIXES`. |
| 3. Consumer paths | UPHELD (two named exceptions) | All D-118 paths route as stated. `scripts/x.py`, `scripts/sub/x.py`, `scripts/deploy.py` unmapped/full; `anti-dark-code/scripts/../other/x.py` authority/full. A consumer file named `adc.py` or `adc_receipt.py` under any `scripts/` is forced full by the template's two non-canonical name entries, which D-118's consequence sentence does not say. |
| 4. Contract | UPHELD | Every one-entry, exact-file, narrowed, widened, fnmatch-equivalent, re-surfaced, re-breadthed, re-sensitised, re-effected variant is refused at load naming the missing entry. Policies keeping both plus cheap duplicates load and still force full. The two documented compatibility branches load and route full. |
| 5. Rows | Rows UPHELD as caught; weaker mutant **BROKEN** | M100/M115/M116 caught (11/12/12 non-integrity failures), but every failure traces to the shipped policy no longer loading plus the literal-tuple test; the behavioural reason in each note is never exercised, and M115 and M116 fail the identical 14 tests. W1, W2 caught the same way. W3 held by exactly one test. **W4 (contract silently stops requiring the source entry) survives: 327 passed, 0 failed**, and under it the D-093 exact-representative policy loads and routes `work_receipt.py`/`adc_efficiency.py` cheap L2. |
| 6. Template vs installed | UPHELD | Same blob `72c05a3f68a8bca5f81ed0a867eb4b2132bc904e`; byte-identical in `nocrlf` (10246 bytes); in `default` the installed copy has 305 CRs (10551 bytes; `.agents/**` has no `eol` attribute, `anti-dark-code/**` has `eol=lf`) and is identical after CRLF→LF. `validate --skill anti-dark-code --mode universal` in `default`: `VALID (universal): 0 errors, 0 warning(s)`, exit 0. |

## Item 1: spellings of a shipped script

Each spelling routed for all five shipped scripts as `modify`/`unstaged`. `adc.py` and `adc_receipt.py` are authority under any spelling containing `/scripts/` via the template's non-canonical `**/scripts/adc.py` / `**/scripts/adc_receipt.py` (droppable; measured in item 4), so the D-118-relevant column is `adc_route.py` / `adc_efficiency.py` / `work_receipt.py`.

| Spelling (`adc_route.py` shown) | HEAD: adc_route / adc_efficiency / work_receipt | HEAD: adc / adc_receipt | Parent `de5ef1d` |
|---|---|---|---|
| `anti-dark-code/scripts/adc_route.py` and the four installed prefixes (controls) | AUTHORITY, full | AUTHORITY, full | AUTHORITY, full |
| `ANTI-DARK-CODE/scripts/adc_route.py` | **CHEAP L2**, `rules=['product-code']`, `force_full=False`, `passes=['10','11']` | AUTHORITY | AUTHORITY, full |
| `Anti-Dark-Code/scripts/adc_route.py` | **CHEAP L2** | AUTHORITY | AUTHORITY, full |
| `.agents/skills/ANTI-DARK-CODE/scripts/adc_route.py` | **CHEAP L2** | AUTHORITY | AUTHORITY, full |
| `.AGENTS/skills/anti-dark-code/scripts/adc_route.py` | AUTHORITY | AUTHORITY | AUTHORITY |
| `anti-dark-code/SCRIPTS/…`, `anti-dark-code/Scripts/…`, `…/ADC_ROUTE.PY` | UNMAPPED, full | UNMAPPED | UNMAPPED |
| `anti-dark-code/scripts/ADC_ROUTE.py` | AUTHORITY | AUTHORITY | AUTHORITY |
| `anti-dark-code\scripts\adc_route.py`, mixed slashes, `.agents\skills\…` | UNMAPPED, full | UNMAPPED | UNMAPPED |
| `./anti-dark-code/scripts/…`, `./.agents/skills/anti-dark-code/scripts/…` | AUTHORITY (via installed glob) | AUTHORITY | AUTHORITY |
| `anti-dark-code/../anti-dark-code/scripts/…`, `x/../anti-dark-code/…`, `../anti-dark-code/…` | AUTHORITY (via installed glob) | AUTHORITY | AUTHORITY |
| `anti-dark-code/scripts/../scripts/…`, `anti-dark-code/scripts/./…` | AUTHORITY (source glob; fnmatch `*` crosses `/`) | AUTHORITY | AUTHORITY |
| `anti-dark-code//scripts/adc_route.py` | **CHEAP L2** (git never emits `//`) | AUTHORITY | AUTHORITY |
| `anti-dark-code/scripts/sub/…`, `.agents/skills/anti-dark-code/scripts/nested/…` | AUTHORITY (globs match nested files; D-100 says "directly under") | AUTHORITY | AUTHORITY |
| `.cursor/skills/anti-dark-code/scripts/…`, `.windsurf/…`, `vendor/tools/anti-dark-code/scripts/…` | AUTHORITY | AUTHORITY | AUTHORITY |
| `.agents/skills/anti-dark-code-fork/scripts/…`, `.agents/skills/adc/…`, `.agents/skills/anti_dark_code/…`, `adc/scripts/…` | **CHEAP L2** (disclosed by D-118) | AUTHORITY | AUTHORITY |
| trailing space | UNMAPPED | UNMAPPED | UNMAPPED |

All 36 change-kind × source shapes of `ANTI-DARK-CODE/scripts/adc_route.py` route at L2 without `force_full` at HEAD; 0 of 36 at the parent.

**Real git, part 1.** Fresh NTFS repo, symlinks staged via `git update-index --add --cacheinfo 120000,<blob>,<path>` (what git records for a symlink on any host), routed through the real `read_change_inputs(repo, "HEAD")`:

- A. `tools/scripts/adc_route.py` symlink → the real router: staged add `000000->120000`, **CHEAP L2** (the disclosed consumer route; the target's own path stays authority).
- B. `.cursor/skills/anti-dark-code` directory symlink → `anti-dark-code`: unmapped, full.
- C. `anti-dark-code/scripts/adc_route.py` type-changed `100644->120000`: authority, full, `rules=['mode-change','product-code','verification-authority']`.
- D. Index-only adds of `ANTI-DARK-CODE/scripts/{adc.py,adc_route.py,work_receipt.py}`: full only because `adc.py` hits `**/scripts/adc.py`; the other two facts are `product/behavior` only. A fresh clone of that commit warned "the following paths have collided … only one from the same colliding group is in the working tree"; upper case sorts first, so the genuine content survived a *fresh clone*.

**Real git, part 2, the pull.** Origin with the genuine scripts; developer clone at base on the same NTFS volume; attacker commit `f5f9faf` (built with `update-index --cacheinfo`, i.e. what a commit from a case-sensitive host looks like) adds `ANTI-DARK-CODE/scripts/{adc_route.py,adc_efficiency.py,work_receipt.py}` containing `# replaced router`:

```text
--- attack commit routed against base ---
  input: committed add     000000->100644 'ANTI-DARK-CODE/scripts/adc_efficiency.py'
  input: committed add     000000->100644 'ANTI-DARK-CODE/scripts/adc_route.py'
  input: committed add     000000->100644 'ANTI-DARK-CODE/scripts/work_receipt.py'
  route: CHEAP L2   force_full=False level=2 rules=['product-code'] facts=['product/behavior']
--- dev pull ---
  rc: 0
  dev anti-dark-code/scripts/adc_route.py: '# replaced router'
  dev anti-dark-code/scripts/adc_efficiency.py: '# replaced router'
  dev anti-dark-code/scripts/work_receipt.py: '# replaced router'
  dev anti-dark-code/scripts/adc.py: '# genuine adc.py'
  dev status: [' M anti-dark-code/scripts/adc_efficiency.py', ' M anti-dark-code/scripts/adc_route.py', ' M anti-dark-code/scripts/work_receipt.py']
--- dev checkout base ---
  dev status: [' D anti-dark-code/scripts/adc_efficiency.py', ' D anti-dark-code/scripts/adc_route.py', ' D anti-dark-code/scripts/work_receipt.py']
```

The router graded the change that replaces the router on every case-insensitive checkout as L2 product code with no `force_full` and no independent review; at the parent commit the same change was verification authority. Two measured limits: a file written through `ANTI-DARK-CODE/scripts/new_tool.py` *on NTFS itself* is recorded by git as `anti-dark-code/scripts/new_tool.py` (authority before and after `git add`), so the variant path must come from a case-sensitive host or `update-index`; and after the pull the genuine paths show ` M` in `git status`, noticeable after the fact.

Fix: treat a changed path whose case-folded spelling matches a shipped-script glob, or which collides case-insensitively with a self-grading guard path, as that path (authority) or as a snapshot problem that forces full, so `ANTI-DARK-CODE/scripts/adc_route.py` cannot take the route `anti-dark-code/scripts/adc_route.py` is refused.

## Item 2: the installer

`install_skill` (`anti-dark-code/scripts/adc.py` 2088–2366): `target = repo / ".agents" / "skills" / "anti-dark-code"` and `adapter = repo / ".claude" / "skills" / "anti-dark-code" / "SKILL.md"` are literals; `command_install`/`command_bootstrap` pass only repo, source, apply, force, hosts and review flags; the `install`/`bootstrap` parsers (4685–4711) have no target or name option. Writes go to `target / r`, `target / calibration`, `target / .adc-managed.json`, and the adapter text. `HOST_SKILL_TREE_PREFIXES` (107–112) equals `INSTALLED_SKILL_PREFIXES` (adc_route.py 902–907), held by `test_the_guard_covers_every_installer_prefix`.

Measured (`adc.py install --repo <fresh repo with CLAUDE.md> --source-skill <clone>/anti-dark-code --apply --hosts all --allow-untagged-source --accept-unbound-calibration`): rc 0, 80 files written, top-level trees `['.agents/skills/anti-dark-code', '.claude/skills/anti-dark-code']`; the five scripts land at `.agents/skills/anti-dark-code/scripts/*.py`; written outside those two trees: `[]`. `.codex/` and `.gemini/` receive nothing (legacy calibration locations / guard probes only).

## Item 3: consumer paths

```text
scripts/x.py                             UNMAPPED->full
a/scripts/x.py                           CHEAP L2   globs=['**/scripts/*.py']
a/b/scripts/x.py                         CHEAP L2
scripts/sub/x.py                         UNMAPPED->full
a/scripts/sub/x.py                       CHEAP L2   (fnmatch * crosses /)
anti-dark-code-fork/scripts/x.py         CHEAP L2
xanti-dark-code/scripts/x.py             CHEAP L2
anti-dark-code/scripts/../other/x.py     AUTHORITY->full  globs=['**/scripts/*.py','anti-dark-code/scripts/*.py']
tools/scripts/build.py, packages/app/scripts/migrate.py, docs/scripts/render.py,
ci/scripts/release.py, src/scripts/__init__.py   CHEAP L2
scripts/deploy.py                        UNMAPPED->full
tools/scripts/adc.py                     AUTHORITY->full  (**/scripts/adc.py)
tools/scripts/adc_receipt.py             AUTHORITY->full  (**/scripts/adc_receipt.py)
tools/scripts/adc_route.py, tools/scripts/work_receipt.py   CHEAP L2
anti-dark-code/x.py, anti-dark-code/tools/x.py, anti-dark-code/scripts/x.{txt,pyw,py.bak}   UNMAPPED->full
```

Everything D-118 names routes as D-118 says. `../other` is authority because fnmatch `*` matches `/` (unreachable from git; fail-closed). Nuance: "an installing repository's own `scripts/*.py` files are product code" is false for files named `adc.py` or `adc_receipt.py`.

## Item 4: the contract

| Variant | Result |
|---|---|
| baseline | LOADED; shipped-script probes AUTHORITY full; `tools/scripts/build.py` CHEAP L2 |
| omit source only | REFUSED: `policy omits canonical self-grading classifier(s): shipped script controls, source (anti-dark-code/scripts/*.py)` |
| omit installed only | REFUSED: `… shipped script controls, installed (**/anti-dark-code/scripts/*.py)` |
| omit both | REFUSED, both named |
| source as exact `anti-dark-code/scripts/adc_route.py`; installed as exact `.agents/skills/anti-dark-code/scripts/adc_route.py` | REFUSED, the replaced entry named |
| installed narrowed to `.agents/skills/anti-dark-code/scripts/*.py` or `**/skills/anti-dark-code/scripts/*.py`; respelled `*/anti-dark-code/scripts/*.py` (fnmatch-equivalent) | REFUSED (spelling-exact contract, fail-closed) |
| source widened to `anti-dark-code/**/*.py` | REFUSED |
| both with surface tests/schema; breadth leaf/runtime; sensitivity release; effect behavior/public-contract; either alone with effect behavior | REFUSED, changed entries named |
| both kept + cheap docs/prose exact `adc_route.py`; + cheap duplicate of installed glob; + old `**/scripts/*.py` as authority | LOADED; every shipped-script probe still AUTHORITY full (union); the third makes consumer scripts full again, which is allowed |
| omit both, every rule `force_full`; omit both, classifier emptied | LOADED, everything full (documented branches) |
| omit both, rules as shipped (all proposed) | REFUSED (proposed rules count) |
| keep pair, drop product `**/scripts/*.py` | LOADED; consumer scripts become unmapped/full |
| keep pair, drop `**/scripts/adc.py` + `**/scripts/adc_receipt.py` | LOADED; shipped scripts still full via the pair |

Observation the tests should know: in the "omit installed only" message, `anti-dark-code/scripts/*.py` is present as a **substring** of `**/anti-dark-code/scripts/*.py`, so `assertIn("anti-dark-code/scripts/*.py", message)` cannot tell the source half of the contract from the installed half. That is what lets W4 survive.

## Item 5: the rows

Applied by bytes-replacing `old` with `new` once, LF preserved, the operation `replay.py` performs. Suites run as `python -m pytest anti-dark-code/tests/test_route.py -q -rfEs -p no:cacheprovider` from the clone root, **without** replay's `-k "not MutationMatrixIntegrity"` so integrity failures are visible and counted separately.

| Mutant | Suite | Non-integrity failures | Integrity failures (replay deselects) |
|---|---|---|---|
| M100 `anti-dark-code/scripts/adc*.py` | 13 failed, 314 passed, 1 skipped, 147.8s | 11 | `test_every_mutant_target_is_present_in_its_source`, `test_no_row_records_a_mutant_as_the_current_source` |
| M115 `**/scripts/*.py` | 14 failed, 313 passed | 12 | same two |
| M116 `.agents/skills/anti-dark-code/scripts/*.py` | 14 failed, 313 passed | 12 (identical set to M115) | same two |
| W1 `**/skills/anti-dark-code/scripts/*.py` | 13 failed, 314 passed | 12 (identical to M115) | `…target_is_present…` |
| W2 source `anti-dark-code/**/*.py` | 12 failed, 315 passed | 11 (identical to M100) | `…target_is_present…` |
| W3 contract skips `label != "shipped script controls, installed"` | 1 failed, 326 passed | `test_source_only_authority_cannot_hide_the_installed_router` only | none |
| W4 contract skips `label != "shipped script controls, source"` | **327 passed, 1 skipped, 0 failed, rc 0** | **none** | none |

Why: under each of M100/M115/M116/W1/W2 the shipped installed policy is refused at load (`policy omits canonical self-grading classifier(s): … (<mutant glob>)`) because the policy file still carries the unmutated entry, so every test calling `_approved_policy()` errors before routing, and the tuple-literal test fails on the string. The notes' behavioural reasons are real but unexercised:

- M100: with a policy carrying the mutant's entries, `anti-dark-code/scripts/work_receipt.py` → CHEAP L2 (`adc_efficiency.py` stays authority under `adc*.py`); `test_every_shipped_script_is_authority_by_location` fails on `assertIn("anti-dark-code/scripts/*.py", globs)` before routing anything.
- M115: with a matching policy, `tools/scripts/build.py` and `packages/app/scripts/migrate.py` → AUTHORITY full. Unexercised.
- M116: with a matching policy, `load_policy` is refused by `_check_self_grading` (D-086): `router code and Git interpretation, installed under .claude/skills/ … takes a route below the full recipe`; the prefix guard holds the note's reason independently of the contract, but the suite reaches M116 only via the load failure. M115 and M116 fail the identical fourteen tests; the suite does not distinguish them.

**W4 in detail.** Mutation inside `_check_authority_classifier_contract`:

```python
        if (glob, surface, effect, breadth, sensitivity) not in actual
        and label != "shipped script controls, source"
    ]
```

The shipped policy loads and routes everything full, so no test moves. What it permits: the D-093 attack shape, replace `anti-dark-code/scripts/*.py` with the exact `anti-dark-code/scripts/adc_route.py` authority entry, keep the installed entry, **loads** (`_check_self_grading` is satisfied: its three probed source scripts are covered exactly or by `**/scripts/adc.py`/`adc_receipt.py`) and routes:

```text
anti-dark-code/scripts/adc_route.py        AUTHORITY->full
anti-dark-code/scripts/adc.py              AUTHORITY->full
anti-dark-code/scripts/adc_receipt.py      AUTHORITY->full
anti-dark-code/scripts/work_receipt.py     CHEAP L2  force_full=False rules=['product-code']
anti-dark-code/scripts/adc_efficiency.py   CHEAP L2  force_full=False rules=['product-code']
.agents/skills/anti-dark-code/scripts/work_receipt.py   AUTHORITY->full
```

At HEAD and under W3 the same policy is refused (`… shipped script controls, source (anti-dark-code/scripts/*.py)`). Merely omitting the source entry is still refused under W4, but by the D-071 guard (`adc_route.py` becomes product-only), not by the contract, so a test that only deletes the entry would not hold W4 either. Claim (c) therefore has a holding test for its installed half (W3 caught by one test) and none for its source half; claim (d) holds in that the rows are caught, but by one mechanism, not by their distinct behaviours.

Fix: add the source-half twin of `test_source_only_authority_cannot_hide_the_installed_router`, replace `anti-dark-code/scripts/*.py` with the exact `anti-dark-code/scripts/adc_route.py` authority entry, keep the installed entry, assert a `PolicyError` whose message contains `shipped script controls, source (anti-dark-code/scripts/*.py)` (the label, not the bare glob, which is a substring of the installed one), and record W4 as a matrix row.

## Item 6: template and installed policy

`git ls-tree HEAD` in `nocrlf`: both files are blob `72c05a3f68a8bca5f81ed0a867eb4b2132bc904e`. Checkout SHA-256: `nocrlf` template and installed both `8A72B7C4…27FB8`, byte-identical (10246 bytes). `default`: template `8A72B7C4…` (0 CRs; `check-attr` → `text: auto`, `eol: lf`), installed `984330C1…` (10551 bytes, 305 CRs; no attributes on `.agents/**`); identical after CRLF→LF (`True`). `gates.json` blobs differ between template and installed (`54811c9f` vs `a0fb98ff`), expected, out of scope. `python anti-dark-code/scripts/adc.py validate --skill anti-dark-code --mode universal` in `default` → `VALID (universal): 0 errors, 0 warning(s)`, exit 0.

## Not measured

- A filesystem symlink on this host (admin required). The index-level symlink is what git records and what the router reads, so the routing verdicts do not depend on it; the on-disk effect of a link was not observed.
- Linux. Every number is Windows 11 at the target commit; W4's survival has no host-dependent branch (the one skip is the filesystem-symlink acquisition test), but a Linux replay is the round's authority, not this report.

# Second challenge: D-119 and the repaired contract at `5872e92`

Challenger: a second fresh-context agent, dispatched on 2026-09-02 against commit `5872e922fc6ff5bf4f7f3e879ffc50fb194871c1`, the head carrying D-119 and the source-half contract test, in its own clones under `J:\TEMP\claude\r21-challenger-2\`: `head`, `parent` (`6930274`), `mut` (mutant replay), and `cli` (item 5, carrying a scratch commit that approves every rule). Windows 11, git 2.50.1, Python 3.14.2; 8.3 short-name generation is off on J: and on for C:, so the 8.3 measurements used two short-lived directories under the user's temp folder on C:. Nothing under `C:\DEV` was touched; no fixes were written. The report is reproduced below with the author's framing note: the two BROKEN verdicts and the two surviving mutants are repaired by D-120 in the commit that follows.

## Verdicts

| Item | Verdict | One line |
|---|---|---|
| 1. Spellings | **BROKEN** (two spellings) | `ANTI-D~1/scripts/adc_route.py` routes cheap L2 with no code at HEAD and parent, and on C: `git reset --hard` / `git checkout -f` of that commit wrote the replaced content over `anti-dark-code/scripts/adc_route.py`. `tools/scripts/ADC.py` routes cheap L2 and a plain `git pull` overwrites `tools/scripts/adc.py`, which the shipped template classifies as verification authority (`**/scripts/adc.py`, non-canonical). Trailing-dot `anti-dark-code./scripts/adc_route.py` is cheap L2 and NTFS resolves it to the genuine directory, but git 2.50.1 for Windows refuses it in all five operations. Every Unicode case variant either records the collision (Kelvin sign, long s, ligatures) or is a distinct name on NTFS (dotless ı, dotted İ, fullwidth, Cyrillic, ZWNJ/ZWJ, combining marks); macOS not measured. |
| 2. Policy | UPHELD | Exact cheap entries, an extra product surface, an approved L0 `paths` rule, dropping `**/scripts/*.py`, and the all-proposed template all keep L3 `force_full` with the code; hints cannot write `unknowns` (HintError) and `force_full: False` is ignored. |
| 3. Candidate | UPHELD at HEAD | `build_candidate_route` is `force_full` for every collision; on the real receipt `_candidate_shadow_context` + `shadow_result` omit no gate. But no test holds it, see item 6. |
| 4. False positives | recorded | Under the shipped template with rules approved, six paths move from below full to full: `docs/skill.md`, `docs/Skill.md`, `guides/References/intro.md`, `guides/REFERENCES/intro.md`, `app/assets/Verification-Capabilities.json`, `vendor/Anti-Dark-Code/scripts/tool.py`. 30 more gain the code while already full via UNMAPPED. With a consumer `**/*` product entry, 25 paths move. |
| 5. Receipt | UPHELD | Read-only `route` on a staged `ANTI-DARK-CODE/scripts/adc_route.py`: `force_full=true rules=product-code`; `--write` receipt has `route.unknowns = ['ADC-ROUTE-AUTHORITY-CASE-COLLISION', 'ADC-ROUTE-UNMAPPED-PATH']`; `--verify` says FRESH. |
| 6. Rows | Rows UPHELD; own mutants **BROKEN** | M117 caught (2 behavioural + 2 integrity), M118 caught (1 + 2). WA (fold last segment only) and WB (scripts globs only) each caught by exactly one test. **WC (candidate-side check disabled) survives: 329 passed**, and under it the shadow record reads the collision commit as a cheap L2 candidate that omitted three gates. WD (`lower()` for `casefold()`) survives; marginal. |

## Item 1: spellings, the measured lab

Attacker commits were built with `git mktree` and `commit-tree`, the shape a commit from a case-sensitive host takes, and routed through the real `parse_raw_z` of `git diff --raw -z -M -C --find-copies-harder`, then applied to a fresh default clone by five operations. The 8.3 branch on C:

```text
[pull --ff-only] rc=1 ... error: The following untracked working tree files would be overwritten by merge: | ANTI-D~1/scripts/adc_route.py
[fresh clone -b attack-8] rc=0 GENUINE_CHANGED=none extra_files=["'ANTI-D~1/scripts/adc_route.py'"]
[fetch + reset --hard FETCH_HEAD] rc=0 HEAD==attack=True GENUINE_CHANGED=["anti-dark-code/scripts/adc_route.py='# replaced\\n'"] status=["' M anti-dark-code/scripts/adc_route.py'"]
[fetch + checkout -f FETCH_HEAD]  rc=0 HEAD==attack=True GENUINE_CHANGED=["anti-dark-code/scripts/adc_route.py='# replaced\\n'"] status=["' M anti-dark-code/scripts/adc_route.py'"]
[fetch + checkout FETCH_HEAD] rc=1 ... untracked working tree files would be overwritten by checkout
route HEAD  : CHEAP L2 ff=False rules=['product-code'] unknowns=[] cand_ff=False
route PARENT: CHEAP L2 ff=False rules=['product-code'] unknowns=[] cand_ff=False
```

`git reset --hard` and `git checkout -f` are what git's own refusal message leads a developer to. The `~1` suffix must match the alias NTFS assigned, but nothing stops a commit from carrying `ANTI-D~1` through `ANTI-D~4`. The template's non-canonical entries are worse: `tools/scripts/ADC.py` needs no special operation, a plain pull overwrites the file. Both cases violate D-119's stated reason; the 8.3 case is outside its literal "case-folded" claim, the second outside its "canonical" scope.

Other spellings, all measured through the real classifier and both builders with every rule approved: `ANTI-DARK-CODE/…`, `.agents/skills/ANTI-DARK-CODE/…`, `./ANTI-DARK-CODE/…`, the Kelvin sign `anti-darK-code`, the long s `ſcripts`, and the ligatures record the collision at HEAD and were cheap at the parent; dotless ı, dotted İ, fullwidth, Cyrillic, ZWNJ, ZWJ, and combining marks route cheap without the code but are distinct names on NTFS; trailing space, backslashes, and mixed separators are unmapped or refused by git; `anti-dark-code/SCRIPTS/…`, `.GITATTRIBUTES`, `.GitHub/workflows/tests.yml`, `anti-dark-code/TESTS/…` are unmapped, full, and carry the code, and pulls of `.GITATTRIBUTES` and `src/Tests/test_y.py` overwrote the genuine files while already routed full.

Fix stated by the challenger: force full with a named code for any component shaped like an NTFS short name, `^[^./]{1,6}~[0-9]+(\.[^./]{1,3})?$`, and run the collision check against the loaded policy's verification-authority globs and force-full rules' paths as well as the canonical set.

## Item 2: turning the check off from a policy

Exact cheap entries for the variant, an extra `ANTI-DARK-CODE/**` product surface, an approved Level 0 rule with `paths=[ANTI-DARK-CODE/**]`, dropping `**/scripts/*.py`, and the shipped all-proposed template all keep `L3 ff=True` with the code. Hints `{'minimum_level': 0}`, `{'force_full': False}`, and `{'passes': []}` leave the route at L3 with the code; `{'unknowns': []}` and `{'unmapped_paths': []}` raise `HintError`. `dataclasses.replace(route, unknowns=frozenset(), force_full=False)` forges a route, which any caller with code access could do and no policy path reaches.

## Item 5: the receipt

In the `cli` clone, after a scratch commit approving every rule and `git update-index --add --cacheinfo 100644,<blob '# replaced router'>,ANTI-DARK-CODE/scripts/adc_route.py`:

```text
$ adc.py route --repo <cli> --base HEAD    ROUTE level=3 passes=07,10,11,14 gates=distribution,full-suite,hostile-environment,mutation-replay,validate-core rules=product-code force_full=true complete=true
$ adc.py route --repo <cli> --base HEAD --write
receipt: route.minimum_level=3 force_full=True matched_rule_ids=['product-code']
         route.unknowns=['ADC-ROUTE-AUTHORITY-CASE-COLLISION', 'ADC-ROUTE-UNMAPPED-PATH']
$ adc.py route --repo <cli> --verify <receipt>    FRESH 73299f1e0918
```

The read-only run isolates the collision as the sole reason for full. The `ADC-ROUTE-UNMAPPED-PATH` in the written receipt is the run store's own `.gitignore`, pre-existing behaviour.

## Item 6: the rows and four own mutants

| Mutant | Suite | Failing tests |
|---|---|---|
| baseline | 329 passed, 1 skipped | – |
| M117 | 4 failed | `test_a_policy_grading_the_router_as_product_code_is_refused`, `test_installed_only_authority_cannot_hide_the_source_router`, two integrity tests |
| M118 | 3 failed | `test_a_case_variant_of_an_authority_path_forces_full`, two integrity tests |
| WA: fold the last segment only | 1 failed | `test_a_case_variant_of_an_authority_path_forces_full` |
| WB: scripts globs only | 1 failed | same |
| **WC: candidate-side check disabled** | **329 passed, 0 failed** | none |
| WD: `lower()` for `casefold()` | 329 passed, 0 failed | none |

Under WC, with the real `adc.shadow_result`, the shadow record for `ANTI-DARK-CODE/scripts/adc_route.py` read `route_class={'matched_rule_ids': ['product-code'], 'force_full': False} omitted=['distribution', 'hostile-environment', 'mutation-replay'] routing_miss=False`, which is the measurement the candidate side exists to refuse. WD survives because every test variant is ASCII; `'ſ'.lower()` is `'ſ'` while `casefold()` gives `'s'`.

## Not measured

- macOS: APFS case folding of U+0131 and HFS+'s ignorable code points, the only remaining Unicode spellings that route cheap without the code; on NTFS all of them are distinct names.
- Linux ext4 casefold directories, which would fold the long s and ligatures the check already catches.
- Git for Windows before 2.24.1, which lacked the `invalid path` refusal that stopped the trailing-dot spelling here.
- The 8.3 alias of the installed prefix, `AGENTS~1/skills/ANTI-D~1/…`, the same mechanism as the measured source spelling.

# Third challenge: D-120 at `38cdff8`

Challenger: a third fresh-context agent, dispatched on 2026-09-02 against commit `38cdff8e0d7b67843a4e08c0870651debf2db02f`, the head carrying D-120, in its own clones under `J:\TEMP\claude\r21-challenger-3\`: `repo`, `mut`, `parent` (`5872e92`), and `cli`. Windows 11, git 2.50.1, Python 3.14.2; 8.3 short names on for C:, off for J:, so filesystem probes ran in the user's temp directory on C:. It disclosed one incident of its own: a probe script's default argument ran a removal against its own first clone, which it discarded and re-cloned; every number comes from pristine clones. Nothing under `C:\DEV` was touched; no fixes were written. The author's framing note: item 2's rule-half finding, the three surviving own mutants, and the cost are repaired by D-121 in the commit that follows; item 1's NTFS verdict is the first uphold of the spelling rule by real git.

## Verdicts

| Item | Verdict | One line |
|---|---|---|
| 1. Spellings | **UPHELD on NTFS; APFS/HFS+ NOT MEASURED** | Every spelling NTFS on C: resolved to a genuine authority path was forced full with a code, or is refused by git 2.50.1 at checkout, reset, pull and clone (`//`, `::$DATA`, tab, trailing dot, `.` component, backslash). Every spelling that still routes cheap without a code (`ANTI-DA~1`, `ANTI-D~`, leading space, NBSP, U+3000, dotless ı, İ, Cyrillic, Greek, U+034F) is a distinct name on NTFS: real git checked them out as new directories beside the genuine one. A sweep of every BMP code point found none that NTFS equates to an ASCII letter. HFS+'s ignorable set is entirely category Cf, so the key strips it; APFS was not measured. |
| 2. Fold-set abuse | **UPHELD**, with one finding outside D-120's stated set | `**/*`, `**`, `*` as verification-authority and force-full `paths: ["**"]` never fire the collision check; they force full through the entry or rule itself. Two observations: a *proposed* force-full rule's paths enter the fold set and change routes; and an approved path rule that raises the level or requires review without `force_full` is outside the fold set, so `Secrets/notes.md` routes L0 without review while `secrets/notes.md` is L3 with review. |
| 3. False positives | recorded | `notes~1.txt`, `a~1`, `v1~2.md`, `Makefile.`, `src/foo~1.c`, `build~10.log`, `backup~1/notes.md` carry `ADC-ROUTE-AMBIGUOUS-SPELLING`; only three paths in the corpus move from below full to full (`backup~1/notes.md`, `tools/scripts/Adc.py`, `tools/scripts/ADC_RECEIPT.py`). |
| 4. Candidate side | **UPHELD** | Written receipt for staged `ANTI-DARK-CODE/scripts/adc_route.py`: `force_full=true`, `unknowns=["ADC-ROUTE-AUTHORITY-CASE-COLLISION"]`; verify FRESH; the shadow context gives a candidate with the full recipe's passes and gates, `omitted={}`. Under M119 committed in the clone the candidate is L2 with three gates omitted. No other path in `adc.py` computes a route. Observation: in this repository's default state every `route --write` also emits the run store's own untracked `.anti-dark-code/.gitignore` as an unmapped fact, so every written receipt is full for that reason alone. |
| 5. Rows and own mutants | Rows UPHELD; own mutants **BROKEN** (three survive) | M118 to M122 each fail the collision test plus the two integrity tests. W1 (no format strip), W2a (lower-case-only regex), W5 (space not ambiguous) caught. **W2b (upper-case-only short-name regex) survives**, and `anti-d~1/scripts/adc_route.py` then routes cheap L2 while real git `checkout -f`, `reset --hard` and a fresh clone wrote it over the genuine router on C:. **W3 (force-full rule paths dropped from the fold set) survives.** **W8 (path key compared to the raw glob) survives**, and `docs/skill.md` routes L0 docs-only while `docs/SKILL.md` is force-full. W4 (`NFKC` + `lower()`) fails only an integrity test. |
| 6. Performance | reported, not a finding | 5,000 facts: `build_route` 0.426 s at HEAD vs 0.138 s at the parent, **3.08×**; `build_candidate_route` 3.09×. The glob keys are recomputed per fact: 165,000 `_spelling_key` calls per route. |

## Item 1: the real-git battery

Attack trees were built byte-exact with `git hash-object -t tree -w --literally --stdin` so any spelling can be carried, then applied in fresh clones on C: by `fetch` + `checkout -f`, `fetch` + `reset --hard`, `pull --ff-only`, and `clone -b`:

```text
[empty component] anti-dark-code//scripts/adc_route.py      route CHEAP L2 no code; fsck: empty filename in tree entry; every operation rc=128; genuine intact
[main data stream] …adc_route.py::$DATA                      route UNMAPPED full; checkout -f / reset --hard / clone: error: invalid path; pull refused; genuine intact
[tab] anti-dark-code\t/scripts/adc_route.py                  route CHEAP L2 no code; every operation: error: invalid path
[dotless i] antı-dark-code/scripts/adc_route.py             route CHEAP L2 no code; all four rc=0, a new directory beside the genuine one, router intact
[leading space], [no-break space]                            route CHEAP L2 no code; all rc=0, new directory, router intact
[short name] ANTI-D~1/… and [lower-case] anti-d~1/…          route CHEAP L3 AMBIG; checkout -f and reset --hard rc=0 router='# replaced', status=[' M anti-dark-code/scripts/adc_route.py']; pull refused; fresh clone of anti-d~1 warned "paths have collided" and left router='# replaced'
[trailing dot], [dot component], [backslashes]               error: invalid path in every operation
[case variant] ANTI-DARK-CODE/…                              route CHEAP L3 CASE; checkout -f, reset --hard, pull rc=0 router='# replaced'
```

NTFS short names assigned on C:: `anti-dark-code`→`ANTI-D~1`, `.agents`→`AGENTS~1`, `adc_route.py`→`ADC_RO~1.PY`, `.gitattributes`→`GITATT~1`, `verification-capabilities.json`→`VERIFI~1.JSO`, `test_route.py`→`TEST_R~1.PY`, `calibration`→`CALIBR~1`. Every spelling git wrote over the genuine file was forced full with a code; every spelling that routed cheap without a code was refused by git or written as a distinct name. An upcase sweep of U+0080 to U+FFFF against ASCII file names on C: found zero code points NTFS equates to an ASCII letter. HFS+'s lower-case table ignores exactly U+200C–U+200F, U+202A–U+202E, U+206A–U+206F and U+FEFF, all category Cf, which the key strips; ext4 casefold directories also strip default-ignorable code points outside Cf, which route cheap without the code, a recorded limit.

## Item 2: the rule half

With an approved rule `paths: ["secrets/**"]`, `minimum_level: 3`, `passes: ["07","14"]`, `independent_review: true` and no `force_full`:

```text
fold set contains 'secrets/**': False
secrets/notes.md          CHEAP L3 ff=False rules=['docs-only','sensitive'] review=True  passes=['06','07','14']
Secrets/notes.md          CHEAP L0 ff=False rules=['docs-only']             review=False passes=['06']
secrets/scripts/rotate.py CHEAP L3 rules=['product-code','sensitive'] review=True passes=['07','10','11','14']
Secrets/scripts/rotate.py CHEAP L2 rules=['product-code']             review=False passes=['10','11']
```

With `force_full: true` on the same rule both variants force full with the code. A proposed force-full rule `paths: ["Docs/**"]` put `docs/guide.md` at L3 with the code while `Docs/guide.md` itself stayed L0, because `_authority_globs` did not check `rule.approved`. Fix stated by the challenger: fold the `paths` of every approved rule whose requirements exceed the empty route, and skip proposed rules.

## Item 5: own mutants

| Mutant | Suite | Failing tests |
|---|---|---|
| M118, M119, M120, M121, M122 | 3 failed each | the collision test and the two integrity tests |
| W1 `stripped = text` | 1 failed | the collision test (ZWNJ spelling) |
| W2a lower-case-only regex | 1 failed | the collision test (`ANTI-D~1`) |
| **W2b upper-case-only regex** | **329 passed** | none; `anti-d~1/scripts/adc_route.py` routes CHEAP L2 |
| **W3 `for rule in ():`** | **329 passed** | none; `Secrets/notes.md` under a force-full `secrets/**` rule routes L0 |
| W4 `.lower()` after NFKC | 1 failed | only the integrity test on M122's target text |
| W5 `endswith(".")` only | 2 failed | the collision test (`anti-dark-code␣/…`) plus an integrity test |
| **W8 `fnmatchcase(key, glob)`** | **329 passed** | none; `docs/skill.md` routes L0 while `docs/SKILL.md` is force-full |

## Item 6: performance

5,000 facts in five shapes, seven timings, minimum and median: HEAD `build_route` 0.426 s, parent 0.138 s, 3.08×; `build_candidate_route` 3.09×. Profile of one route: 165,000 `_spelling_key` calls, 1.128 s of 1.476 s, 2.7 million `unicodedata.category` calls.

## Not measured

- APFS and HFS+ on a real Mac; ext4 casefold directories on Linux; git for Windows before 2.24.1.
- An NTFS volume where the assigned short name of `anti-dark-code` is not `ANTI-D~1`; the hash form and `~2` to `~4` were routed, all ambiguous, but not resolved.
- `adc.py gates --route <receipt>` end to end; the shadow record was computed through the same functions `command_gates` calls, on the real written receipt.
