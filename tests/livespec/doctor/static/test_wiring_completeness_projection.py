"""Coverage for the bundled canonical-slug source used by doctor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import _wiring_completeness_projection as projection
from livespec.doctor.static import wiring_completeness_cross_repo
from livespec.doctor.static._wiring_completeness_resolve import resolve_project_check_source
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_projection_reader_rejects_unreadable_and_malformed_data(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The projection has no empty or partially parsed success state."""
    missing = tmp_path / "missing.yml"
    monkeypatch.setattr(projection, "_PROJECTION_PATH", missing)
    assert projection.canonical_slugs_from_projection() is None

    malformed = tmp_path / "malformed.yml"
    malformed.write_text("check-not-a-yaml-item\n", encoding="utf-8")
    monkeypatch.setattr(projection, "_PROJECTION_PATH", malformed)
    assert projection.canonical_slugs_from_projection() is None

    duplicate = tmp_path / "duplicate.yml"
    duplicate.write_text("- check-one\n- check-one\n", encoding="utf-8")
    monkeypatch.setattr(projection, "_PROJECTION_PATH", duplicate)
    assert projection.canonical_slugs_from_projection() is None


def test_project_source_falls_back_to_justfile_then_reports_no_source(*, tmp_path: Path) -> None:
    """The consumer reads its root directly, preferring its target inventory."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    justfile = project_root / "justfile"
    justfile.write_text("check:\n    targets=(\n    )\n", encoding="utf-8")

    source = unsafe_perform_io(resolve_project_check_source(project_root=project_root)).unwrap()
    assert source is not None
    assert source.kind == "justfile"

    justfile.unlink()
    unresolved = unsafe_perform_io(resolve_project_check_source(project_root=project_root)).unwrap()
    assert unresolved is None


def test_unreadable_bundled_projection_fails_the_conformance_check(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unavailable canonical source is a failure, never a skipped finding."""
    monkeypatch.setattr(
        wiring_completeness_cross_repo, "canonical_slugs_from_projection", lambda: None
    )
    project_root = tmp_path / "project"
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir(parents=True)
    (project_root / ".livespec.jsonc").write_text(
        json.dumps({"cross_repo_conformance_targets": {}}), encoding="utf-8"
    )

    finding = unsafe_perform_io(
        wiring_completeness_cross_repo.run(
            ctx=DoctorContext(project_root=project_root, spec_root=spec_root)
        )
    ).unwrap()
    assert finding.status == "fail"
