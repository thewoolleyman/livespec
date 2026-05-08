---
topic: minimal-prune-history-no-retention-horizon
author: claude-opus-4-7
created_at: 2026-05-08T17:47:15Z
---

## Proposal: Align minimal sub-spec prune-history scenario with actual mechanic

### Target specification files

- SPECIFICATION/templates/minimal/scenarios.md

### Summary

Rewrite the `## End-to-end prune-history no-op` scenario in the minimal sub-spec scenarios.md to match the actual prune-history API. The current scenario describes the no-op case but frames it through a non-existent `retention horizon 5` parameter. The actual prune-history wrapper has no retention-horizon flag — the no-op short-circuit fires when only v001/ exists OR the oldest surviving v-directory is already a PRUNED_HISTORY.json marker. Same root cause as the main-spec prune-history scenario alignment that landed in v055; refile of doctor-critique deferred sub-proposal #10.

### Motivation

Internal-contradiction finding originally surfaced by the doctor LLM-driven objective phase and deferred during the v055 livespec-doctor-critique modify-revise. The proposal predates v055 but its target — `templates/minimal/scenarios.md` — is in a different sub-spec tree from the main-spec revise that processed the doctor-critique batch, so it could not apply in that pass and needs its own per-sub-spec revise. The scenario MUST reflect the actual API: prune-history takes no retention-horizon argument; when only v001/ exists, the wrapper emits a structured `prune-history-no-op` finding and exits 0. The current scenario misleads readers about the API surface.

### Proposed Changes

The `## End-to-end prune-history no-op` section in `SPECIFICATION/templates/minimal/scenarios.md` MUST be rewritten. The current Feature line and Scenario MUST be replaced with:

```gherkin
Feature: e2e — prune-history short-circuits when there is nothing to prune

Scenario: Prune with only v001/ in history (no-op short-circuit)
  Given the fixture repo has history/v001/ only
  When the user invokes /livespec:prune-history
  Then the wrapper emits a single-finding JSON document with check_id 'prune-history-no-op' and status 'skipped'
  And the finding's message reads 'nothing to prune; oldest surviving history is already PRUNED_HISTORY.json or is the only version'
  And the wrapper exits 0
  And no version directories are removed
  And the post-step doctor static phase emits zero fail findings
```

The surrounding `## End-to-end prune-history no-op` heading MUST remain unchanged; the section's content MUST replace the existing Feature/Scenario block byte-for-byte except as described above. No retention-horizon flag MAY appear in the rewritten scenario — the actual mechanic is described in `SPECIFICATION/spec.md` §"Sub-command lifecycle" prune-history paragraph and `SPECIFICATION/contracts.md` §"Wrapper CLI surface"; both consistently describe a parameterless prune-history.
