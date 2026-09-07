# Capability-restricting builds

Trigger: a compiler or release setting removes reflection, dynamic code, or another runtime capability.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

A build flag chosen for release can remove a runtime capability from every build, including builds that never ship. The code still compiles, so the loss surfaces only when a dependent line executes.

Verified case: an ahead-of-time-compilation opt-in, set for the shipped target, also wrote a reflection-disabled feature switch into the debug runtime configuration, and reflection-based serialization then threw in ordinary debug runs. Three separate code paths failed on that one flag within two days of adoption, each surfaced by a live run rather than a build error, the last one inside a commit path. The test host did not carry the switch, so no gate could reproduce any of the three.

Treat a capability-restricting build flag as a repo-wide change, not a release setting. When one is adopted or changed:

- name the restricted capability and the exact switch that carries it, read from the generated runtime or build configuration rather than from the flag's documentation
- check whether the test and tooling hosts run under that same switch; a gate running in the permissive mode cannot fail on the restriction
- run a one-shot deterministic sweep for every use of that capability across source, test, and script trees, and confirm the sweep separates the restricted form from the safe form before trusting its count
- migrate every site the sweep found, then add a Level 0 gate that fails when an unmigrated site reappears
- either run the selected gates in the same capability mode as the shipped artifact, or adopt the restricted mode as the baseline for every build and every target that shares the code

The second option is not free. Restricted modes often disable the dynamic-code features that debuggers, hot reload, and mocking frameworks depend on. Prefer it when the shared code has more build targets than gates, and record what the restriction costs the inner loop.

Where the restriction arrives as a runtime switch rather than a compile-time condition, a restricted capability still compiles and fails only when its line executes, so without the sweep discovery is one runtime failure at a time.

Result: a validated deterministic sweep covers every restricted use, a regression gate rejects recurrence, and actual test/shipped hosts exercise the declared capability mode.
