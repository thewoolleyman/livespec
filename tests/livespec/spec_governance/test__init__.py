"""Mirror-paired test for the spec-governance package initializer."""

from __future__ import annotations

from livespec import spec_governance

__all__: list[str] = []


def test_spec_governance_init_declares_no_public_reexports() -> None:
    """The package initializer stays side-effect-free and export-neutral."""
    assert spec_governance.__all__ == []
    assert "Spec-governance registry" in (spec_governance.__doc__ or "")
