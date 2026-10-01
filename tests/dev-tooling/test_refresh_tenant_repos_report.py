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

import pytest

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


@pytest.mark.parametrize(
    ("marker", "operation"),
    [
        ("CHERRY_PICK_HEAD", "cherry-pick"),
        ("MERGE_HEAD", "merge"),
        ("REVERT_HEAD", "revert"),
        ("rebase-apply", "rebase"),
        ("rebase-merge", "rebase"),
    ],
)
def test_an_interrupted_operation_is_offered_a_labelled_choice_of_both_ways_out(
    *, tmp_path: Path, marker: str, operation: str
) -> None:
    """Which way out of a half-finished operation is the MAINTAINER's choice.

    Finishing it keeps the conflict resolution already done; abandoning it
    throws that away. A tool that picked one would be wrong half the time,
    so both are printed and the refresher runs neither — and the OUTPUT
    says in words that they are alternatives, because two adjacent commands
    with nothing between them read as a sequence, and running the abort
    after the continue destroys exactly the work the continue preserved.
    The commands are specific to the operation the marker names: a
    `merge --abort` does nothing for an interrupted cherry-pick.

    Each label is a `#` comment, so the list a maintainer pastes into a
    shell still runs only the command they chose.
    """
    module = _load_module()
    dest = tmp_path / "my repos" / "widget"

    assert "markers" in module.RepoProblem.__dataclass_fields__

    commands = module.cleanup_commands(
        dest=dest, default_branch="master", state=module.INTERRUPTED, markers=(marker,)
    )

    assert commands == [
        f"git -C '{dest}' status --short --branch",
        f"# CHOOSE ONE of the next two commands for the interrupted {operation}."
        " Do NOT run both:",
        "#   (1) finish it, keeping the conflict resolution already done:",
        f"git -C '{dest}' {operation} --continue",
        "#   (2) OR abandon it, discarding that work:",
        f"git -C '{dest}' {operation} --abort",
    ]


def test_an_interrupted_bisect_is_offered_its_one_way_out_rather_than_a_choice(
    *, tmp_path: Path
) -> None:
    """A bisect cannot be finished, so presenting a choice would be a lie."""
    module = _load_module()
    dest = tmp_path / "my repos" / "widget"

    commands = module.cleanup_commands(
        dest=dest, default_branch="master", state=module.INTERRUPTED, markers=("BISECT_LOG",)
    )

    assert commands == [
        f"git -C '{dest}' status --short --branch",
        "# the interrupted bisect cannot be finished. Ending it is the only way out:",
        f"git -C '{dest}' bisect reset",
    ]


def test_an_unrecognized_marker_is_reported_with_fewer_instructions_not_a_crash(
    *, tmp_path: Path
) -> None:
    """The markers come from one fixed set; drift must not break the report.

    This module and the git helper would have to disagree about that set
    for an unknown marker to arrive at all. If they ever do, the repo is
    still preserved and still reported — with the inspection line and
    nothing it cannot stand behind — rather than crashing the explanation
    of why it was preserved.
    """
    module = _load_module()
    dest = tmp_path / "widget"

    commands = module.cleanup_commands(
        dest=dest, default_branch="master", state=module.INTERRUPTED, markers=("UNHEARD_OF",)
    )

    assert commands == [f"git -C {dest} status --short --branch"]


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
