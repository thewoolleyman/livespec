"""Tests for spec-governance safe-default config parsing."""

from __future__ import annotations

from livespec.spec_governance.config import parse_config_text

__all__: list[str] = []


def test_missing_block_resolves_to_safe_defaults() -> None:
    declared = parse_config_text(text='{"template": "livespec"}')

    assert declared.effective.propose_change_mode == "interactive"
    assert declared.effective.critique_mode == "interactive"
    assert declared.effective.in_flight_alignment == "prompt"
    assert declared.effective.doctor_dispositions == {}
    assert declared.effective.revise_decision_mode == "manual"
    assert declared.effective.drift_acceptance_mode == "human"
    assert declared.effective.ratification_review == "manual-spawn"
    assert declared.effective.ratification_reviewer_model is None
    assert declared.effective.ratification_min_review_age_seconds == 1
    assert declared.effective.spec_pr_merge == "manual"
    assert declared.diagnostics


def test_malformed_jsonc_resolves_to_safe_defaults() -> None:
    declared = parse_config_text(text="{")

    assert declared.raw == {}
    assert declared.effective.ratification_review == "manual-spawn"
    assert "malformed" in declared.diagnostics[0]


def test_invalid_entries_are_ignored_without_losing_valid_siblings() -> None:
    declared = parse_config_text(
        text="""
        {
          "spec_governance": {
            "propose_change_mode": "robot",
            "critique_mode": "batch",
            "in_flight_alignment": 7,
            "doctor_dispositions": {
              "doctor-good-check": "defer",
              "bad id": "dismiss",
              "doctor-bad-value": "nope"
            },
            "revise_decision_mode": "robot",
            "drift_acceptance_mode": "delegated",
            "ratification_review": "auto-spawn",
            "ratification_reviewer_model": "bad model!",
            "ratification_min_review_age_seconds": 0,
            "spec_pr_merge": "delegate"
          }
        }
        """,
    )

    assert declared.effective.propose_change_mode == "interactive"
    assert declared.effective.critique_mode == "batch"
    assert declared.effective.in_flight_alignment == "prompt"
    assert declared.effective.doctor_dispositions == {"doctor-good-check": "defer"}
    assert declared.effective.revise_decision_mode == "manual"
    assert declared.effective.drift_acceptance_mode == "human"
    assert declared.effective.ratification_review == "auto-spawn"
    assert declared.effective.ratification_reviewer_model is None
    assert declared.effective.ratification_min_review_age_seconds == 1
    assert declared.effective.spec_pr_merge == "manual"
    assert len(declared.diagnostics) == 9


def test_wrong_typed_doctor_dispositions_map_resolves_to_empty() -> None:
    declared = parse_config_text(
        text='{"spec_governance": {"doctor_dispositions": "defer"}}',
    )

    assert declared.effective.doctor_dispositions == {}
    assert "invalid map" in declared.diagnostics[0]


def test_all_valid_entries_project_to_effective_config() -> None:
    declared = parse_config_text(
        text="""
        {
          "spec_governance": {
            "propose_change_mode": "batch",
            "critique_mode": "batch",
            "in_flight_alignment": "default-align",
            "doctor_dispositions": {"doctor-x": "fix-now"},
            "revise_decision_mode": "delegated",
            "drift_acceptance_mode": "consensus",
            "ratification_review": "auto-spawn",
            "ratification_reviewer_model": "fable/model-1",
            "ratification_min_review_age_seconds": 120,
            "spec_pr_merge": "auto-on-green"
          }
        }
        """,
    )

    assert declared.effective.propose_change_mode == "batch"
    assert declared.effective.critique_mode == "batch"
    assert declared.effective.in_flight_alignment == "default-align"
    assert declared.effective.doctor_dispositions == {"doctor-x": "fix-now"}
    assert declared.effective.revise_decision_mode == "delegated"
    assert declared.effective.drift_acceptance_mode == "consensus"
    assert declared.effective.ratification_review == "auto-spawn"
    assert declared.effective.ratification_reviewer_model == "fable/model-1"
    assert declared.effective.ratification_min_review_age_seconds == 120
    assert declared.effective.spec_pr_merge == "auto-on-green"
    assert declared.diagnostics == []
