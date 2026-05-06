---
proposal: file-lloc-soft-warn-release-gate.md
decision: accept
---

## Decision and Rationale

Accept as proposed. Closes the M3 soft-band drift loophole user-flagged 2026-05-03. Mirrors the existing check-no-todo-registry release-gate pattern: per-commit ergonomic (warning), tag-push enforcement (block). Implementation lands atomically per the v035 D5a / v033 D5b spec-then-implementation precedent.
