"""Tests for spec-governance policy edits."""

from __future__ import annotations

import json
from pathlib import Path

from livespec.spec_governance.editing import EditResult, apply_action

__all__: list[str] = []


def test_global_action_preserves_unrelated_jsonc_comments(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        '// keep me\n{\n  "template": "livespec"\n}\n',
        encoding="utf-8",
    )

    result = apply_action(
        project_root=tmp_path,
        action="set-propose-change-mode:batch",
    )

    assert isinstance(result, EditResult)
    text = config_path.read_text(encoding="utf-8")
    assert "// keep me" in text
    assert '"propose_change_mode": "batch"' in text


def test_clear_global_action_removes_only_selected_key(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        json.dumps(
            {
                "spec_governance": {
                    "propose_change_mode": "batch",
                    "critique_mode": "batch",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = apply_action(project_root=tmp_path, action="set-propose-change-mode:clear")

    assert isinstance(result, EditResult)
    text = config_path.read_text(encoding="utf-8")
    assert "propose_change_mode" not in text
    assert "critique_mode" in text


def test_doctor_map_action_sets_and_clears_entry(*, tmp_path: Path) -> None:
    set_result = apply_action(
        project_root=tmp_path,
        action="set-doctor-disposition:doctor-static-x:defer",
    )
    clear_result = apply_action(
        project_root=tmp_path,
        action="set-doctor-disposition:doctor-static-x:clear",
    )

    assert isinstance(set_result, EditResult)
    assert isinstance(clear_result, EditResult)
    assert "doctor-static-x" not in (tmp_path / ".livespec.jsonc").read_text(encoding="utf-8")


def test_global_clear_and_validation_error_paths(*, tmp_path: Path) -> None:
    set_model = apply_action(
        project_root=tmp_path,
        action="set-ratification-reviewer-model:fable/model",
    )
    clear_review = apply_action(
        project_root=tmp_path,
        action="set-ratification-review:global:clear",
    )
    set_review = apply_action(
        project_root=tmp_path,
        action="set-ratification-review:global:auto-spawn",
    )

    assert isinstance(set_model, EditResult)
    assert isinstance(clear_review, EditResult)
    assert isinstance(set_review, EditResult)
    assert isinstance(apply_action(project_root=tmp_path, action="unknown"), str)
    assert isinstance(
        apply_action(project_root=tmp_path, action="set-ratification-reviewer-model:bad model!"),
        str,
    )
    assert isinstance(
        apply_action(project_root=tmp_path, action="set-doctor-disposition:not-a-doctor:defer"),
        str,
    )
    assert isinstance(
        apply_action(project_root=tmp_path, action="set-doctor-disposition:doctor-x:nope"),
        str,
    )
    assert isinstance(
        apply_action(project_root=tmp_path, action="set-ratification-review:global:nope"),
        str,
    )
    assert isinstance(
        apply_action(project_root=tmp_path, action="set-ratification-review:proposal"),
        str,
    )
    assert isinstance(
        apply_action(project_root=tmp_path, action="set-ratification-review:bad:x"),
        str,
    )


def test_ratification_proposal_validation_and_missing_front_matter_paths(*, tmp_path: Path) -> None:
    proposal_dir = tmp_path / "SPECIFICATION" / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    (proposal_dir / "bad.md").write_text("no front matter\n", encoding="utf-8")
    (proposal_dir / "unterminated.md").write_text("---\ntopic: x\n", encoding="utf-8")

    assert isinstance(
        apply_action(
            project_root=tmp_path, action="set-ratification-review:proposal:Bad:auto-spawn"
        ),
        str,
    )
    assert isinstance(
        apply_action(project_root=tmp_path, action="set-ratification-review:proposal:bad:nope"),
        str,
    )


def test_config_parse_error_from_action_returns_diagnostic(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text('{"spec_governance": [}', encoding="utf-8")

    assert isinstance(apply_action(project_root=tmp_path, action="set-critique-mode:batch"), str)


def test_doctor_action_preserves_mixed_existing_map_values(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        '{"spec_governance": {"doctor_dispositions": {"doctor-x": "defer", "doctor-y": 1}}}',
        encoding="utf-8",
    )
    result = apply_action(
        project_root=tmp_path,
        action="set-doctor-disposition:doctor-y:dismiss",
    )
    assert isinstance(result, EditResult)
    text = config_path.read_text(encoding="utf-8")
    assert "doctor-x" in text
    assert "doctor-y" in text


def test_proposal_override_preserves_markdown_body_bytes(*, tmp_path: Path) -> None:
    proposal_dir = tmp_path / "SPECIFICATION" / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    proposal = proposal_dir / "topic-a.md"
    body = "\n---\n\n## Proposal\n\nBody bytes stay.\n"
    proposal.write_text("---\ntopic: topic-a\n---" + body, encoding="utf-8")

    set_result = apply_action(
        project_root=tmp_path,
        action="set-ratification-review:proposal:topic-a:auto-spawn",
    )
    clear_result = apply_action(
        project_root=tmp_path,
        action="set-ratification-review:proposal:topic-a:clear",
    )

    assert isinstance(set_result, EditResult)
    assert isinstance(clear_result, EditResult)
    text = proposal.read_text(encoding="utf-8")
    assert "ratification_review_policy" not in text
    assert text.endswith(body)


def test_invalid_action_returns_diagnostic_without_mutation(*, tmp_path: Path) -> None:
    result = apply_action(project_root=tmp_path, action="set-critique-mode:robot")

    assert isinstance(result, str)
    assert not (tmp_path / ".livespec.jsonc").exists()
