"""Tests for livespec.io.git.

Per style doc §"Skill layout — `io/`": io/ is the
impure boundary; every operation that touches the git working
tree lives here under `@impure_safe` so the railway flows
through `IOResult`. The git facade exposes the typed primitive
that `livespec.commands.revise.main` (and `seed.main`'s revision-
auto-capture path) compose against to populate the
revision-file `author_human` field per PROPOSAL.md §"Revision
file format" and `revision_front_matter.schema.json`.

The seam is named `io.git.get_git_user` per PROPOSAL.md + `revision_front_matter.schema.json` description on
the `author_human` property. Cycle 5.c.1 lands the smallest
viable surface: a single `get_git_user` primitive that returns
`"Name <email>"` from local git config when both values are
set; later cycles (or consumer pressure) widen the unset/missing-
git fallbacks under a fully-typed Failure carrier.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from livespec.io import git as io_git
from returns.result import Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def _git_init_with_user(*, cwd: Path, name: str, email: str) -> None:
    """Initialize a git repo at `cwd` and set local user.name + user.email.

    Uses `--local` so the test never writes to the developer's
    global git config. Mirrors the fixture shape in
    `tests/dev-tooling/checks/test_commit_pairs_source_and_test.py`'s
    `_git` helper.
    """
    _ = subprocess.run(
        ["git", "init", "--quiet"],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "config", "--local", "user.name", name],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "config", "--local", "user.email", email],
        cwd=cwd,
        check=True,
    )


def test_get_git_user_returns_combined_name_and_email(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`get_git_user()` returns IOSuccess('Name <email>') when both values set.

    Smallest viable behavior: a fresh `git init` repo in
    `tmp_path` with local `user.name` and `user.email` set,
    monkeypatch cwd to that repo, call `get_git_user()`, assert
    the IOSuccess carrier holds the conventional Git author
    format `"Name <email>"` per PROPOSAL.md §"Revision file
    format". Drives the `livespec/io/git.py`
    module into existence (importing it fails at HEAD).

    Per the cwd-fallback isolation rule, monkeypatch.chdir is
    required to scope the git-config read to the test fixture
    repo and not the developer's surrounding repo.
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)

    result = io_git.get_git_user()
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == "Test User <test@example.com>"
        case _:
            raise AssertionError(
                f"expected IOSuccess('Test User <test@example.com>'), got {result!r}",
            )
