---
topic: python-style-complexity-thresholds
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T17:15:00Z
---

## Proposal: Migrate style-doc §"Complexity thresholds" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 16 of Plan Phase 8 item 2. RENAME `## File LLOC ceiling` → `## Complexity thresholds` and EXPAND body with the full set of thresholds from source-doc lines 1717-1740: cyclomatic complexity ≤10 (ruff C901), function body ≤30 logical lines (ruff PLR0915), file ≤200/250 LLOC (existing content retained), nesting depth ≤4 (ruff PLR), arguments ≤6 counted two ways (ruff PLR0913 + PLR0917), no waivers. The heading rename requires updating the `tests/heading-coverage.json` entry.
