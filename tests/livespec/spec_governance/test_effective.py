"""Tests for spec-governance effective policy resolvers."""

from __future__ import annotations

from dataclasses import replace

from livespec.spec_governance import effective as effective_module
from livespec.spec_governance.config import SpecGovernanceConfig
from livespec.spec_governance.effective import (
    DoctorContext,
    RatificationContext,
    awaits_ratification_review,
    effective_critique_mode,
    effective_doctor_disposition,
    effective_in_flight_alignment,
    effective_propose_change_mode,
    effective_ratification_review,
    requires_critique_input,
    requires_doctor_disposition_input,
    requires_propose_change_input,
)

__all__: list[str] = []


def test_authoring_hard_floor_precedes_invocation_and_global() -> None:
    config = SpecGovernanceConfig(propose_change_mode="batch")

    policy = effective_propose_change_mode(
        config=config,
        invocation_mode="batch",
        contradictory_envelope=True,
    )

    assert policy.source == "hard-floor"
    assert requires_propose_change_input(policy=policy)


def test_authoring_invocation_precedes_global_then_default() -> None:
    config = SpecGovernanceConfig(propose_change_mode="batch")

    invocation = effective_propose_change_mode(config=config, invocation_mode="interactive")
    global_policy = effective_propose_change_mode(config=config)
    default_policy = effective_propose_change_mode(config=SpecGovernanceConfig())

    assert invocation.source == "invocation"
    assert invocation.value == "interactive"
    assert global_policy.source == "global"
    assert global_policy.value == "batch"
    assert default_policy.source == "default"
    assert default_policy.value == "interactive"


def test_in_flight_alignment_conflict_floor_blocks_default_align() -> None:
    policy = effective_in_flight_alignment(
        config=SpecGovernanceConfig(in_flight_alignment="default-align"),
        semantic_conflict=True,
    )

    assert policy.source == "hard-floor"
    assert policy.requires_input


def test_in_flight_alignment_global_default_align_path() -> None:
    policy = effective_in_flight_alignment(
        config=SpecGovernanceConfig(in_flight_alignment="default-align"),
    )

    assert policy.source == "global"
    assert not policy.requires_input


def test_critique_incomplete_batch_and_alignment_invocation_paths() -> None:
    critique = effective_critique_mode(
        config=SpecGovernanceConfig(critique_mode="batch"),
        invocation_mode="batch",
        batch_complete=False,
    )
    alignment = effective_in_flight_alignment(
        config=SpecGovernanceConfig(),
        invocation_relationship="align",
    )

    assert requires_critique_input(policy=critique)
    assert alignment.source == "invocation"
    assert alignment.value == "align"


def test_doctor_disposition_precedence_and_predicate() -> None:
    config = SpecGovernanceConfig(doctor_dispositions={"doctor-a": "defer"})

    invocation = effective_doctor_disposition(
        config=config,
        check_id="doctor-a",
        context=DoctorContext(invocation_disposition="dismiss"),
    )
    global_policy = effective_doctor_disposition(
        config=config,
        check_id="doctor-a",
        context=DoctorContext(),
    )
    unmapped = effective_doctor_disposition(
        config=config,
        check_id="doctor-b",
        context=DoctorContext(),
    )
    floor = effective_doctor_disposition(
        config=config,
        check_id="doctor-a",
        context=DoctorContext(design_record_blocked=True),
    )

    assert invocation.source == "invocation"
    assert invocation.value == "dismiss"
    assert global_policy.source == "global"
    assert global_policy.value == "defer"
    assert requires_doctor_disposition_input(policy=unmapped)
    assert floor.source == "hard-floor"


def test_doctor_accepts_only_canonical_ids_and_allowed_dispositions() -> None:
    config = SpecGovernanceConfig(doctor_dispositions={"doctor-a": "defer"})

    invalid_id = effective_doctor_disposition(
        config=config,
        check_id="not-a-doctor-id",
        context=DoctorContext(invocation_disposition="dismiss"),
    )
    invalid_invocation = effective_doctor_disposition(
        config=config,
        check_id="doctor-a",
        context=DoctorContext(invocation_disposition="nope"),
    )
    allowed = [
        effective_doctor_disposition(
            config=SpecGovernanceConfig(doctor_dispositions={"doctor-a": verb}),
            check_id="doctor-a",
            context=DoctorContext(),
        )
        for verb in (
            "fix-now",
            "capture-as-work-item",
            "propose-change",
            "defer",
            "dismiss",
        )
    ]

    assert invalid_id.requires_input
    assert invalid_id.value is None
    assert invalid_invocation.source == "invocation"
    assert invalid_invocation.requires_input
    assert [policy.value for policy in allowed] == [
        "fix-now",
        "capture-as-work-item",
        "propose-change",
        "defer",
        "dismiss",
    ]


