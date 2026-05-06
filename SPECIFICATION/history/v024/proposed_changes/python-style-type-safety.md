---
topic: python-style-type-safety
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T16:00:00Z
---

## Proposal: Migrate style-doc §"Type safety" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 9 of Plan Phase 8 item 2 per-section migration. EXPAND existing `## Typechecker constraints (Phase 1 pin)` (retain heading, replace 2-paragraph body with the merged content from source-doc lines 842-1103), adding six `###` sub-sections: `### @override and assert_never import source`, `### Module API surface`, `### Domain primitives via NewType`, `### Inheritance and structural typing`, `### Exhaustiveness`, `### Vendored-lib type-safety integration`. Also corrects the stale strict-plus diagnostic list (Phase 6 seed had the pre-v025-D1 list; style doc + pyproject.toml both carry the correct v025-D1 seven). BCP-14-restructured. Cross-references cycle 1 deviation rationale.

### Proposed Changes

One atomic edit to **SPECIFICATION/constraints.md**: replace the body of `## Typechecker constraints (Phase 1 pin)` (retain heading) with the merged content, terminating before `## File LLOC ceiling`.
