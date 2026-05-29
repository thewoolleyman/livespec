#!/bin/sh
# git-hook-wrapper — dispatch to mise-managed lefthook (v033 D5a Option-3).
#
# The lefthook-generated pre-commit hook tries to find `lefthook` on PATH or
# in node_modules; neither resolves for livespec's mise-pinned setup unless
# mise activation has fired in the user's shell config. Zsh sessions without
# a mise-activate line in `~/.zshrc` (e.g., Claude Code's default Bash tool)
# silently no-op the lefthook hook with "Can't find lefthook in PATH",
# defeating the v033 D5a per-commit gate. This wrapper bypasses the PATH
# search entirely by invoking mise directly (mise itself resolves to
# `/usr/bin/mise`, which is on every shell's default PATH).
#
# `--no-auto-install` is critical: without it, every `lefthook run` invocation
# attempts to "sync" `.git/hooks/<name>` against lefthook's own standard
# template, which (a) backs up our custom wrapper to `<name>.old` and (b)
# replaces the active hook with the PATH-searching standard wrapper that
# silently no-ops in Claude Code's bash. The auto-sync is fundamentally
# incompatible with our custom-wrapper design — its "fix" defeats the very
# purpose of this wrapper. `--no-auto-install` disables the sync attempt,
# eliminating both the `sync hooks: ❌` warning noise and the clobber risk.
#
# `just bootstrap` installs this same script as both `.git/hooks/pre-commit`
# and `.git/hooks/pre-push`; the basename of `$0` distinguishes which hook
# is firing so lefthook can dispatch the right command list from `lefthook.yml`.
HOOK_NAME="$(basename "$0")"
# git injects GIT_DIR=<worktree-gitdir> (plus GIT_INDEX_FILE/GIT_WORK_TREE/
# GIT_PREFIX) into the hook environment when a hook fires inside a worktree.
# lefthook run with that env set misreads the repo as bare and writes
# `core.bare=true` into the shared `.git/config`, corrupting every checkout
# that shares it (root cause li-iroguc). Clearing these vars makes lefthook
# detect the repo from the current working directory instead.
unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_PREFIX
exec mise exec lefthook -- lefthook run --no-auto-install "$HOOK_NAME" "$@"