def test_doctor_executability_failures_do_not_fall_through() -> None:
    config = SpecGovernanceConfig(doctor_dispositions={"doctor-a": "fix-now"})
    policy = effective_doctor_disposition(
        config=config, check_id="doctor-a", context=DoctorContext(action_available=False)
    )
    no_consent = effective_doctor_disposition(
        config=config, check_id="doctor-a", context=DoctorContext(downstream_consent=False)
    )
    journal_failed = effective_doctor_disposition(
        config=config, check_id="doctor-a", context=DoctorContext(journal_ok=False)
    )
    execution_failed = effective_doctor_disposition(
        config=config, check_id="doctor-a", context=DoctorContext(execution_ok=False)
    )

    assert policy.value is None
    assert policy.requires_input
    assert no_consent.requires_input
    assert no_consent.source == "global"
    assert journal_failed.requires_input
    assert execution_failed.requires_input


def test_ratification_review_requires_model_and_evidence() -> None:
    missing_model = effective_ratification_review(
        config=SpecGovernanceConfig(),
        context=RatificationContext(),
    )
    proposal_override = effective_ratification_review(
        config=SpecGovernanceConfig(ratification_reviewer_model="fable"),
        context=RatificationContext(proposal_override="auto-spawn"),
    )
    satisfied = effective_ratification_review(
        config=SpecGovernanceConfig(ratification_reviewer_model="fable"),
        context=RatificationContext(no_blockers_evidence=True),
    )

    assert awaits_ratification_review(policy=missing_model)
    assert proposal_override.source == "proposal"
    assert proposal_override.value == "auto-spawn"
    assert not awaits_ratification_review(policy=satisfied)


def test_ratification_blocker_and_global_paths() -> None:
    blocked = effective_ratification_review(
        config=SpecGovernanceConfig(ratification_reviewer_model="fable"),
        context=RatificationContext(blockers_present=True),
    )
    global_policy = effective_ratification_review(
        config=SpecGovernanceConfig(
            ratification_review="auto-spawn",
            ratification_reviewer_model="fable",
        ),
        context=RatificationContext(),
    )

    assert blocked.source == "hard-floor"
    assert global_policy.source == "global"
    assert global_policy.value == "auto-spawn"


def test_revise_decision_floors_precede_proposal_and_global_modes() -> None:
    assert hasattr(effective_module, "effective_revise_decision_mode")
    from livespec.spec_governance.effective import (
        ReviseDecisionContext,
        effective_revise_decision_mode,
        requires_revise_decision_input,
    )

    clear = ReviseDecisionContext(
        proposal_override_present=True,
        proposal_override="delegated",
        delegated_decider_accepts=True,
        decision_evidence_exact=True,
        review_no_blockers=True,
        review_evidence_exact=True,
    )
    floor_contexts = (
        replace(clear, design_record_contradiction=True),
        replace(clear, design_record_unavailable=True),
        replace(clear, ratification_blocker=True),
        replace(clear, drift_origin=True),
    )

    policies = [
        effective_revise_decision_mode(
            config=SpecGovernanceConfig(revise_decision_mode="delegated"),
            context=context,
        )
        for context in floor_contexts
    ]

    assert all(policy.source == "hard-floor" for policy in policies)
    assert all(requires_revise_decision_input(policy=policy) for policy in policies)


def test_revise_decision_override_resolution_is_safe_and_file_scoped() -> None:
    assert hasattr(effective_module, "effective_revise_decision_mode")
    from livespec.spec_governance.effective import (
        ReviseDecisionContext,
        effective_revise_decision_mode,
        requires_revise_decision_input,
    )

    config = SpecGovernanceConfig(revise_decision_mode="delegated")
    inherited = effective_revise_decision_mode(
        config=config,
        context=ReviseDecisionContext(
            delegated_decider_accepts=True,
            decision_evidence_exact=True,
            review_no_blockers=True,
            review_evidence_exact=True,
        ),
    )
    malformed = [
        effective_revise_decision_mode(
            config=config,
            context=ReviseDecisionContext(
                proposal_override_present=True,
                proposal_override=value,
            ),
        )
        for value in (True, 7, "robot", None)
    ]

    assert inherited.value == "delegated"
    assert inherited.source == "global"
    assert not requires_revise_decision_input(policy=inherited)
    assert all(policy.value == "manual" for policy in malformed)
    assert all(policy.source == "proposal" for policy in malformed)
    assert all(requires_revise_decision_input(policy=policy) for policy in malformed)


