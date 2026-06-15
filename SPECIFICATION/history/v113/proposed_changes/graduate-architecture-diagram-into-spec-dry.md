---
topic: graduate-architecture-diagram-into-spec-dry
author: livespec-zkmn-diagram-dry
created_at: 2026-06-15T03:53:25Z
---

## Proposal: Graduate the canonical architecture diagram into spec.md as a DRY single source

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify the canonical architecture diagram into the SPECIFICATION tree (W7/zkmn, Phase 6) without creating duplication. The Mermaid architecture diagram previously lived only in the repo-root README and spec.md merely referenced it; this moves the diagram itself into spec.md §"Contract + reference implementations architecture" → "Canonical architecture diagram" as a single-source fenced Mermaid block (matching the existing lifecycle diagram in §"Revision loop"). The repo README now references that block instead of embedding a copy, so the diagram has exactly one source of truth and cannot duplicate, rot, or drift.

### Motivation

Advance epic livespec-4moata W7 (zkmn) diagram-codification half. Per spec.md §"Template manifest", Mermaid is livespec's standard format and Mermaid diagrams are markdown content authored as fenced blocks inside kind:markdown spec files — requiring no manifest entry, render command, or paired rendered artifact. The architecture diagram was the lone canonical diagram living OUTSIDE the spec tree (in the repo README); the lifecycle diagram already lives in spec.md. User directive (2026-06-15): the diagram must be DRY — one source, no duplication/rot/drift. Graduating it into spec.md as the single source, with the README referencing it, satisfies both 'codify into the SPECIFICATION template' and DRY.

### Proposed Changes

Replace the "Canonical architecture diagram" paragraph in spec.md §"Contract + reference implementations architecture" so it (a) embeds the canonical Mermaid `flowchart TB` block inline as the single source of truth, (b) states the DRY invariant (exactly one copy; the repo README references this section rather than embedding its own), and (c) flips the prior forward-looking 'Phase 6 graduates the diagrams into the SPECIFICATION template / maintained in the README' language to present-tense done. No `## ` heading is added, renamed, or removed (the diagram lives under the existing §"Contract + reference implementations architecture" H2; "Canonical architecture diagram" is a bold lead-in, not a heading), so tests/heading-coverage.json is unaffected. The repo-root README.md change (remove the duplicate block, add a reference link) rides the same PR but is not a spec-target file.
