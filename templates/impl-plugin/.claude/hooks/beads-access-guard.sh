#!/bin/sh
# beads-access-guard — PreToolUse hook (Bash tool).
#
# Blocks a bare `bd` / `dolt` / direct-tenant `mysql` invocation unless the
# command runs under a recognized per-project env wrapper (`with-<id>-env.sh`).
# Registered in `.claude/settings.json` under `hooks.PreToolUse` with matcher
# `Bash`.
#
# Fail-open: if `python3` is absent, pass through (exit 0). All matching and
# decision logic lives in the paired `beads_access_guard.py`, kept importable
# so it is unit-testable without spawning a subprocess.
if ! command -v python3 >/dev/null 2>&1; then
    exit 0
fi
exec python3 "$(dirname "$0")/beads_access_guard.py"
