# Reference: Writing, Comment, and Commit Hygiene

Use this reference when an agent or a person wrote or edited comments, docs, ADRs, runbooks, unknowns files, commit messages, PR notes, or task summaries and the text needs to read like careful human work.

**Mode:** text-only cleanup. No logic or behavior changes.

For the canonical writing rules referenced here, see `00-conventions.md`.

## Goal

Clean touched text so it is plain, specific, and easy to trust. Remove canned phrasing, loose claims, and style habits that make careful work sound machine-made.

## Scope

Review only text touched in the current task, plus any nearby text that now clashes with the rewrite.

Common targets:
- inline comments
- doc comments
- READMEs
- ADRs
- runbooks
- unknowns files
- architecture notes
- audit notes
- commit messages
- PR close-out notes
- task summaries returned to the user

## Hard rules

- Keep meaning intact.
- Keep scope claims honest.
- Do not hide uncertainty.
- Do not add new technical claims unless repo evidence already supports them.
- ASCII punctuation and straight quotes only.
- Commas, periods, or parentheses instead of long-dash punctuation.
- Keep the repo's local voice when it already reads like careful human work.
- Preserve intentional style differences between tool-specific files when the repo uses them that way.
- Merge any caller-supplied banned-term list into this pass as a hard rule.

## What good text looks like

Good text in this workflow should:
- name the subject early
- name the risk directly
- name the safeguard or limit directly
- keep sentences short when the point is sharp
- use plain words over padded words
- sound like a careful engineer, not a brochure or a press release

## What to cut or rewrite

Rewrite text that leans on any of these habits:
- stiff corporate phrasing
- legal-boilerplate phrasing outside actual legal text
- stock transition adverbs at paragraph openings
- stock wrap-up lines that add no evidence
- mirror-contrast slogans built around a negated first clause
- default triplet cadence when two or four items fit better
- vague openings that hide the subject
- apology filler
- hype words
- padded claims with no evidence
- summary lines that repeat the paragraph without adding signal
- repeated sentence shapes that make a section sound generated

## Comment rules

Comments should earn their place.

Keep comments that explain:
- why the code exists
- what must stay true
- what breaks if someone moves the code carelessly
- what data is trusted or untrusted
- what ordering, idempotency, privacy, or state rule matters here
- what language, locale, or rendered-copy boundary must stay downstream of structured truth

Rewrite or remove comments that only restate syntax.

## Commit message rules

Good commit messages usually:
- start with the area changed
- say what changed in direct words
- avoid hype and slogans
- stay specific enough that a later reader can scan history fast

Bad commit messages usually:
- sound like marketing copy
- hide the subject behind broad nouns
- claim large certainty without evidence
- pretend one touched area proves the whole repo is understood
- use filler to sound polished
- say too little to help a later reviewer find the real change

## PR note rules

PR notes should cover:
- what changed
- why it changed
- what is still unclear
- what risk changed, if any
- what approval is still needed, if any

Keep each point short. Do not pad with softeners or stock courtesy lines.

## Unknowns file rules

Unknowns files should read like working notes from a careful reviewer. Use the canonical entry shape from `00-conventions.md` and do not turn an unknown into a guess dressed up as confidence.

## Self-check before finishing

Read touched text once for facts and once for tone.

On the tone pass, check for:
- hidden subjects
- repeated sentence shapes
- repeated opener words
- canned transitions
- canned wrap-up lines
- fake certainty
- scope claims that outrun the evidence
- loose adjectives doing the work of evidence
- punctuation drift away from ASCII and straight quotes
- generic summaries that could fit any repo

If the text still sounds generic, cut more words.

If the text still sounds padded, name the subject sooner.

If the text still sounds too smooth, add the missing limit or uncertainty.

## Deliverable summary

When done, return:
- the text cleaned or the files touched
- any caller-supplied lint rules applied
- any lines left alone on purpose because changing them would alter meaning

## Acceptance checklist

The final text should:
- keep the original meaning
- sound plain and specific
- avoid canned phrasing and stock transitions
- keep comments, docs, commits, and PR notes in one believable voice
- use ASCII punctuation and straight quotes only
- merge any caller-supplied banned-term list into the final text check
