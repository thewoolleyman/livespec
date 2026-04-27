"""Tests for dev-tooling/checks/check_tools.py.

The `test_main_passes_against_real_repo` pattern is intentionally
OMITTED — running `main()` from the test process exercises the
host environment (which may not have mise's pinned just/lefthook
on PATH or the exact pinned uv version). The check's correctness
is verified by the unit cases below + by `just check-tools`
running in CI / a fully-bootstrapped dev env.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import check_tools  # noqa: E402

__all__: list[str] = []


_GOOD_MISE = """[tools]
uv       = "0.5.20"
just     = "1.36.0"
lefthook = "1.10.10"
"""

_GOOD_PYPROJECT = """[project]
name = "x"

[dependency-groups]
dev = [
    "ruff==0.8.6",
    "pytest==8.3.4",
]
"""


def test_parse_mise_tools(*, tmp_path: Path) -> None:
    (tmp_path / ".mise.toml").write_text(_GOOD_MISE, encoding="utf-8")
    pins = check_tools._parse_mise_tools(  # noqa: SLF001
        path=tmp_path / ".mise.toml"
    )
    assert pins == {"uv": "0.5.20", "just": "1.36.0", "lefthook": "1.10.10"}


def test_parse_mise_missing_returns_none(*, tmp_path: Path) -> None:
    assert (
        check_tools._parse_mise_tools(  # noqa: SLF001
            path=tmp_path / "absent.toml"
        )
        is None
    )


def test_parse_mise_skips_other_sections(*, tmp_path: Path) -> None:
    """Lines under sections other than [tools] are ignored."""
    content = """[other]
something = "1.0"

[tools]
uv = "0.5.20"
"""
    (tmp_path / ".mise.toml").write_text(content, encoding="utf-8")
    pins = check_tools._parse_mise_tools(  # noqa: SLF001
        path=tmp_path / ".mise.toml"
    )
    assert pins == {"uv": "0.5.20"}


def test_parse_pyproject_dev_deps(*, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(_GOOD_PYPROJECT, encoding="utf-8")
    pins = check_tools._parse_pyproject_dev_deps(  # noqa: SLF001
        path=tmp_path / "pyproject.toml"
    )
    assert pins == {"ruff": "0.8.6", "pytest": "8.3.4"}


def test_parse_pyproject_missing_returns_none(*, tmp_path: Path) -> None:
    assert (
        check_tools._parse_pyproject_dev_deps(  # noqa: SLF001
            path=tmp_path / "absent.toml"
        )
        is None
    )


def test_parse_pyproject_skips_non_dev_dependency_groups(*, tmp_path: Path) -> None:
    """Other sections inside [dependency-groups] don't bleed in."""
    content = """[dependency-groups]
test = [
    "x==1.0",
]
dev = [
    "ruff==0.8.6",
]
"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    pins = check_tools._parse_pyproject_dev_deps(  # noqa: SLF001
        path=tmp_path / "pyproject.toml"
    )
    assert pins == {"ruff": "0.8.6"}


def test_check_repo_no_mise_fails(*, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(_GOOD_PYPROJECT, encoding="utf-8")
    violations = check_tools.check_repo(repo_root=tmp_path)
    assert any("[tools]" in v for v in violations)


def test_check_repo_no_pyproject_fails(*, tmp_path: Path) -> None:
    (tmp_path / ".mise.toml").write_text(_GOOD_MISE, encoding="utf-8")
    violations = check_tools.check_repo(repo_root=tmp_path)
    assert any("dependency-groups" in v for v in violations)
