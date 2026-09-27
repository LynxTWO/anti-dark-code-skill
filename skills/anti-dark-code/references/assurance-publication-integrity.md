# Publication and authorization integrity

Trigger: approved work is about to be enabled, integrated, released, or published.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

## Verify a publication against its approval, not its paperwork

When approved work is published, a squash merge of a reviewed branch, a paused implementation finally pushed, a release cut from a tag, verify the published bytes against the approval rather than against the prose that accompanied them.

- Tree identity first. The integration commit's tree hash either equals the approved head's tree hash or it does not.
- Recompute every declared postimage from the published artifact.
- Treat every "unchanged" claim about bytes as a computation to run, never an assertion to accept.
- Record the current receipt as current and the old one as superseded, in that order.

## A byte receipt states its algorithm and its normalization

The shapes that actually occur:

- **Checkout-rewritten line endings.** Where version control rewrites line endings on checkout, a receipt taken from a working copy differs from one taken from the stored bytes.
- **Different receipt kinds.** A version-control object id and a file digest are both sound, and they are not comparable. A checker must reproduce whichever kind the document it is verifying used, so a document that mixes kinds across entries cannot be checked in one pass.
- **Mixed normalization inside one document**, which is the same failure wearing a disguise: entries that look like a series and are not.

The rule: every recorded receipt names its algorithm and its normalization, raw stored bytes or line-ending-normalized, and a verifier reproduces both. Where a file's raw and normalized digests are equal, record that they agree; one line rules out the entire class for that entry.

## Authorization documents drift; diff them against their authority before they become executable

The dangerous moment is the enabling act: the label, approval reply, or sign-off that makes one copy executable. Compare the executable copy against the approved authority immediately before enabling it, as a required step of enabling it, not as review that already happened somewhere upstream.

- Diff against the approved artifact itself, never against anyone's memory of it.
- Missing visibility into the authority is a reason to require the comparison, not a reason to skip it; the author least able to see the authority is the one most likely to have drifted from it.
- A reconciled copy records what it was reconciled against, so the next comparison has a fixed point.

Result: the executable/published copy is compared against its actual approved authority, receipt algorithm and normalization are reproduced, and current/superseded receipts are explicit. Hashes bind bytes; they do not grant permission or prove semantic truth.
