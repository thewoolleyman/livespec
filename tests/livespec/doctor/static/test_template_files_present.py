"""Tests for livespec.doctor.static.template_files_present.

 this is the third of the eight Phase-3
minimum-subset doctor checks. It asserts that the canonical
template-materialized files are present in the spec_root.

Phase-3 minimum scope: the check verifies that the canonical
`<spec_root>/spec.md` file (the file every livespec-template
seed materializes step 2) is present
on disk. the per-prompt regeneration widens this to walk the template's full
declared file manifest (template.json + recursively-discovered
template-source files).  lands the success arm only;
 lands the missing-file failure arm.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import template_files_present
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def test_template_files_present_run_returns_pass_when_spec_md_exists(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when <spec_root>/spec.md exists.

    Seeds a project root with a populated spec_root containing
    the canonical `spec.md` and asserts the check yields a
    pass-status Finding with the canonical
    `doctor-template-files-present` check_id.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = (spec_root / "spec.md").write_text("# Spec\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-template-files-present",
        status="pass",
        message="canonical template-materialized files are present",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert template_files_present.run(ctx=ctx) == IOSuccess(expected)


def _seed_v2_project(*, tmp_path: Path) -> tuple[Path, Path]:
    """Materialize a project whose active template declares a markdown-only v2 manifest."""
    import json

    project_root = tmp_path / "project"
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir(parents=True)
    template_dir = project_root / "mytpl"
    template_dir.mkdir()
    _ = (template_dir / "template.json").write_text(
        json.dumps(
            {
                "template_format_version": 2,
                "spec_root": "SPECIFICATION/",
                "spec_files": {
                    "spec.md": {"kind": "markdown"},
                    "contracts.md": {"kind": "markdown"},
                    "constraints.md": {"kind": "markdown"},
                },
            },
        ),
        encoding="utf-8",
    )
    _ = (project_root / ".livespec.jsonc").write_text(
        json.dumps({"template": "mytpl"}),
        encoding="utf-8",
    )
    return project_root, spec_root


def test_template_files_present_fails_naming_missing_manifest_paths(
    *,
    tmp_path: Path,
) -> None:
    """Under a v2 manifest, missing declared files fire `fail` naming them.

    Per `SPECIFICATION/spec.md`
    "Heading-coverage and doctor-static rewiring": under v2
    templates the manifest is the source of truth for the
    template-files-present enumeration. Only `spec.md` is on disk;
    the two other markdown files are missing and MUST be named
    (sorted).
    """
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    _ = (spec_root / "spec.md").write_text("# Spec\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-template-files-present",
        status="fail",
        message=(
            f"template-files-present: 2 manifest-declared spec file(s) "
            f"missing from {spec_root}: constraints.md, contracts.md"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert template_files_present.run(ctx=ctx) == IOSuccess(expected)


def test_template_files_present_passes_when_every_manifest_path_exists(
    *,
    tmp_path: Path,
) -> None:
    """Under a v2 manifest, the check passes when every declared file exists."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    _ = (spec_root / "spec.md").write_text("# Spec\n", encoding="utf-8")
    _ = (spec_root / "contracts.md").write_text("# Contracts\n", encoding="utf-8")
    _ = (spec_root / "constraints.md").write_text("# Constraints\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-template-files-present",
        status="pass",
        message="canonical template-materialized files are present",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert template_files_present.run(ctx=ctx) == IOSuccess(expected)


def test_template_files_present_keeps_spec_md_arm_for_sub_spec_trees(
    *,
    tmp_path: Path,
) -> None:
    """Sub-spec trees keep the spec.md-presence arm (no template manifest)."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    sub_spec_root = spec_root / "templates" / "mytpl"
    sub_spec_root.mkdir(parents=True)
    _ = (sub_spec_root / "spec.md").write_text("# Sub-spec\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=sub_spec_root)
    expected = Finding(
        check_id="doctor-template-files-present",
        status="pass",
        message="canonical template-materialized files are present",
        path=None,
        line=None,
        spec_root=str(sub_spec_root),
    )
    assert template_files_present.run(ctx=ctx) == IOSuccess(expected)
