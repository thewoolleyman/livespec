"""Tests for the spec-governance registry projection."""

from __future__ import annotations

import importlib
from pathlib import Path

__all__: list[str] = []


def test_registry_module_exists_and_projects_seven_ratified_rows() -> None:
    """The registry module exposes the six Increment 1 rows plus Increment 2."""
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
        "ratification_review",
        "ratification_reviewer_model",
    ]
    revise_mode = registry.CONFIG_KEYS[4]
    assert revise_mode.value_type == "enum"
    assert revise_mode.safe_default == "manual"
    assert revise_mode.per_proposal_override == "decision_policy"
    assert revise_mode.allowed_values == ["manual", "delegated", "consensus"]
