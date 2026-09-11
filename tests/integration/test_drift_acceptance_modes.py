"""Integration-tier coverage for `SPECIFICATION/scenarios.md`.

Covers the H2 section "Drift acceptance under each mode" end-to-end over
the shipped drift-acceptance resolver (`effective_drift_acceptance_mode`),
the revise-decision router (`effective_revise_decision_mode`), and the
shipped control surface (`apply_action` over a real `.livespec.jsonc`):

- drift acceptance defaults to human — an undeclared mode requires
  maintainer input on a drift-origin decision.
- armed consensus accepts only on conforming evidence — `consensus` with
  present, fresh, conforming, journalled evidence owns the acceptance
  (`requires_input` false); the SAME mode with non-conforming evidence
  escalates.
- delegated is refused for drift acceptance — the control surface refuses
  `set-drift-acceptance-mode:global:delegated` with the allowed-value
  diagnostic and leaves the effective value unchanged.
- revise_decision_mode cannot route drift — a repo declaring
  `revise_decision_mode: consensus` and no drift mode still resolves a
  drift-origin decision through the drift path to `human`.

The consensus-accepts case is the POSITIVE CONTROL that makes the
resolver return `requires_input=False`, proving the escalation pins are
not vacuously always-true.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.spec_governance.config import parse_config_text
from livespec.spec_governance.editing import EditResult, apply_action
from livespec.spec_governance.effective import (
    DriftAcceptanceContext,
    ReviseDecisionContext,
    effective_drift_acceptance_mode,
    effective_revise_decision_mode,
    requires_revise_decision_input,
)

__all__: list[str] = []

pytestmark = pytest.mark.integration

_CONSENSUS = '{"spec_governance": {"drift_acceptance_mode": "consensus"}}'
_CONFORMING = DriftAcceptanceContext(consensus_evidence_conforming=True, journal_ok=True)


def test_drift_acceptance_defaults_to_human() -> None:
    """An undeclared drift mode requires maintainer input."""
    config = parse_config_text(text="{}").effective

    policy = effective_drift_acceptance_mode(config=config, context=_CONFORMING)

    assert policy.value == "human"
    assert policy.source == "default"
    assert policy.requires_input


def test_armed_consensus_accepts_only_on_conforming_evidence() -> None:
    """POSITIVE CONTROL: conforming evidence lets consensus own acceptance."""
    config = parse_config_text(text=_CONSENSUS).effective

    conforming = effective_drift_acceptance_mode(config=config, context=_CONFORMING)
    non_conforming = effective_drift_acceptance_mode(
        config=config,
        context=DriftAcceptanceContext(consensus_evidence_conforming=False),
    )
    journal_failed = effective_drift_acceptance_mode(
        config=config,
        context=DriftAcceptanceContext(consensus_evidence_conforming=True, journal_ok=False),
    )

    assert not conforming.requires_input
    assert conforming.value == "consensus"
    # Escalation arms: absent/stale evidence and a failed journal both block.
    assert non_conforming.requires_input
    assert journal_failed.requires_input


def test_control_surface_refuses_delegated_for_drift(*, tmp_path: Path) -> None:
    """`set-drift-acceptance-mode:global:delegated` is refused and unchanged."""
    seeded = apply_action(
        project_root=tmp_path, action="set-drift-acceptance-mode:global:consensus"
    )
    refused = apply_action(
        project_root=tmp_path, action="set-drift-acceptance-mode:global:delegated"
    )

    assert isinstance(seeded, EditResult)
    assert isinstance(refused, str)
    assert "delegated" in refused or "human" in refused
    text = (tmp_path / ".livespec.jsonc").read_text(encoding="utf-8")
    assert '"drift_acceptance_mode": "consensus"' in text


def test_revise_decision_mode_cannot_route_drift() -> None:
    """A consensus revise-decision mode cannot route a drift-origin decision."""
    config = parse_config_text(
        text='{"spec_governance": {"revise_decision_mode": "consensus"}}'
    ).effective

    policy = effective_revise_decision_mode(
        config=config,
        context=ReviseDecisionContext(
            drift_origin=True,
            drift_acceptance=_CONFORMING,
        ),
    )

    # No drift mode is declared, so even a conforming-evidence context
    # resolves through the drift path to the human default, never through
    # the consensus revise_decision_mode.
    assert policy.value == "human"
    assert requires_revise_decision_input(policy=policy)
