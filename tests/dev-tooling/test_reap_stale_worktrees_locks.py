"""Mirror tests for `dev-tooling/reap_stale_worktrees_locks.py`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "reap_stale_worktrees_locks.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("reap_stale_worktrees_locks", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_worktrees_handles_branch_lock_and_detached_records() -> None:
    module = _load_module()
    porcelain = (
        "worktree /repo/primary\n"
        "HEAD aaaa\n"
        "branch refs/heads/master\n"
        "\n"
        "worktree /repo/wt\n"
        "HEAD bbbb\n"
        "detached\n"
        "locked orchestration hold (pid 1234)\n"
    )

    primary, secondary = module._parse_worktrees(porcelain=porcelain)  # noqa: SLF001

    assert primary.path == "/repo/primary"
    assert primary.branch == "master"
    assert primary.is_primary is True
    assert primary.locked_reason is None
    assert secondary.path == "/repo/wt"
    assert secondary.branch is None
    assert secondary.is_primary is False
    assert secondary.locked_reason == "orchestration hold (pid 1234)"


def test_parse_locked_pid_extracts_pid_or_none() -> None:
    module = _load_module()

    assert module._parse_locked_pid(reason="held by dispatcher (pid 9876)") == 9876  # noqa: SLF001
    assert module._parse_locked_pid(reason="held without process token") is None  # noqa: SLF001
