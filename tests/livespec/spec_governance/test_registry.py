"""Tests for the spec-governance registry projection."""

from __future__ import annotations

import importlib
from pathlib import Path

__all__: list[str] = []


def test_registry_module_exists_and_projects_ten_ratified_rows() -> None:
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
        "ratification_min_review_age_seconds",
        "spec_pr_merge",
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
    review_age = registry.CONFIG_KEYS[8]
    assert review_age.value_type == "integer"
    assert review_age.safe_default == 1
    assert review_age.per_proposal_override is None
    assert review_age.allowed_values == []
    spec_pr_merge = registry.CONFIG_KEYS[9]
    assert spec_pr_merge.value_type == "enum"
    assert spec_pr_merge.safe_default == "manual"
    assert spec_pr_merge.per_proposal_override == "spec_pr_merge_policy"
    assert spec_pr_merge.allowed_values == ["manual", "auto-on-green"]


def test_spec_governance_manifest_and_block_logic_delegate_to_runtime() -> None:
    """Core keeps compatibility modules, while runtime owns the manifest/checker."""
    package_path = (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec"
        / "spec_governance"
    )

    registry_source = (package_path / "registry.py").read_text(encoding="utf-8")
    default_block_source = (package_path / "default_block.py").read_text(encoding="utf-8")

    assert "livespec_runtime.spec_governance.registry" in registry_source
    assert "livespec_runtime.spec_governance.default_block" in default_block_source
    assert "ConfigKey(" not in registry_source
    assert "def verify_default_block" not in default_block_source
