#!/bin/sh
# livespec commit-refuse hook — refuses commits/pushes at the primary checkout,
# and delegates to mise-managed lefthook everywhere else (v033 D5a Option-3
# + post-v095 commit-refuse mechanism).
#
# Two responsibilities, in order:
#
#   (1) Per `SPECIFICATION/non-functional-requirements.md` §"Primary-checkout
#       commit-refuse hook" and `SPECIFICATION/contracts.md`
#       §"`primary-checkout-commit-refuse-hook-installed`": at the primary
#       checkout, this hook MUST refuse commits/pushes and exit 1. The
#       canonical fingerprint substring `# livespec commit-refuse hook`,
#       the `git rev-parse --show-toplevel` invocation, and the `exit 1`
#       branch are all required for the dev-tooling check to recognize
#       the body. Refuse-at-primary is detected by comparing the
#       current toplevel to the configured `livespec.primaryPath`
#       (set during `just bootstrap`).
#
#   (2) On secondary worktrees (toplevel != primary path), delegate to
#       lefthook so the per-hook gates in `lefthook.yml` fire. The
#       lefthook-generated wrapper tries to find `lefthook` on PATH or
#       in node_modules; neither resolves for livespec's mise-pinned
#       setup unless mise activation has fired in the user's shell config.
#       Zsh sessions without a mise-activate line in `~/.zshrc` (e.g.,
#       Claude Code's default Bash tool) silently no-op the lefthook
#       hook with "Can't find lefthook in PATH", defeating the v033 D5a
#       per-commit gate. This wrapper bypasses the PATH search entirely
#       by invoking mise directly (mise itself resolves to
#       `/usr/bin/mise`, which is on every shell's default PATH).
#
# `--no-auto-install` is critical: without it, every `lefthook run` invocation
# attempts to "sync" `.git/hooks/<name>` against lefthook's own standard
# template, which (a) backs up our custom wrapper to `<name>.old` and (b)
# replaces the active hook with the PATH-searching standard wrapper that
# silently no-ops in Claude Code's bash. The auto-sync is fundamentally
# incompatible with our custom-wrapper design — its "fix" defeats the very
# purpose of this wrapper, AND it clobbers the commit-refuse hook body the
# `primary-checkout-commit-refuse-hook-installed` invariant requires.
# `--no-auto-install` disables the sync attempt.
#
# `just bootstrap` installs this same script as both `.git/hooks/pre-commit`
# and `.git/hooks/pre-push`; the basename of `$0` distinguishes which hook
# is firing so lefthook can dispatch the right command list from `lefthook.yml`.

primary_path="$(git config --get livespec.primaryPath || true)"
toplevel="$(git rev-parse --show-toplevel)"
if [ -n "$primary_path" ] && [ "$toplevel" = "$primary_path" ]; then
  echo "livespec: refusing commit/push at primary checkout ($toplevel); use a worktree" >&2
  exit 1
fi

HOOK_NAME="$(basename "$0")"
# git injects GIT_DIR=<worktree-gitdir> (plus GIT_INDEX_FILE/GIT_WORK_TREE/
# GIT_PREFIX) into the hook environment when a hook fires inside a worktree.
# lefthook run with that env set misreads the repo as bare and writes
# `core.bare=true` into the shared `.git/config`, corrupting every checkout
# that shares it (root cause li-iroguc). Clearing these vars makes lefthook
# detect the repo from the current working directory instead.
unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_PREFIX
exec mise exec lefthook -- lefthook run --no-auto-install "$HOOK_NAME" "$@"
