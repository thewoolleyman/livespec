"""Tests for livespec.doctor.static.template_exists.

Per Plan Phase 3 +: this is the second of the eight Phase-3
minimum-subset doctor checks. It asserts that the project's
`.livespec.jsonc` `template` field resolves to a known template
— either a built-in template name (one of {`livespec`,
`minimal`}) or a path-as-string to a custom template directory
present on disk relative to the project root.

Cycle 134 lands the success arm for the built-in template
resolution: a config declaring `template: "livespec"` yields
IOSuccess(Finding(status='pass', ...)). Subsequent cycles
extend to cover the failure arm (unknown template, missing
custom-template directory) and the path-resolution branch.
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
