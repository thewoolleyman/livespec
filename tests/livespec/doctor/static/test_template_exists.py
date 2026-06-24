"""Tests for livespec.doctor.static.template_exists.

The check asserts that the project's `.livespec.jsonc` `template`
field resolves to a known template — either a built-in template name
(one of {`livespec`, `livespec-with-diagrams`, `minimal`}) or a
path-as-string to a custom template directory present on disk
relative to the project root and carrying `template.json`. Resolution
is delegated to the shared `livespec.templates.resolve_template_value`,
so these tests exercise both resolution outcomes through the doctor's
pass/fail `Finding` surface:

- pass: a built-in name (`livespec`, `livespec-with-diagrams`) and a
  valid custom template path;
- fail: an unknown name (no on-disk directory) and a custom path whose
  directory exists but lacks `template.json`.

The `livespec-with-diagrams` and custom-path pass arms are the
livespec-kfjd regression coverage — before the shared resolver,
`template_exists` rejected both.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import template_exists
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def test_template_exists_run_returns_pass_for_builtin_template(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when template is a builtin name.

    Seeds a project root with a `.livespec.jsonc` declaring
    `template: "livespec"` — a built-in template per
    livespec_config.schema.json's `template` field default.
    Asserts the check yields a pass-status Finding with the
    canonical `doctor-template-exists` check_id.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = '{\n  "template": "livespec"\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-template-exists",
        status="pass",
        message="template resolves to a known builtin or existing path",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert template_exists.run(ctx=ctx) == IOSuccess(expected)


def test_template_exists_run_returns_fail_for_unknown_name(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for an unknown non-path name.

    Drives the unknown-template-name failure arm: when the
    config's `template` is a bare string that is neither a
    member of the built-in allowlist nor an on-disk relative
    path, the check yields a fail-status Finding naming the
    offending value. The string `unknown-template` is chosen
    because it has no path separator (so the on-disk branch
    cannot rescue it) and no match against the built-in set.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = '{\n  "template": "unknown-template"\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-template-exists",
        status="fail",
        message="template 'unknown-template' is neither a builtin nor an existing path",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert template_exists.run(ctx=ctx) == IOSuccess(expected)


def test_template_exists_run_returns_pass_for_builtin_livespec_with_diagrams(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) passes for the `livespec-with-diagrams` built-in (livespec-kfjd).

    Before the shared resolver, `template_exists` recognized only
    `{livespec, minimal}` and emitted a fail-Finding for
    `livespec-with-diagrams` even though `resolve_template` accepted
    it — blocking the entire `/livespec:*` lifecycle for any project
    on that builtin. This pins the now-passing arm.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = '{\n  "template": "livespec-with-diagrams"\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-template-exists",
        status="pass",
        message="template resolves to a known builtin or existing path",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert template_exists.run(ctx=ctx) == IOSuccess(expected)


def test_template_exists_run_returns_pass_for_valid_custom_template_path(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) passes for a project-relative custom template dir (livespec-kfjd).

    The custom-template on-disk path-resolution branch was never
    implemented in `template_exists`; a `template` value naming a
    project-relative directory that exists and carries `template.json`
    now resolves and yields a pass-Finding (matching `resolve_template`).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    template_dir = project_root / "my-template"
    template_dir.mkdir()
    _ = (template_dir / "template.json").write_text("{}", encoding="utf-8")
    config_text = '{\n  "template": "my-template"\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-template-exists",
        status="pass",
        message="template resolves to a known builtin or existing path",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert template_exists.run(ctx=ctx) == IOSuccess(expected)


def test_template_exists_run_returns_fail_for_custom_path_missing_template_json(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) fails for a custom path whose dir lacks `template.json`.

    The directory exists relative to the project root, but it is not a
    template (no `template.json`), so resolution fails and the check
    yields a fail-Finding naming the offending value.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    bare_dir = project_root / "bare-template"
    bare_dir.mkdir()
    config_text = '{\n  "template": "bare-template"\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-template-exists",
        status="fail",
        message="template 'bare-template' is neither a builtin nor an existing path",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert template_exists.run(ctx=ctx) == IOSuccess(expected)
