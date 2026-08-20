# Reference: Adversarial Edge-Case Review

Use this reference after the first architecture pass and first slice plan when you want to challenge the current repo understanding instead of extending it.

**Mode:** read-only review of code plus docs.

For confidence levels, the unknowns entry shape, the canonical approval-gated list, and the canonical sensitive-data class list, see `00-conventions.md`.

## Goal

Try to break the current picture of the repo. Look for blind spots, hidden runtime paths, weak trust-boundary notes, protected-area mistakes, and false claims of coverage.

The point is not to make output look nicer. The point is to make overclaiming harder.

## When to run this

Run when one or more fit:
- the repo is old, mixed, or large
- the repo has many scripts, tools, or side channels
- the repo has auth, billing, secrets, deletion, migrations, or other high-risk paths
- the repo is a game repo, mobile stack, infra repo, AI system, or data system
- the repo has locale, transcreation, authored-content, generated-prose, or saved-text boundaries
- earlier passes claimed confidence that feels broader than the evidence

## Deliverables

Create or update:
- `docs/review/adversarial-pass.md`
- `docs/unknowns/adversarial-pass.md`

Update the coverage ledger when this pass changes confidence, scope, or slice order.

## What to challenge

### 1. Claimed repo shape

Check whether the system map and slice plan missed:
- hidden runtime entrypoints
- admin-only tools
- backfills or one-shot scripts with live side effects
- package scripts or task targets that hit live systems
- notebooks used for prod support, data repair, or model operations
- feature flags that bypass normal paths
- scheduled jobs that act like quiet control planes
- editor tools or import hooks that change shipped behavior
- test helpers or fixtures that ship into real runtimes
- generated code that hides hand-written logic nearby
- bootstrap scripts that set permissions, state, or seeds
- CI or CD jobs that deploy, seed, migrate, backfill, or repair live state
- release tooling or platform-console steps that quietly change shipped behavior
- submodules, workspace links, or sibling repos that own part of the live path
- remote config, feature flags, or CMS content that alter behavior outside the repo
- locale files, content overlays, generated copy, prompt text, or CMS prose that silently changes runtime decisions

### 2. Trust boundaries

Check whether trust changes were mapped honestly. Boundaries include:
- public user to authenticated user
- standard user to admin user
- client to backend
- service to database
- service to queue
- queue to worker
- repo to third-party platform
- CI or CD system to cloud control plane
- release tooling to app-store or platform console
- source-locale text to translated or transcreated text
- rendered copy to structured runtime truth
- model or agent layer to tool execution
- game client to authoritative server
- mobile client to secure storage or native bridge
- infra runner to cloud control plane

### 3. Protected areas

Check whether protected areas were handled with enough caution. Use the approval-gated list from `00-conventions.md` as the baseline. Add repo-specific protected areas verified from the repo: saved rendered text that participates in replay, hashes, audit trails, user history, or product commitments; training data lineage; model routing; eval gates; tool execution; live economy; anti-cheat; platform purchase flows; infra state backends; IAM edges; runners; secret stores; privileged CI or CD automation; release tooling; support tooling with production reach.

If a prior pass edited a protected area without approval, call that out plainly.

### 4. Coverage honesty

Check whether the coverage ledger overstates what was actually reviewed. Look for:
- one helper treated as if it covered a whole flow
- one service treated as if it covered a whole monorepo
- a single comment pass treated as if a critical path is done
- a logging audit that skipped client telemetry, crash reports, worker logs, or support tools
- large excluded areas with no plan to explain them elsewhere
- one clean path used to hide a dirtier parallel path through scripts, tools, notebooks, CI jobs, release tooling, or remote config

### 5. Specialty-stack traps

Pick the branch that fits.

**Game repo:** client-authority mistakes, live economy logic outside the server boundary, entitlement checks split across client and server, narrative text that invents mechanics, locale text that rewrites canonical ids, analytics or crash events with player data, asset or scripting paths that bypass normal review, save, replay, or anti-cheat paths that expose trust mistakes.

**Mobile or native app:** local storage of sensitive data, permission flows under-documented, native bridge calls with weak validation, push or background tasks with hidden side effects, crash or analytics SDKs with rich payload capture, build or release or provisioning steps that quietly change runtime behavior, app-store or platform-console steps outside normal repo review.

**Infra-as-code repo:** remote state risks, IAM sprawl, secret-store drift, modules that look read-only but write live state, runner or pipeline permissions that exceed their job, environment-specific behavior hidden in variables or templates, import or migration steps that bypass normal guardrails.

**AI or data system:** prompt or response logging, tool traces with raw user content, notebooks that feed production without clear guardrails, eval sets or labeled data with weak lineage, routing layers that change model behavior quietly, safety filters that sit outside the documented flow, support scripts that can read or write prod data outside the main runtime, model prompts or tool schemas or safety settings pulled from remote stores or dashboards.

**Locale-heavy or content-heavy repo:** English copy parsed as truth, translated text changing ids or keys, saved rendered strings used for replay or hashes, shared UI widgets hiding copy policy, locale overlays targeting unapproved fields, transcreated prose adding mechanics or policy claims the structured system does not support.

