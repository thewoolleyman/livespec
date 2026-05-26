---
topic: spec-impl-commitment-tracking
author: claude-opus-4-7
created_at: 2026-05-26T07:30:00Z
---

## Proposal: add-spec-commitments-front-matter-field

### Target specification files

- SPECIFICATION/spec.md

### Summary

Extend the propose-change file format (`spec.md` §"Proposed-change and
revision file formats") with an optional structured
`spec_commitments.impl_followups[]` YAML front-matter field. Each entry
in the array declares one impl-side work-item the propose-change
obligates as a post-revise follow-up. The field is the
machine-readable surface that the companion
`unresolved-spec-commitment` doctor invariant (proposed in the
sibling section below) consumes. Today the same obligation can be
expressed only as freeform Markdown prose inside the propose-change
body (e.g., a `## Impl-side follow-ups` heading the author invents);
nothing parses prose, so commitments declared in propose-change bodies
silently drop on the floor when revise closes out.

### Motivation

This propose-change emerged from a concrete incident in the
`livespec-runtime` sibling repo. A doctor-findings bundle propose-change
filed there (`SPECIFICATION/history/v003/proposed_changes/doctor-findings-bundle-second-pass.md`)
carried 10 `## Proposal:` sections plus a final
`## Impl-side follow-ups (filed as work-items, not spec changes)`
section enumerating two impl-side tasks that the bundle's own text said
"SHOULD be filed via `/livespec-impl-plaintext:capture-work-item` after
this proposed change is accepted and the spec edits are revised in."
The revise wrapper accepted all 10 proposals, cut a `v003/` snapshot,
moved the bundle byte-identical into `history/v003/proposed_changes/`,
and paired it with `-revision.md`. The two follow-ups were never filed
as work-items — they sat as inert prose in the history archive.
`/livespec-impl-plaintext:next` continued to report
`{"action":"none","reason":"no work-items are ready"}`, masking the gap.

A root-cause analysis surfaced four layered causes:

1. **No structured commitment surface.** The follow-ups were freeform
   Markdown under an author-invented heading. There is no schema field
   that names them, so no mechanical consumer can find them.
2. **No post-revise commitment check.** Doctor's static invariants are
   structural (version contiguity, revision pairing, anchor refs,
   well-formed `depends_on`). None inspect the revised propose-change
   for unfulfilled cross-side commitments.
3. **Cross-side composition gap.** Spec-side and impl-side ledgers are
   independent (per `spec.md` §"Three-layer orchestration architecture").
   No invariant correlates "spec change with declared impl follow-ups"
   against "work-items referencing that spec change."
4. **LLM-trust gradient.** Today the LLM authoring a propose-change is
   the only actor that knows about declared follow-ups. If the LLM
   forgets to file them post-merge, no other actor — machine or
   process — surfaces the gap.

The deepest cause is that the obligation lives entirely in narration
and LLM attention. That class of obligation will silently fail every
time. The fix is to make the commitment a machine-readable field, then
add a doctor invariant that fails closed until each declared
commitment maps to a filed work-item. This proposal lands the
front-matter half; the sibling
`add-unresolved-spec-commitment-doctor-invariant` proposal lands the
doctor half.

### Proposed Changes

Edit `SPECIFICATION/spec.md` §"Proposed-change and revision file
formats" by adding a new paragraph between the existing
"Filename stem vs. front-matter `topic` distinction" paragraph (v017
Q7, line 221) and the `<spec-target>/proposed_changes/<topic>-revision.md`
paragraph (line 223):

> **Spec→impl commitment declaration (this proposal).** A
> proposed-change file MAY declare cross-boundary obligations via an
> optional top-level YAML front-matter field `spec_commitments`. The
> field's shape:
>
> ```yaml
> spec_commitments:
>   impl_followups:
>     - id_hint: <author-chosen kebab-case slug>
>       description: |
>         <one-paragraph description of the impl change required after
>          this propose-change is revised in>
> ```
>
> Each `impl_followups[]` entry declares one impl-side work-item that
> MUST be filed in the active impl-plugin's store before the
> propose-change is considered closed. The `id_hint` is a
> human-author-chosen kebab-case slug (NOT a generated work-item id);
> the active impl-plugin's `capture-work-item` skill MUST accept an
> optional `spec_commitment_hint: <id_hint>` field that pairs the
> resulting work-item to the originating propose-change. The pairing
> is what the companion `unresolved-spec-commitment` doctor invariant
> (defined in `contracts.md` §"Doctor cross-boundary invariants")
> consumes.
>
> The field is OPTIONAL. Propose-changes with no cross-boundary
> obligation omit it; revise treats absent `spec_commitments` as a
> zero-commitment payload. The field is only meaningful for
> propose-changes that revise accepts (decision `accept` or `modify`);
> rejected propose-changes create no obligation regardless of their
> declared `spec_commitments`.
>
> Authors MUST NOT smuggle impl-follow-up declarations into freeform
> Markdown headings (e.g., `## Impl-side follow-ups`); those headings
> are invisible to the doctor invariant. The structured front-matter
> field is the supported and only surface for declaring cross-boundary
> obligations.

The propose-change wrapper (`bin/propose_change.py`) SHOULD validate
the field shape on write (e.g., `id_hint` is a non-empty kebab-case
slug, `description` is a non-empty string) and exit `4` on
schema-violation per the existing `propose_change_findings.schema.json`
boundary. The exact wrapper-side validation algorithm is
mechanism-level detail per the architecture-vs-mechanism discipline
already established in this section.


## Proposal: add-unresolved-spec-commitment-doctor-invariant

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a new `unresolved-spec-commitment` doctor cross-boundary invariant
to `contracts.md` §"Doctor cross-boundary invariants". The invariant
walks every `history/vNNN/proposed_changes/<topic>.md` whose paired
`<topic>-revision.md` carries `decision: accept` or `decision: modify`,
reads each declared `spec_commitments.impl_followups[]` entry, and
fires `fail` when the entry's `id_hint` does not appear as a
`spec_commitment_hint` field on at least one work-item in the active
impl-plugin's store. Pair the spec-side and impl-side ledgers
mechanically; close the silent-drop gap described in the sibling
`add-spec-commitments-front-matter-field` proposal.

### Motivation

Same root-cause incident as the sibling proposal: a propose-change in
the `livespec-runtime` sibling repo declared two impl-side follow-ups
in Markdown prose, revise closed out without checking them, and the
declared obligation evaporated into the history archive without ever
becoming work-items in the active impl-plugin's store.

The front-matter field proposed in the sibling section creates the
machine-readable surface. This proposal turns that surface into a
gating check: revise's post-step doctor MUST refuse to cut the
new `vNNN/` snapshot until every declared `impl_followups[]` entry has
a corresponding work-item in the impl-plugin's store. The check also
runs on subsequent doctor invocations so post-merge drift (a work-item
deleted, superseded, or never filed despite the revise PR being
hand-merged) is surfaced.

### Proposed Changes

Insert a new subsection in `SPECIFICATION/contracts.md` §"Doctor
cross-boundary invariants" immediately after the existing
`### depends_on-ref-wellformedness` subsection (current line 136):

> ### `unresolved-spec-commitment`
>
> Every accepted propose-change's declared cross-boundary obligation
> MUST resolve to a filed work-item. The check walks every
> `<spec-target>/history/vNNN/proposed_changes/<stem>.md` whose paired
> `<stem>-revision.md` carries `decision: accept` or `decision:
> modify`, reads the `<stem>.md`'s front-matter
> `spec_commitments.impl_followups[]` (per `spec.md` §"Proposed-change
> and revision file formats" → "Spec→impl commitment declaration"),
> and for each entry's `id_hint` queries the active impl-plugin's
> `list-work-items --json` thin-transport skill for a work-item
> carrying `spec_commitment_hint: <id_hint>`. The check fires `fail`
> when any entry's `id_hint` is absent from the work-items store, with
> narration directing the user to file the work-item via the active
> impl-plugin's `capture-work-item` skill.
>
> Work-items matched against the commitment MAY be in any status
> (`open`, `in_progress`, `blocked`, `closed`, `deferred`,
> `superseded`). The invariant verifies the work-item exists; per-item
> closure timing is the impl-plugin's `next` ranker's concern, not
> doctor's. A work-item with `status: deferred` is acceptable proof
> that the commitment is tracked.
>
> The check runs at every doctor static invocation, including revise's
> post-step doctor. When revise's post-step doctor fires `fail` on this
> invariant, the revise wrapper exits `3` per the existing exit-code
> table — revise MUST NOT cut a new `vNNN/` snapshot until the
> commitments resolve. The user's corrective action is to file the
> declared work-items via the active impl-plugin's `capture-work-item`
> skill, then re-invoke revise.
>
> Propose-changes with `decision: reject` are exempt: a rejected
> propose-change creates no spec→impl obligation, so no
> `spec_commitments` entry it declares is checked. Propose-changes
> that omit `spec_commitments` entirely are exempt vacuously
> (zero-commitment payload).
>
> Supersession: when a later propose-change accepted in a subsequent
> `vNNN/` carries `spec_commitments.supersedes: [<earlier-id_hint>,
> ...]`, the listed `id_hint`s are no longer subject to this check —
> the later propose-change has either absorbed the obligation or
> revoked it; the supersession declaration is the spec-side
> acknowledgement. The `supersedes` sub-field is OPTIONAL and is
> defined in `spec.md` §"Proposed-change and revision file formats"
> alongside the `impl_followups` sub-field.
>
> Cross-repo: when the active project's `.livespec.jsonc` lacks an
> impl-plugin (e.g., spec-only repos that do not adopt an impl-plugin),
> this invariant is `skipped` rather than `fail`. The `spec_commitments`
> field's semantic is impl-plugin-relative; without an impl-plugin the
> declaration has no destination to land in. Spec-only repos relying on
> propose-change declarations for impl follow-ups in a separate repo
> SHOULD route those declarations through the consuming repo's own
> propose-change cycle, not this repo's `spec_commitments` field.


## Proposal: extend-impl-plugin-contract-with-spec-commitment-hint

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Extend the impl-plugin contract surface (`contracts.md`
§"Implementation-plugin contract — the 10-skill surface") to require
that every impl-plugin's work-item record schema carry an optional
`spec_commitment_hint: <string>` field, populated by the
`capture-work-item` skill when the work-item is filed in response to a
spec-side commitment. This is the impl-plugin counterpart to the spec
front-matter field defined in the sibling
`add-spec-commitments-front-matter-field` proposal; together they form
the spec↔impl pairing the `unresolved-spec-commitment` doctor
invariant consumes.

### Motivation

The doctor invariant needs a structured way to match propose-change
declarations against work-items. Matching by free-text description or
title would be LLM-judgment-grade and unsafe to gate on. A dedicated
optional field — populated only when the work-item arises from a
spec-side commitment, otherwise absent — makes the pairing exact and
mechanical. The field is OPTIONAL because freeform work-items (bugs,
refactors, tactical tasks unrelated to any propose-change) have no
spec-side commitment to point at.

### Proposed Changes

Insert a new subsection in `SPECIFICATION/contracts.md`
§"Implementation-plugin contract — the 10-skill surface" immediately
after the existing §"Backend-variability asymmetry" subsection
(current line 332):

> ### Work-item `spec_commitment_hint` field
>
> Every impl-plugin's work-item record schema MUST carry an OPTIONAL
> `spec_commitment_hint: string | null` field. The field is populated
> by the `capture-work-item` skill when the work-item is filed in
> response to a propose-change's
> `spec_commitments.impl_followups[].id_hint` declaration (per
> `spec.md` §"Proposed-change and revision file formats"); its value
> MUST equal the originating `id_hint` verbatim. The field is `null`
> for freeform work-items not tied to any propose-change commitment.
>
> The field is the impl-plugin-side surface the
> `unresolved-spec-commitment` doctor invariant queries to verify each
> declared spec→impl commitment maps to a filed work-item. Impl-plugins
> MUST surface the field in their `list-work-items --json` output so
> doctor's invariant can match without invoking
> implementation-private machinery.
>
> The `capture-work-item` skill MUST accept an optional
> `--spec-commitment-hint <id_hint>` CLI flag (or the equivalent in
> backends that use a different invocation surface) that populates the
> field on write. When the user invokes `capture-work-item` without
> the flag, the resulting work-item carries
> `spec_commitment_hint: null` (the freeform case). When the user
> invokes it WITH the flag, the resulting work-item is paired against
> the named commitment for the duration of its lifetime.
>
> Renaming or removing this field on any future impl-plugin schema
> evolution is a major-version bump of the impl-plugin's contract pin
> (per §"Cross-repo coordination — pin-and-bump"). The field's
> presence + value semantics are part of the load-bearing 10-skill
> surface.


## Proposal: thread-spec-commitments-end-to-end-through-supporting-machinery

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Ensure the three preceding proposals compose correctly end-to-end by
threading the `spec_commitments` field through (a) the
`propose-change`-wrapper schema validation surface, (b) the `revise`-
wrapper post-step doctor invocation, and (c) the
`/livespec:next` ranker's `propose-change` candidate emission. Each
touch point is small (one paragraph in `contracts.md`); the proposal
groups them so a reviewer accepting the three structural proposals
above does not have to chase loose ends.

### Motivation

The three preceding proposals define the front-matter field, the
doctor invariant, and the impl-plugin field independently. They
compose correctly only when the supporting machinery acknowledges
them in three places. Filing the threading as a separate proposal
makes the supporting edits reviewable in isolation; a reviewer who
wants to accept the structural three and modify the threading edits
can do so without rejecting the load-bearing changes.

### Proposed Changes

Three minor edits to `SPECIFICATION/contracts.md`:

**Edit 1.** Append to `SPECIFICATION/contracts.md` §"Sub-command wire
contracts" → §"`critique` payload validation" (or its propose-change
sibling) a clarification that the schema-validation wrapper exit-4 path
covers the new front-matter field's structural validation:

> The `spec_commitments` top-level field (when present) MUST validate
> against the structured shape codified in `spec.md` §"Proposed-change
> and revision file formats" → "Spec→impl commitment declaration"
> before the propose-change file is written. A propose-change payload
> declaring a malformed `spec_commitments` block (missing `id_hint`,
> empty `description`, non-kebab-case slug) MUST cause the wrapper to
> exit `4`, retryable via the LLM regeneration path. The wrapper does
> NOT validate that the declared `id_hint` is unique across the spec
> tree; collisions are surfaced post-revise by the
> `unresolved-spec-commitment` doctor invariant when two distinct
> declarations point at conflicting work-items.

**Edit 2.** Append to `SPECIFICATION/contracts.md` §"Sub-command wire
contracts" → §"`revise` payload validation" a clarification on the
post-step doctor's interaction with the new invariant:

> Revise's post-step doctor MUST run the `unresolved-spec-commitment`
> invariant against the freshly-cut `vNNN/` snapshot. Pre-step doctor
> runs the same invariant against the pre-revise state, surfacing any
> previously-accepted commitments that have lost their work-item
> coverage between the prior revise and this one (e.g., a work-item
> deleted out-of-band, or a propose-change accepted in an earlier
> revise whose commitments were never filed). The post-step run is the
> gating point; pre-step provides early visibility but does NOT block
> revise's execution.

**Edit 3.** Append to `SPECIFICATION/contracts.md` §"`/livespec:next`
spec-side thin-transport skill" → §"Ranker semantics" a clarification
on whether `unresolved-spec-commitment` findings rank candidates:

> The ranker MUST NOT emit `revise` candidates whose pre-step doctor
> would `fail` on the `unresolved-spec-commitment` invariant. A
> propose-change with unresolved cross-boundary commitments is not yet
> ripe for revise — the user MUST file the declared work-items via the
> active impl-plugin first. The ranker surfaces this as a
> `capture-work-item` candidate (action: the impl-plugin's
> `capture-work-item` skill, not a livespec-side action), with
> narration naming the unresolved `id_hint`s and the originating
> propose-change topic.
