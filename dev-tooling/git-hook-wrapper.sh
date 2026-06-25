#!/bin/sh
# livespec commit-refuse hook — refuses commits/pushes at the primary checkout,
# and delegates to mise-managed lefthook everywhere else.
#
# STRUCTURAL refuse (no livespec.primaryPath arming step): a primary checkout
# has `git rev-parse --git-dir` == `git rev-parse --git-common-dir`; a secondary
# worktree's git-dir is `.git/worktrees/<name>` while its git-common-dir is the
# primary's `.git`, so the two differ and the refuse branch is skipped. The hook
# is therefore ARMED ON INSTALL — there is no config key to set and so no
# fail-open window. This supersedes the livespec.primaryPath mechanism, which
# failed OPEN whenever its arming step was missed (the console-incident root
# cause: an installed-but-unarmed hook reads as protected but silently no-ops).
#
# SANDBOX EXEMPTION: a Fabro sandbox is a fresh FULL clone (structurally a
# primary) that legitimately commits during Red-Green-Replay. Its prepare step
# sets `git config livespec.sandboxExempt true`, an EXPLICIT, DECLARED marker
# this hook reads; with it set the refuse branch is skipped so in-sandbox
# commits proceed (and the lefthook delegation below still fires the RGR gates).
# This is the Exemption slot of the Conformance Pattern's concern #1
# Worktree-discipline (livespec core non-functional-requirements
# §"Conformance Pattern"): a variation point is a marker the hook reads, never
# an incidental fail-open side effect.
#
# The recognized canonical fingerprint (per livespec-dev-tooling's
# primary_checkout_commit_refuse_hook_installed check) is the marker comment
# `# livespec commit-refuse hook` + a `git rev-parse --git-common-dir`
# invocation + an `exit 1` branch. The fingerprint match is substring-based and
# tolerant of portable-shell rewrites; it also still accepts the legacy
# `git rev-parse --show-toplevel` body during the fleet migration.
#
# `--no-auto-install` is critical: lefthook's auto-sync would otherwise back up
# this canonical body to `<name>.old` and replace it with its PATH-searching
# standard wrapper (which silently no-ops in an off-PATH hook shell AND loses
# the refuse-at-primary branch). Disabling the sync attempt eliminates both the
# `sync hooks: ❌` warning noise and the clobber risk.

# git injects GIT_DIR=<gitdir> (plus GIT_INDEX_FILE/GIT_WORK_TREE/GIT_PREFIX)
# into the hook environment when a hook fires inside a worktree. Clear them
# FIRST so BOTH the structural primary detection below AND the lefthook
# delegation resolve the repo from the current working directory (the worktree
# root). Leaving GIT_DIR set also makes lefthook misread the repo as bare and
# write core.bare=true into the shared .git/config, corrupting every checkout
# that shares it (root cause li-iroguc).
unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_PREFIX

git_dir="$(git rev-parse --git-dir 2>/dev/null || true)"
common_dir="$(git rev-parse --git-common-dir 2>/dev/null || true)"
sandbox_exempt="$(git config --get livespec.sandboxExempt || true)"
if [ -n "$git_dir" ] && [ "$git_dir" = "$common_dir" ] && [ "$sandbox_exempt" != "true" ]; then
  echo "livespec: refusing commit/push at primary checkout; use a worktree" >&2
  exit 1
fi

# Delegate to lefthook at worktrees (and in declared-exempt sandboxes) so the
# repo's existing pre-commit / pre-push / commit-msg gates fire. The hook-name
# is derived from the basename of $0 so the same script serves every hook.
hook_name="$(basename "$0")"
exec mise exec -- lefthook run --no-auto-install "$hook_name" "$@"
