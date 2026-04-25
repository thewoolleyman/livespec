# v022 — critique-fix overlay against v021

## Origin

Unlike v018-v021 (each authored via a formal critique pass with paired
`proposal-critique-vNN.md` and `proposal-critique-vNN-revision.md`
files), v022 lands as a direct critique-fix commit captured in the
git history at `2696248c26d173555458d6693eeb3b81d93d78ea`
(`Critique-fix proposal and bootstrap plan: prompt-reference-metadata
file class + 4 plan-level corrections.`). The commit message records
the five decisions and their motivations.

This file is the v022 archival record so that `history/v022/PROPOSAL.md`
has the standard accompanying `proposed_changes/` directory shape,
even though the underlying changes were not produced via the
critique-and-revise loop.

## Decisions captured in v022

1. **PROPOSAL §"Built-in template: `livespec`"** — names a new
   template-root file class **template-bundled prompt-reference
   materials**. The `livespec` template's `livespec-nlspec-spec.md`
   is the v1 instance: an LLM-time read-only rubric the template's
   prompts cite at runtime, with no skill-side parsing or behavioral
   contract. The class is structurally distinct from `template.json`,
   `prompts/`, and `specification-template/`. Files in this class
   are NOT sub-spec-governed and are NOT agent-regenerated in Phase 7
   of the bootstrap plan; their post-bootstrap evolution is via
   direct edit of the bundled file under ordinary PR review, exempt
   from the Plan §3 cutover-principle ban on hand-editing files
   under `.claude-plugin/specification-templates/<name>/`.

2. **PROPOSAL §"Template resolution contract — Deferred future
   feature"** — extends the new file class to custom templates:
   custom templates MAY ship analogous prompt-reference materials at
   their template root, governed identically (direct edit; no
   sub-spec coupling even when the custom template ships its own
   sub-spec).

3. **PROPOSAL §"Companion documents and migration classes" table
   row for `livespec-nlspec-spec.md`** — refined destination column
   and migration-class label to reflect the new class. Reclassified
   from `ARCHIVE-ONLY + TEMPLATE-BUNDLED` to
   `ARCHIVE-ONLY + TEMPLATE-BUNDLED-PROMPT-REFERENCE`. The
   destination column now spells out the post-bootstrap evolution
   path (direct edit at the bundled-file path under the
   prompt-reference-metadata carve-out; not sub-spec-governed; not
   Phase-7 agent-regenerated).

## Plan-level decisions paired with v022 (companion plan edits)

The bootstrap plan was edited in the same commit; the plan-level
decisions are companion to the v022 PROPOSAL changes:

- **Plan §3 cutover principle** — carves out the new file class
  from the hand-edit ban (matches PROPOSAL decisions 1-3 above).
- **Plan Phase 8 item 2** (`python-style-doc-into-constraints`) —
  rewrites the migration as one propose-change/revise per top-level
  source-doc section, matching the granularity Phase 8 item 3
  already uses for companion docs. Ends a single 92KB unreviewable
  revise risk.
- **Plan Phase 8 item 14** (`end-to-end-integration-test`) —
  replaces the one-line "see Phase 9" pointer with an explicit
  forward-pointing bookkeeping-closure mechanism: Phase 8 files a
  closure record; Phase 9 builds the harness as ordinary Phase 9
  work. Phase 8's exit criterion ("every deferred-item entry has a
  paired revision") is cleanly satisfiable without leaking the
  Phase 8/9 boundary.
- **Plan Phase 3 stub policy + Phase 7 work-item list** — switches
  from "stub the 4 deferred doctor-static checks as `skipped`
  findings" to "register only the 8 implemented checks at Phase 3;
  Phase 7 adds the remaining four to `static/__init__.py` alongside
  their implementations." Resolves the conflict between the
  `skipped`-status reservation (lines 749-753), the original stub
  policy (lines 770-776), and Phase 6's "all marked `pass`" exit
  criterion.
- **Plan Phase 7 ordering preamble** — promotes §6 Risk #5
  mitigation language into the work-item list: shared-dependency
  widening cycles before dependent regeneration; in-line catalogue
  widening per regen cycle; prompt-QA harness before any regen
  cycle that verifies via the harness.
- **Plan Phase 5 line 980 typo** — corrects "Phase 8" to "Phase 9"
  for the e2e-content fleshing reference (matches the Phase 8 item
  14 forward-pointing-closure decision).

## Why no formal critique-and-revise

The critique pass that surfaced these decisions was a one-off
discussion with the user; the decisions are uncontested and
narrow. Spinning up a full critique-and-revise paperwork cycle
would be ceremonial overhead disproportionate to the scope. The
disciplined version-snapshot lives at `history/v022/PROPOSAL.md`;
this file documents the decision provenance.
