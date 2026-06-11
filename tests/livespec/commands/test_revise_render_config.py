"""Tests for livespec.commands._revise_render_config.

The config/manifest loaders the revise render lifecycle composes
against. The end-to-end render behavior is covered in
`test_revise_render.py`; these tests pin the loader's degrade
branches (unknown/non-string template values, non-dict configs,
built-in template resolution) directly.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.commands import _revise_render_config
from returns.io import IOResult

__all__: list[str] = []


def test_resolve_template_dir_maps_builtin_names_into_bundle(*, tmp_path: Path) -> None:
    """Built-in template names resolve into the bundled templates tree."""
    resolved = _revise_render_config._resolve_template_dir(  # noqa: SLF001
        template_value="livespec",
        project_root=tmp_path,
    )
    assert resolved is not None
    assert resolved.name == "livespec"
    assert resolved.parent.name == "specification-templates"
    assert (resolved / "template.json").is_file()


def test_resolve_template_dir_yields_none_for_unresolvable_value(*, tmp_path: Path) -> None:
    """A template value that is neither built-in nor an existing dir yields None."""
    resolved = _revise_render_config._resolve_template_dir(  # noqa: SLF001
        template_value="no/such/dir",
        project_root=tmp_path,
    )
    assert resolved is None


def test_load_spec_files_yields_none_for_builtin_v1_template(*, tmp_path: Path) -> None:
    """The built-in `livespec` template is v1 → no manifest."""
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": "livespec"}),
        encoding="utf-8",
    )
    result = _revise_render_config._load_spec_files(  # noqa: SLF001
        project_root=tmp_path,
    )
    assert result == IOResult.from_value(None)


def test_load_spec_files_yields_none_for_non_dict_config(*, tmp_path: Path) -> None:
    """A parseable non-dict config defaults to the v1 `livespec` template."""
    _ = (tmp_path / ".livespec.jsonc").write_text("[]", encoding="utf-8")
    result = _revise_render_config._load_spec_files(  # noqa: SLF001
        project_root=tmp_path,
    )
    assert result == IOResult.from_value(None)


def test_load_spec_files_yields_none_for_non_string_template_value(
    *,
    tmp_path: Path,
) -> None:
    """A non-string `template` value defaults to the v1 `livespec` template."""
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": 7}),
        encoding="utf-8",
    )
    result = _revise_render_config._load_spec_files(  # noqa: SLF001
        project_root=tmp_path,
    )
    assert result == IOResult.from_value(None)


def test_load_spec_files_yields_none_for_unresolvable_template(*, tmp_path: Path) -> None:
    """An unresolvable template value degrades to no-manifest."""
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"template": "no/such/dir"}),
        encoding="utf-8",
    )
    result = _revise_render_config._load_spec_files(  # noqa: SLF001
        project_root=tmp_path,
    )
    assert result == IOResult.from_value(None)


def test_load_spec_files_yields_none_when_config_missing(*, tmp_path: Path) -> None:
    """No `.livespec.jsonc` → the trailing lash degrades to no-manifest."""
    result = _revise_render_config._load_spec_files(  # noqa: SLF001
        project_root=tmp_path,
    )
    assert result == IOResult.from_value(None)
