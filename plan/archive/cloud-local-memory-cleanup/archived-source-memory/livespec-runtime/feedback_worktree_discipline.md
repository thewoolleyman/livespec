---
name: feedback-worktree-discipline
description: "For every livespec-governed repo (livespec, livespec-runtime, livespec-impl-*, livespec-dev-tooling), every change MUST land via a git worktree → PR → merge → cleanup cycle. No direct edits to master, no leaving dirty state, no asking the user whether to commit."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d2e1550c-8a13-4b97-bd9c-90858a6bdab2
---

Every change to a livespec-governed repo MUST follow the worktree-PR-merge-cleanup discipline:

1. Create a fresh git worktree on a new branch (e.g., `git worktree add ../<repo>-<topic> -b <topic>` from master).
2. Do all the work inside that worktree.
3. Commit with conventional-commits subject; rebase-merge-only per the repo's own rules.
4. Push the branch and open a PR via `gh pr create`.
5. Merge the PR to master (rebase-merge).
6. Remove the worktree (`git worktree remove`) and prune the local branch only after the merge lands.

**Why:** The user pushed back hard when I asked "should I commit and push?" as if leaving an unresolved dirty state were a real option. Their words: "Why would I want you to leave a dirty, unresolved state? ... we really should do is start using a discipline of: every change happens on a work tree and the work tree gets successfully processed and cleaned up once the PR is successfully landed and merged to the main line branch."

The cleanup side of this is already codified in `livespec/SPECIFICATION/contracts.md` as the `no-stale-worktree` doctor invariant. The **prescriptive** side (every change MUST start on a worktree) is NOT codified anywhere as of 2026-05-25. The discipline is practiced — `~/.claude/projects/` shows multiple active livespec worktree shims — just nowhere written.

The fix lands as part of the upstream `livespec/SPECIFICATION/` propose-change pair (project-name-prefix rule + worktree-discipline rule); see [[project-livespec-version-prefix-and-worktree-rule]] once that PR merges.

**How to apply:** Whenever the user asks me to "fix", "land", "ship", "make the change", or invoke any livespec sub-command flow that produces edits, default to the worktree path without asking. Asking "should I commit?" is the failure mode this rule prevents. The only legitimate confirmation gates are scope (which proposals to include) and push-to-third-party-state (which is already on the harness's confirm-by-default list, and which the user authorized once for this session).

**Worktree path convention:** Per the user's "Create worktree on a new branch" answer earlier in the same conversation, use `../<repo>-<topic-slug>` for the worktree path. Topic slug matches the conventional-commits / livespec topic slug.
