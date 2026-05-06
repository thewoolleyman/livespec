---
topic: companion-docs-lifecycle
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T19:00:00Z
---

## Proposal: Migrate companion docs lifecycle diagrams + terminology into `SPECIFICATION/spec.md`

### Target specification files

- SPECIFICATION/spec.md

### Summary

Phase 8 item 3 (companion-docs-mapping) — part C. Migrates four SUPERSEDED-by-section companion docs per PROPOSAL.md §"Companion documents and migration classes":

- `2026-04-19-nlspec-lifecycle-diagram.md` — Mermaid flowchart showing the seed→spec→implement→observe→propose→revise loop
- `2026-04-19-nlspec-lifecycle-diagram-detailed.md` — subordinate to above
- `2026-04-19-nlspec-lifecycle-legend.md` — legend for the diagram
- `2026-04-19-nlspec-terminology-and-structure-summary.md` — terminology rationale (why `spec.md`, why the loop model)

All four docs → NEW `## Lifecycle` section in spec.md, inserted before `## Prior Art`. New `## Lifecycle` heading registered in `tests/heading-coverage.json`.
