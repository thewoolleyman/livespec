"""Top-level pytest conftest — autouse env scrubbing for inherited GIT_* vars.

When the test suite runs under a git pre-commit hook (lefthook),
git exports `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, etc.,
pointing at the surrounding repository's git directory. Tests that
invoke `subprocess.run(["git", ...], cwd=tmp_path)` without
explicitly scrubbing those env vars will silently operate on the
surrounding repo (because `git init` with `GIT_DIR` set
re-initializes the GIT_DIR target rather than the cwd, and
subsequent commits go to the surrounding repo's refs).

The autouse fixture below scrubs the inherited GIT_* vars from
`os.environ` for the duration of every test, so subprocess git
calls inherit a clean environment and operate on the
tmp_path-scoped `.git` they create themselves.

Per-test-file `_scrub_git_env` helpers (in many existing tests)
remain as documentation + defense-in-depth and continue to work
unchanged — `monkeypatch.delenv` is idempotent when the var has
already been removed by this fixture.
"""

from __future__ import annotations

import pytest

__all__: list[str] = []


_GIT_ENV_PASSTHROUGH_VARS: tuple[str, ...] = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_LITERAL_PATHSPECS",
    "GIT_PREFIX",
)


@pytest.fixture(autouse=True)
def _scrub_inherited_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove inherited GIT_* env vars for every test."""
    for var in _GIT_ENV_PASSTHROUGH_VARS:
        monkeypatch.delenv(var, raising=False)
