---
topic: no-stalled-epic-invariant
author: claude-opus-4-7
created_at: 2026-05-20T08:43:30Z
---

## Proposal: Add no-stalled-epic doctor invariant

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Doctor's cross-boundary invariant catalogue MUST gain a fifth work-item structural invariant, `no-stalled-epic`, that fires `fail` when a work-item of type `epic` carries `status` in `{open, in_progress}` while every entry in its `depends_on` array resolves to a work-item with `status` of `closed`. An empty `depends_on` MUST NOT fire the invariant (vacuous-truth guard). The two enumerations that name the existing four invariants — `contracts.md` §"Doctor cross-boundary invariants" and `constraints.md` §"Cross-boundary doctor static checks" — MUST be updated to enumerate five invariants by name and update their accompanying count.

### Motivation

A live drift discovered while walking the multi-repo-split execution plan's session-start protocol on a clean master surfaced `li-6t5` (the Phase D epic in this repo's dogfooded `work-items.jsonl`) sitting at `status:in_progress` for an extended interval after every Phase D sub-task closed and after the dogfooding cutover landed (PR #140). None of the four currently spec'd doctor work-item invariants — `gap-tracking-one-to-one`, `no-orphan-blocker`, `no-stale-gap-tied`, `no-duplicate-gap-id` — cover this drift class. They target gap-id integrity and blocker resolvability, not epic-to-sub-task rollup. The drift is structural per `spec.md` §"Terminology" — an epic is by definition the aggregation of its sub-tasks; an epic remaining open while every blocker has closed is a logical inconsistency in the work-items data model, not a productivity-grade staleness signal. Structural invariants on durable-pending items are explicitly in-scope for doctor; productivity heuristics are not. The `no-stalled-epic` invariant is the structural form of this class.

### Proposed Changes

The doctor cross-boundary invariant catalogue MUST add `no-stalled-epic` as a fifth work-item structural invariant. The invariant's semantics are:

- The check MUST fire `fail` when a work-item with `type == "epic"` AND `status` in `{open, in_progress}` has a non-empty `depends_on` array whose every entry resolves to an existing work-item with `status == "closed"`.
- The check MUST NOT fire when `depends_on` is the empty list — a freshly filed epic with no declared sub-tasks is not in the same logical state as an epic whose declared sub-tasks have all closed, and the vacuous-truth case would otherwise flag every newly-filed open epic.
- Unresolvable entries in `depends_on` (referenced ids missing from the store) MUST NOT fire `no-stalled-epic`; that drift class is the existing `no-orphan-blocker` invariant's domain and SHOULD continue to surface there.
- The `fail` (not `warn`) classification reflects that this is a structural contract violation rather than a productivity-grade nudge: the epic↔sub-task aggregation is a load-bearing data-model invariant, and `warn` is reserved per the existing `no-stale-gap-tied` precedent for productivity heuristics.
- The check ID MUST follow the existing lowercase-hyphenated slug convention (`no-stalled-epic`) and MUST appear in the `livespec.doctor.static` registry per the enumerability requirement already codified in `constraints.md` §"Cross-boundary doctor static checks".
- The check's narration on `fail` MUST direct the user to either close the epic with an appropriate `resolution` (when the work is genuinely complete) OR add fresh `depends_on` entries (when the original sub-tasks were not the complete set of blockers).

The two enumeration sites MUST be updated:

- `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" line 103 currently reads "The catalogue MUST include the four work-item invariants and the contract-version-compatibility invariant below." — this MUST become "five work-item invariants". A new `### no-stalled-epic` subsection MUST be inserted between `### no-duplicate-gap-id` and `### contract-version-compatibility`, in the same H3-style as the existing four. The §"Implementation-plugin contract — the 9-skill surface" prose on line 212 referencing "doctor's four work-item structural invariants" MUST also be updated to "doctor's five work-item structural invariants".
- `SPECIFICATION/constraints.md` §"Cross-boundary doctor static checks" line 285 currently enumerates the four invariants by slug — `no-stalled-epic` MUST be appended to this enumeration. The accompanying count ("The four work-item structural invariants") MUST become "The five work-item structural invariants". Line 287's parallel reference ("the four work-item invariants above") MUST become "the five work-item invariants above".

This proposal does NOT prescribe implementation order between (a) the `no-stalled-epic` invariant and (b) the four already-spec'd invariants whose implementation remains a known follow-up per `tests/heading-coverage.json`. The five invariants SHOULD land together in a single implementation PR; if separation is needed, `no-stalled-epic` MAY land independently because its data dependency (`depends_on` array) is a different field from the four existing invariants' data dependency (`gap_id` and `blocked_by`).

An orthogonal observation worth surfacing but explicitly OUT OF SCOPE for this proposal: the beads-to-JSONL migration that landed at D.10 produced records with `depends_on: []` for every migrated work-item; the dependency graph captured in the original beads store was not preserved across the migration. This affects the `no-stalled-epic` invariant's effective coverage (against the current data, it would not fire because every `depends_on` is vacuously empty). A separate work-item, NOT a spec proposal, SHOULD be filed to backfill the dependency edges from the plan-doc's enumerations and the original beads dolt commit history. The invariant spec is correct independent of the data shape.
