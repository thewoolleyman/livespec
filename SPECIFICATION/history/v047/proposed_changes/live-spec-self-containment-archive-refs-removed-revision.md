---
proposal: live-spec-self-containment-archive-refs-removed.md
decision: accept
revised_at: 2026-05-06T18:27:09Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: livespec-bootstrap-phase12
---

## Decision and Rationale

Removes the six brainstorming/bootstrap path references from the live SPECIFICATION/ tree (5 in spec.md, 1 in constraints.md). The spec body has been self-contained since the Phase 8 migration; the remaining external pointers were vestigial provenance breadcrumbs from the Phase 6 seed and the bootstrap-window carve-out. After Phase 12 archives bootstrap/ + brainstorming/, those paths no longer exist at repo root, and the live spec must stand on its own per the LIVESPEC self-containment principle. Each removed reference had its substantive content already captured in adjacent spec prose (non-goals enumeration, lifecycle diagram, prior-art citations, subdomain-routing conclusion); this revise drops the external pointers without losing intent.

## Resulting Changes

- spec.md
- constraints.md
