"""PreToolUse beads-access guard — deny un-wrapped tenant tooling.

Shipped in the impl-plugin template's `.claude/hooks/` and registered as a
`PreToolUse` hook on the `Bash` tool in `.claude/settings.json`. It blocks a
bare `bd` / `dolt` / direct-tenant `mysql` invocation unless the command runs
under the governed project's configured credential-injection wrapper — the
`credential_wrapper` array declared in `$CLAUDE_PROJECT_DIR/.livespec.jsonc`
(its first token is the wrapper CLI). The conventional `with-<id>-env.sh` name
is recognized as a fallback default, so a repo with no `credential_wrapper`
configured (or an unreadable config) still passes the established wrapper.
This turns the silent "ran outside the wrapper -> tenant auth failure" footgun
into an actionable deny that names the wrapper.

`should_block` takes the governed project's directory explicitly, so it is
import-testable (no subprocess); `main` resolves it from `$CLAUDE_PROJECT_DIR`.
Fail-open: any malformed input, unreadable/absent config, or unexpected shape
is a silent pass-through — the hook only ever blocks on a POSITIVE match.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

__all__: list[str] = ["main", "should_block"]

_CONFIG_NAME = ".livespec.jsonc"

# Fallback default: the conventional per-project credential-injection wrapper
# name (`with-<id>-env.sh`). Recognized even when no `credential_wrapper` is
# configured, so the established naming convention keeps passing the guard.
_WRAPPER_RE = re.compile(r"with-[a-z0-9-]+-env\.sh")

_BD = re.compile(r"(?:^|[\s;&|()`$])bd(?:\s|$)")
_DOLT = re.compile(r"(?:^|[\s;&|()`$])dolt(?:\s|$)")
_MYSQL = re.compile(r"(?:^|[\s;&|()`$])mysql(?:\s|$)")
_TENANT_HINTS = ("3307", "127.0.0.1")

# Minimal stdlib JSONC scrub: keep string literals verbatim, drop `//` line and
# `/* */` block comments, then strip trailing commas — enough to hand the
# result to stdlib `json`. Mirrors the vendored `jsoncomment` shim the rest of
# the package uses, WITHOUT importing it: this hook ships standalone into an
# adopter's `.claude/hooks/`, where that vendored lib is absent.
_JSONC_TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/', re.DOTALL)
_TRAILING_COMMA_RE = re.compile(r",(?=\s*[}\]])")

_REASON = (
    "Blocked: direct beads/Dolt tenant access must run under your project's "
    "configured credential_wrapper (the `.livespec.jsonc` key naming your "
    "credential-injection CLI, e.g. `with-<project>-env.sh -- <command>`). An "
    "'Access denied' / 'no beads database found' failure means you are OUTSIDE "
    "the wrapper (the bare BEADS_DOLT_PASSWORD is absent) — never hand-hunt the "
    "secret or reach around the seam with raw mysql/dolt/sudo."
)


def _strip_jsonc_comments(*, text: str) -> str:
    """Return `text` with `//` and `/* */` comments removed and trailing commas
    dropped, leaving JSON that stdlib `json.loads` accepts. String literals are
    preserved verbatim, so a `//` inside a value is not mistaken for a comment.
    """
    without_comments = _JSONC_TOKEN_RE.sub(
        lambda match: match.group(0) if match.group(0).startswith('"') else "",
        text,
    )
    return _TRAILING_COMMA_RE.sub("", without_comments)


def _configured_wrapper_token(*, project_dir: str | None) -> str | None:
    """Return the first token of the governed project's `credential_wrapper`,
    or None when `project_dir` is unset, the config is absent/unreadable/
    malformed, or the first token is not a string. Fail-open: never raises.
    """
    if not project_dir:
        return None
    try:
        text = (Path(project_dir) / _CONFIG_NAME).read_text(encoding="utf-8")
        token = json.loads(_strip_jsonc_comments(text=text))["credential_wrapper"][0]
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        return None
    return token if isinstance(token, str) else None


def should_block(*, command: str, project_dir: str | None = None) -> bool:
    """Return True iff `command` is an un-wrapped tenant-tooling invocation.

    A command running under the governed project's configured
    `credential_wrapper` (its first token, read from
    `<project_dir>/.livespec.jsonc`, appears in the command) — or under the
    conventional `with-<id>-env.sh` fallback wrapper — is never blocked.
    Otherwise a bare `bd` or `dolt` word, or a `mysql` invocation aimed at the
    tenant endpoint (`127.0.0.1` / port `3307`), is blocked. Any config
    read/parse error falls back to the `with-<id>-env.sh` regex.
    """
    token = _configured_wrapper_token(project_dir=project_dir)
    if token and token in command:
        return False
    if _WRAPPER_RE.search(command):
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
    if not command or not should_block(
        command=command, project_dir=os.environ.get("CLAUDE_PROJECT_DIR")
    ):
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
