"""livespec.io.git — git read-only primitives.

Pulled into existence under consumer pressure from
`livespec.commands.seed.main` at v032 TDD redo cycle 8: the seed
auto-captured `seed-revision.md` requires `author_human` populated
from `git config --get user.name` and `git config --get user.email`,
with the literal `"unknown"` fallback when either config value is
unset or git is unavailable. Per PROPOSAL.md §"Git" lines 685-711,
the canonical seam is `livespec.io.git.get_git_user() ->
IOResult[str, GitUnavailableError]`.

Cycle-8 smallest-thing-that-could-possibly-work: a single
collapsed-fallback function `current_user_or_unknown() -> str`
that returns `"<name> <email>"` on full success or `"unknown"` on
ANY non-success path (binary missing, config unset, subprocess
error). This collapses PROPOSAL's three-branch IOResult semantics
(`IOSuccess("<name> <email>")` / `IOSuccess("unknown")` /
`IOFailure(GitUnavailableError)`) into a string-returning shape
so the supervisor doesn't yet need to discriminate the
`GitUnavailableError` exit-3 path from the anonymous-attribution
path. Refactor to the full IOResult three-branch shape lands
when a failure-path test (e.g., the seed-aborts-when-git-unavailable
behavior at PROPOSAL.md line 705-708) forces the discrimination.

`subprocess` is permitted here per the architectural seam:
filesystem and subprocess effects live exclusively in
`livespec/io/**`. The cycle-2 `io.fs.write_text` is the
filesystem analog; this module is the git/subprocess analog.
"""

from __future__ import annotations

import subprocess

__all__: list[str] = ["current_user_or_unknown"]


def current_user_or_unknown() -> str:
    name = _git_config_value(key="user.name")
    email = _git_config_value(key="user.email")
    if name == "" or email == "":
        return "unknown"
    return f"{name} {email}"


def _git_config_value(*, key: str) -> str:
    try:
        # S603/S607: argv is a fixed list of literal strings; `key` comes from
        # in-package callers (literals like "user.name"); no shell, no untrusted input.
        result = subprocess.run(  # noqa: S603
            ["git", "config", "--get", key],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()
