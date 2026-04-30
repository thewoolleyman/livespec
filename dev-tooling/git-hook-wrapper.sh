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
# `just bootstrap` installs this same script as both `.git/hooks/pre-commit`
# and `.git/hooks/pre-push`; the basename of `$0` distinguishes which hook
# is firing so lefthook can dispatch the right command list from `lefthook.yml`.
HOOK_NAME="$(basename "$0")"
exec mise exec lefthook -- lefthook run "$HOOK_NAME" "$@"
