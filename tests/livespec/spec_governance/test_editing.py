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


def test_revise_decision_global_action_is_surgical_and_clearable(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    before = (
        "// outer comment\n"
        "{\n"
        '  "template": "livespec",\n'
        '  "spec_governance": {\n'
        "    // policy comment\n"
        '    "critique_mode": "batch",\n'
        '    "revise_decision_mode": "manual"\n'
        "  },\n"
        '  "unrelated": true\n'
        "}\n"
    )
    config_path.write_text(before, encoding="utf-8")

    set_result = apply_action(
        project_root=tmp_path,
        action="set-revise-decision-mode:global:delegated",
    )

    assert isinstance(set_result, EditResult)
    armed = config_path.read_text(encoding="utf-8")
    assert armed == before.replace(
        '"revise_decision_mode": "manual"',
        '"revise_decision_mode": "delegated"',
    )
    assert armed.count("//") == before.count("//")

    clear_result = apply_action(
        project_root=tmp_path,
        action="set-revise-decision-mode:global:clear",
    )

    assert isinstance(clear_result, EditResult)
    cleared = config_path.read_text(encoding="utf-8")
    assert "revise_decision_mode" not in cleared
    assert "// outer comment" in cleared
    assert "// policy comment" in cleared
    assert '"critique_mode": "batch"' in cleared
    assert '"unrelated": true' in cleared


def test_drift_acceptance_global_action_refuses_delegated_and_clears(
    *,
    tmp_path: Path,
) -> None:
    set_result = apply_action(
        project_root=tmp_path,
        action="set-drift-acceptance-mode:global:consensus",
    )
    invalid_result = apply_action(
        project_root=tmp_path,
        action="set-drift-acceptance-mode:global:delegated",
    )
    invalid_shape = apply_action(
        project_root=tmp_path,
        action="set-drift-acceptance-mode:proposal:topic-a:consensus",
    )

    assert isinstance(set_result, EditResult)
    assert isinstance(invalid_result, str)
    assert "human" in invalid_result
    assert "consensus" in invalid_result
    assert isinstance(invalid_shape, str)
    text_after_invalid = (tmp_path / ".livespec.jsonc").read_text(encoding="utf-8")
    assert '"drift_acceptance_mode": "consensus"' in text_after_invalid

    clear_result = apply_action(
        project_root=tmp_path,
        action="set-drift-acceptance-mode:global:clear",
    )

    assert isinstance(clear_result, EditResult)
    assert "drift_acceptance_mode" not in (tmp_path / ".livespec.jsonc").read_text(encoding="utf-8")


def test_revise_decision_proposal_action_preserves_body_and_refuses_invalid_input(
    *,
    tmp_path: Path,
) -> None:
    proposal_dir = tmp_path / "SPECIFICATION" / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    proposal = proposal_dir / "topic-c.md"
    before = (
        "---\n"
        "topic: topic-c\n"
        "# keep front-matter comment\n"
        "decision_policy: manual\n"
        "---\n"
        "\n"
        "## Proposal\n"
        "\n"
        "Body bytes stay exactly.\n"
    )
    proposal.write_text(before, encoding="utf-8")

    set_result = apply_action(
        project_root=tmp_path,
        action="set-revise-decision-mode:proposal:topic-c:consensus",
    )

    assert isinstance(set_result, EditResult)
    armed = proposal.read_text(encoding="utf-8")
    assert armed == before.replace("decision_policy: manual", "decision_policy: consensus")

    invalid_before = armed
    invalid_value = apply_action(
        project_root=tmp_path,
        action="set-revise-decision-mode:proposal:topic-c:robot",
    )
    invalid_stem = apply_action(
        project_root=tmp_path,
        action="set-revise-decision-mode:proposal:Bad:manual",
    )

    assert isinstance(invalid_value, str)
    assert "manual" in invalid_value
    assert "delegated" in invalid_value
    assert "consensus" in invalid_value
    assert isinstance(invalid_stem, str)
    assert proposal.read_text(encoding="utf-8") == invalid_before

    clear_result = apply_action(
        project_root=tmp_path,
        action="set-revise-decision-mode:proposal:topic-c:clear",
    )

    assert isinstance(clear_result, EditResult)
    cleared = proposal.read_text(encoding="utf-8")
    assert "decision_policy" not in cleared
    assert cleared.endswith("\n---\n\n## Proposal\n\nBody bytes stay exactly.\n")


def test_editing_decision_modes_module_is_a_leaf() -> None:
    """The extracted decision-mode handlers must not import back into `editing`.

    `EditResult` and `_edit_result` are shared by handlers on BOTH sides of
    the split and were moved into the child so the dependency runs one way:
    `editing` imports them back and re-exports `EditResult` as its public
    surface. Reversing that would form an import cycle.
    """
    source = (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec"
        / "spec_governance"
        / "_editing_decision_modes.py"
    ).read_text(encoding="utf-8")
    assert "spec_governance.editing" not in source, (
        "the decision-modes module must not import from `editing`; the "
        "one-way dependency is what prevents an import cycle"
    )
