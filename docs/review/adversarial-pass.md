# Adversarial review: round eighteen

Date: 2026-09-02

## Area reviewed

This pass challenged R-032, classifier glob semantics across host operating
systems. R-021 and R-053 were excluded because rounds seventeen and eighteen
touched their evidence.

The review followed the live path from `collect_change_facts` through
`_matching_classifications`. It also checked R-032's entry in
`design/routing/requirement-evidence.json` and its mapped test,
`ClassificationTests::test_glob_matching_is_case_sensitive_on_every_platform`.

## What the earlier evidence got right

The classifier uses `fnmatch.fnmatchcase` on Git path strings. It does not use
the host-normalizing `fnmatch.fnmatch`, and it does not branch on the operating
system. An unmatched path becomes an `unknown` fact, so a case-only mismatch
does not inherit the matched rule's sensitivity.

The mapped test is discriminating on Windows. Replacing `fnmatchcase` with
`fnmatch` makes its `AUTH/login.py` probe match the lowercase pattern on that
host.

## Direct challenge

The same probe ran through the real classifier on Windows and T540P Linux. It
covered these path and pattern pairs:

- exact case: `auth/login.py` and `auth/*.py`;
- directory case: `AUTH/login.py` and `auth/*.py`;
- suffix case: `auth/Login.PY` and `auth/*.py`;
- bracket class case: `pkg/A.py` and `pkg/[a-z].py`; and
- Unicode case: `CAF\u00c9.py` and `caf\u00e9.py`.

Both hosts produced byte-identical canonical JSON with SHA-256
`2a7b70cc3c5c0d6fed7103418e55fe6653bde876217f7aad0c118eb3d49e1e2c`.
Only the exact-case probe matched. Each case-only variant produced one
`unknown` fact.

The first fixture attempt used a non-enum surface and failed validation on both
hosts. It produced no classifier result and is not evidence. The corrected
fixture asserted five completed records before comparing outputs.

## Coverage verdict

R-032 is upheld. The live code, the discriminating mapped test, and the
two-host probe agree. This pass did not change requirement confidence, slice
order, or the empty `untraced` list.

## Risks and protected areas

No risk moved up or down. This review did not touch an approval-gated area and
does not authorize a routing-policy rule. SLICE-001 remains open for owner
acceptance.

# Adversarial review: round nineteen

Date: 2026-09-02

## Area reviewed

This pass challenged R-011, that agent hints may raise but never lower
requirements. R-021, R-032, and R-053 were excluded because rounds seventeen
and eighteen touched their evidence.

The review followed `apply_hints` and its mapped tests in `HintTests`, and
checked that `assert_route_not_lower` derives its field list from the `Route`
dataclass rather than naming fields.

## Direct challenge

Twenty-eight hostile hint documents ran through the real `apply_hints` against
eight real routes: four paths (a README, the router module, a site page, and an
unmapped binary) under the shipped policy and under the same policy with every
rule approved in memory. The hints included lowered and out-of-range levels,
boolean and string level values, false and non-boolean flags, empty and
string-typed pass lists, unknown passes, empty obligations, obligations pairing
a capability with a gate no reviewed rule binds, unknown capabilities, and
attempts to write `matched_rule_ids`, `unknowns`, `unmapped_paths`, and
`considered_rule_ids`.

For every route: 19 hints were refused with `HintError`, 9 were accepted, and
no accepted hint lowered any `Route` field or changed `matched_rule_ids`. The
accepted hints were additive or no-ops: a pass already present, an obligation
already bound by the full recipe, `force_full` already true.

A non-object hint document (a list, an integer, or `None`) raises `TypeError`
rather than `HintError`. No command-line path constructs hints, so the call is
reachable only from code; it is recorded here as a robustness note, not a
routing defect.

## Coverage verdict

R-011 is upheld. The live code refuses every lowering hint by type and value,
the field comparison is derived from the dataclass, and the two-policy probe
found no accepted hint that narrowed a route. This pass did not change
requirement confidence, slice order, or the empty `untraced` list.

## Risks and protected areas

No risk moved up or down. This review did not touch an approval-gated area and
does not authorize a routing-policy rule. SLICE-001 remains open for owner
acceptance.
