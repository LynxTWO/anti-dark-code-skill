# Proportionality and the need trace

Load at selection when the request asks for assurance, a campaign, a harness, an observer or a guarantee, and whenever a reframe trigger fires. The [core](../SKILL.md) controls evidence and authority; this reference bounds how much proof a need can justify. It waives no stop: an observed violation, exposure or cleanup failure still stops.

## Need trace

Before loading a task card, record three lines in the work record:

- Need: the product or operational outcome, in plain words, one sentence.
- Authority: the specification line, decision record, issue or owner instruction that names that need, with its locator.
- Worst case: what happens to users, data, money or secrets if the need goes unmet.

A request that names an activity ("get the campaign to pass", "prove the container cannot leak") is not a need. Trace it to the outcome it serves. If no authority names the need, the work is a proposal: the missing decision blocks execution planning, so state it and stop. An owner's willingness to spend is not evidence that the need exists.

## Consequence class

Every `guarantee` claim carries a consequence class taken from the worst case:

| Class | Worst case | Assurance ceiling |
|---|---|---|
| `none` | no user, data, money or secret is affected | record the fact; build no assurance |
| `local_only` | one developer's machine or a disposable resource | `observed_behavior` from existing checks |
| `user_data` | user-visible incident or real people's data | matching assurance contract, bounded scenarios |
| `money` | payment, entitlement or billing effect | matching assurance contract plus independent falsifier |
| `production_secrets` | credential, key or token with production reach | matching assurance contract plus independent falsifier |

Stock local development credentials inside disposable containers, networks or volumes are `none`. A class of `none` or `local_only` never justifies a new campaign, harness, observer or custody layer. Raise a class only with evidence that the same path carries the higher-class value; a hypothetical future use raises nothing. A finding's severity keeps the stored `low` to `critical` scale; the class bounds assurance for a guarantee and does not replace severity.

## Boring option

Before designing any mechanism, name the platform built-in or the simplest existing control that meets the need, and the specific gap that makes it insufficient. Record both. Design a custom mechanism only for that gap. A design that arrives without this comparison is incomplete, whoever wrote it and however many checks it passed.

## Reframe trigger

Produce a reframe packet and stop for the owner's decision when any predicate holds:

- The work's own pass/fail ledger shows zero passed after three attempts. A repository may record a different limit in its calibration invariants.
- The subject under test is a harness, observer, custody or evidence tool rather than product code, and no authority names that tool's own need.
- The verification inventory (checks, surfaces, predicates) grew since the last attempt while the product code under it did not change.

The packet contains the need trace, the consequence class with its evidence, the boring option and its gap, attempts and time so far, and one question the owner can answer. A retry is not a reframe. Changing the observer, the allowlist, the sampling window or a timeout is an attempt.

## Rationalizations

| Rationalization | Reality |
|---|---|
| "The owner wants it done" | Authority to spend is not authority that the need exists. Trace it. |
| "We have sunk days into this" | Cost so far goes in the packet as a reason to reframe, not to continue. |
| "One more run with a fixed observer" | That is an attempt. The ledger is still at zero. |
| "Leaking these matters if the path later carries real secrets" | A hypothetical raises no class. Show the higher-class value on that path. |
| "The next run needs a new question" | A new question about the harness is still work on the harness. Answer the need question first. |
| "Cut this campaign and replace it with a smaller one" | A smaller campaign needs its own need trace and class. |
| "The design is written and tested; just review it" | Review starts with the boring option. |
| "I will raise the cost question after the next session" | The packet comes before the session, not after it. |

## Red flags

Write the packet when you notice any of these: a session plan drafted before the need is recorded; a `guarantee` with no class; a harness as the subject; an attempt count in the request; a plan that describes the observer more than the users.
