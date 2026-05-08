---
proposal: livespec-implementation-workflow.md
decision: reject
revised_at: 2026-05-08T03:42:41Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Filed before non-functional-requirements.md existed (2026-05-07T08:49:51Z, predates v009 sub-spec change at 2026-05-07T22:30:02Z and the v053 main-spec migration at 2026-05-08T03:17:18Z). The proposal's content — repo-local implementation workflow, beads task tracker, /livespec-implementation:* slash commands, implementation:* justfile namespace, hook chaining invariants, gap-tracking schema — is almost entirely contributor-facing and now belongs in non-functional-requirements.md under its 5-section mirror structure (Spec/Contracts/Constraints/Scenarios), NOT spread across spec.md/contracts.md/constraints.md/scenarios.md as the original proposal targeted. Three substantive concerns also need addressing in re-authoring: (1) the constraints.md section over-specifies setup-beads mechanism (0700 permissions, refs/dolt/data source preference, lock-file cleanup semantics, symlink-corruption detection, workspace identity mismatch detection, timestamped backup before rebuild) — these are implementation details for setup-beads.sh, not spec content (see the user's 'Specify architecture, not mechanism' principle); (2) ~25 inline Open Brain commit-pinned URLs in the proposed_changes prose belong in this propose-change file's audit trail but bleed inappropriately into final spec content if accepted as-is; (3) several restated invariants (no force-push, no --no-verify, no bulk staging, atomic commits) are redundant with existing constraints. A re-authored proposal targeting non-functional-requirements.md will land via /livespec:propose-change in this same revise cycle. Future re-proposal: see the new propose-change file co-authored alongside this rejection-revision.

## Rejection Notes

Rejection rationale captured in §"Decision and Rationale" above. Future re-proposal would need to address that critique.
