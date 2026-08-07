"""Mirror tests for `dev-tooling/reap_stale_worktrees_git.py`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "reap_stale_worktrees_git.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("reap_stale_worktrees_git", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _worktree(*, branch: str | None) -> object:
    module = _load_module()
    return module.GitWorktree(
        path=Path("/repo/wt"),
        head="aaaa",
        branch=branch,
        detached=branch is None,
        prunable_reason=None,
    )


def test_candidate_on_default_branch_matches_only_the_named_default() -> None:
    module = _load_module()
    assert (
        module._candidate_on_default_branch(  # noqa: SLF001
            candidate=_worktree(branch="master"), default_branch="master"
        )
        is True
    )
    assert (
        module._candidate_on_default_branch(  # noqa: SLF001
            candidate=_worktree(branch="feature"), default_branch="master"
        )
        is False
    )


def test_candidate_on_default_branch_never_matches_a_detached_worktree() -> None:
    """A detached worktree holds no named branch, so there is nothing to `branch -D`."""
    module = _load_module()
    assert (
        module._candidate_on_default_branch(  # noqa: SLF001
            candidate=_worktree(branch=None), default_branch="master"
        )
        is False
    )


def test_candidate_on_default_branch_matches_nothing_when_default_unresolved() -> None:
    """An unresolved default branch must not make every candidate look mainline."""
    module = _load_module()
    assert (
        module._candidate_on_default_branch(  # noqa: SLF001
            candidate=_worktree(branch="master"), default_branch=None
        )
        is False
    )


def test_module_carries_no_mutating_git_call() -> None:
    """This is the reaper's READ-ONLY side; the destructive calls stay in the parent.

    The split is only safe because everything here reads. If a `worktree
    remove` / `branch -D` / `prune` call ever migrates in, that reasoning
    silently stops holding — for a tool whose whole job is deleting
    branches and worktrees.
    """
    source = _SCRIPT.read_text(encoding="utf-8")
    for mutating in ('"worktree", "remove"', '"branch", "-D"', '"worktree", "prune"'):
        assert mutating not in source, (
            f"{mutating} is a MUTATING git call and belongs in the reaper's action "
            f"layer, not in its read-only query side"
        )


def test_module_is_a_leaf() -> None:
    """It must not import from its parent, or the two form an import cycle."""
    source = _SCRIPT.read_text(encoding="utf-8")
    assert "from reap_stale_worktrees import" not in source, (
        "the git-query module must not import from `reap_stale_worktrees`; the "
        "one-way dependency is what prevents an import cycle"
    )
