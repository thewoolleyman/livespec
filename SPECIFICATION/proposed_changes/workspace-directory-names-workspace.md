---
topic: workspace-directory-names-workspace
author: claude-opus-5-5
created_at: 2026-11-14T00:03:29Z
---

## Proposal: Name ~/workspace as the workspace directory in the worktree-root rule

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

§"Worktree root and mise trust" names the workspace directory as `/data/projects/<repo>`. Name it as `~/workspace/<repo>`, the canonical home of project clones on every host, and state that on a host whose data disk lives elsewhere `~/workspace` is a symlink to that location.

### Motivation

Maintainer ruling, 2026-11-14 (verbatim): "Fix this on all repos, everything should refer to $HOME/workspace as the place canonical project clones live, never in /data/projects, even if that's the rreal one workspace should always be syumlinked. Fix this across all livespec tenants." A seat on a host whose checkouts live in a real ~/workspace, where /data does not exist, followed the hard-coded path and failed. The rule (worktrees never sit as peers of the first-class clones) is unchanged; only the named directory changes.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Worktree root and mise trust", replace

```
NEVER as a peer of the first-class clones in the workspace directory (`/data/projects/<repo>`). The workspace directory therefore holds only original clones,
```

with

```
NEVER as a peer of the first-class clones in the workspace directory (`~/workspace/<repo>`). `~/workspace` is the canonical home of project clones on every host; on a host whose data disk lives elsewhere, `~/workspace` MUST be a symlink to that location rather than a different path. The workspace directory therefore holds only original clones,
```

The rest of the paragraph is unchanged.
