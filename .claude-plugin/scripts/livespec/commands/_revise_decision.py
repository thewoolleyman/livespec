"""Effective revise-decision ownership enforcement before governed mutation."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from returns.io import IOResult

from livespec.commands._revise_ratification import _canonical_ratification_digest
from livespec.errors import LivespecError, ValidationError
from livespec.parse import front_matter
from livespec.schemas.dataclasses.revise_input import RevisionInput
from livespec.spec_governance.config import SpecGovernanceConfig, parse_config_text
from livespec.spec_governance.effective import (
    ReviseDecisionContext,
    effective_revise_decision_mode,
    requires_revise_decision_input,
)
from livespec.spec_governance.journal import append_journal_payload

__all__: list[str] = ["enforce_revise_decisions"]


def enforce_revise_decisions(
    *, revise_input: RevisionInput, project_root: Path, spec_target: Path
) -> IOResult[RevisionInput, LivespecError]:
    """Resolve each file policy and append every automated event before mutation."""
    config = _effective_config(project_root=project_root)
    for decision in revise_input.decisions:
        topic = str(decision.get("proposal_topic", ""))
        proposal_path = spec_target / "proposed_changes" / f"{topic}.md"
        try:
            proposal_bytes = proposal_path.read_bytes()
            proposal_text = proposal_bytes.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return IOResult.from_failure(
                ValidationError(f"revise: decision proposal cannot be read: {exc}")
            )
        parsed = front_matter.parse_front_matter(text=proposal_text).value_or({})
        raw_front = parsed
        context_data = decision.get("revise_decision_context")
        raw_context = cast(
            dict[str, object], context_data if isinstance(context_data, dict) else {}
        )
        evidence_data = decision.get("delegated_decision_evidence")
        evidence = cast(dict[str, object], evidence_data if isinstance(evidence_data, dict) else {})
        review_data = decision.get("ratification_evidence")
        review = cast(dict[str, object], review_data if isinstance(review_data, dict) else {})
        digest = _canonical_ratification_digest(
            decision=decision,
            proposal_bytes=proposal_bytes,
        )
        context = ReviseDecisionContext(
            proposal_override_present="decision_policy" in raw_front,
            proposal_override=raw_front.get("decision_policy"),
            delegated_decider_accepts=evidence.get("accepted") is True,
            decision_evidence_exact=(
                evidence.get("proposal_stem") == topic
                and evidence.get("content_digest") == digest
                and evidence.get("selected_decision") == decision.get("decision")
            ),
            review_no_blockers=review.get("verdict") == "NO BLOCKERS",
            review_evidence_exact=(
                review.get("proposal_stem") == topic and review.get("content_digest") == digest
            ),
            design_record_contradiction=raw_context.get("design_record_contradiction") is True,
            design_record_unavailable=raw_context.get("design_record_unavailable") is True,
            ratification_blocker=raw_context.get("ratification_blocker") is True,
            drift_origin=raw_context.get("drift_origin") is True,
            consensus_evidence_available=raw_context.get("consensus_evidence_available") is True,
        )
        policy = effective_revise_decision_mode(config=config, context=context)
        if requires_revise_decision_input(policy=policy):
            explicit_confirmation_needed = policy.source == "hard-floor" or policy.value in {
                "delegated",
                "consensus",
            }
            if (
                explicit_confirmation_needed
                and raw_context.get("human_decision_confirmed") is not True
            ):
                return IOResult.from_failure(
                    ValidationError(f"revise: human decision input required: {policy.reason}")
                )
            continue
        journal_result = append_journal_payload(
            project_root=project_root,
            event={
                "event_type": "revise_decision",
                "proposal_stem": topic,
                "content_digest": digest,
                "effective_mode": policy.value,
                "effective_source": policy.source,
                "selected_decision": decision.get("decision"),
                "decider_identity": evidence.get("decider_identity"),
                "decider_model": evidence.get("decider_model"),
                "review_outcome": review.get("verdict"),
                "final_outcome": "proceed",
                "escalation_reason": "",
                "outcome": "selected",
            },
        )
        if isinstance(journal_result, str):
            return IOResult.from_failure(
                ValidationError(f"revise: governed mutation blocked: {journal_result}")
            )
    return IOResult.from_value(revise_input)


def _effective_config(*, project_root: Path) -> SpecGovernanceConfig:
    config_path = project_root / ".livespec.jsonc"
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        text = "{}"
    return parse_config_text(text=text).effective
