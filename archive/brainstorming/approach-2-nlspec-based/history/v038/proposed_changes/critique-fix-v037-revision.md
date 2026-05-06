# critique-fix v037 → v038 revision

## Origin

Phase 7 sub-step 5.a (filing the propose-change for
`livespec/commands/revise.py`'s full-feature-parity widening
against `SPECIFICATION/`) drafted a Proposal that needed to
codify the version-cut rule for an all-`reject` revise
invocation. The cascading-impact scan against PROPOSAL.md
caught an internal contradiction in §"Versioning" between two
adjacent bullets:

- **Statement A** (line 1734-1736, paired with §"`revise`"
  line 2483): "A new version is cut **when, and only when**,
  `revise` either accepts or modifies at least one proposal
  in `<spec-root>/proposed_changes/`." The `when, and only
  when` clause is an iff that excludes the all-reject case.
  §"`revise`" line 2483 ("If any decision is `accept` or
  `modify`, a new version `vN` is cut") aligns with this
  reading.

- **Statement B** (line 1739-1745): "A `revise` invocation
  that processes proposals but rejects all of them **MUST
  still cut a new version**. The version's specification
  files are byte-identical copies of the prior version's
  specification files; the version's
  `<spec-root>/history/vNNN/` directory contains the
  proposed-change files and rejection revisions. This
  preserves the audit trail for every proposal that ever
  reached `revise`."

Statement A and Statement B cannot both hold mechanically:
A's iff excludes all-reject; B mandates a cut on all-reject.
The contradiction was latent through every prior revision
because no actual all-reject revise had been run during
bootstrap to date — every revise invocation on record (the
seed at v001, the v002-v010 widening cycles, the v010 critique
acceptance at sub-step 4.b) accepted at least one proposal,
so the cut-iff-accept reading and the cut-on-non-empty
reading produced the same observable behavior.

Phase 7's revise-widening propose-change forced the choice
because the wrapper's Phase-7 widening must implement ONE
canonical version-cut semantic, and the codified contract
must be unambiguous for a clean re-implementation.

PROPOSAL.md line 1745's stated intent — "This preserves the
audit trail for every proposal that ever reached `revise`" —
is the architectural anchor: the rejection event is
architecturally meaningful and deserves a stable home in
`history/vNNN/proposed_changes/`. Statement A would require a
new sub-architecture deciding *where* rejection revisions land
(back to `proposed_changes/` for re-iteration, or moved into
the most-recent existing `history/vNNN/proposed_changes/`, or
a new graveyard directory), none of which is currently
codified and each of which has its own awkwardness. Statement
B's "always cut on non-empty processing" is the simpler
architecture and matches PROPOSAL.md's stated intent at line
1745.

The remedy is a v038 revision covering two decisions:

- **D1** Statement B authoritative. Soften the §"Versioning"
  iff at line 1734-1736 from `when, and only when, accepts
  or modifies` to `on every successful revise invocation
  (i.e., whenever revise processes at least one proposal)`.
  Update §"`revise`" line 2483 to match: a new version is
  cut on every successful revise; when no decision is
  `accept` or `modify`, the new version's spec files are
  byte-identical copies of the prior version's spec files.
  Retain the §"Versioning" line 1739-1745 paragraph
  verbatim — it is the explicit case-handler for the
  all-reject case under Statement B.
- **D2** Plan-text + housekeeping. Plan §"Version basis"
  preamble gains a v038 decision-block; Phase 0 step-1
  byte-identity → `history/v038/`; Phase 0 step-2
  frozen-status → "Frozen at v038" (per the no-op
  convention since v024 — the literal PROPOSAL.md header
  line never actually changes; the PLAN's narrative
  reference is what bumps); Execution-prompt block
  authoritative-version → v038; STATUS.md updates.

The v038 codification commit is spec-only. No follow-up
implementation commit is needed — the Phase-3 minimum-viable
`livespec/commands/revise.py` already implements Statement B's
"always cut on non-empty processing" semantic via
`_process_decisions` always calling `_next_history_version_dir`
regardless of decision content. The "byte-identical-to-prior
spec files on all-reject" property is a downstream consequence
of `_bind_resulting_files`'s short-circuit on non-accept-or-
modify decisions: no `resulting_files[]` writes fire on
all-reject, so the working spec is unchanged when the snapshot
into `history/vNNN/` happens during the Phase-7 sub-step 5.c
widening (which lands the working-spec → `history/vNNN/`
snapshot per §"`revise`" line 2487-2490). Sub-step 5.a's
propose-change re-authoring against v038 will codify the
behavior in `SPECIFICATION/` for the widened wrapper without
contradicting the existing impl.

## Decisions captured in v038

### D1 — Statement B authoritative on the version-cut rule

**Surface in PROPOSAL.md.** Two locations:

- §"Versioning" (lines 1734-1745) — the contradiction lives
  here. Line 1734-1736 carries Statement A's iff; line
  1739-1745 carries Statement B's case-handler. Resolution
  rewrites lines 1734-1736 to no longer be an iff that
  excludes the all-reject case; lines 1739-1745 stay
  verbatim.
- §"`revise`" (line 2483-2484) — the wrapper-side echo of
  Statement A. Resolution rewrites the bullet to match the
  rewritten §"Versioning" wording.

**Decision.** Statement B is the canonical version-cut
rule. A new version is cut on every successful revise
invocation (i.e., whenever `<spec-root>/proposed_changes/`
contains at least one in-flight proposal at the time revise
runs and every proposal is processed to a decision). When
at least one decision is `accept` or `modify`, the
working-spec files named in those decisions' `resulting_files[]`
are updated in place before the snapshot. When every decision
is `reject`, the new version's spec files are byte-identical
copies of the prior version's spec files. The all-reject case
preserves the audit trail in the new `history/vNNN/proposed_changes/`
directory, which carries the rejection-revision records and
the byte-identical-moved proposed-change files.

**Rationale.** PROPOSAL.md line 1745's stated intent is the
architectural anchor: "This preserves the audit trail for
every proposal that ever reached `revise`." Statement B's
"always cut on non-empty processing" delivers that anchor
naturally — every proposal-bearing revise produces a stable
audit-trail home in `<spec-root>/history/vNNN/proposed_changes/`,
contiguous with the version-cut-on-accept case.

Statement A would require a new sub-architecture deciding
where rejection revisions land:

- **Back to `proposed_changes/` for re-iteration.** The file
  is no longer in flight; the user has explicitly rejected
  the proposal. Leaving the rejection-revision file in
  `proposed_changes/` mixes a finalized audit record with
  unprocessed work — confusing for both the user and for
  the next `revise` invocation, which would now have to
  distinguish "rejected revision that should not be
  reprocessed" from "fresh proposal awaiting a decision".
  Rejected.
- **Into the most-recent existing `history/vNNN/proposed_changes/`.**
  Mixing audit-trail records across version cuts breaks the
  invariant that `history/vNNN/proposed_changes/` reflects
  the proposals decided AT vNNN. A future doctor check
  walking `history/vNNN/proposed_changes/` to verify
  every revision pairs with a proposed-change in the same
  directory would now find revisions that don't belong to
  vNNN's decision set. Rejected.
- **Into a new `<spec-root>/rejected/` graveyard
  directory.** Adds a third top-level subdirectory under
  `<spec-root>/` alongside `proposed_changes/` and
  `history/`. Inflates the spec-tree shape. Doctor checks
  that walk the spec-tree shape would all need to recognize
  the new directory. Rejected.

Statement B avoids all three sub-architectures by reusing
the existing `history/vNNN/proposed_changes/` as the
audit-trail home regardless of decision mix.

A potential concern about Statement B: "every revise
produces a version, even when no spec content changes,
which feels wasteful." The waste is bounded — the
all-reject version's spec-file copies are byte-identical to
the prior version's, so storage cost is duplicate-content
proportional. Git's content-addressed storage deduplicates
identical blobs, so the on-disk cost in the `history/`
tree is approximately one tree-object per version (the
file-content blobs are shared with the prior version's
snapshot). The semantic clarity benefit (every revise has
a stable history-side audit-trail home) outweighs the
modest storage cost.

A second potential concern: "Statement A's `when, and only
when` was deliberate; we should treat it as the iff and
delete Statement B." Rejected because PROPOSAL.md line 1745's
intent statement explicitly preserves audit trail for every
proposal that ever reached revise — and Statement A would
require additional architectural work (where rejection
revisions land) that has not been codified anywhere in the
PROPOSAL.md body. Statement A is the older wording; Statement
B is the newer, intent-aligned wording. Reading the two
together, the iff in line 1734-1736 is the codification
slip that needs the wording fix.

**PROPOSAL edits.** Two locations:

1. §"Versioning" lines 1734-1738 — replace:

   > - A new version is cut when, and only when, `revise` either
   >   accepts or modifies at least one proposal in
   >   `<spec-root>/proposed_changes/`. A `revise` invocation that finds no
   >   proposals MUST fail hard and direct the user to
   >   `propose-change`.

   with:

   > - A new version is cut on every successful `revise`
   >   invocation — that is, whenever
   >   `<spec-root>/proposed_changes/` contains at least one
   >   in-flight proposal at the time `revise` runs and every
   >   proposal is processed to a decision (accept, modify, or
   >   reject). A `revise` invocation that finds no proposals
   >   MUST fail hard and direct the user to `propose-change`.

   Lines 1739-1745 (the Statement B case-handler paragraph)
   stay verbatim.

2. §"`revise`" line 2483-2484 — replace:

   > - If any decision is `accept` or `modify`, a new version `vN`
   >   is cut.

   with:

   > - A new version `vN` is cut on every successful revise
   >   invocation (per §"Versioning"). When at least one decision
   >   is `accept` or `modify`, the working-spec files named in
   >   those decisions' `resulting_files[]` are updated in place
   >   before the snapshot. When every decision is `reject`, the
   >   new version's spec files are byte-identical copies of the
   >   prior version's spec files (preserving the audit trail per
   >   §"Versioning").

### D2 — Plan-text and housekeeping edits

**Surface in plan and PROPOSAL.**

1. PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md §"Version
   basis": preamble decision block gains a v038 entry
   (D1-D2 summary line).

2. PLAN §"Phase 0 step 1": byte-identity check reference
   bumps from `history/v037/` to `history/v038/` (and the
   nested narrative chain extends with the v038 substance
   line).

3. PLAN §"Phase 0 step 2": frozen-status header literal
   reference bumps from "Frozen at v037" to "Frozen at v038"
   (per the established no-op convention — see §"Implementation
   note" below).

4. PLAN §"Execution prompt": authoritative-version line
   bumps from "Treat PROPOSAL.md v037 as authoritative" to
   v038.

5. STATUS.md: refresh `last_updated` and `last_commit` after
   the v038 codification commit lands; brief mention of v038
   D1 in the Phase 7 sub-step 5.a halt-and-revise narrative.

**No companion-doc edits required** — the
`python-skill-script-style-requirements.md`, `NOTICES.md`,
`.vendor.jsonc`, and `pyproject.toml` don't reference the
version-cut rule.

**No follow-up implementation commit required** — the
Phase-3 minimum-viable `livespec/commands/revise.py` already
implements Statement B's semantic via `_process_decisions`
always invoking `_next_history_version_dir` regardless of
decision content. Phase 7 sub-step 5.c will widen the impl
under v038's now-canonical contract; the eventual widened
wrapper will continue to cut on non-empty processing, with
the `_bind_resulting_files` short-circuit naturally yielding
byte-identical-to-prior spec files on all-reject.

## Implementation note

The "Phase 0 step 2 frozen-status header bump" instruction
present in every revision file from v025 onward (and
re-stated here as v038 D2 item 3) refers to the LITERAL
text in the PLAN's Phase 0 step 2 description (which says
"`> **Status:** Frozen at vNNN`"), NOT to the actual
PROPOSAL.md `> **Status:** Frozen at v024.` line at
PROPOSAL.md:3. The PROPOSAL.md frozen-status header has
remained "Frozen at v024" across every snapshot
(`history/v024/PROPOSAL.md` through
`history/v037/PROPOSAL.md` all carry "Frozen at v024" at
line 3). Treating the header as marking "the version at
which the spec entered the frozen-evolution-via-
SPECIFICATION/ regime" (set once at v024; stable since)
is the established convention. v038 follows the same
convention — the PROPOSAL.md edit set above does NOT
include the header bump; only the PLAN's Phase 0 step 2
narrative reference is bumped.
