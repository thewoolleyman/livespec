"""Tests for spec-governance effective policy resolvers."""

from __future__ import annotations

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
