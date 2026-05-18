---
topic: cross-tree-revise-narration
author: claude-opus-4-7
created_at: 2026-05-18T09:50:59Z
---

## Proposal: Widen revise stale-pending-proposal narration to enumerate every spec tree

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md §"revise skill-prose responsibilities" currently scopes the stale-pending-proposal narration to `<spec-target>/proposed_changes/` only. Widen the rule so the skill prose MUST also surface, per spec tree, a one-line summary of any pending proposals in every OTHER tree (the main spec plus every `<main-spec-root>/templates/<name>/` sub-spec) — so the user sees the full pending state across all trees and is not silently blind to pending work in a sub-spec when invoking revise against the main spec (or vice versa). Other-tree lines are omitted when that tree has zero in-flight proposals.

### Motivation

The current single-tree narration is silent on pending work in other trees, which is an ambiguous/incomplete view of the project's revise queue. A real-session failure mode: invoking /livespec:revise against the main spec surfaced 2 pending main-spec proposals but did NOT mention that both templates/livespec/proposed_changes/ and templates/minimal/proposed_changes/ ALSO carried pending scrub-bootstrap-residue.md proposals plus an older claude-opus-4-7-critique.md each. The unclear pending-state across trees led to a duplicate-critique error during the post-step LLM-driven phase. The narration's purpose (pending-proposal-accumulation visibility) is undercut when sub-spec queues are silently invisible.

### Proposed Changes

Replace the existing single-clause stale-pending-proposal narration bullet in spec.md §"revise skill-prose responsibilities" with a two-clause rule: (a) preserve the current `<spec-target>/proposed_changes/` line and (b) add a per-tree summary of pending proposals in every OTHER spec tree in the project. Other-tree enumeration is determined by walking the main spec root (resolved from `.livespec.jsonc`) and listing `<main-spec-root>/templates/<name>/` for every sub-spec directory present. The narration MUST emit one informational line per OTHER tree that carries at least one in-flight proposal; trees with zero in-flight proposals MUST NOT be surfaced (no noise lines). All existing non-gating / non-blocking guarantees on the narration MUST be preserved. The concrete rewrite of the bullet is bundled into the same revise commit so the spec MUST land in one atomic vNNN cut. The companion `.claude-plugin/skills/revise/SKILL.md` Step 3 narration prose MUST be updated to match the new two-clause rule alongside the spec change (the SKILL.md update lands as a non-revise plugin-source edit in the same git commit, per the impl-tracks-spec convention).
