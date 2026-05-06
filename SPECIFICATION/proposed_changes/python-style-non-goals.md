---
topic: python-style-non-goals
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T18:30:00Z
---

## Proposal: Migrate style-doc §"Non-goals" into `SPECIFICATION/spec.md`

### Target specification files

- SPECIFICATION/spec.md

### Summary

Cycle 23 (final) of Plan Phase 8 item 2. EXPAND existing `## Non-goals` in `spec.md` by appending the Python-implementation non-goals from source-doc lines 2211-2231 (interactive CLI, Windows, async, performance tuning, runtime dependency resolution, LLM-from-Python, mypy, non-Python hooks, automated vendor-drift detection). These are complementary to the existing spec-level non-goals already in the section. No new `##` headings. This completes the 23-cycle python-style-doc migration.
