---
topic: companion-docs-prior-art-subdomains
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T18:50:00Z
---

## Proposal: Migrate companion docs prior-art.md + subdomains-and-unsolved-routing.md into `SPECIFICATION/spec.md`

### Target specification files

- SPECIFICATION/spec.md

### Summary

Phase 8 item 3 (companion-docs-mapping) — part A+B. Migrates two SUPERSEDED-by-section companion docs per PROPOSAL.md §"Companion documents and migration classes":

- `prior-art.md` (SUPERSEDED-by-section → `spec.md` "Prior Art" appendix): New `## Prior Art` section in spec.md summarizing the 22 annotated references that shaped the livespec model.
- `subdomains-and-unsolved-routing.md` (SUPERSEDED-by-section → `spec.md` "Non-goals" appendix): Brief `## Subdomain routing` non-goal note appended after `## Non-goals`.

Both companion docs remain archived in `brainstorming/approach-2-nlspec-based/` (frozen). `spec.md` becomes the authoritative reference for both topics in the living specification.

New `##` headings registered in `tests/heading-coverage.json`: `## Prior Art`, `## Subdomain routing`.
