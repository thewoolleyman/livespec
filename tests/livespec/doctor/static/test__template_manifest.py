"""Tests for livespec.doctor.static._template_manifest.

The shared active-template manifest loader for the manifest-driven
static check `template_files_present`. The load-bearing properties:

- `is_main_spec_root` mirrors `run_static`'s tree enumeration
  (`<project_root>/SPECIFICATION` is the main tree);
- `load_active_template_spec_files` yields the `spec_files` dict
  for a resolvable schema-valid v2 template and `None` for v1
  templates AND for every resolution failure (degrade, never
  fail — config-validity failure modes are owned by
  `livespec_jsonc_valid` / `template_exists`).
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static._template_manifest import (
    is_main_spec_root,
    load_active_template_spec_files,
)
from livespec.schemas.dataclasses.template_config import SpecFileDecl
from returns.io import IOResult

__all__: list[str] = []


def test_is_main_spec_root_true_for_project_specification(*, tmp_path: Path) -> None:
    """`<project_root>/SPECIFICATION` is the main tree."""
    spec_root = tmp_path / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=tmp_path, spec_root=spec_root)
    assert is_main_spec_root(ctx=ctx) is True


def test_is_main_spec_root_false_for_sub_spec_tree(*, tmp_path: Path) -> None:
    """`<main>/templates/<name>/` sub-spec trees are not the main tree."""
    sub_spec_root = tmp_path / "SPECIFICATION" / "templates" / "livespec"
    sub_spec_root.mkdir(parents=True)
    ctx = DoctorContext(project_root=tmp_path, spec_root=sub_spec_root)
    assert is_main_spec_root(ctx=ctx) is False


def test_load_yields_none_when_livespec_jsonc_missing(*, tmp_path: Path) -> None:
    """No `.livespec.jsonc` → no manifest (degrade, never fail)."""
    result = load_active_template_spec_files(project_root=tmp_path)
    assert result == IOResult.from_value(None)


def test_load_yields_none_for_builtin_v1_template(*, tmp_path: Path) -> None:
    """The built-in `livespec` template is v1 → no manifest.

    Doubles as an integration assertion that built-in names resolve
    into the bundled `specification-templates/` tree.
    """
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": "livespec"}),
        encoding="utf-8",
    )
    result = load_active_template_spec_files(project_root=tmp_path)
    assert result == IOResult.from_value(None)


def test_load_yields_manifest_for_builtin_v2_template(*, tmp_path: Path) -> None:
    """The built-in `livespec-with-diagrams` template is v2 → markdown-only manifest dict.

    Pins the bundled Mermaid-first variant's six markdown spec
    files; livespec manages no diagram file kinds, so the manifest
    declares only `kind: markdown` entries.
    """
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": "livespec-with-diagrams"}),
        encoding="utf-8",
    )
    result = load_active_template_spec_files(project_root=tmp_path)
    expected: dict[str, SpecFileDecl] = {
        "spec.md": SpecFileDecl(kind="markdown"),
        "contracts.md": SpecFileDecl(kind="markdown"),
        "constraints.md": SpecFileDecl(kind="markdown"),
        "non-functional-requirements.md": SpecFileDecl(kind="markdown"),
        "scenarios.md": SpecFileDecl(kind="markdown"),
        "README.md": SpecFileDecl(kind="markdown"),
    }
    assert result == IOResult.from_value(expected)


def test_load_yields_manifest_for_custom_v2_template(*, tmp_path: Path) -> None:
    """A project-root-relative custom v2 template resolves to its manifest."""
    template_dir = tmp_path / "mytpl"
    template_dir.mkdir()
    _ = (template_dir / "template.json").write_text(
        json.dumps(
            {
                "template_format_version": 2,
                "spec_root": "SPECIFICATION/",
                "spec_files": {"spec.md": {"kind": "markdown"}},
            },
        ),
        encoding="utf-8",
    )
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": "mytpl"}),
        encoding="utf-8",
    )
    result = load_active_template_spec_files(project_root=tmp_path)
    expected: dict[str, SpecFileDecl] = {
        "spec.md": SpecFileDecl(kind="markdown"),
    }
    assert result == IOResult.from_value(expected)


def test_load_yields_none_when_template_value_unresolvable(*, tmp_path: Path) -> None:
    """An unknown template value degrades to no-manifest."""
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": "no/such/dir"}),
        encoding="utf-8",
    )
    result = load_active_template_spec_files(project_root=tmp_path)
    assert result == IOResult.from_value(None)


def test_load_yields_none_when_template_json_schema_invalid(*, tmp_path: Path) -> None:
    """A schema-invalid template.json degrades to no-manifest.

    (`template_exists` / template-version checks own the
    config-validity failure modes; the manifest consumers only need
    the binary "is a v2 manifest available" answer.)
    """
    template_dir = tmp_path / "mytpl"
    template_dir.mkdir()
    _ = (template_dir / "template.json").write_text(
        json.dumps({"template_format_version": 2}),  # v2 without spec_files: invalid
        encoding="utf-8",
    )
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": "mytpl"}),
        encoding="utf-8",
    )
    result = load_active_template_spec_files(project_root=tmp_path)
    assert result == IOResult.from_value(None)


def test_load_defaults_template_to_livespec_when_key_absent(*, tmp_path: Path) -> None:
    """A config without a `template` key defaults to the built-in v1 `livespec`."""
    _ = (tmp_path / ".livespec.jsonc").write_text("{}", encoding="utf-8")
    result = load_active_template_spec_files(project_root=tmp_path)
    assert result == IOResult.from_value(None)


def test_load_defaults_template_when_config_not_a_dict(*, tmp_path: Path) -> None:
    """A non-dict (but parseable) config defaults to the v1 `livespec` template."""
    _ = (tmp_path / ".livespec.jsonc").write_text("[]", encoding="utf-8")
    result = load_active_template_spec_files(project_root=tmp_path)
    assert result == IOResult.from_value(None)


def test_load_defaults_template_when_value_not_a_string(*, tmp_path: Path) -> None:
    """A non-string `template` value defaults to the v1 `livespec` template."""
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": 7}),
        encoding="utf-8",
    )
    result = load_active_template_spec_files(project_root=tmp_path)
    assert result == IOResult.from_value(None)
