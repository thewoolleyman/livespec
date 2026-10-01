"""Tests for `dev-tooling/refresh_tenant_repos_report.py` — the preserved-repo report.

Pure string building, so every case runs with no git repository and no
process: the point under test is that a maintainer handed a refusal gets
the commands that actually apply to the state detected, with every path
and branch shell-quoted.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "refresh_tenant_repos_report.py"


def _load_module() -> ModuleType:
    """Import the report helper by file path (`dev-tooling/` is not a package)."""
    spec = importlib.util.spec_from_file_location("refresh_tenant_repos_report", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_a_repo_problem_carries_both_the_state_and_the_sentence() -> None:
    """The state selects the commands; the detail is what the maintainer reads."""
    module = _load_module()

    problem = module.RepoProblem(state=module.UNPUSHED, detail="two commits are local only")

    assert problem.state == "unpushed-commits"
    assert problem.detail == "two commits are local only"


def test_cleanup_commands_are_specific_to_the_detected_state(*, tmp_path: Path) -> None:
    """Three states a maintainer can clear locally, three distinct sequences.

    A single generic sequence would tell someone whose default branch has
    diverged to stash nothing, and someone holding unpushed commits to
    discard them.
    """
    module = _load_module()
    dest = tmp_path / "widget"

    uncommitted = module.cleanup_commands(
        dest=dest, default_branch="master", state=module.UNCOMMITTED
    )
    unpushed = module.cleanup_commands(dest=dest, default_branch="master", state=module.UNPUSHED)
    diverged = module.cleanup_commands(dest=dest, default_branch="master", state=module.DIVERGED)

    assert f"git -C {dest} stash push --include-untracked" in uncommitted
    assert f"git -C {dest} push origin HEAD" in unpushed
    assert f"git -C {dest} rebase origin/master" in diverged
    assert len({tuple(uncommitted), tuple(unpushed), tuple(diverged)}) == 3


def test_cleanup_commands_shell_quote_every_path_and_branch(*, tmp_path: Path) -> None:
    """A peer root or branch holding a space still yields a pasteable line."""
    module = _load_module()
    dest = tmp_path / "my repos" / "widget"

    commands = module.cleanup_commands(
        dest=dest, default_branch="release branch", state=module.DIVERGED
    )

    assert f"git -C '{dest}' status --short --branch" == commands[0]
    assert f"git -C '{dest}' rebase 'origin/release branch'" in commands


def test_cleanup_commands_show_what_a_repo_is_when_nothing_local_can_clear_it(
    *, tmp_path: Path
) -> None:
    """A foreign `origin` or an unresolved identity is not a stash-and-land case."""
    module = _load_module()
    dest = tmp_path / "widget"

    foreign = module.cleanup_commands(
        dest=dest, default_branch="master", state=module.IDENTITY_MISMATCH
    )
    unresolved = module.cleanup_commands(
        dest=dest, default_branch=None, state=module.IDENTITY_MISMATCH
    )

    assert foreign == [
        f"git -C {dest} status --short --branch",
        f"git -C {dest} remote --verbose",
    ]
    assert unresolved == foreign
