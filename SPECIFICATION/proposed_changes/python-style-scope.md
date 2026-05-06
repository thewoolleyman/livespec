---
topic: python-style-scope
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T04:38:00Z
---

## Proposal: Migrate style-doc §"Scope" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

First cycle of the Plan Phase 8 item 2 per-section migration of `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md` into `SPECIFICATION/`. Lands the source doc's §"Scope" content (lines 43-71) as a new `## Constraint scope` section in `SPECIFICATION/constraints.md` (inserted after the intro paragraph, before `## Python runtime constraint`). Restructures the prose for BCP 14 normative language per `SPECIFICATION/constraints.md` §"BCP14 normative language". Also updates the file's intro paragraph: the Phase-6 deferral note ("...migrate via a Phase 8 propose-change cycle and are NOT seeded into this file") is rewritten to point at the in-progress Phase-8 item-2 migration.

### Motivation

Per Plan Phase 8 item 2 (`python-style-doc-into-constraints`), the source-doc §"Scope" content enumerates which Python code is governed by livespec's style rules and which code is exempt — a meta-rule that bounds the rest of constraints.md's reach. Codifying this scope in the spec target gives every subsequent migrated rule a clear domain of application: a future maintainer or doctor check can look up "do these rules apply to extension-author code?" by reading constraints.md alone, without consulting the brainstorming source doc.

This is the FIRST cycle of the per-section migration. The source-doc reading order is the chosen sequencing per Plan Phase 8 item 2 ("the executor selects a section ordering (e.g., source-doc reading order)"). Subsequent cycles will migrate the remaining 22 source-doc sections (`Non-interactive execution`, `Interpreter and Python version`, `Runtime dependencies`, …, `Non-goals`) per the same per-cycle pattern.

The plan also requires the FIRST cycle's revise body to acknowledge the deviation from `deferred-items.md` §`python-style-doc-into-constraints`'s "at seed time" guidance. The deferral was documented in Phase 6's seeded `SPECIFICATION/constraints.md` intro paragraph: the per-section split was preferred over a single 92KB seed-time migration to (a) keep the Phase-6 seed scope bounded and (b) preserve audit granularity per cycle (each section's revision is human-reviewable in isolation, and later need to revisit a particular style rule does not have to contend with a single 92KB historical revision). Subsequent cycles cross-reference this first cycle's revise body for the deviation rationale.

The destination is `SPECIFICATION/constraints.md` (not `spec.md`) per the Plan Phase 8 item 2 heuristic "destination heading taxonomy fits better": constraints.md is the file enumerating architecture-level constraints, and §"Scope" defines the domain over which those constraints apply — meta to the constraint enumeration itself, but firmly within the constraint-bounding genre.

### Proposed Changes

One atomic edit to **SPECIFICATION/constraints.md**:

1. **Update the file's intro paragraph (line 3).** Current:

   > This file enumerates the architecture-level constraints `livespec` MUST satisfy. Per the plan's Phase-6 scope guidance, only the constraints PROPOSAL.md states directly land here; the bulk of the python-skill-script style requirements migrate via a Phase 8 propose-change cycle and are NOT seeded into this file.

   Replace with:

   > This file enumerates the architecture-level constraints `livespec` MUST satisfy. The Phase-6 seed contained only constraints stated directly in PROPOSAL.md; the bulk of the python-skill-script style requirements migrate per-section via Phase-8 propose-change cycles per Plan Phase 8 item 2 (`python-style-doc-into-constraints`).

2. **Insert a new `## Constraint scope` section** after the intro paragraph and before `## Python runtime constraint`:

   > ## Constraint scope
   >
   > The constraints in this file MUST be satisfied by:
   >
   > - Every Python module bundled with the plugin under `.claude-plugin/scripts/livespec/**`.
   > - Every Python shebang-wrapper executable under `.claude-plugin/scripts/bin/*.py`, including the shared `_bootstrap.py` module.
   > - Every Python module or script under `<repo-root>/dev-tooling/**`.
   >
   > The constraints DO NOT apply to:
   >
   > - Vendored third-party code under `.claude-plugin/scripts/_vendor/**`. Vendored libs ship at pinned upstream versions per the v018 Q3 / v026 D1 vendoring procedure and are EXEMPT from livespec's own style rules.
   > - User-provided Python modules loaded via custom-template extension hooks (e.g., `template.json`'s `doctor_static_check_modules`). Extension code is the extension author's responsibility; livespec's enforcement suite MUST NOT scope to it. Extension authors MUST satisfy only the calling-API contract — the `TEMPLATE_CHECKS` export shape, the `CheckRunFn` signature, and the `Finding` payload shape, all defined inside `livespec/`. Inside an extension module, the author MAY use any library, architecture, and patterns of their choosing; livespec MUST NOT impose requirements beyond invocability per the contract.
   >
   > Tests under `<repo-root>/tests/` MUST comply unless a test explicitly exercises a non-conforming input, in which case the non-conformance MUST be declared in a docstring at the top of the fixture.
