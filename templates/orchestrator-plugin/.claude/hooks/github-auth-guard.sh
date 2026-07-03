#!/bin/sh
# github-auth-guard — PreToolUse hook (Bash tool).
#
# Blocks bare `gh` / `git push` invocations that could fall through to an
# ambient human OAuth credential. Commands running under the project's
# configured credential wrapper or naming the App-token helper path are allowed.
# Registered in `.claude/settings.json` under `hooks.PreToolUse` with matcher
# `Bash`.
#
# Fail-open: if `python3` is absent, pass through (exit 0). All matching and
# decision logic lives in the paired `github_auth_guard.py`, kept importable so
# it is unit-testable without spawning a subprocess.
if ! command -v python3 >/dev/null 2>&1; then
    exit 0
fi
exec python3 "$(dirname "$0")/github_auth_guard.py"
