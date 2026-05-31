"""Shared sys.path setup + env scrubbing for tests/e2e-cli/.

Adds `tests/e2e-cli/` to `sys.path` so the consumer test module resolves
without per-module sys.path manipulation. Mirrors `tests/e2e/conftest.py`
per SPECIFICATION/contracts.md §"CLI end-to-end harness contract".

Also auto-scrubs inherited `GIT_*` environment variables (set by lefthook
when tests run as a pre-commit hook) so the harness's tmp-`HOME` /
tmp-`project_root` fixtures operate in isolation rather than leaking into
the surrounding repo's git state.

Honors `LIVESPEC_E2E_HARNESS=real` by auto-skipping every
`@pytest.mark.mock_only` test (per the contract: mock-only scenarios MUST
be skipped in real mode).
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
    """Auto-applied env scrub for every e2e-cli test."""
    for var in _GIT_ENV_PASSTHROUGH_VARS:
        monkeypatch.delenv(var, raising=False)
