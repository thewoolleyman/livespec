"""PreToolUse beads-access guard — deny un-wrapped tenant tooling.

Shipped in the impl-plugin template's `.claude/hooks/` and registered as a
`PreToolUse` hook on the `Bash` tool in `.claude/settings.json`. It blocks a
bare `bd` / `dolt` / direct-tenant `mysql` invocation unless the command runs
under the family 1Password env wrapper (`with-livespec-env.sh`) — turning the
silent "ran outside the wrapper -> tenant auth failure" footgun into an
actionable deny that names the wrapper.

The matching `should_block` predicate is pure so it can be unit-tested by
import (no subprocess). Fail-open: any malformed input or unexpected shape is a
silent pass-through — the hook only ever blocks on a POSITIVE match.
"""

from __future__ import annotations

import json
import re
import sys

__all__: list[str] = ["main", "should_block"]

_WRAPPER = "with-livespec-env.sh"
_BD = re.compile(r"(?:^|[\s;&|()`$])bd(?:\s|$)")
_DOLT = re.compile(r"(?:^|[\s;&|()`$])dolt(?:\s|$)")
_MYSQL = re.compile(r"(?:^|[\s;&|()`$])mysql(?:\s|$)")
_TENANT_HINTS = ("3307", "127.0.0.1")

_REASON = (
    "Blocked: direct beads/Dolt tenant access must run under the family "
    "1Password env wrapper. Re-run as "
    "`/data/projects/1password-env-wrapper/with-livespec-env.sh -- <command>`. "
    "An 'Access denied' / 'no beads database found' failure means you are "
    "OUTSIDE the wrapper (the bare BEADS_DOLT_PASSWORD is absent) — never "
    "hand-hunt the secret or reach around the seam with raw mysql/dolt/sudo."
)


def should_block(*, command: str) -> bool:
    """Return True iff `command` is an un-wrapped tenant-tooling invocation.

    A command already running under the family env wrapper is never blocked.
    Otherwise a bare `bd` or `dolt` word, or a `mysql` invocation aimed at the
    tenant endpoint (`127.0.0.1` / port `3307`), is blocked.
    """
    if _WRAPPER in command:
        return False
    if _BD.search(command) or _DOLT.search(command):
        return True
    return bool(_MYSQL.search(command)) and any(hint in command for hint in _TENANT_HINTS)


def main() -> int:
    """Read the PreToolUse hook input on stdin; deny on a positive match.

    Always exits 0 (fail-open): a malformed payload, a non-Bash tool, or any
    unexpected shape is a silent pass-through.
    """
    try:
        payload = json.loads(sys.stdin.read())
    except (ValueError, TypeError):
        return 0
    command = _command_of(payload=payload)
    if not command or not should_block(command=command):
        return 0
    sys.stdout.write(
        json.dumps(
            {
                "decision": "block",
                "reason": _REASON,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _REASON,
                },
            }
        )
    )
    return 0


def _command_of(*, payload: object) -> str:
    """Extract `tool_input.command` from the hook payload, or empty string."""
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


if __name__ == "__main__":
    raise SystemExit(main())
