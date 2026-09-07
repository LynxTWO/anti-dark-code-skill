# Compatibility, UI policy, and external input

Trigger: a guarantee concerns one of the boundaries below. Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe grants no additional authority.

Apply only sections whose named boundary occurs in the claimed behavior. A simple DOM result does not imply plugins, streaming, external providers, GPU rendering, or file ingestion. Inside a section, platform-specific obligations apply only when that platform or mechanism is present. State omitted boundaries when they limit the claim.

## Selected implementation or external compatibility

- Resolve and health-check the exact selected implementation before scarce-resource ownership or expensive input reads. Freeze its stable identity in the job and queue snapshot.
- Inspect every serializer and migration before changing defaults. A previously omitted old-default value is indistinguishable from unset without an explicit migration.
- Treat public plugin and legacy-assembly signatures as binary contracts. In-repo rebuild success does not prove external compatibility.
- Treat in-process plugins as code-execution grants, not sandboxes. Registration rollback cannot undo arbitrary initialization side effects.

## Streaming protocol

- Exercise real protocol payload, sustained transfer, authentication failure, final flush, and server-side receipt. Connect success alone does not prove streaming.

## UI outcomes and asynchronous presentation

- Keep persistence and publication results separate from the main operation result in UI state. Never display a side effect that failed or was not attempted.
- Treat UI notifications, progress callbacks, and rendering observers as ancillary. Contain their exceptions after durable transitions so presentation cannot change producer correctness or cleanup.
- For code-drawn, GPU, or animated UI, lock the semantic state contract independently of rendering. Require deterministic offscreen state matrices, actual themed-window captures, and post-warmup allocation bounds for hot loops.
- Carry stable model identity through filtered or sorted views. Never persist a rendered ordinal when rows can move, skip, or fail.
- For asynchronous presentation, use bounded ownership-safe transfer. A slow UI may drop presentation samples, but it must not block, allocate on, or alter the producer's correctness path.

## Measured hot paths

- Keep hot paths allocation, blocking, I/O, dispatch, and ownership aware. Verify behavior first, then measure the touched path against a stated budget.

## Optional external providers

- Verify optional providers from authoritative documentation. Collect only the credential the protocol uses, protect it with a purpose-specific scope, and keep providers off until attribution, distribution, rate, and failure-isolation rules are satisfied.

## External input and background selection

- Read local user input once into bounded immutable bytes. Reject unsafe links, unsupported magic, oversized encoded or decoded input, and replacement between validation and use.
- Separate candidate ranking from automatic eligibility. Freeze the user's exact selected bytes and subject generation when a background job begins.
- Test malformed, truncated, oversized, replaced, multi-item, cancellation, outage, rate-limit, stale-generation, override, fallback, no-selection, and final-output cases.

Result: evidence for the selected boundary, its inputs and final outcomes, with unexercised branches explicit. Do not claim the other boundaries were verified.
