"""Tests for dev-tooling/checks/schema_dataclass_pairing.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import schema_dataclass_pairing  # noqa: E402

__all__: list[str] = []


_LIVESPEC_PATH = Path(".claude-plugin/scripts/livespec")


def _make_repo(*, tmp_path: Path) -> Path:
    """Create the three-tree skeleton under tmp_path; return repo_root."""
    schemas_dir = tmp_path / _LIVESPEC_PATH / "schemas"
    dataclasses_dir = schemas_dir / "dataclasses"
    validate_dir = tmp_path / _LIVESPEC_PATH / "validate"
    schemas_dir.mkdir(parents=True)
    dataclasses_dir.mkdir()
    validate_dir.mkdir()
    return tmp_path


def _write_schema(*, repo: Path, name: str, content: str) -> None:
    (repo / _LIVESPEC_PATH / "schemas" / f"{name}.schema.json").write_text(
        content,
        encoding="utf-8",
    )


def _write_dataclass(*, repo: Path, name: str, content: str) -> None:
    (repo / _LIVESPEC_PATH / "schemas" / "dataclasses" / f"{name}.py").write_text(
        content,
        encoding="utf-8",
    )


def _write_validator(*, repo: Path, name: str, content: str = '"""stub"""\n') -> None:
    (repo / _LIVESPEC_PATH / "validate" / f"{name}.py").write_text(
        content,
        encoding="utf-8",
    )


_GOOD_SCHEMA = """{
  "$id": "thing.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["name"],
  "properties": {
    "name": {"type": "string"},
    "count": {"type": "integer"},
    "active": {"type": "boolean"},
    "items": {"type": "array", "items": {"type": "string"}}
  }
}"""

_GOOD_DATACLASS = '''"""docstring"""
from dataclasses import dataclass

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    name: str
    count: int
    active: bool
    items: list[str]
'''


def test_three_way_pairing_passes(*, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(repo=repo, name="thing", content=_GOOD_SCHEMA)
    _write_dataclass(repo=repo, name="thing", content=_GOOD_DATACLASS)
    _write_validator(repo=repo, name="thing")
    assert schema_dataclass_pairing.check_repo(repo_root=repo) == []


def test_missing_dataclass_fails(*, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(repo=repo, name="thing", content=_GOOD_SCHEMA)
    _write_validator(repo=repo, name="thing")
    violations = schema_dataclass_pairing.check_repo(repo_root=repo)
    assert any("schemas/dataclasses/thing.py" in v for v in violations)


def test_missing_validator_fails(*, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(repo=repo, name="thing", content=_GOOD_SCHEMA)
    _write_dataclass(repo=repo, name="thing", content=_GOOD_DATACLASS)
    violations = schema_dataclass_pairing.check_repo(repo_root=repo)
    assert any("validate/thing.py" in v for v in violations)


def test_missing_schema_fails(*, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path=tmp_path)
    _write_dataclass(repo=repo, name="thing", content=_GOOD_DATACLASS)
    _write_validator(repo=repo, name="thing")
    violations = schema_dataclass_pairing.check_repo(repo_root=repo)
    assert any("schemas/thing.schema.json" in v for v in violations)


def test_dataclass_field_missing_fails(*, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(repo=repo, name="thing", content=_GOOD_SCHEMA)
    _write_dataclass(
        repo=repo,
        name="thing",
        content='''"""d"""
from dataclasses import dataclass

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    name: str
    # `count`, `active`, `items` deliberately missing
''',
    )
    _write_validator(repo=repo, name="thing")
    violations = schema_dataclass_pairing.check_repo(repo_root=repo)
    assert any("lacks field `count`" in v for v in violations)
    assert any("lacks field `active`" in v for v in violations)
    assert any("lacks field `items`" in v for v in violations)


def test_schema_property_missing_fails(*, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(
        repo=repo,
        name="thing",
        content="""{
  "$id": "thing.schema.json",
  "type": "object",
  "properties": {"name": {"type": "string"}}
}""",
    )
    _write_dataclass(repo=repo, name="thing", content=_GOOD_DATACLASS)
    _write_validator(repo=repo, name="thing")
    violations = schema_dataclass_pairing.check_repo(repo_root=repo)
    assert any("schema lacks property `count`" in v for v in violations)


def test_type_mismatch_fails(*, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(
        repo=repo,
        name="thing",
        content="""{
  "$id": "thing.schema.json",
  "type": "object",
  "properties": {"name": {"type": "integer"}}
}""",
    )
    _write_dataclass(
        repo=repo,
        name="thing",
        content='''"""d"""
from dataclasses import dataclass

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    name: str
''',
    )
    _write_validator(repo=repo, name="thing")
    violations = schema_dataclass_pairing.check_repo(repo_root=repo)
    assert any("schema `integer` expects" in v for v in violations)


def test_newtype_string_alias_accepted(*, tmp_path: Path) -> None:
    """`TemplateName` (NewType-of-str from livespec.types) is accepted for `string`."""
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(
        repo=repo,
        name="thing",
        content="""{
  "$id": "thing.schema.json",
  "type": "object",
  "properties": {"template": {"type": "string"}}
}""",
    )
    _write_dataclass(
        repo=repo,
        name="thing",
        content='''"""d"""
from dataclasses import dataclass
from livespec.types import TemplateName

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    template: TemplateName
''',
    )
    _write_validator(repo=repo, name="thing")
    assert schema_dataclass_pairing.check_repo(repo_root=repo) == []


def test_local_string_literal_alias_accepted(*, tmp_path: Path) -> None:
    """A module-level `Status = Literal["a","b"]` alias is accepted for `string`."""
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(
        repo=repo,
        name="thing",
        content="""{
  "$id": "thing.schema.json",
  "type": "object",
  "properties": {"status": {"type": "string"}}
}""",
    )
    _write_dataclass(
        repo=repo,
        name="thing",
        content='''"""d"""
from dataclasses import dataclass
from typing import Literal

__all__: list[str] = ["Status", "Thing"]


Status = Literal["pass", "fail"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    status: Status
''',
    )
    _write_validator(repo=repo, name="thing")
    assert schema_dataclass_pairing.check_repo(repo_root=repo) == []


def test_optional_field_with_pipe_none(*, tmp_path: Path) -> None:
    """`field: str | None` is accepted for non-required string field."""
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(
        repo=repo,
        name="thing",
        content="""{
  "$id": "thing.schema.json",
  "type": "object",
  "properties": {"name": {"type": "string"}}
}""",
    )
    _write_dataclass(
        repo=repo,
        name="thing",
        content='''"""d"""
from dataclasses import dataclass

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    name: str | None
''',
    )
    _write_validator(repo=repo, name="thing")
    assert schema_dataclass_pairing.check_repo(repo_root=repo) == []


def test_array_requires_list_annotation(*, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path=tmp_path)
    _write_schema(
        repo=repo,
        name="thing",
        content="""{
  "$id": "thing.schema.json",
  "type": "object",
  "properties": {"items": {"type": "array"}}
}""",
    )
    _write_dataclass(
        repo=repo,
        name="thing",
        content='''"""d"""
from dataclasses import dataclass

__all__: list[str] = ["Thing"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Thing:
    items: tuple[str, ...]
''',
    )
    _write_validator(repo=repo, name="thing")
    violations = schema_dataclass_pairing.check_repo(repo_root=repo)
    assert any("expects `list[...]`" in v for v in violations)


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """The shipped schemas/ + dataclasses/ + validate/ trees are pair-aligned."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert schema_dataclass_pairing.main() == 0
