"""Tests for livespec.doctor.static.diagram_source_rendered_drift.

Per `SPECIFICATION/spec.md` §"Template manifest" →
"Heading-coverage and doctor-static rewiring": the
`doctor-diagram-source-rendered-drift` check SHOULD warn when a
`diagram_rendered` file's content does not match a fresh
re-render of its `derived_from` source, or (as a cheaper proxy)
when the rendered file's mtime predates the source's mtime. It
catches the case where someone edits diagram source manually
outside the revise flow and forgets to re-render.

The check is manifest-driven: pairings come from the active
template's `spec_files` manifest (v2 templates only). Sub-spec
trees carry no template manifest, and v1 templates declare no
manifest, so both yield a `skipped` finding. File-presence is
owned by `template_files_present`; pairs whose files are absent
are silently skipped here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import diagram_source_rendered_drift
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _seed_v2_project(*, tmp_path: Path) -> tuple[Path, Path]:
    """Materialize a project root whose active template is a v2 manifest.

    The custom template `mytpl/` declares one markdown file plus a
    `diagrams/example.puml` (diagram_source) / `diagrams/example.svg`
    (diagram_rendered) pairing. The spec tree carries `spec.md`;
    diagram files are written per-test so each test controls
    presence and mtimes.
    """
    project_root = tmp_path / "project"
    spec_root = project_root / "SPECIFICATION"
    (spec_root / "diagrams").mkdir(parents=True)
    _ = (spec_root / "spec.md").write_text("# Spec\n", encoding="utf-8")
    template_dir = project_root / "mytpl"
    template_dir.mkdir()
    _ = (template_dir / "template.json").write_text(
        json.dumps(
            {
                "template_format_version": 2,
                "spec_root": "SPECIFICATION/",
                "spec_files": {
                    "spec.md": {"kind": "markdown"},
                    "diagrams/example.puml": {"kind": "diagram_source"},
                    "diagrams/example.svg": {
                        "kind": "diagram_rendered",
                        "derived_from": "diagrams/example.puml",
                    },
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


def _finding(*, spec_root: Path, status: str, message: str) -> Finding:
    """Construct the expected Finding payload for this check."""
    return Finding(
        check_id="doctor-diagram-source-rendered-drift",
        status=status,
        message=message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )


def test_drift_check_skips_on_sub_spec_tree(*, tmp_path: Path) -> None:
    """Sub-spec trees yield `skipped` — they carry no template manifest."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    sub_spec_root = spec_root / "templates" / "mytpl"
    sub_spec_root.mkdir(parents=True)
    ctx = DoctorContext(project_root=project_root, spec_root=sub_spec_root)
    expected = _finding(
        spec_root=sub_spec_root,
        status="skipped",
        message=("diagram-source-rendered-drift: sub-spec trees carry no template manifest"),
    )
    assert diagram_source_rendered_drift.run(ctx=ctx) == IOSuccess(expected)


def test_drift_check_skips_when_no_manifest_resolves(*, tmp_path: Path) -> None:
    """A project without a resolvable v2 manifest yields `skipped`.

    No `.livespec.jsonc` → the template defaults to the built-in
    v1 `livespec` template → no `spec_files` manifest → no
    pairings to check.
    """
    project_root = tmp_path / "project"
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir(parents=True)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _finding(
        spec_root=spec_root,
        status="skipped",
        message=(
            "diagram-source-rendered-drift: the active template declares "
            "no diagram_source/diagram_rendered pairings"
        ),
    )
    assert diagram_source_rendered_drift.run(ctx=ctx) == IOSuccess(expected)


def test_drift_check_warns_when_rendered_predates_source(*, tmp_path: Path) -> None:
    """A rendered output older than its source fires `warn` naming the pair."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    source = spec_root / "diagrams" / "example.puml"
    rendered = spec_root / "diagrams" / "example.svg"
    _ = source.write_text("@startuml\nA -> B\n@enduml\n", encoding="utf-8")
    _ = rendered.write_text("<svg/>\n", encoding="utf-8")
    os.utime(source, (2_000_000_000, 2_000_000_000))
    os.utime(rendered, (1_000_000_000, 1_000_000_000))
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _finding(
        spec_root=spec_root,
        status="warn",
        message=(
            "diagram-source-rendered-drift: 1 rendered output(s) predate "
            "their source: diagrams/example.svg predates diagrams/example.puml. "
            "Corrective action: re-render via a revise pass that touches the "
            "source (or run the project's render command directly)"
        ),
    )
    assert diagram_source_rendered_drift.run(ctx=ctx) == IOSuccess(expected)


def test_drift_check_passes_when_rendered_is_fresh(*, tmp_path: Path) -> None:
    """A rendered output at least as fresh as its source passes."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    source = spec_root / "diagrams" / "example.puml"
    rendered = spec_root / "diagrams" / "example.svg"
    _ = source.write_text("@startuml\nA -> B\n@enduml\n", encoding="utf-8")
    _ = rendered.write_text("<svg/>\n", encoding="utf-8")
    os.utime(source, (1_000_000_000, 1_000_000_000))
    os.utime(rendered, (2_000_000_000, 2_000_000_000))
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _finding(
        spec_root=spec_root,
        status="pass",
        message=(
            "diagram-source-rendered-drift: every declared diagram_rendered "
            "output is at least as fresh as its diagram_source"
        ),
    )
    assert diagram_source_rendered_drift.run(ctx=ctx) == IOSuccess(expected)


def test_drift_check_skips_pair_whose_files_are_absent(*, tmp_path: Path) -> None:
    """Pairs with missing files are skipped — presence is template-files-present's job."""
    project_root, spec_root = _seed_v2_project(tmp_path=tmp_path)
    source = spec_root / "diagrams" / "example.puml"
    _ = source.write_text("@startuml\nA -> B\n@enduml\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _finding(
        spec_root=spec_root,
        status="pass",
        message=(
            "diagram-source-rendered-drift: every declared diagram_rendered "
            "output is at least as fresh as its diagram_source"
        ),
    )
    assert diagram_source_rendered_drift.run(ctx=ctx) == IOSuccess(expected)
