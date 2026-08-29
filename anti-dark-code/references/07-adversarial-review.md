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

### Verify a publication against its approval, not its paperwork

When approved work is published, a squash merge of a reviewed branch, a paused implementation finally pushed, a release cut from a tag, verify the published bytes against the approval rather than against the prose that accompanied them.

- Tree identity first. The integration commit's tree hash either equals the approved head's tree hash or it does not. One comparison proves that shared history contains exactly what was approved and nothing else, and it costs less than reading any diff.
- Recompute every declared postimage from the published artifact. A byte receipt recorded against unpublished work-in-progress describes bytes that may never ship: adaptation to a moved base, a portability amendment, or a final touch-up changes the publication while the paperwork keeps the paused-state hash.
- Treat every "unchanged" claim about bytes as a computation to run, never an assertion to accept. In one dogfeeding incident at a consuming repository, a publication declared four postimage receipts; three verified, and the one carried forward from the paused state did not, while the same document correctly recorded current-plus-historical receipts for a different file it knew had changed. Same author, same document, both patterns available; only the receipt that was recomputed at publication survived contact with the bytes.
- A receipt that goes stale for a legitimate reason is history, and history is not a defect. Record the current receipt as current and the old one as superseded, in that order. Presenting history as the present is the defect, and it is the same class as release notes that describe a different artifact than the tag reproduces.

### A byte receipt states its algorithm and its normalization

Two honest people can hash the same approved file and record different values, for reasons that have nothing to do with its contents. A receipt that does not say how it was computed cannot be reproduced, and an unreproducible receipt is not evidence.

The shapes that actually occur:

- **Checkout-rewritten line endings.** Where version control rewrites line endings on checkout, a receipt taken from a working copy differs from one taken from the stored bytes. The same approved file then verifies on one contributor's machine and fails on another's, and neither is wrong.
- **Different receipt kinds.** A version-control object id and a file digest are both sound, and they are not comparable. A checker must reproduce whichever kind the document it is verifying used, so a document that mixes kinds across entries cannot be checked in one pass.
- **Mixed normalization inside one document**, which is the same failure wearing a disguise: entries that look like a series and are not.

The rule: every recorded receipt names its algorithm and its normalization, raw stored bytes or line-ending-normalized, and a verifier reproduces both. Where a file's raw and normalized digests are equal, record that they agree; one line rules out the entire class for that entry.

What omitting it costs is not a wrong answer but an unfalsifiable disagreement. A mismatch could be corruption, an unauthorized edit, or a checkout setting, and the record cannot distinguish them. In one dogfeeding incident a published postimage disagreed with its recorded receipt, and the explanation, a receipt computed on a line-ending-rewriting checkout while the published bytes were stored normalized, was only reachable because someone still had both artifacts to compare. Had either been gone, an approved change would have been indistinguishable from a silent substitution.

### Authorization documents drift; diff them against their authority before they become executable

When authorization is document-driven, an issue text, a work order, a contract copy, parallel workstreams produce divergent copies of what is authorized, and each copy reads as authoritative to whoever holds it. The dangerous moment is the enabling act: the label, approval reply, or sign-off that makes one copy executable. Compare the executable copy against the approved authority immediately before enabling it, as a required step of enabling it, not as review that already happened somewhere upstream.

In one dogfeeding incident, a work order proposed in good faith against all state visible to its author authorized a materially wider scope than the owner-approved contract that had been developed in parallel and was not yet visible to that author. The pre-enabling comparison caught it, and the mismatch was scope, not wording. Nobody was wrong; the copies drifted, which is what copies do.

- Diff against the approved artifact itself, never against anyone's memory of it.
- Missing visibility into the authority is a reason to require the comparison, not a reason to skip it; the author least able to see the authority is the one most likely to have drifted from it.
- A reconciled copy records what it was reconciled against, so the next comparison has a fixed point.

### Unfalsifiable checks are a named defect class

An assertion that no execution can fail is worse than a missing assertion, because it reports coverage that does not exist. Treat one as a finding, not a style nit.

The recurring shapes, in the order they tend to surface:

- a field written as a fixed literal by a producer and pinned to that same literal by a checker
- an assertion comparing a value to itself, or to a constant it was already compared against
- a claimed property with no probe behind it
- a boolean literal asserted in place of a captured outcome
- a checker pinned to a document string that later becomes false
- a tolerance or threshold wider than the reachable range, or a matcher that accepts every candidate

The test for the class is the falsifying input: name the concrete, producible input or state that would make the check fail. A check whose author cannot name one gets rewritten or removed. In the sharpest form of this defect the producer can emit only one value and the checker requires exactly that value, which makes the acceptance criterion permanently unsatisfiable and would reject an honest recording of a genuine result.

Naming the class obliges a sweep. Repairing only the instance that surfaced leaves the rest in place, and a remediation written while the class is already named can introduce fresh instances of it. Sweep the whole verification surface once the class is named, and re-sweep after remediating it.

The exception is a deliberate restatement of a property already proven elsewhere. Such a restatement must cite the probe that proves it, at the restatement. Requiring the citation is the cheap discriminator: the danger is not the restatement itself but the undocumented case, where a value with no probe behind it hides among values that have one. Deterministic gates share this rule; see the gate-authoring cautions in `14-deterministic-verification.md`.

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
