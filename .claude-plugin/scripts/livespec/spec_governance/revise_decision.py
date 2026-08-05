"""Effective revise-decision ownership and attention predicate."""

from __future__ import annotations

from dataclasses import dataclass, field

from livespec.spec_governance.config import SpecGovernanceConfig
from livespec.spec_governance.policy import EffectivePolicy, Source

__all__: list[str] = [
    "DriftAcceptanceContext",
    "ReviseDecisionContext",
    "effective_drift_acceptance_mode",
    "effective_revise_decision_mode",
    "requires_revise_decision_input",
]


@dataclass(frozen=True, kw_only=True, slots=True)
class DriftAcceptanceContext:
    """Floors and consensus evidence for one drift-origin revise decision."""

    design_record_contradiction: bool = False
    design_record_unavailable: bool = False
    ratification_blocker: bool = False
    consensus_evidence_conforming: bool = False
    journal_ok: bool = True


@dataclass(frozen=True, kw_only=True, slots=True)
class ReviseDecisionContext:
    """Floors, override bytes, and exact evidence for one revise decision."""

    proposal_override_present: bool = False
    proposal_override: object = None
    delegated_decider_accepts: bool = False
    decision_evidence_exact: bool = False
    review_no_blockers: bool = False
    review_evidence_exact: bool = False
    design_record_contradiction: bool = False
    design_record_unavailable: bool = False
    ratification_blocker: bool = False
    drift_origin: bool = False
    drift_acceptance: DriftAcceptanceContext = field(default_factory=DriftAcceptanceContext)
    consensus_evidence_available: bool = False
    journal_ok: bool = True


def effective_drift_acceptance_mode(
    *, config: SpecGovernanceConfig, context: DriftAcceptanceContext
) -> EffectivePolicy:
    """Resolve drift acceptance ownership after every non-overridable floor."""
    floor_reason = _drift_acceptance_floor_reason(context=context)
    if floor_reason is not None:
        return _input(reason=floor_reason)
    mode = config.drift_acceptance_mode
    source: Source = "global" if mode != "human" else "default"
    if mode == "human":
        return EffectivePolicy(
            value=mode,
            source=source,
            requires_input=True,
            reason="human drift acceptance requires maintainer input",
        )
    if not context.journal_ok:
        return EffectivePolicy(
            value=mode,
            source=source,
            requires_input=True,
            reason="journal write failed",
        )
    return EffectivePolicy(
        value=mode,
        source=source,
        requires_input=False,
        reason="drift_acceptance_mode consensus owns conforming drift evidence",
    )


def _drift_acceptance_floor_reason(*, context: DriftAcceptanceContext) -> str | None:
    if context.design_record_contradiction:
        return "design-record contradiction requires maintainer input"
    if context.design_record_unavailable:
        return "design record is missing or unreachable"
    if context.ratification_blocker:
        return "ratification-review blocker requires maintainer input"
    if not context.consensus_evidence_conforming:
        return "consensus-tier evidence is absent, stale, or non-conforming"
    return None


def effective_revise_decision_mode(
    *, config: SpecGovernanceConfig, context: ReviseDecisionContext
) -> EffectivePolicy:
    """Resolve one proposal's decision owner after every non-overridable floor."""
    if (
        context.design_record_contradiction
        or context.design_record_unavailable
        or context.ratification_blocker
    ):
        return _input(reason="design, review, or drift authority requires human input")
    if context.drift_origin:
        return effective_drift_acceptance_mode(
            config=config,
            context=context.drift_acceptance,
        )
    if context.proposal_override_present:
        value = context.proposal_override
        if not isinstance(value, str) or value not in {"manual", "delegated", "consensus"}:
            return EffectivePolicy(
                value="manual",
                source="proposal",
                requires_input=True,
                reason="invalid proposal decision_policy resolves safely to manual",
            )
        mode = value
        source: Source = "proposal"
    else:
        mode = config.revise_decision_mode
        source = "global" if mode != "manual" else "default"
    if mode in {"manual", "consensus"}:
        reason = (
            "manual decision ownership requires human input"
            if mode == "manual"
            else "consensus decision evidence is unavailable"
        )
        return EffectivePolicy(value=mode, source=source, requires_input=True, reason=reason)
    if not context.journal_ok:
        return EffectivePolicy(
            value=mode,
            source=source,
            requires_input=True,
            reason="journal write failed",
        )
    exact_agreement = all(
        (
            context.delegated_decider_accepts,
            context.decision_evidence_exact,
            context.review_no_blockers,
            context.review_evidence_exact,
        )
    )
    return EffectivePolicy(
        value=mode,
        source=source,
        requires_input=not exact_agreement,
        reason=(
            "delegated decider and independent no-blockers review agree on exact bytes"
            if exact_agreement
            else "delegated decision or independent review evidence is missing or disagrees"
        ),
    )


def requires_revise_decision_input(*, policy: EffectivePolicy) -> bool:
    """Return true unless one valid automated owner owns the exact decision."""
    return policy.requires_input


def _input(*, reason: str) -> EffectivePolicy:
    return EffectivePolicy(value=None, source="hard-floor", requires_input=True, reason=reason)
