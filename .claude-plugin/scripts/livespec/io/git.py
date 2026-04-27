"""Git read-only operations (`@impure_safe`).

`livespec` is a strict reader of git state — never a writer. Every
function in this module wraps a single read-only `git` invocation
under `@impure_safe`.

Per PROPOSAL.md §"Git", v1 has exactly two documented git readers:

1. `doctor-out-of-band-edits` (uses `git show HEAD:` to detect
   committed-vs-history drift; lands at Phase 7).
2. `get_git_user()` — reads `user.name` and `user.email` from
   `git config` to populate `author_human` on auto-captured
   revisions for `revise` and `seed`.

Both observe the read-only contract: livespec never invokes `git
commit`, `git push`, `git tag`, or any tree-mutating operation.

The full per-edge-case semantics for `get_git_user()` are codified
in `deferred-items.md`'s `static-check-semantics` entry (`io/
git.get_git_user()` semantics); this module implements the
documented three-branch v1 contract.
"""

import subprocess
from pathlib import Path

from returns.io import impure_safe

from livespec.errors import GitUnavailableError

__all__: list[str] = [
    "GIT_USER_UNKNOWN",
    "get_git_user",
]


GIT_USER_UNKNOWN = "unknown"
"""Sentinel returned when git is present but `user.name` or
`user.email` is unset. The `revise` / `seed` wrappers proceed with
this anonymous attribution rather than aborting; the user can edit
the auto-captured revision afterward to attribute correctly."""


@impure_safe(exceptions=(GitUnavailableError,))
def get_git_user(*, project_root: Path | None = None) -> str:
    """Read `git config --get user.name` and `user.email`.

    Returns one of three values per PROPOSAL.md §"Git":

    - `"<name> <email>"` on full success (git binary present AND
      both config values set; the standard auto-capture path).
    - `GIT_USER_UNKNOWN` (`"unknown"`) when git is present but
      either `user.name` or `user.email` is unset. This is a domain
      fallback (continue the write with an anonymous attribution),
      NOT a failure.
    - `IOFailure(GitUnavailableError)` when the git binary is
      absent from PATH. This is a domain error (exit 3); the
      `revise` / `seed` supervisors pattern-match on it and direct
      the user to install git (or set `LIVESPEC_AUTHOR_LLM` and
      proceed if human attribution is not required).

    `project_root` is optional and defaults to the current working
    directory. Passing it explicitly makes the lookup deterministic
    when invoked from outside a worktree.
    """
    cwd = str(project_root) if project_root is not None else None
    try:
        name_proc = subprocess.run(  # noqa: S603 — argv is hard-coded; no untrusted input
            ["git", "config", "--get", "user.name"],  # noqa: S607 — PATH-based git lookup is the intended contract
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
        )
        email_proc = subprocess.run(  # noqa: S603 — argv is hard-coded; no untrusted input
            ["git", "config", "--get", "user.email"],  # noqa: S607 — PATH-based git lookup is the intended contract
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
        )
    except FileNotFoundError as e:
        raise GitUnavailableError(
            "git binary not found on PATH; install git or set LIVESPEC_AUTHOR_LLM",
        ) from e

    name = name_proc.stdout.strip()
    email = email_proc.stdout.strip()
    if not name or not email:
        return GIT_USER_UNKNOWN
    return f"{name} {email}"
