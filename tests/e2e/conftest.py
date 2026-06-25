"""Shared sys.path setup + env scrubbing for tests/e2e/.

Adds `tests/e2e/` to `sys.path` so test modules can `import fake_claude`,
`import real_claude`, and `import harness` without per-module sys.path
manipulation. Mirrors the tests/prompts/conftest.py pattern per
SPECIFICATION/contracts.md.

Also auto-scrubs inherited `GIT_*` environment variables (set by lefthook
when tests run as a pre-commit hook) so the wrapper-chain's internal git
calls operate on the tmp_path fixture's `.git` directory rather than the
surrounding repo's. Without this scrub, e2e tests that invoke wrappers
running `git config --local ...` would silently mutate the surrounding
repo's config or its working-tree commits.

Honors `LIVESPEC_E2E_HARNESS=real` by auto-skipping every `@pytest.mark.mock_only`
test (per the contract: mock-only scenarios MUST be skipped in real mode).
The `@pytest.mark.e2e_golden` marker selects the multi-turn flagship tests
that exercise the most user-dialogue surface; the `just` recipe drives
inclusion / exclusion explicitly per the Q2 hybrid prompt strategy.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from pathlib import Path

import pytest

__all__: list[str] = []


sys.path.insert(0, str(Path(__file__).resolve().parent))


# pytest invokes its hooks with positional args, so this hook is the lone
# exception to the keyword-only-args discipline in this file. The keyword-
# only style does not apply to third-party plugin hooks (see the
# keyword_only_args check's "hook" carve-out).
def pytest_collection_modifyitems(
    config: pytest.Config,
    items: Iterable[pytest.Item],
) -> None:
    """Auto-skip `mock_only` items when running the real harness tier."""
    _ = config
    harness = os.environ.get("LIVESPEC_E2E_HARNESS", "mock").strip().lower() or "mock"
    if harness != "real":
        return
    skip_marker = pytest.mark.skip(
        reason="mock_only test skipped under LIVESPEC_E2E_HARNESS=real",
    )
    for item in items:
        if item.get_closest_marker("mock_only") is not None:
            item.add_marker(skip_marker)


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
