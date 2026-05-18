---
topic: claude-opus-4-7-critique
author: claude-opus-4-7
created_at: 2026-05-10T07:49:39Z
---

## Proposal: Drop literal-message duplication from prune-history no-op scenario

### Target specification files

- SPECIFICATION/templates/minimal/scenarios.md

### Summary

templates/minimal/scenarios.md §"End-to-end prune-history no-op" asserts that the wrapper's no-op finding `message` reads `"nothing to prune; oldest surviving history is already PRUNED_HISTORY.json or is the only version"`. The canonical no-op message is pinned in main `SPECIFICATION/constraints.md` §"`prune-history` file-shaping mechanics" as `"nothing to prune; oldest surviving history is already PRUNED_HISTORY.json"` (no trailing `or is the only version` clause). The two trees disagree on the exact message text. DRY the duplication: drop the literal-message assertion from the scenario; the `check_id` and `status` assertions already encode the load-bearing wire contract, and the message text belongs in main `constraints.md` as the single source of truth.

### Motivation

Two spec trees state the same wire-level message text inconsistently. The minimal sub-spec scenario adds a trailing `or is the only version` clause that the main constraint does not include; either the constraint is incomplete or the scenario is overspecified. The deeper problem is that the literal message string is duplicated across two files at all — DRY violation that makes future message edits silently inconsistent. The canonical fix is to drop the literal-message duplication from the scenario, since the `check_id` and `status` are the actual wire contract a downstream consumer would assert against; the message text is documentation that belongs only in main `constraints.md`.

### Proposed Changes

In `SPECIFICATION/templates/minimal/scenarios.md` §"End-to-end prune-history no-op", remove the line `And the finding's message reads 'nothing to prune; oldest surviving history is already PRUNED_HISTORY.json or is the only version'` from the Then-block. The remaining `check_id 'prune-history-no-op'` + `status 'skipped'` assertion is the load-bearing wire contract; the literal message text is documented in main `SPECIFICATION/constraints.md` §"`prune-history` file-shaping mechanics" and SHOULD NOT be duplicated here. The rest of the scenario (the Given, the When, the remaining Thens about exit code and history-version preservation) MUST be preserved unchanged.
