"""Effective policy resolvers and shared attention predicates."""

from __future__ import annotations

from dataclasses import dataclass

from livespec.spec_governance._effective_authoring import _authoring_mode, _input
from livespec.spec_governance.config import DOCTOR_CHECK_ID_PATTERN, SpecGovernanceConfig
from livespec.spec_governance.policy import EffectivePolicy, Source
from livespec.spec_governance.registry import CONFIG_KEYS
from livespec.spec_governance.revise_decision import (
    DriftAcceptanceContext,
    ReviseDecisionContext,
    effective_drift_acceptance_mode,
    effective_revise_decision_mode,
    requires_revise_decision_input,
)
from livespec.spec_governance.spec_pr_merge import awaits_manual_spec_pr_merge

__all__: list[str] = [
    "DoctorContext",
    "DriftAcceptanceContext",
    "EffectivePolicy",
    "RatificationContext",
    "ReviseDecisionContext",
    "awaits_manual_spec_pr_merge",
    "awaits_ratification_review",
    "effective_critique_mode",
    "effective_doctor_disposition",
    "effective_drift_acceptance_mode",
    "effective_in_flight_alignment",
    "effective_propose_change_mode",
    "effective_ratification_review",
    "effective_revise_decision_mode",
    "requires_critique_input",
    "requires_doctor_disposition_input",
    "requires_propose_change_input",
    "requires_revise_decision_input",
]

_DOCTOR_DISPOSITIONS = frozenset(
    disposition
    for row in CONFIG_KEYS
    if row.key == "doctor_dispositions"
    for disposition in row.allowed_values
)


@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorContext:
    """Hard-floor and executability facts for one doctor finding."""

    design_record_blocked: bool = False
    invocation_disposition: str | None = None
    action_available: bool = True
    downstream_consent: bool = True
    journal_ok: bool = True
    execution_ok: bool = True


@dataclass(frozen=True, kw_only=True, slots=True)
class RatificationContext:
    """Hard-floor and override facts for one ratification review."""

    proposal_override: str | None = None
    blockers_present: bool = False
    reviewer_unavailable: bool = False
    no_blockers_evidence: bool = False


def effective_propose_change_mode(
    *,
    config: SpecGovernanceConfig,
    invocation_mode: str | None = None,
    contradictory_envelope: bool = False,
    batch_complete: bool = True,
) -> EffectivePolicy:
    """Resolve propose-change mode: hard floors, invocation, global, default."""
    return _authoring_mode(
        global_value=config.propose_change_mode,
        invocation_mode=invocation_mode,
        contradictory_envelope=contradictory_envelope,
        batch_complete=batch_complete,
    )


def effective_critique_mode(
    *,
    config: SpecGovernanceConfig,
    invocation_mode: str | None = None,
    contradictory_envelope: bool = False,
    batch_complete: bool = True,
) -> EffectivePolicy:
    """Resolve critique mode: hard floors, invocation, global, default."""
    return _authoring_mode(
        global_value=config.critique_mode,
        invocation_mode=invocation_mode,
        contradictory_envelope=contradictory_envelope,
        batch_complete=batch_complete,
    )


def effective_in_flight_alignment(
    *,
    config: SpecGovernanceConfig,
    invocation_relationship: str | None = None,
    semantic_conflict: bool = False,
    supersession_requested: bool = False,
) -> EffectivePolicy:
    """Resolve in-flight alignment after conflict/supersession floors."""
    if semantic_conflict or supersession_requested:
        return EffectivePolicy(
            value=None,
            source="hard-floor",
            requires_input=True,
            reason="conflict or supersession requires human alignment input",
        )
    if invocation_relationship is not None:
        return EffectivePolicy(
            value=invocation_relationship,
            source="invocation",
            requires_input=False,
            reason="invocation relationship supplied",
        )
    return EffectivePolicy(
        value=config.in_flight_alignment,
        source="global" if config.in_flight_alignment != "prompt" else "default",
        requires_input=config.in_flight_alignment == "prompt",
        reason="resolved from global policy or safe default",
    )


def effective_doctor_disposition(
    *,
    config: SpecGovernanceConfig,
    check_id: str,
    context: DoctorContext,
) -> EffectivePolicy:
    """Resolve doctor disposition with hard floors before any map lookup."""
    if context.design_record_blocked:
        return _input(reason="design-record contradiction or absence requires input")
    if DOCTOR_CHECK_ID_PATTERN.fullmatch(check_id) is None:
        return _input(source="default", reason="doctor check id is invalid")
    if context.invocation_disposition is not None:
        selected = context.invocation_disposition
        source: Source = "invocation"
    else:
        selected = config.doctor_dispositions.get(check_id)
        source = "global" if selected is not None else "default"
    if selected is None:
        return _input(source=source, reason="no executable disposition is mapped")
    if selected not in _DOCTOR_DISPOSITIONS:
        return _input(source=source, reason="doctor disposition is invalid")
    failed_reason = _doctor_execution_failure_reason(context=context)
    if failed_reason is not None:
        return _input(source=source, reason=failed_reason)
    return EffectivePolicy(
        value=selected,
        source=source,
        requires_input=False,
        reason="one valid executable disposition owns the finding",
    )


def effective_ratification_review(
    *,
    config: SpecGovernanceConfig,
    context: RatificationContext,
) -> EffectivePolicy:
    """Resolve ratification review initiation policy under the review floor."""
    if context.no_blockers_evidence:
        return EffectivePolicy(
            value=None,
            source="hard-floor",
            requires_input=False,
            reason="matching no-blockers evidence already exists",
        )
    if context.blockers_present or context.reviewer_unavailable:
        return _input(reason="review blockers or reviewer unavailability require input")
    if config.ratification_reviewer_model is None:
        return _input(reason="ratification reviewer model is unconfigured")
    if context.proposal_override is not None:
        return EffectivePolicy(
            value=context.proposal_override,
            source="proposal",
            requires_input=True,
            reason="independent review still awaits evidence",
        )
    return EffectivePolicy(
        value=config.ratification_review,
        source="global" if config.ratification_review != "manual-spawn" else "default",
        requires_input=True,
        reason="independent review still awaits evidence",
    )


def requires_propose_change_input(*, policy: EffectivePolicy) -> bool:
    """Return true when propose-change still needs human input."""
    return policy.requires_input


def requires_critique_input(*, policy: EffectivePolicy) -> bool:
    """Return true when critique still needs human input."""
    return policy.requires_input


def requires_doctor_disposition_input(*, policy: EffectivePolicy) -> bool:
    """Return true when doctor disposition still needs human input."""
    return policy.requires_input


def awaits_ratification_review(*, policy: EffectivePolicy) -> bool:
    """Return true until matching no-blockers evidence exists."""
    return policy.requires_input


def _doctor_execution_failure_reason(*, context: DoctorContext) -> str | None:
    if not context.action_available:
        return "mapped action is unavailable"
    if not context.downstream_consent:
        return "downstream store-write consent is absent"
    if not context.journal_ok:
        return "journal write failed"
    if not context.execution_ok:
        return "selected action failed"
    return None
