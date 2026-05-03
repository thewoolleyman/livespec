"""Tests for livespec.doctor.static.template_files_present.

Per Plan Phase 3 line 1596-1602 + PROPOSAL.md §"`doctor` →
Static-phase checks": this is the third of the eight Phase-3
minimum-subset doctor checks. It asserts that the canonical
template-materialized files are present in the spec_root.

Phase-3 minimum scope: the check verifies that the canonical
`<spec_root>/spec.md` file (the file every livespec-template
seed materializes per PROPOSAL §"`seed`" step 2) is present
on disk. Phase 7 widens this to walk the template's full
declared file manifest (template.json + recursively-discovered
template-source files). Cycle 136 lands the success arm only;
cycle 137 lands the missing-file failure arm.
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
