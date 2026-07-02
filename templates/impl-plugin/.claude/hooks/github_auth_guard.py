"""PreToolUse GitHub auth guard — deny ambient human-OAuth fallthrough.

Shipped in the impl-plugin template's `.claude/hooks/` and registered as a
`PreToolUse` hook on the `Bash` tool in `.claude/settings.json`. It blocks a
bare `gh` / `git push` invocation unless the command names the governed
project's configured credential-injection wrapper — the `credential_wrapper`
array declared in `$CLAUDE_PROJECT_DIR/.livespec.jsonc` (its first token is the
wrapper CLI) — the conventional `with-<id>-env.sh` fallback wrapper, or the
fleet App-token helper path.

This is defense-in-depth only: the real boundary is the host's per-tenant OS
identity. The hook turns the local "agent accidentally used the maintainer's
ambient `gho_` OAuth credential" failure mode into an actionable deny.

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
_APP_AUTH_HELPER_PATH = ".claude-plugin/scripts/bin/mint_app_token.py"

# Fallback default: the conventional per-project credential-injection wrapper
# name (`with-<id>-env.sh`). Recognized even when no `credential_wrapper` is
# configured, matching the Beads guard's repo-family convention.
_WRAPPER_RE = re.compile(r"with-[a-z0-9-]+-env\.sh")

_SHELL_SPLIT_RE = re.compile(r"[;&|]+")

# Minimal stdlib JSONC scrub: keep string literals verbatim, drop `//` line and
# `/* */` block comments, then strip trailing commas — enough to hand the
# result to stdlib `json`. Mirrors the vendored `jsoncomment` shim the rest of
# the package uses, WITHOUT importing it: this hook ships standalone into an
# adopter's `.claude/hooks/`, where that vendored lib is absent.
_JSONC_TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/', re.DOTALL)
_TRAILING_COMMA_RE = re.compile(r",(?=\s*[}\]])")

_REASON = (
    "Blocked: automated GitHub access must use the project App-token path, not "
    "ambient human OAuth (`gho_`). Run GitHub operations under your project's "
    "configured credential_wrapper and the App-token helper "
    "`.claude-plugin/scripts/bin/mint_app_token.py`; do not use bare `gh` or "
    "`git push` from agent context."
)


def _strip_jsonc_comments(*, text: str) -> str:
    """Return `text` with JSONC comments removed and trailing commas dropped."""
    without_comments = _JSONC_TOKEN_RE.sub(
        lambda match: match.group(0) if match.group(0).startswith('"') else "",
        text,
    )
    return _TRAILING_COMMA_RE.sub("", without_comments)


def _configured_wrapper_token(*, project_dir: str | None) -> str | None:
    """Return the first token of the governed project's `credential_wrapper`.

    Returns None when `project_dir` is unset, the config is absent/unreadable/
    malformed, or the first token is not a string. Fail-open: never raises.
    """
    if not project_dir:
        return None
    try:
        text = (Path(project_dir) / _CONFIG_NAME).read_text(encoding="utf-8")
        token = json.loads(_strip_jsonc_comments(text=text))["credential_wrapper"][0]
    except (OSError, ValueError, TypeError, KeyError, IndexError):  # pragma: no cover
        return None
    return token if isinstance(token, str) else None


def should_block(*, command: str, project_dir: str | None = None) -> bool:
    """Return True iff `command` is a bare GitHub-mutating invocation.

    A command that names the governed project's configured `credential_wrapper`,
    the conventional `with-<id>-env.sh` fallback wrapper, or the App-token helper
    path is allowed. Otherwise any `gh` command or `git push` segment is blocked
    because it could fall through to the ambient human OAuth credential.
    """
    token = _configured_wrapper_token(project_dir=project_dir)
    if token and token in command:
        return False
    if _WRAPPER_RE.search(command) or _APP_AUTH_HELPER_PATH in command:
        return False
    return any(_is_blocked_segment(segment=segment) for segment in _SHELL_SPLIT_RE.split(command))


def _is_blocked_segment(*, segment: str) -> bool:
    """Return True when one shell segment contains `gh` or `git ... push`."""
    words = re.findall(r"[A-Za-z0-9_./:-]+", segment)
    for index, word in enumerate(words):
        basename = word.rsplit("/", 1)[-1]
        if basename == "gh":
            return True
        if basename == "git" and "push" in words[index + 1 :]:
            return True
    return False


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
    if not isinstance(tool_input, dict):  # pragma: no cover
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


if __name__ == "__main__":
    raise SystemExit(main())
