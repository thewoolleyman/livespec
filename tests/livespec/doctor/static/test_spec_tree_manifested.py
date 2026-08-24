"""Tests for livespec.doctor.static.spec_tree_manifested.

Per SPECIFICATION/spec.md "Spec-tree path closure": under a
template that declares its `spec_files` manifest explicitly, a file
present under the spec root and absent from that manifest is a
`fail` naming the path. These tests carry the positive control (a
conforming tree passes) and the NEGATIVE CONTROL (an undeclared
path is refused, naming it), plus the three stated exemptions.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import spec_tree_manifested

__all__: list[str] = []


def _seed_v2_project(*, tmp_path: Path, version: int = 2) -> tuple[Path, Path]:
    """Materialize a project whose active template declares a v2 markdown manifest."""
    project_root = tmp_path / "project"
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir(parents=True)
    template_dir = project_root / "mytpl"
    template_dir.mkdir()
    config: dict[str, object] = {
        "template_format_version": version,
        "spec_root": "SPECIFICATION/",
    }
    if version == 2:
        config["spec_files"] = {
            "spec.md": {"kind": "markdown"},
            "contracts.md": {"kind": "markdown"},
        }
    _ = (template_dir / "template.json").write_text(json.dumps(config), encoding="utf-8")
    _ = (project_root / ".livespec.jsonc").write_text(
        json.dumps({"template": "mytpl"}),
        encoding="utf-8",
    )
    for name in ("spec.md", "contracts.md"):
        _ = (spec_root / name).write_text(f"# {name}\n", encoding="utf-8")
    return project_root, spec_root


def test_spec_tree_manifested_fails_naming_the_undeclared_path(
    *,
    tmp_path: Path,
) -> None:
    """NEGATIVE CONTROL: an undeclared file under a v2 spec root is refused, named.

    This is the case the mechanism must correctly REFUSE: a
    directory of executable checks appears under the spec root,
    declared by no manifest entry. The finding MUST be `fail`
    status (never `warn`, never a silent pass) and MUST name the
    offending path.
    """
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    checks_dir = spec_root / "checks"
    checks_dir.mkdir()
    _ = (checks_dir / "probe.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = spec_tree_manifested.run(ctx=ctx)
    finding = result.unwrap()._inner_value  # noqa: SLF001
    assert finding.status == "fail"
    assert finding.check_id == "doctor-spec-tree-manifested"
    assert "checks/probe.sh" in finding.message


def test_spec_tree_manifested_passes_on_a_conforming_tree(*, tmp_path: Path) -> None:
    """POSITIVE CONTROL: a tree whose every file is declared passes."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    finding = spec_tree_manifested.run(ctx=ctx).unwrap()._inner_value  # noqa: SLF001
    assert finding.status == "pass"


def test_spec_tree_manifested_ignores_lifecycle_owned_subdirectories(
    *,
    tmp_path: Path,
) -> None:
    """history/, proposed_changes/ and templates/ are never 'unmanifested'."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    for owned in ("history", "proposed_changes", "templates"):
        directory = spec_root / owned
        directory.mkdir()
        _ = (directory / "README.md").write_text("x\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    finding = spec_tree_manifested.run(ctx=ctx).unwrap()._inner_value  # noqa: SLF001
    assert finding.status == "pass"


def test_spec_tree_manifested_skips_v1_templates(*, tmp_path: Path) -> None:
    """A v1 template has no declaration form, so the tree is not closed."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path, version=1)
    _ = (spec_root / "undeclared.md").write_text("x\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    finding = spec_tree_manifested.run(ctx=ctx).unwrap()._inner_value  # noqa: SLF001
    assert finding.status == "skipped"
    assert "template_format_version 1" in finding.message


def test_spec_tree_manifested_skips_project_root_spec_roots(*, tmp_path: Path) -> None:
    """A single-file shape (spec_root == project root) has no dedicated tree."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=project_root)
    finding = spec_tree_manifested.run(ctx=ctx).unwrap()._inner_value  # noqa: SLF001
    assert finding.status == "skipped"
    assert "project root" in finding.message


def test_spec_tree_manifested_skips_sub_spec_trees(*, tmp_path: Path) -> None:
    """A sub-spec tree carries no template manifest of its own, so it is exempt."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    sub_spec_root = spec_root / "templates" / "child"
    sub_spec_root.mkdir(parents=True)
    _ = (sub_spec_root / "undeclared.md").write_text("x\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=sub_spec_root)
    finding = spec_tree_manifested.run(ctx=ctx).unwrap()._inner_value  # noqa: SLF001
    assert finding.status == "skipped"
    assert "sub-spec" in finding.message
