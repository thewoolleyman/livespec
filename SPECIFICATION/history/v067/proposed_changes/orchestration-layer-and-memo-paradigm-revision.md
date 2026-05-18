---
proposal: orchestration-layer-and-memo-paradigm.md
decision: accept
revised_at: 2026-05-18T22:56:02Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

All three `## Proposal` sections in this proposed-change file land atomically per the user's session prompt directing acceptance of the entire file. Proposal 1 (Three-layer orchestration architecture) adds a new top-level §"Three-layer orchestration architecture" to spec.md between §"Sub-command lifecycle" and §"Versioning" — the placement the proposal text suggests — and adds a #### Project-local orchestration layer sub-section to non-functional-requirements.md §"Implementation plugin ecosystem". Proposal 2 (Layer 3 loop driver — required shape and discipline) nests as ##### Layer 3 loop driver — required shape and discipline under the new Project-local orchestration layer sub-section per its explicit cross-reference. Proposal 3 (Memo paradigm) adds three terms — Memo, Disposition (memo), Persistent Agent Knowledge — to spec.md §"Terminology" (placed adjacent to the existing Transient term they elaborate) and adds a ### Persistent Agent Knowledge realization sub-section to contracts.md §"Implementation-plugin contract — the 9-skill surface". The existing stub forward-reference in NFR §"Shared content provenance" that pointed at this propose-change cycle is updated to point at the now-extant §"Project-local orchestration layer" sub-section. tests/heading-coverage.json gains one TODO entry for the new H2 in spec.md.

## Resulting Changes

- spec.md
- non-functional-requirements.md
- contracts.md
- ../tests/heading-coverage.json
