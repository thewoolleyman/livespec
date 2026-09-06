# Live evidence: a raw `git worktree add` worktree commits and pushes with no bootstrap — 2026-09-06

Captured 2026-09-06 03:25–03:40 UTC in the livespec repo, after the three
PRs of child `livespec-igowet` landed on `master`: the proposed change
(#2579, amended in #2580), its v219 ratification (#2581), and the lefthook
implementation (#2582, commit `d6e3d6a8`). This note is itself the payload
of the proof: it was authored inside the worktree described below and is
the only tracked change that worktree carries. Every observation is read
from a command's output at the stated time; nothing is inferred.

## Setup — the exact trap the plan opened on

From the primary checkout, with the pack's `just worktree-create` recipe
deliberately NOT used:

```bash
mise exec -- git -C /data/projects/livespec worktree add -b probe/optimize-gates-raw-worktree \
  "$HOME/.worktrees/livespec/probe/optimize-gates-raw-worktree" master
# HEAD is now at d6e3d6a8 chore(hooks): run `just install-worktree-pack` first at pre-commit and pre-push; …
```

Observed immediately afterwards inside the new worktree:

- `dev-tooling/*.sh` and `dev-tooling/*.just`: zero files present — the pack
  is absent, exactly the `worktree_pack_absent` starting state that made
  the pre-push gate fail in the sessions this plan's first research note
  records.
- `.venv`: absent.
- `just bootstrap`: NOT run, before or after, at any point in this proof.

## What the proof asserts

1. `mise exec -- git commit` of this file succeeds: the commit-refuse hook
   body delegates to lefthook, whose first pre-commit command is now
   `00-install-worktree-pack`, so the pack exists before
   `03-check-pre-commit` runs.
2. `mise exec -- git push` succeeds through the detached gate runner: the
   first pre-push command installs (idempotently re-asserts) the pack, then
   `01-check-pre-push` runs the full aggregate, whose
   `check-primary-checkout-commit-refuse-hook-installed` member
   byte-verifies the pack and passes.
3. No `just bootstrap`, no `just install-worktree-pack` typed by hand.

The commit-hook and push-gate transcripts are journaled on the ledger item
`livespec-igowet` and in the plan epic `livespec-xms725` handoff, because a
note cannot contain the log of the commit and push that carry it.

## Boundary of this evidence

This proves the livespec repository's wiring (R1 for one member). It does
not prove the other nine members (child `livespec-ltthxr`), the central
row that keeps every member wired (`livespec-dev-tooling-lptplj`), or the
package-side proof test (`livespec-dev-tooling-tndwz5`). Those carry their
own evidence.

## Side observation for the package-side children

On every hook invocation in this session the installer logged
`installed canonical worktree-pack file` for all seven files even when the
installed bytes were already identical (for example on the implementation
branch's own commit, seconds after `just worktree-create` had provisioned
them). Either it rewrites unconditionally or it logs "installed" for a
no-op; `livespec-dev-tooling-tndwz5`'s acceptance already requires a
write-nothing-when-identical proof, and the log wording should follow it.
