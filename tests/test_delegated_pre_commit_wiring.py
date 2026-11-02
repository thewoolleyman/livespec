"""Lockstep coverage for the delegated pre-commit aggregate wiring."""

from __future__ import annotations

import re
from pathlib import Path

from livespec_dev_tooling.config import load_delegated_pre_commit

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_JUSTFILE = _REPO_ROOT / "justfile"
_PRE_COMMIT_SCRIPT = _REPO_ROOT / "dev-tooling/check-pre-commit.sh"
_GATED_TREE_SCRIPT = _REPO_ROOT / "dev-tooling/check-pre-commit-gated-tree.sh"
_DELEGATE = "livespec_dev_tooling.pre_commit_delegate run"


def _recipe_body(*, name: str) -> list[str]:
    """Return the non-comment body of one root justfile recipe."""
    lines = _JUSTFILE.read_text(encoding="utf-8").splitlines()
    opener = re.compile(rf"^{re.escape(name)}\s*:")
    opens = [index for index, line in enumerate(lines) if opener.match(line) is not None]
    assert len(opens) == 1, f"expected exactly one {name} recipe, found {len(opens)}"
    start = opens[0] + 1
    ends = [
        index
        for index in range(start, len(lines))
        if lines[index].strip() and not lines[index][:1].isspace()
    ] + [len(lines)]
    return [
        line
        for line in lines[start : ends[0]]
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_repository_opts_in_to_delegated_pre_commit() -> None:
    """The shared client sees this repository's pre-commit opt-in."""
    assert load_delegated_pre_commit(repo_root=_REPO_ROOT) is True


def test_pre_commit_delegates_before_its_local_aggregate() -> None:
    """Only the delegate's local-fallback status may reach the local recipe."""
    body = _recipe_body(name="check-pre-commit")
    assert body == ["    bash dev-tooling/check-pre-commit.sh"]
    script = _PRE_COMMIT_SCRIPT.read_text(encoding="utf-8")
    assert _DELEGATE in script
    assert "exec just check-pre-commit-local" in script
    assert script.index(_DELEGATE) < script.index(
        "exec just check-pre-commit-local"
    ), "the shared delegate must run before the local aggregate can start"
    assert "75)" in script, "only the local-fallback status may continue locally"


def test_gated_tree_recipe_restores_the_staged_tree_before_local_gating() -> None:
    """The gate Job validates its temporary staged-tree commit without recursion."""
    body = _recipe_body(name="check-pre-commit-gated-tree")
    assert body == ["    bash dev-tooling/check-pre-commit-gated-tree.sh"]
    rendered = _GATED_TREE_SCRIPT.read_text(encoding="utf-8")
    assert "git rev-list --parents -n 1 HEAD" in rendered
    assert "git reset --soft 'HEAD^'" in rendered
    assert "git write-tree)" in rendered
    assert "LIVESPEC_GATE_CONTEXT=1 just check-pre-commit" in rendered
