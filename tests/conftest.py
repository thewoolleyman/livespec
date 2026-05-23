"""Repo-wide pytest conftest.

Currently carries ONE concern: scrubbing inherited `GIT_*` env vars
so test-level `subprocess.run(["git", ...], cwd=tmp_path)` invocations
target the test's tmp_path-local `.git/` instead of an outer repo's
index. The scrub matters when pytest itself runs inside a git hook
(e.g., `lefthook pre-commit` → `just check` → `pytest`), because git
hooks set `GIT_INDEX_FILE`, `GIT_DIR`, `GIT_WORK_TREE`, and friends
in the hook process's environment. Those env vars take precedence
over `cwd=`/`-C` flags when subprocess-inherited, so any test that
runs `git add` / `git commit` against tmp_path silently writes to the
outer worktree's index — yielding spurious "fixture commits" on the
developer's feature branch that get reset by the developer
manually. This autouse fixture removes the leak by deleting every
`GIT_*` env var for the duration of each test.

Scope: `autouse=True` applies to every test; this is intentional.
The cost (a dict-comprehension on `os.environ` per test) is trivial
and the alternative — opting in per-test or per-file — leaves the
trap armed for every new test that shells out to git. Production
code is unaffected; this fixture only mutates the test process's
env, not subprocess defaults outside pytest.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

__all__: list[str] = []


@pytest.fixture(autouse=True)
def _scrub_git_env_vars(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Scrub every `GIT_*` env var for the duration of each test.

    `monkeypatch.delenv(raising=False)` is idempotent — variables
    that don't exist are skipped — and `monkeypatch` restores the
    original environment when the test tears down.
    """
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    return
