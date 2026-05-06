---
topic: python-style-purity-io
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T15:45:00Z
---

## Proposal: Migrate style-doc §"Purity and I/O isolation" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 8 of Plan Phase 8 item 2 per-section migration. EXPAND existing `## Pure / IO boundary` (retain heading, replace 2-paragraph body with the merged content from source-doc lines 698-838), adding `### Import-Linter contracts (minimum configuration)` sub-section including the illustrative TOML shape, the two authoritative rules, the raise-discipline retraction note, and the Phase 4 implementation overlay. BCP-14-restructured. Cross-references cycle 1 deviation rationale.

### Motivation

The existing `## Pure / IO boundary` stub (2 paragraphs) covers only the structural import direction and raise-site restriction at a high level. The style doc's §"Purity and I/O isolation" adds the detailed directory-based purity model (exact forbidden imports per layer), the validator-stays-pure-by-factory-shape rule, the Import-Linter contract shape, the two authoritative layered-architecture rules, and the Phase 4 implementation overlay (why `returns.io` and `pathlib` are absent from the realized `forbidden_modules` list). These are load-bearing constraints for anyone implementing or extending livespec modules.

### Proposed Changes

One atomic edit to **SPECIFICATION/constraints.md**: replace the body of `## Pure / IO boundary` (retain heading) with the merged content, terminating before `## ROP composition`.
