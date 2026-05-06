---
proposal: python-style-package-layout.md
decision: accept
revised_at: 2026-05-06T08:03:08Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: Claude Opus 4.7 (1M context)
---

## Decision and Rationale

Accept as proposed. Cycle 5 of Plan Phase 8 item 2 per-section migration. New `## Package layout` section between `## Vendored-library discipline` and `## Pure / IO boundary`. Three ### sub-sections preserved: Dataclass authorship, Context dataclasses (verbatim code block), CLI argument parsing seam. Cross-references cycle 1 deviation rationale.

## Resulting Changes

- constraints.md
