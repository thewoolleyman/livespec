#!/usr/bin/env bash
# refuse-primary-commit.sh — refuse a `git commit` made on the PRIMARY checkout.
#
# Generated from livespec/templates/impl-plugin/dev-tooling/refuse-primary-commit.sh
# at copier-copy time; re-sync via `copier update --vcs-ref=master` when
# livespec publishes a new release.
#
# Mechanical enforcement of the worktree-only repository mutation protocol
# (see AGENTS.md §"Repository mutation protocol"): every change to a tracked
# file happens in an ISOLATED worktree under ~/.worktrees/<repo>/<branch>,
# NEVER on the shared primary checkout. Multiple agent sessions share the one
# primary working tree; committing directly on it causes the cross-track
# collisions, orphaned worktrees, and detached-HEAD incidents this discipline
# exists to prevent.
#
# Wired (see lefthook.yml) as BOTH the first pre-commit job AND a commit-msg
# backstop. The commit-msg copy catches `git commit --allow-empty`, which
# lefthook v2 skips at pre-commit (it skips pre-commit jobs when there are
# zero staged files). It runs in BOTH the primary and linked worktrees
# because git worktrees share the common .git/hooks; it distinguishes them
# with PORTABLE, CONFIG-FREE detection:
#   - PRIMARY checkout: `git rev-parse --git-common-dir` and `--git-dir`
#     resolve to the SAME path -> REFUSE.
#   - linked worktree: they DIFFER (git-dir is <primary>/.git/worktrees/<n>)
#     -> ALLOW.
# This is the same test worktree-lib.sh uses, so the gate and the lifecycle
# helpers always agree on what "primary" means — and it needs no `git config`
# key, working in every clone identically.
#
# Escape, in order of preference:
#   1. Do the change in a worktree (the intended path; see AGENTS.md and
#      dev-tooling/worktree-lib.sh).
#   2. Operator-only emergency: `git commit --no-verify` (agents MUST NOT use
#      this without explicit operator permission).

set -euo pipefail

common_dir="$(git rev-parse --git-common-dir)"
git_dir="$(git rev-parse --git-dir)"

# Normalize via `cd … && pwd -P` so a relative `.git` and an absolute path
# compare correctly (mirrors dev-tooling/worktree-lib.sh).
common_dir_abs="$(cd "$common_dir" && pwd -P)"
git_dir_abs="$(cd "$git_dir" && pwd -P)"

if [ "$common_dir_abs" != "$git_dir_abs" ]; then
    # Linked worktree — committing here is the blessed path.
    exit 0
fi

toplevel="$(git rev-parse --show-toplevel)"
repo="$(basename "$toplevel")"

cat >&2 <<EOF
refuse-primary-commit: BLOCKED — committing on the PRIMARY checkout is forbidden.

  primary: $toplevel

Multiple agent sessions share this one working tree; committing directly on
it causes cross-track collisions, orphaned worktrees, and detached-HEAD
incidents. Do the change in an isolated worktree instead:

  ./dev-tooling/worktree-lib.sh create <branch>
  cd ~/.worktrees/$repo/<branch>
  # ...edit + commit here, then land via this repo's chosen path:
  ./dev-tooling/worktree-lib.sh land

Full protocol: AGENTS.md §"Repository mutation protocol".
(Operator emergency override only: git commit --no-verify.)
EOF
exit 1
