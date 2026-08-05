"""Direct module-surface test for revise-decision policy exports."""

from livespec.spec_governance import revise_decision
from livespec.spec_governance.config import SpecGovernanceConfig

__all__: list[str] = []


def test_revise_decision_module_exports_resolver_context_and_predicate() -> None:
    assert set(revise_decision.__all__) == {
        "DriftAcceptanceContext",
        "ReviseDecisionContext",
        "effective_drift_acceptance_mode",
        "effective_revise_decision_mode",
        "requires_revise_decision_input",
    }


def test_valid_proposal_override_owns_only_that_resolution() -> None:
    policy = revise_decision.effective_revise_decision_mode(
        config=SpecGovernanceConfig(revise_decision_mode="manual"),
        context=revise_decision.ReviseDecisionContext(
            proposal_override_present=True,
            proposal_override="delegated",
            delegated_decider_accepts=True,
            decision_evidence_exact=True,
            review_no_blockers=True,
            review_evidence_exact=True,
        ),
    )

    assert policy.value == "delegated"
    assert policy.source == "proposal"
    assert not revise_decision.requires_revise_decision_input(policy=policy)


def test_drift_acceptance_consensus_requires_journal_success() -> None:
    policy = revise_decision.effective_drift_acceptance_mode(
        config=SpecGovernanceConfig(drift_acceptance_mode="consensus"),
        context=revise_decision.DriftAcceptanceContext(
            consensus_evidence_conforming=True,
            journal_ok=False,
        ),
    )

    assert policy.value == "consensus"
    assert policy.source == "global"
    assert revise_decision.requires_revise_decision_input(policy=policy)
    assert policy.reason == "journal write failed"
