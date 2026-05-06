---
topic: python-style-keyword-only-args
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T17:00:00Z
---

## Proposal: Migrate style-doc §"Keyword-only arguments" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 14 of Plan Phase 8 item 2. NEW `## Keyword-only arguments` section in `SPECIFICATION/constraints.md`, inserted before `## Heading taxonomy`. Source-doc lines 1562-1653: every def uses `*` separator, dataclass strict triple, exemptions (dunders, Exception.__init__, ROP-chain DSL callbacks, Protocol method definitions). New heading registered in `tests/heading-coverage.json`.
