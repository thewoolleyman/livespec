---
name: reference-livespec-repo-is-bare
description: "The upstream livespec repo at /data/projects/livespec has `core.bare = true` set, so `git pull --rebase` fails — use `git fetch origin master:master` to sync the local master ref instead. Worktree-add still works normally from a bare-flagged repo."
metadata: 
  node_type: memory
  type: reference
  originSessionId: b6d9f09d-5c02-4c32-b392-f81ccae805e1
---

The upstream livespec repository at `/data/projects/livespec/` has `core.bare = true` in its `.git/config`, even though a working tree exists alongside it. This is an intentional setup choice by the user.

Practical implications:

- `git -C /data/projects/livespec pull --rebase` fails with `fatal: this operation must be run in a work tree`.
- `git -C /data/projects/livespec status` works (reports the apparent working tree).
- `git -C /data/projects/livespec fetch --prune` works.
- **To sync local `master` to upstream**: use `git -C /data/projects/livespec fetch origin master:master` — fetch with an explicit refspec updates the bare ref directly.
- `git -C /data/projects/livespec worktree add -b <branch> <path> master` works normally — this is the established workflow for landing changes in livespec per [[feedback-worktree-discipline]].

The discipline `worktree → PR → merge → cleanup` from `feedback_worktree_discipline.md` applies the same way; only the post-merge "sync master" step changes shape.

`/data/projects/livespec-runtime` (the sibling library) is NOT bare and behaves normally.