## What to put in `docs/review/adversarial-pass.md`

Record:
- areas reviewed in this pass
- what earlier passes got right
- what earlier passes overstated or missed
- which risks moved up or down after this review
- which slices should move earlier in the queue
- which protected areas need human approval before any edit

Direct tone. Name the claim. Name the evidence. Name the gap.

## What to put in `docs/unknowns/adversarial-pass.md`

Use the unknowns entry shape from `00-conventions.md`.

## Finding-class verification

Scale verification to the way the claim can be settled.

- Deterministic failing test, invariant, schema, or exact diff: one strong verifier plus the local evidence is normally enough.
- Economy, incentives, emergent behavior, or statistical balance: use independent refuters and an aggregate fixed-input probe.
- Projection or adapter drift: import or invoke the canonical rule and diff behavior.
- Architecture or cycle claim: use a dependency graph, import rule, or AST check before agent debate.
- Performance claim: require a fixed workload, baseline, and budget.
- Security or privacy claim: trace a concrete source, transformation, sink, and guard.
- Exclusion, locking, or single-owner claim (file locks, share modes, mutexes, unique constraints, distributed locks): run a live second-claimant probe in every environment the claim covers and require an observed denial, because the enforcement is supplied by the operating system, filesystem, database engine, or service tier rather than by the calling code, and the same call can be enforced in one and a silent no-op in the next. A passing denial in one environment does not transfer to another; where the primitive cannot be proven, choose explicitly between failing closed and declaring the guarantee absent, and never let it degrade silently.
- Determinism or canonical-output claim: shuffle the inputs and require byte-identical serialized output, and include a fixture pair of distinct raw representations of one parsed value (two offset spellings of one instant, two spellings of one number), because ordering keyed on a parsed value is not total over raw representations and can pass a shuffle test by luck.

Verifiers receive the claim and evidence, not the finder's persuasive explanation.

## Extra adversarial targets learned through dogfeeding

Challenge:

- tests written by the same agent that wrote the implementation
- a green targeted battery standing in for aggregate world or system behavior
- duplicated rule logic across engine, view, adapter, migration, and compatibility boundaries
- manifest fields whose strictest, broadest, or first-match aggregation can let one file reclassify the whole system
- batch or chunk boundaries that change total results even when chunking should be semantically irrelevant
- diagnostics that accidentally feed authoritative behavior
- architecture exceptions with no owner, expiry, or finding id
- test edits that make a red patch green by weakening the contract
- two-way platform, architecture, or runtime splits whose else branch routes an untested third target down another target's assumptions

For emergent regressions, prefer a deterministic output-counting probe, a parent-commit or baseline diff, and one configuration or content unit unwired at a time before broad code reading.

For platform, architecture, or runtime branches, read the else branch as an unstated claim that no third target exists. Family identifiers hide the gap: one identifier can match several targets that share a name but not a capability. Separate a deliberate portable fallback, which needs nothing the unlisted target lacks, from a branch that quietly depends on a sibling's capability. The second kind usually half-works instead of crashing, and the worst cases fail open, leaving an exclusion or permission mechanism that excludes nobody. Require each branch to name the targets it was built and tested on, then make unlisted targets fail closed on operations (refuse and say why) and honest on observations (report nothing rather than fabricate). Audit these branches before adding a target, not after.

### Review freshly shipped fixes independently

Budget a bounded adversarial follow-up for detector logic, instrumentation, trust-boundary adapters, platform integration, and other changes whose own tests may share the same mistaken model as the implementation. Give the challenger the changed artifact, contracts, and raw evidence, not the author's conclusion. Require an independently observed failure or falsifier before opening a new finding. Scale this review by risk; it is not a mandatory fan-out for every small edit.

### Unfalsifiable checks are a named defect class

An assertion that no execution can fail is worse than a missing assertion, because it manufactures confidence while verifying nothing. Treat one as a finding, not a style nit. Recurring shapes: a value compared to itself or to the expression that produced it; a tolerance or threshold wider than the reachable range; a check inside a branch no input reaches; a matcher that accepts every candidate; a verifier reading back state written for that verifier's benefit. The test for the class is the falsifying input: name the concrete input or state that would make the check fail. A check whose author cannot name one gets rewritten or removed. The exception is a deliberate restatement of a property already proven elsewhere, which may stand when recorded as documentation rather than verification. Deterministic gates share this rule; see the gate-authoring cautions in `14-deterministic-verification.md`.

## Rules

- No application code changes.
- Do not turn suspicion into fact without evidence.
- Do not flatten specialty stacks into generic web-app language.
- Do not let one clean path hide a dirtier parallel path.
- Do not claim a risk is closed when the evidence only covers one branch.
- Mark cross-repo or out-of-repo boundaries when they shape the live path.

## Acceptance checklist

The result should:
- challenge earlier confidence with evidence
- catch blind spots in runtime shape, trust boundaries, or protected areas
- tighten the coverage ledger instead of making it look nicer than it is
- surface specialty-stack risks when the repo is not a plain web app
- leave the next reviewer with a clearer map of what still needs proof
