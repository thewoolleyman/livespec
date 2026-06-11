---
topic: rename-impl-plaintext-examples-to-impl-git-jsonl
author: claude-fable-5
created_at: 2026-06-11T00:06:24Z
---

## Proposal: rename-impl-plaintext-examples-to-impl-git-jsonl

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The livespec-impl-plaintext sibling repo is renamed to livespec-impl-git-jsonl (W5 repo surgery, work-item livespec-p7az, per spec.md v105 §"Contract + reference implementations architecture"). Three live example mentions in non-functional-requirements.md still carry the old name: the impl-plugin naming-examples list, the architecture-summary.html tooling-name list, and the version-prefix example. Rename all three to livespec-impl-git-jsonl.

### Motivation

Keep live spec prose consistent with the renamed git-jsonl reference orchestrator repo; frozen history snapshots are deliberately untouched.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md: (1) in the sibling-repo-topology section's examples list, replace `livespec-impl-plaintext` with `livespec-impl-git-jsonl`; (2) in the research/workflow-processes artifact-separation rule, replace `livespec-impl-plaintext` with `livespec-impl-git-jsonl` in the tooling-specific name list; (3) in the version-prefix discipline examples, replace `livespec-impl-plaintext v0.x` with `livespec-impl-git-jsonl v0.x`. Pure mechanical rename; no heading changes.
