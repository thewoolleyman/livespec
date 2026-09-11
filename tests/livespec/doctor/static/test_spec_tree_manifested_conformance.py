"""Conformance coverage for `SPECIFICATION/spec.md` "Spec-tree path closure".

The clause is settled on the implementation side by the shipped
`doctor-spec-tree-manifested` check. This module converges the heading via
a CONFORMANCE test rather than by re-testing the check in the abstract: it
runs the shipped check-runner against THIS repository's real spec tree and
asserts the result is not a `fail` (no undeclared path under a closed
manifest), PLUS a control-armed violating fixture the same runner catches
with a `fail` that names the offending path.

This repository's active template is `template_format_version: 1`, so the
runner reports `skipped` here (a v1 template declares no explicit manifest
to close). The conformance assertion pins that this repo is never `fail`;
were it to migrate to a v2 manifest, the same assertion would then pin
genuine closure of the tree.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import spec_tree_manifested

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _finding(result: object) -> object:
    return result.unwrap()._inner_value  # type: ignore[attr-defined]  # noqa: SLF001


def test_this_repo_spec_tree_is_not_undeclared() -> None:
    """CONFORMANCE: the shipped check does not `fail` on this repo's spec tree."""
    ctx = DoctorContext(
        project_root=_REPO_ROOT,
        spec_root=_REPO_ROOT / "SPECIFICATION",
    )

    finding = _finding(spec_tree_manifested.run(ctx=ctx))

    assert finding.check_id == "doctor-spec-tree-manifested"
    assert finding.status != "fail", finding.message
    assert finding.status in {"pass", "skipped"}


def test_undeclared_path_under_a_v2_manifest_is_caught(*, tmp_path: Path) -> None:
    """CONTROL: an undeclared file under a v2 manifest is a `fail` naming it."""
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
                "spec_files": {"spec.md": {"kind": "markdown"}},
            }
        ),
        encoding="utf-8",
    )
    _ = (project_root / ".livespec.jsonc").write_text(
        json.dumps({"template": "mytpl"}), encoding="utf-8"
    )
    _ = (spec_root / "spec.md").write_text("# spec.md\n", encoding="utf-8")
    _ = (spec_root / "smuggled.md").write_text("# undeclared\n", encoding="utf-8")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    finding = _finding(spec_tree_manifested.run(ctx=ctx))

    assert finding.status == "fail"
    assert "smuggled.md" in finding.message
