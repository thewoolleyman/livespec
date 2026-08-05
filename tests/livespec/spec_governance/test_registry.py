"""Tests for the spec-governance registry projection."""

from __future__ import annotations

import importlib
from pathlib import Path

__all__: list[str] = []


def test_registry_module_exists_and_projects_eight_ratified_rows() -> None:
    """The registry module exposes the ratified spec-governance key set."""
    module_path = (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec"
        / "spec_governance"
        / "registry.py"
    )
    assert module_path.is_file()

    registry = importlib.import_module("livespec.spec_governance.registry")

    assert [row.key for row in registry.CONFIG_KEYS] == [
        "propose_change_mode",
        "critique_mode",
        "in_flight_alignment",
        "doctor_dispositions",
        "revise_decision_mode",
        "drift_acceptance_mode",
        "ratification_review",
        "ratification_reviewer_model",
    ]
    revise_mode = registry.CONFIG_KEYS[4]
    assert revise_mode.value_type == "enum"
    assert revise_mode.safe_default == "manual"
    assert revise_mode.per_proposal_override == "decision_policy"
    assert revise_mode.allowed_values == ["manual", "delegated", "consensus"]
    drift_mode = registry.CONFIG_KEYS[5]
    assert drift_mode.value_type == "enum"
    assert drift_mode.safe_default == "human"
    assert drift_mode.per_proposal_override is None
    assert drift_mode.allowed_values == ["human", "consensus"]
