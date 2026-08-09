# Anti-Dark-Code Flow-Back Proposal

Promotion status: promoted in `2026.08.09-unified.5` to the adversarial-review and maintenance-harness references.

Source repo identity: `06595e2df2f962e79a20604a7f213b48d1325998`
Installed skill version: `2026.08.06-unified.3`

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-010: Adversarially review your own freshly shipped fixes (shipping-green is not correct-green)

- Scope: repo-agnostic
- Lesson: A find-then-independently-verify adversarial pass over a session's own fixes catches defects the passing tests structurally cannot see (detector logic errors, props silently dropped by a platform layer). Budget such a pass for detector, instrumentation, and platform-boundary work.
- Evidence: 2026-07-11, a 20-agent adversarial workflow over that session's own readiness/determinism/a11y fixes confirmed 12 real issues, all previously green; all 12 remediated and desktop-verified (findings ledger ADVERSARIAL-SELF-REVIEW-12)
- Limits: cost is high; likely justified for detectors, instrumentation, and platform-boundary code, not every slice. NOTE: drafted during the 2026-08-06 migration from findings-ledger evidence, not from LEARNINGS.md; confirmed ready by Daniel 2026-08-06.
- Proposed target: adversarial-review reference (self-review variant) or the remediation-loop closing step
- Proposed change: add a "review your own fixes" recipe with the verify-independently rule

## ADC-LOCAL-011: Thresholds are what make a lint honest

- Scope: repo-agnostic
- Lesson: A correlation or co-movement lint without calibrated thresholds is noise. The naive any-co-movement version of this repo's double-fold environment lint produced 49 ignorable warnings; the thresholded version (outsized combined effect only) produced zero false positives on clean content and still catches the real class. New lints should ship with thresholds tuned so current-clean content is silent.
- Evidence: `scripts/lint-environment.ts` (WQ6-DOUBLE-FOLD, 2026-07-10)
- Limits: thresholds can also hide real drift; record the threshold rationale next to the lint. NOTE: drafted during the 2026-08-06 migration from findings-ledger evidence, not from LEARNINGS.md; confirmed ready by Daniel 2026-08-06.
- Proposed target: maintenance-harness lint guidance
- Proposed change: one paragraph on threshold calibration for new lints
