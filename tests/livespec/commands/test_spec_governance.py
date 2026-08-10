"""Tests for livespec.commands.spec_governance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest
from livespec.commands import spec_governance
from livespec.errors import UsageError
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_show_effective_emits_manifest_declared_effective_and_diagnostics(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance": {"propose_change_mode": "batch"}}',
        encoding="utf-8",
    )

    exit_code = spec_governance.main(
        argv=["--project-root", str(tmp_path), "--show-effective"],
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert len(payload["manifest"]) == 10
    assert payload["declared"] == {"propose_change_mode": "batch"}
    assert payload["effective"]["propose_change_mode"] == "batch"
    assert payload["effective"]["revise_decision_mode"] == "manual"
    assert payload["effective"]["drift_acceptance_mode"] == "human"


def test_show_effective_defaults_project_root_to_cwd(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = spec_governance.main(argv=["--show-effective"])

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["effective"]["propose_change_mode"] == "interactive"


def test_show_effective_reports_every_safe_default(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=["--project-root", str(tmp_path), "--show-effective"],
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["effective"] == {
        "critique_mode": "interactive",
        "doctor_dispositions": {},
        "drift_acceptance_mode": "human",
        "in_flight_alignment": "prompt",
        "propose_change_mode": "interactive",
        "ratification_review": "manual-spawn",
        "ratification_reviewer_model": None,
        "ratification_min_review_age_seconds": 1,
        "revise_decision_mode": "manual",
        "spec_pr_merge": "manual",
    }
    assert payload["declared"] == {}
    assert payload["diagnostics"] == ["missing spec_governance block; safe defaults applied"]


def test_check_default_block_accepts_matching_consumer_config(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    source = tmp_path / ".livespec.jsonc"
    source.write_text(
        _matching_commented_spec_governance_block(),
        encoding="utf-8",
    )

    exit_code = spec_governance.main(argv=["--check-default-block", str(source)])

    assert exit_code == 0
    assert "spec-governance-default-block-ok" in capsys.readouterr().out


def test_check_default_block_rejects_missing_manifest_key(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    source = tmp_path / ".livespec.jsonc"
    source.write_text(
        _matching_commented_spec_governance_block().replace(
            '  //     "propose_change_mode": "interactive",\n',
            "",
        ),
        encoding="utf-8",
    )

    exit_code = spec_governance.main(argv=["--check-default-block", str(source)])

    assert exit_code == 2
    assert "spec-governance-default-block-drift" in capsys.readouterr().err


def test_check_default_block_rejects_config_without_commented_block(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    source = tmp_path / ".livespec.jsonc"
    _ = source.write_text('{"template": "livespec"}', encoding="utf-8")

    exit_code = spec_governance.main(argv=["--check-default-block", str(source)])

    assert exit_code == 2
    assert "spec-governance-default-block-drift" in capsys.readouterr().err


def test_action_updates_config_and_emits_changed_path(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-revise-decision-mode:global:delegated",
        ],
    )

    assert exit_code == 0
    payload: dict[str, str] = json.loads(capsys.readouterr().out)
    assert payload["changed_path"] == ".livespec.jsonc"
    assert '"revise_decision_mode": "delegated"' in (tmp_path / ".livespec.jsonc").read_text(
        encoding="utf-8"
    )


def test_drift_acceptance_action_applies_refuses_invalid_and_clears(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    set_exit = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-drift-acceptance-mode:global:consensus",
        ],
    )
    refused_exit = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-drift-acceptance-mode:global:delegated",
        ],
    )
    clear_exit = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-drift-acceptance-mode:global:clear",
        ],
    )

    captured = capsys.readouterr()
    assert set_exit == 0
    assert refused_exit == 2
    assert clear_exit == 0
    assert "drift acceptance mode" in captured.err
    assert "delegated" not in (tmp_path / ".livespec.jsonc").read_text(encoding="utf-8")
    assert "drift_acceptance_mode" not in (tmp_path / ".livespec.jsonc").read_text(encoding="utf-8")


def test_invalid_action_exits_usage_error(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-revise-decision-mode:global:robot",
        ],
    )

    assert exit_code == 2
    assert "revise decision mode" in capsys.readouterr().err


def test_invalid_revise_decision_action_shape_exits_usage_error(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-revise-decision-mode:project:manual",
        ],
    )

    assert exit_code == 2
    assert "requires global" in capsys.readouterr().err


def test_journal_event_appends_and_emits_digest(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "event_type": "authoring_auto_consumption",
                "operation": "critique",
                "governing_key": "critique_mode",
                "effective_source": "global",
                "input_envelope_digest": "d" * 64,
                "outcome": "consumed",
            },
        ),
        encoding="utf-8",
    )

    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--journal-event-json",
            str(event_path),
        ],
    )

    assert exit_code == 0
    payload: dict[str, str] = json.loads(capsys.readouterr().out)
    assert payload["journal_path"] == "tmp/livespec-spec-governance-journal.jsonl"
    assert len(payload["event_digest"]) == 64


def test_invalid_journal_event_exits_usage_error(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text("[]", encoding="utf-8")

    exit_code = spec_governance.main(
        argv=["--project-root", str(tmp_path), "--journal-event-json", str(event_path)],
    )

    assert exit_code == 2
    assert "JSON object" in capsys.readouterr().err


def test_pr_effective_policy_zero_match_resolves_manual(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance": {"spec_pr_merge": "auto-on-green"}}',
        encoding="utf-8",
    )

    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--show-effective",
            "--pr-effective-policy",
            "--proposal-stem",
            "missing-proposal",
        ],
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["effective"]["spec_pr_merge"] == "auto-on-green"
    assert payload["pr_effective_policy"]["spec_pr_merge"] == "manual"


def test_pr_effective_policy_multi_match_conservative_fold(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    _write_history_proposal(
        root=tmp_path,
        version="v032",
        stem="repeated-topic",
        front_matter="spec_pr_merge_policy: auto-on-green\n",
    )
    _write_history_proposal(
        root=tmp_path,
        version="v034",
        stem="repeated-topic",
        front_matter="spec_pr_merge_policy: manual\n",
    )

    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--show-effective",
            "--pr-effective-policy",
            "--proposal-stem",
            "repeated-topic",
        ],
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["pr_effective_policy"]["spec_pr_merge"] == "manual"


def test_pr_effective_policy_all_auto_fold(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    _write_history_proposal(
        root=tmp_path,
        version="v001",
        stem="topic-a",
        front_matter="spec_pr_merge_policy: auto-on-green\n",
    )
    _write_history_proposal(
        root=tmp_path,
        version="v002",
        stem="topic-b",
        front_matter="spec_pr_merge_policy: auto-on-green\n",
    )

    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--show-effective",
            "--pr-effective-policy",
            "--proposal-stem",
            "topic-a",
            "--proposal-stem",
            "topic-b",
        ],
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["pr_effective_policy"]["spec_pr_merge"] == "auto-on-green"


def test_pr_effective_policy_any_manual_floors_fold(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance": {"spec_pr_merge": "auto-on-green"}}',
        encoding="utf-8",
    )
    _write_history_proposal(
        root=tmp_path,
        version="v001",
        stem="topic-a",
        front_matter="spec_pr_merge_policy: auto-on-green\n",
    )
    _write_history_proposal(
        root=tmp_path,
        version="v002",
        stem="topic-b",
        front_matter="spec_pr_merge_policy: manual\n",
    )

    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--show-effective",
            "--pr-effective-policy",
            "--proposal-stem",
            "topic-a",
            "--proposal-stem",
            "topic-b",
        ],
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["pr_effective_policy"]["spec_pr_merge"] == "manual"


def test_pr_effective_policy_explicitly_empty_set_resolves_manual(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance": {"spec_pr_merge": "auto-on-green"}}',
        encoding="utf-8",
    )

    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--show-effective",
            "--pr-effective-policy",
        ],
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["pr_effective_policy"]["spec_pr_merge"] == "manual"


def test_proposal_stem_without_pr_effective_policy_is_usage_error(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--show-effective",
            "--proposal-stem",
            "topic-a",
        ],
    )

    assert exit_code == 2
    assert "--proposal-stem requires --pr-effective-policy" in capsys.readouterr().err


def test_dispatch_rejects_namespace_without_operation() -> None:
    result = unsafe_perform_io(
        spec_governance.dispatch(
            namespace=argparse.Namespace(
                project_root=None,
                show_effective=False,
                action=None,
                journal_event_json=None,
                pr_effective_policy=False,
                proposal_stem=[],
            ),
        ),
    )

    assert isinstance(result.failure(), UsageError)


def _matching_commented_spec_governance_block() -> str:
    return (
        "{\n"
        '  "template": "livespec"\n'
        "\n"
        "  // Optional \u2014 spec_governance: policy levers for livespec's spec-side\n"
        "  // operations. The commented defaults below are derived from the shipped\n"
        "  // spec-governance manifest.\n"
        '  //   "spec_governance": {\n'
        '  //     "propose_change_mode": "interactive",\n'
        '  //     "critique_mode": "interactive",\n'
        '  //     "in_flight_alignment": "prompt",\n'
        '  //     "doctor_dispositions": {},\n'
        '  //     "revise_decision_mode": "manual",\n'
        '  //     "drift_acceptance_mode": "human",\n'
        '  //     "ratification_review": "manual-spawn",\n'
        '  //     "ratification_reviewer_model": null,\n'
        '  //     "ratification_min_review_age_seconds": 1,\n'
        '  //     "spec_pr_merge": "manual"\n'
        "  //   }\n"
        "  //\n"
        "  // Optional \u2014 credential_wrapper: next block\n"
        "}\n"
    )


def _write_history_proposal(
    *,
    root: Path,
    version: str,
    stem: str,
    front_matter: str,
) -> None:
    proposal_dir = root / "SPECIFICATION" / "history" / version / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    (proposal_dir / f"{stem}.md").write_text(
        f"---\ntopic: {stem}\n{front_matter}---\n\n## Proposal\n\nBody.\n",
        encoding="utf-8",
    )
