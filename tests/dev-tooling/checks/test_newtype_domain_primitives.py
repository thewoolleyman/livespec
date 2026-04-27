"""Tests for dev-tooling/checks/newtype_domain_primitives.py.

The `test_main_passes_against_real_repo` pattern (used by every
other check) is intentionally OMITTED here — the live livespec/
tree currently has 23 known-drift NewType violations across 9
files. The check correctly catches them; the cleanup is deferred
to a dedicated Phase-4-exit sub-step (recorded in
`bootstrap/decisions.md` at 2026-04-27T02:26:43Z with the full
list of file/field/expected-NewType triples). The check's
correctness is verified by the unit cases below.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import newtype_domain_primitives  # noqa: E402

__all__: list[str] = []


def _check(*, source: str, tmp_path: Path) -> list[str]:
    target = tmp_path / "module.py"
    target.write_text(source, encoding="utf-8")
    return newtype_domain_primitives.check_file(path=target)


def test_dataclass_field_with_newtype_passes(*, tmp_path: Path) -> None:
    source = '''"""docstring"""
from dataclasses import dataclass
from livespec.types import CheckId

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    check_id: CheckId
'''
    assert _check(source=source, tmp_path=tmp_path) == []


def test_dataclass_field_with_raw_str_fails(*, tmp_path: Path) -> None:
    source = '''"""docstring"""
from dataclasses import dataclass

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    check_id: str
'''
    violations = _check(source=source, tmp_path=tmp_path)
    assert len(violations) == 1
    assert "check_id" in violations[0]
    assert "CheckId" in violations[0]


def test_function_param_with_newtype_passes(*, tmp_path: Path) -> None:
    source = '''"""docstring"""
from livespec.types import RunId

__all__: list[str] = ["thing"]


def thing(*, run_id: RunId) -> None:
    return None
'''
    assert _check(source=source, tmp_path=tmp_path) == []


def test_function_param_with_raw_str_fails(*, tmp_path: Path) -> None:
    source = '''"""docstring"""
__all__: list[str] = ["thing"]


def thing(*, run_id: str) -> None:
    return None
'''
    violations = _check(source=source, tmp_path=tmp_path)
    assert len(violations) == 1
    assert "run_id" in violations[0]
    assert "RunId" in violations[0]


def test_unrelated_field_name_skipped(*, tmp_path: Path) -> None:
    """Fields whose name isn't in the L8 mapping are out of scope."""
    source = '''"""docstring"""
from dataclasses import dataclass

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    name: str
    count: int
'''
    assert _check(source=source, tmp_path=tmp_path) == []


def test_self_param_skipped(*, tmp_path: Path) -> None:
    """`self` and `cls` are skipped (no annotation typically)."""
    source = '''"""docstring"""
__all__: list[str] = ["Thing"]


class Thing:
    def go(self, *, name: str) -> None:
        return None
'''
    assert _check(source=source, tmp_path=tmp_path) == []


def test_optional_with_newtype_passes(*, tmp_path: Path) -> None:
    source = '''"""docstring"""
from dataclasses import dataclass
from livespec.types import Author

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    author_human: Author | None = None
'''
    assert _check(source=source, tmp_path=tmp_path) == []


def test_template_root_path_not_flagged(*, tmp_path: Path) -> None:
    """`template_root: Path` is the resolved directory, not the L8-mapped `template`."""
    source = '''"""docstring"""
from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    template_root: Path
'''
    assert _check(source=source, tmp_path=tmp_path) == []


def test_all_three_author_aliases_share_newtype(*, tmp_path: Path) -> None:
    """`author`, `author_human`, `author_llm` all map to `Author`."""
    source = '''"""docstring"""
from dataclasses import dataclass
from livespec.types import Author

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    author: Author
    author_human: Author
    author_llm: Author
'''
    assert _check(source=source, tmp_path=tmp_path) == []


def test_spec_root_expects_spec_root_newtype(*, tmp_path: Path) -> None:
    source = '''"""docstring"""
from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    spec_root: Path
'''
    violations = _check(source=source, tmp_path=tmp_path)
    assert len(violations) == 1
    assert "SpecRoot" in violations[0]
