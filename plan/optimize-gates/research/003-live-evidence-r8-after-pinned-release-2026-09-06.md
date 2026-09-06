# 003 — R8 live evidence: raw worktree push with no bootstrap after the pinned release (2026-09-06)

Plan `optimize-gates`, epic `livespec-xms725`, child `livespec-lnt6mf` (R8).
Companion to `002-…` (the proof taken before the dev-tooling release carrying
R1–R3 existed). This note is written FROM the worktree it describes.

## Setup

- livespec master pinned to livespec-dev-tooling `v1.52.3` (bump PR #2607,
  merged 2026-09-06T11:24:57Z), the release line carrying the six dev-tooling
  children (R1 proof, R2, R3, R5, R6, R7).
- Worktree created with a RAW `git worktree add` — not `just worktree-create`
  — so no pack was provisioned and no `just bootstrap` ran:

```bash
mise exec -- git -C /data/projects/livespec worktree add -b docs/optimize-gates-r8-live-evidence \
  "$HOME/.worktrees/livespec/docs/optimize-gates-r8-live-evidence" master
```

At creation `dev-tooling/` did not exist in the worktree.

## Commit (pre-commit hook transcript)

_Filled in after the first commit._

## Push (pre-push gate transcript)

_Filled in after the first push._
