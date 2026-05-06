---
topic: live-spec-self-containment-purge-proposal-citations
author: livespec-bootstrap-phase13
created_at: 2026-05-06T18:50:20Z
---

## Proposal: live-spec-self-containment-purge-proposal-citations

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Strips every PROPOSAL.md citation pattern from the four live SPECIFICATION/ files. PROPOSAL.md is archived; the live spec IS the authoritative source per the LIVESPEC self-containment principle. Each citation was a vestigial Phase-6 seed / Phase-8 migration provenance breadcrumb that added no current information beyond what the surrounding spec body states.

### Motivation

Phase 13 — codify live-spec authority. The live SPECIFICATION/ tree must stand on its own; no production-permanent file may cite the archived PROPOSAL.md as the authority for any rule. This is the live-spec sub-step (Phase 13.2). Subsequent sub-steps purge the same citation pattern from impl, tests, skills, templates, and tooling.

### Proposed Changes

~21 distinct edits across 4 spec files:

**spec.md** (16 edits): drop parenthetical attributions like `(PROPOSAL.md §"X" lines N-M)` from §"Sub-command lifecycle" sub-paragraphs (orchestration, seed-exemption, critique-internal-delegation, revise-lifecycle, prune-history-lifecycle, pre-step-skip-control, version-directories-complete-exemption); drop `per PROPOSAL.md §...` trailing citations from §"Proposed-change and revision file formats" + §"Test-Driven Development discipline" + §"Definition of Done" + §"Self-application"; rewrite the §132 first sentence (which named PROPOSAL.md as the canonical reference) to recognize this section IS canonical; rewrite the Plan Phase 7 line 3383 inner reference to plain prose.

**contracts.md** (2 edits): drop `per PROPOSAL.md §"Wrapper CLI surface" lines 349-356` from §"Wrapper CLI surface"; drop `per PROPOSAL.md §"Exit code contract"` from §"Lifecycle exit-code table".

**constraints.md** (8 edits): rewrite §"Constraint scope" intro to drop Phase-6-seed historical pointer; drop trailing `See PROPOSAL.md §"Runtime dependencies" v025 D1` from §"Locked vendored libs"; rewrite §"Package layout" to drop the `maintained in PROPOSAL.md §"Skill layout inside the plugin"` redirection; drop `per PROPOSAL.md §"Wrapper shape"` from §"Shebang-wrapper contract"; rewrite §"File naming and invocation" hyphen-policy bullet to drop `in PROPOSAL.md prose`; drop `in PROPOSAL.md §"Canonical target list" and` from §"Enforcement suite"; drop `per PROPOSAL.md §"Coverage registry" (lines 3771-3813)` from §"Heading taxonomy"; rewrite §"Self-application bootstrap exception" to drop `per PROPOSAL.md §"Self-application" v018 Q2 / v019 Q1` + the stale `(this revision)` inner reference.

**scenarios.md** (1 edit): rewrite §intro to drop `the recovery paths from PROPOSAL.md §"seed", §"doctor", and §"Pruning history"` and re-anchor on the scenarios this file actually carries.

No new spec content added; every edit is removal or rephrase preserving substantive intent.
