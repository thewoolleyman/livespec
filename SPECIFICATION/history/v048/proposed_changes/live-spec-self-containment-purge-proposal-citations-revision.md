---
proposal: live-spec-self-containment-purge-proposal-citations.md
decision: accept
revised_at: 2026-05-06T18:50:39Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: livespec-bootstrap-phase13
---

## Decision and Rationale

Strip every PROPOSAL.md citation pattern from the four live spec files (spec.md, contracts.md, constraints.md, scenarios.md). PROPOSAL.md is archived; the live SPECIFICATION/ tree IS the authoritative source per the LIVESPEC self-containment principle. Each citation was a vestigial provenance breadcrumb pointing at the Phase-6 seed origin (or a Phase-8-migration source) and added no current information beyond what the surrounding spec body states directly. Edits cover ~21 distinct citation sites: parenthetical attributions like `(PROPOSAL.md §"X" lines N-M)`, trailing `per PROPOSAL.md §X` citations, the bootstrap-exception section's stale `(this revision)` self-reference, and the §132 first-sentence redirection that named PROPOSAL.md as canonical (now corrected — the live spec IS canonical).

## Resulting Changes

- spec.md
- contracts.md
- constraints.md
- scenarios.md
