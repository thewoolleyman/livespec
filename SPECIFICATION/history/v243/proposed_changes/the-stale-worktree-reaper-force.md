---
topic: the-stale-worktree-reaper-force
author: claude-opus-5-5
created_at: 2026-11-12T05:42:56Z
---

## Proposal: The stale-worktree reaper never force-removes a worktree with any change

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a paragraph to §"Worktree root and mise trust". A tool that reaps stale worktrees under the per-user root never removes a worktree whose `git status --porcelain` shows any tracked or untracked entry, whatever its detection seam returns. It logs and skips that worktree and goes on to the next candidate. A prunable candidate, whose working directory is already gone, is still pruned.

### Motivation

Implementation item livespec-inmgc7 (livespec tenant) is the consumer-side defence in depth for a data-loss hazard routed to the dev-host-disk-retention plan (livespec-dev-tooling-qgwxo4) by legacy-coordinator-agent on 2026-11-11. The dispatch-stage spec-change tier refused it on 2026-11-12 at 05:37:29Z (topic the-stale-worktree-reaper-force), because livespec's spec states no rule for the reaper.

- `dev-tooling/reap_stale_worktrees.py` removes every candidate it accepts with `git worktree remove --force`. It takes the candidates from `livespec_runtime.hygiene_scan.detect_stale_worktrees`.
- From livespec-runtime v0.22.3 (livespec-runtime-ciq) until v0.30.2, that detector also returned a landed worktree whose only dirt was untracked files. On such a runtime the reaper deleted authored untracked files. livespec#3168's CI proved it: `test_skips_dirty_worktree` failed at runtime v0.30.1.
- The runtime side is fixed: livespec-runtime-gyukpl, v0.30.2, with livespec-runtime spec v035/v036 stating the detector's removable set is only worktrees whose `git status --porcelain` is empty. But the reaper still trusts whatever the detector returns. A future detector regression would turn it back into a data-loss path, so the consumer needs its own rule.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Worktree root and mise trust", insert this paragraph directly after the section's first paragraph (the one beginning "Every git worktree lives under a single per-user root"):

> **A reaper never removes a changed worktree.** A tool that reaps stale worktrees, such as `dev-tooling/reap_stale_worktrees.py`, MUST NOT remove a worktree whose `git status --porcelain` shows any entry, tracked or untracked, whatever the detection seam it consumes returns. It MUST skip that worktree, log that the worktree has changes and was left, and continue with the next candidate. A prunable candidate, whose working directory is already gone, MUST still be pruned. The reaper's own guards are defence in depth: a regression in the detection seam MUST NOT be able to make the reaper delete authored or untracked work.
