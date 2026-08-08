# Anti-Dark-Code Flow-Back Proposal

Source repo identity: `b0d0864b6512e72d196ee373e37325fa77461318`
Installed skill version: `2026.08.06-unified.4`

This is a proposal only. It does not modify shared core policy.

## ADC-CUETOOLS-001: Bind deterministic gates to a reviewed process environment

- Scope: repo-agnostic
- Lesson: A command array is not a complete gate identity when child resolution depends on inherited PATH, module paths, locale, runtime variables, or shell startup behavior. Capture a bounded environment identity, support reviewed per-gate environment overlays, and make nested-shell ambiguity visible rather than blaming the repository command.
- Evidence: `.anti-dark-code/runs/20260808T124124989313Z-c602faf5a7/ADC-FAIL-33020a4014c4.json` and `.anti-dark-code/runs/20260808T124235430196Z-c602faf5a7/` reproduced three failures where Python inherited PowerShell 7's module path and launched Windows PowerShell 5.1, which resolved an incompatible utility module and lost `Get-FileHash`; the exact direct replay passed 137 checks, and the same gates passed under `pwsh` in `.anti-dark-code/runs/20260808T124404065977Z-1a062eec7f/`.
- Limits: The concrete failure is Windows-specific, but the rule applies only to gates whose executable or dependency lookup is environment-sensitive. Environment capture must remain allowlisted and secret-safe.
- Proposed target: `scripts/adc.py`, `tests/test_adc.py`, and `references/14-deterministic-verification.md`
- Proposed change: Add an optional reviewed `env` map and a redacted environment fingerprint to gate definitions and failure packets; test nested-shell module/PATH contamination, and document that the runner must either normalize or explicitly preserve the environment used by the authoritative lane.

## ADC-CUETOOLS-002: Preserve completed phases and semantic identity across later failures

- Scope: repo-agnostic
- Lesson: In multi-phase recovery or publication, later confirmation failure must not erase an already completed owned stage. Keep phase completion separate from composite assurance, retain the stage in an explicit held state, and verify names, metadata, sidecars, ordering, and collision behavior as part of artifact preservation.
- Evidence: Commits `869aada899578c139990d169ab5589458071681c`, `b7d3bb56f7f9487c52da54444dae9ec725fb19ff`, and `eb10d694eb3abbb21ef83660d6af9819c4d920e0` fixed deletion of a completed first phase, missing repair entry from the producer completion route, and loss of filenames/tags during repair; regression coverage is in `CUETools.Wpf.Tests/Services/RipServiceTests.cs` and related repair tests.
- Limits: A held stage is not final success and must not be auto-promoted. Retention requires explicit ownership, bounded user resolution, and safe handling of stale proof fields.
- Proposed target: `references/11-remediation-loop.md`
- Proposed change: Add a compact checklist for phase evidence, held-result ownership, producer-route repair reachability, and semantic artifact preservation beyond payload bytes.

## ADC-CUETOOLS-003: Separate damaged subject data from hardware and transport failure

- Scope: repo-agnostic
- Lesson: At device boundaries, classify bad subject data separately from transport, command, readiness, removal, and hardware failures. Probe the exact runtime command shape and range, treat safety-relevant positive calibration conservatively, serialize control transitions with payload I/O, and require branch-activation evidence beyond a green end-to-end result.
- Evidence: Commits `49ba99d91ba4380d6b1590f3421624ad728c9a6e`, `e2c3ba6b56684d7aeec0ee72882b59aab62d6c38`, `bc49c3aa21a5df5fe85d6b4751d3355b964d67f8`, `d1ae6ccef454bb6e084766af8feb617959e8328c`, and `b7d3bb56f7f9487c52da54444dae9ec725fb19ff` were driven by real-device failures after simpler software and opening probes passed; pure classifier and recovery tests live under `CUETools.Ripper.Tests/`.
- Limits: Retry classes, settle times, and conservative measurement direction are device- and quantity-specific. The rule does not justify retrying unknown failures or treating larger calibration values as universally safer.
- Proposed target: `references/11-remediation-loop.md` and `references/08-scenario-stress-test.md`
- Proposed change: Add a measurement-driven hardware checklist covering exact command shape, positive-vs-absent evidence, transition serialization, nested error identity, bounded decomposition, and real-device activation beyond the original failure point.

## ADC-CUETOOLS-004: Prove external runtime support separately from redistribution and ABI compatibility

- Scope: repo-agnostic
- Lesson: Product support for an external executable or native runtime is distinct from permission to redistribute it. Exercise the exact released binary and finalization path, bind packaged bytes and source/license evidence, prefer receipt-bound user overrides, and validate managed/native ABI identity plus real shipped-architecture behavior before advertising availability.
- Evidence: Commits `f21c12d583f7f355f33b4fa21f8003b35e63ad2a`, `054d9a9241ae25d9df3fbbc837d516c171ef4658`, and `99041d485d0fb3bb6bcb5d6169a4bd956b31950a` found ignored finalization results, native wrapper/runtime load failures, and misleading codec availability; exact runtime probes and artifact contracts now cover bundled architectures.
- Limits: License and patent conclusions still require authoritative legal/source evidence. A version-symbol probe is useful but cannot replace encode/finalize/decode or equivalent functional coverage.
- Proposed target: `references/11-remediation-loop.md` and `assets/verification-capabilities.json`
- Proposed change: Add an external-runtime checklist that separates invocation, redistribution, provenance, runtime selection, ABI compatibility, finalization, user override, and per-architecture artifact probes.

## ADC-CUETOOLS-005: Treat signing, normalization, and collection as final-byte build phases

- Scope: repo-agnostic
- Lesson: Signing and deterministic manifest normalization mutate release evidence. They must occur before final hashes, provenance, SBOM sidecars, archive creation, and publication; collection must remain bound to the exact build inputs and lease, and hosted success must be followed by downloaded-artifact and annotation inspection.
- Evidence: Commits `6417b86ba12fb6ec770774ec84ce09b6402be7f6`, `b6a3ea273a5765be03c4a7bb250018f1455f9f7d`, `eab2bd73f74fca3f927e7fb2d8b83de750f73289`, `86bddbdcd7dc920c386852f6a781a6a84fe166c2`, and `131073fe94f7a3a1933bbabb132db6c4979b4980` closed stale-build collection, shell/runtime drift, native-input provenance, and SBOM semantic-validation gaps; release run `30849431011` plus its downloaded evidence verified the final closure.
- Limits: Exact signing and notarization order depends on platform packaging. Hosted artifacts and logs do not replace protected signing identities or an independent trust decision.
- Proposed target: `references/11-remediation-loop.md`, `references/10-maintenance-harness.md`, and release-related verification capability guidance
- Proposed change: Add a final-byte checklist for signing order, generated manifest/sidecar refresh, source/input receipts, single release lease, workflow-shell execution, hosted annotations, and post-download closure verification.
