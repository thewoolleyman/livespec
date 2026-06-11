"""Tests for livespec.commands._revise_render — the revise render lifecycle.

Per `SPECIFICATION/spec.md` §"Template manifest" → "Rendering in
the revise lifecycle": when a revise pass writes updated
`diagram_source` content via `resulting_files[]`, the revise
wrapper MUST invoke the project-declared render command
(`.livespec.jsonc` `render_commands.diagram_source`, an argv-form
array with `{source}` / `{output_dir}` substitution, run with cwd
at the project root, no shell) AFTER writing the source and BEFORE
snapshotting to `history/vNNN/`; the rendered output sits
alongside its source at the manifest-named relative path.

The pass MUST be transactional: a non-zero render exit fails the
entire revision (exit 3, the supervisor's PreconditionError path)
and leaves `<spec-target>/` untouched — sources are staged to a
working location under the project root, rendered there, and only
committed into the spec tree on full success.

Per spec.md §"Template manifest" → "Per-kind behavior axes",
history snapshots MUST include all three kinds — so manifest-
declared files in subdirectories (the diagrams/ pairing) land in
`history/vNNN/` alongside the immediate spec-root files.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from livespec.commands import revise

__all__: list[str] = []


_RENDER_SCRIPT = (
    "import sys, pathlib; "
    "src = pathlib.Path(sys.argv[1]); "
    "out = pathlib.Path(sys.argv[2]); "
    "(out / (src.stem + '.svg')).write_text("
    "'<svg>' + src.read_text(encoding='utf-8') + '</svg>', encoding='utf-8')"
)

_NEW_PUML = "@startuml\nnew-content\n@enduml\n"


def _working_render_argv() -> list[str]:
    """An argv-form render command that renders `<stem>.svg` beside the source."""
    return [sys.executable, "-c", _RENDER_SCRIPT, "{source}", "{output_dir}"]


def _failing_render_argv() -> list[str]:
    """An argv-form render command that always exits non-zero."""
    return [sys.executable, "-c", "import sys; sys.exit(7)"]


def _seed_render_project(
    *,
    tmp_path: Path,
    render_argv: list[str] | None,
) -> tuple[Path, Path]:
    """Materialize a v2-manifest project with one diagram pairing on disk.

    `render_argv=None` omits the `render_commands` block from
    `.livespec.jsonc` (driving the missing-render-command
    precondition arm).
    """
    project_root = tmp_path / "project"
    spec_root = project_root / "SPECIFICATION"
    (spec_root / "diagrams").mkdir(parents=True)
    (spec_root / "proposed_changes").mkdir()
    (spec_root / "history" / "v001").mkdir(parents=True)
    _ = (spec_root / "spec.md").write_text("# Spec\nOld.\n", encoding="utf-8")
    _ = (spec_root / "diagrams" / "example.puml").write_text(
        "@startuml\nold-content\n@enduml\n",
        encoding="utf-8",
    )
    _ = (spec_root / "diagrams" / "example.svg").write_text(
        "<svg>old</svg>",
        encoding="utf-8",
    )
    _ = (spec_root / "proposed_changes" / "demo.md").write_text(
        "## Proposal: demo\n",
        encoding="utf-8",
    )
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
    config: dict[str, object] = {"template": "mytpl"}
    if render_argv is not None:
        config["render_commands"] = {"diagram_source": render_argv}
    _ = (project_root / ".livespec.jsonc").write_text(json.dumps(config), encoding="utf-8")
    return project_root, spec_root


def _write_diagram_payload(*, tmp_path: Path) -> Path:
    """An accept decision updating the diagram source via resulting_files."""
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "proposal_topic": "demo",
                        "decision": "accept",
                        "rationale": "Update the diagram.",
                        "resulting_files": [
                            {"path": "diagrams/example.puml", "content": _NEW_PUML},
                        ],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    return payload_path


def _run_revise(*, payload_path: Path, project_root: Path, spec_root: Path) -> int:
    """Drive revise.main against the fixture project."""
    return revise.main(
        argv=[
            "--revise-json",
            str(payload_path),
            "--project-root",
            str(project_root),
            "--spec-target",
            str(spec_root),
        ],
    )


def test_revise_renders_diagram_source_and_snapshots_all_kinds(
    *,
    tmp_path: Path,
) -> None:
    """A diagram_source write renders, lands the output, and snapshots all kinds.

    Success path: the source is updated, the rendered output is
    regenerated from the NEW source content, both land in the
    `history/v002/` snapshot at their manifest-named relative
    paths, and no render-staging directory is left behind.
    """
    project_root, spec_root = _seed_render_project(
        tmp_path=tmp_path,
        render_argv=_working_render_argv(),
    )
    payload_path = _write_diagram_payload(tmp_path=tmp_path)
    exit_code = _run_revise(
        payload_path=payload_path,
        project_root=project_root,
        spec_root=spec_root,
    )
    assert exit_code == 0
    source = spec_root / "diagrams" / "example.puml"
    rendered = spec_root / "diagrams" / "example.svg"
    assert source.read_text(encoding="utf-8") == _NEW_PUML
    assert rendered.read_text(encoding="utf-8") == f"<svg>{_NEW_PUML}</svg>"
    snapshot_source = spec_root / "history" / "v002" / "diagrams" / "example.puml"
    snapshot_rendered = spec_root / "history" / "v002" / "diagrams" / "example.svg"
    assert snapshot_source.read_text(encoding="utf-8") == _NEW_PUML
    assert snapshot_rendered.read_text(encoding="utf-8") == f"<svg>{_NEW_PUML}</svg>"
    assert not list(project_root.glob(".livespec-render-staging-*"))


def test_revise_render_failure_is_transactional_exit_3(*, tmp_path: Path) -> None:
    """A non-zero render exit fails the revision and leaves the tree untouched.

    Per the transactional clause: no half-applied state — the
    source keeps its old content, no `history/v002/` is cut, the
    proposal stays in-flight, and the staging directory is
    removed.
    """
    project_root, spec_root = _seed_render_project(
        tmp_path=tmp_path,
        render_argv=_failing_render_argv(),
    )
    payload_path = _write_diagram_payload(tmp_path=tmp_path)
    exit_code = _run_revise(
        payload_path=payload_path,
        project_root=project_root,
        spec_root=spec_root,
    )
    assert exit_code == 3
    source = spec_root / "diagrams" / "example.puml"
    rendered = spec_root / "diagrams" / "example.svg"
    assert source.read_text(encoding="utf-8") == "@startuml\nold-content\n@enduml\n"
    assert rendered.read_text(encoding="utf-8") == "<svg>old</svg>"
    assert not (spec_root / "history" / "v002").exists()
    assert (spec_root / "proposed_changes" / "demo.md").is_file()
    assert not list(project_root.glob(".livespec-render-staging-*"))


def test_revise_diagram_write_without_render_command_exit_3(
    *,
    tmp_path: Path,
) -> None:
    """A diagram_source write with no render_commands declared is exit 3.

    Per `contracts.md` §".livespec.jsonc render-commands shape":
    projects whose active template declares any diagram_source
    entry MUST declare `render_commands`; revising a diagram
    source without one is a precondition failure, before any
    tree mutation.
    """
    project_root, spec_root = _seed_render_project(
        tmp_path=tmp_path,
        render_argv=None,
    )
    payload_path = _write_diagram_payload(tmp_path=tmp_path)
    exit_code = _run_revise(
        payload_path=payload_path,
        project_root=project_root,
        spec_root=spec_root,
    )
    assert exit_code == 3
    source = spec_root / "diagrams" / "example.puml"
    assert source.read_text(encoding="utf-8") == "@startuml\nold-content\n@enduml\n"
    assert not (spec_root / "history" / "v002").exists()


def test_revise_markdown_only_pass_snapshots_manifest_subdir_files(
    *,
    tmp_path: Path,
) -> None:
    """A markdown-only revise under a v2 manifest snapshots the diagram files too.

    No render is invoked (the rendered output keeps its old
    content), but the `history/v002/` snapshot includes the
    manifest-declared diagrams/ pairing per the
    all-three-kinds-in-history axis.
    """
    project_root, spec_root = _seed_render_project(
        tmp_path=tmp_path,
        render_argv=_working_render_argv(),
    )
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "proposal_topic": "demo",
                        "decision": "accept",
                        "rationale": "Markdown-only edit.",
                        "resulting_files": [
                            {"path": "spec.md", "content": "# Spec\nNew.\n"},
                        ],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    exit_code = _run_revise(
        payload_path=payload_path,
        project_root=project_root,
        spec_root=spec_root,
    )
    assert exit_code == 0
    rendered = spec_root / "diagrams" / "example.svg"
    assert rendered.read_text(encoding="utf-8") == "<svg>old</svg>"
    snapshot_source = spec_root / "history" / "v002" / "diagrams" / "example.puml"
    snapshot_rendered = spec_root / "history" / "v002" / "diagrams" / "example.svg"
    assert snapshot_source.read_text(encoding="utf-8") == ("@startuml\nold-content\n@enduml\n")
    assert snapshot_rendered.read_text(encoding="utf-8") == "<svg>old</svg>"
    assert (spec_root / "history" / "v002" / "spec.md").read_text(
        encoding="utf-8",
    ) == "# Spec\nNew.\n"
