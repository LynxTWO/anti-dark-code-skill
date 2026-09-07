# Hardware and nested recovery

Trigger: a claim depends on measured device capability, timing, cache behavior, boundary reads, or persisted calibration.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

Use this section when correctness depends on device capability, timing, cache behavior, boundary reads, media state, or persisted calibration.

- Treat newly required calibration as a state migration. Trigger it before the first operation that relies on it, version the record, and refuse assurance when the probe cannot complete.
- Distinguish positive evidence from failure to observe. Once a device demonstrates a safety-relevant behavior, a later noisy run that does not observe it does not prove disappearance.
- Retain a conservative high-water measurement only when oversizing costs performance and undersizing invalidates evidence. State why that direction is safe.
- Make proof-establishing side effects complete or explicit. A partial flush, shortened scrub, ignored status, or incomplete seek-away read is not an independent reread.
- Separate bad subject data from device, reader, transport, command, protocol, readiness, or removal failure. Convert only the subject-data class into explicitly untrusted evidence. Keep other failures fatal unless narrower recovery has independent evidence.
- Probe the exact command, transfer shape, flags, range, and offset the runtime consumes. A nearby or larger probe may reject a valid operation; a successful flag is useless if the runtime bypasses it.
- Treat completion of a control command as evidence for that command only. Serialize control transitions with payload I/O, apply only a measured bounded settle, and retry only the observed transition-bound failure.
- Decompose a rejected batch only when items can be read independently. Continue only from independently successful child results. Never consume bytes from a rejected parent.
- Snapshot the innermost failure before another operation can overwrite shared error state. Preserve the child identity, parent ancestry, address, range, and failure class.
- Require corroborating parent evidence and a bounded repeat before a child failure enters an untrusted-subject path. A different repeat keeps its own fatal class.
- Persist semantic evidence roles. Baseline, Test, Copy, confirmation, and tie-break results are not interchangeable values.
- Publish immutable phase evidence when the phase completes. Do not hide or erase it because a later phase failed.
- Keep a completed recoverable stage in an explicit held or pending state when later confirmation fails. Do not auto-promote it, but do not delete the only completed result.
- Bind displayed and persisted capability results to the exact physical device. Invalidate stale identity on selection changes, and freeze or lock selection while an operation owns the device.
- Exercise real hardware beyond the prior failure time, location, or transition. A quick open or metadata smoke test does not prove repeated flush, seek, reread, or edge behavior.
- Report unavailable hardware, access-denied resets, wedged handles, and incomplete probes as evidence gaps, not negative capabilities or passing tests.

Result: identity-bound phase evidence, bounded recovery ancestry, and real-device observations for the claimed operating range; unavailable probes remain gaps.
