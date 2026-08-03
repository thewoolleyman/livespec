"""Tests for the spec-governance registry projection."""

from __future__ import annotations

import importlib
from pathlib import Path

__all__: list[str] = []


def test_registry_module_exists_and_projects_six_increment_one_rows() -> None:
    """The registry module exists and exposes the six ratified rows."""
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
        "ratification_review",
        "ratification_reviewer_model",
    ]
