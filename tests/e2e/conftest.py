"""Shared sys.path setup + env scrubbing for tests/e2e/.

Adds `tests/e2e/` to `sys.path` so test modules can `import fake_claude`
without per-module sys.path manipulation. Mirrors the tests/prompts/conftest.py
pattern per SPECIFICATION/contracts.md §"E2E harness contract".

Also auto-scrubs inherited `GIT_*` environment variables (set by lefthook
when tests run as a pre-commit hook) so the wrapper-chain's internal git
calls operate on the tmp_path fixture's `.git` directory rather than the
surrounding repo's. Without this scrub, e2e tests that invoke wrappers
running `git config --local core.bare true` would silently mutate the
surrounding repo's config or its working-tree commits.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

__all__: list[str] = []


sys.path.insert(0, str(Path(__file__).resolve().parent))


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
def _scrub_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-applied env scrub for every e2e test."""
    for var in _GIT_ENV_PASSTHROUGH_VARS:
        monkeypatch.delenv(var, raising=False)