def test_delegated_revise_requires_both_exact_independent_signals() -> None:
    assert hasattr(effective_module, "effective_revise_decision_mode")
    from livespec.spec_governance.effective import (
        ReviseDecisionContext,
        effective_revise_decision_mode,
        requires_revise_decision_input,
    )

    config = SpecGovernanceConfig(revise_decision_mode="delegated")
    agreed = ReviseDecisionContext(
        delegated_decider_accepts=True,
        decision_evidence_exact=True,
        review_no_blockers=True,
        review_evidence_exact=True,
    )
    disagreements = (
        replace(agreed, delegated_decider_accepts=False),
        replace(agreed, decision_evidence_exact=False),
        replace(agreed, review_no_blockers=False),
        replace(agreed, review_evidence_exact=False),
    )

    accepted = effective_revise_decision_mode(config=config, context=agreed)
    escalated = [
        effective_revise_decision_mode(config=config, context=context) for context in disagreements
    ]

    assert not requires_revise_decision_input(policy=accepted)
    assert all(requires_revise_decision_input(policy=policy) for policy in escalated)


def test_consensus_unavailable_and_journal_failure_always_escalate() -> None:
    assert hasattr(effective_module, "effective_revise_decision_mode")
    from livespec.spec_governance.effective import (
        ReviseDecisionContext,
        effective_revise_decision_mode,
        requires_revise_decision_input,
    )

    consensus = effective_revise_decision_mode(
        config=SpecGovernanceConfig(revise_decision_mode="consensus"),
        context=ReviseDecisionContext(consensus_evidence_available=True),
    )
    journal_failed = effective_revise_decision_mode(
        config=SpecGovernanceConfig(revise_decision_mode="delegated"),
        context=ReviseDecisionContext(
            delegated_decider_accepts=True,
            decision_evidence_exact=True,
            review_no_blockers=True,
            review_evidence_exact=True,
            journal_ok=False,
        ),
    )

    assert requires_revise_decision_input(policy=consensus)
    assert requires_revise_decision_input(policy=journal_failed)


def test_drift_acceptance_resolves_floors_before_global_consensus() -> None:
    assert hasattr(effective_module, "effective_drift_acceptance_mode")
    from livespec.spec_governance.effective import (
        DriftAcceptanceContext,
        effective_drift_acceptance_mode,
        requires_revise_decision_input,
    )

    clear = DriftAcceptanceContext(consensus_evidence_conforming=True)
    floor_contexts = (
        replace(clear, design_record_contradiction=True),
        replace(clear, design_record_unavailable=True),
        replace(clear, ratification_blocker=True),
        replace(clear, consensus_evidence_conforming=False),
    )

    policies = [
        effective_drift_acceptance_mode(
            config=SpecGovernanceConfig(drift_acceptance_mode="consensus"),
            context=context,
        )
        for context in floor_contexts
    ]
    default = effective_drift_acceptance_mode(
        config=SpecGovernanceConfig(),
        context=clear,
    )
    consensus = effective_drift_acceptance_mode(
        config=SpecGovernanceConfig(drift_acceptance_mode="consensus"),
        context=clear,
    )

    assert all(policy.source == "hard-floor" for policy in policies)
    assert all(requires_revise_decision_input(policy=policy) for policy in policies)
    assert default.value == "human"
    assert default.source == "default"
    assert requires_revise_decision_input(policy=default)
    assert consensus.value == "consensus"
    assert consensus.source == "global"
    assert not requires_revise_decision_input(policy=consensus)


def test_revise_decision_routes_drift_only_through_drift_acceptance() -> None:
    assert hasattr(effective_module, "effective_revise_decision_mode")
    from livespec.spec_governance.effective import (
        DriftAcceptanceContext,
        ReviseDecisionContext,
        effective_revise_decision_mode,
        requires_revise_decision_input,
    )

    drift = effective_revise_decision_mode(
        config=SpecGovernanceConfig(
            revise_decision_mode="delegated",
            drift_acceptance_mode="consensus",
        ),
        context=ReviseDecisionContext(
            proposal_override_present=True,
            proposal_override="delegated",
            delegated_decider_accepts=True,
            decision_evidence_exact=True,
            review_no_blockers=True,
            review_evidence_exact=True,
            drift_origin=True,
            drift_acceptance=DriftAcceptanceContext(consensus_evidence_conforming=True),
        ),
    )

    assert drift.value == "consensus"
    assert drift.source == "global"
    assert "drift_acceptance_mode" in drift.reason
    assert not requires_revise_decision_input(policy=drift)
