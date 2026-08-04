"""Tests for pre-mutation revise-decision ownership enforcement."""

from __future__ import annotations

from pathlib import Path

from livespec.commands import _revise_decision
from livespec.commands._revise_ratification import _canonical_ratification_digest
from livespec.schemas.dataclasses.revise_input import RevisionInput
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_delegated_journal_failure_blocks_downstream_mutation(
    *, tmp_path: Path, monkeypatch
) -> None:  # pyright: ignore[reportUnknownParameterType,reportMissingParameterType]
    spec_target = tmp_path / "SPECIFICATION"
    proposals = spec_target / "proposed_changes"
    proposals.mkdir(parents=True)
    proposal = proposals / "demo.md"
    proposal.write_text(
        "---\ntopic: demo\nauthor: agent\ncreated_at: 2026-08-04T00:00:00Z\n---\nbody\n",
        encoding="utf-8",
    )
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance":{"revise_decision_mode":"delegated"}}',
        encoding="utf-8",
    )
    decision: dict[str, object] = {
        "proposal_topic": "demo",
        "decision": "accept",
        "rationale": "accepted",
        "resulting_files": [{"path": "spec.md", "content": "new"}],
    }
    digest = _canonical_ratification_digest(
        decision=decision,
        proposal_bytes=proposal.read_bytes(),
    )
    decision["ratification_evidence"] = {
        "proposal_stem": "demo",
        "content_digest": digest,
        "verdict": "NO BLOCKERS",
    }
    decision["delegated_decision_evidence"] = {
        "decider_identity": "delegate",
        "decider_model": "model",
        "proposal_stem": "demo",
        "content_digest": digest,
        "selected_decision": "accept",
        "accepted": True,
    }
    monkeypatch.setattr(
        _revise_decision,
        "append_journal_payload",
        lambda **_kwargs: "induced journal failure",
    )
    result = unsafe_perform_io(
        _revise_decision.enforce_revise_decisions(
            revise_input=RevisionInput(author=None, decisions=[decision]),
            project_root=tmp_path,
            spec_target=spec_target,
        )
    )
    assert isinstance(result, Failure)
    assert not (spec_target / "spec.md").exists()


def test_delegated_exact_agreement_appends_before_success(*, tmp_path: Path) -> None:
    spec_target = tmp_path / "SPECIFICATION"
    proposals = spec_target / "proposed_changes"
    proposals.mkdir(parents=True)
    proposal = proposals / "demo.md"
    proposal.write_text(
        "---\ntopic: demo\nauthor: agent\ncreated_at: 2026-08-04T00:00:00Z\n---\nbody\n",
        encoding="utf-8",
    )
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance":{"revise_decision_mode":"delegated"}}',
        encoding="utf-8",
    )
    decision: dict[str, object] = {
        "proposal_topic": "demo",
        "decision": "accept",
        "rationale": "accepted",
        "resulting_files": [],
    }
    digest = _canonical_ratification_digest(decision=decision, proposal_bytes=proposal.read_bytes())
    decision["ratification_evidence"] = {
        "proposal_stem": "demo",
        "content_digest": digest,
        "verdict": "NO BLOCKERS",
    }
    decision["delegated_decision_evidence"] = {
        "decider_identity": "delegate",
        "decider_model": "model",
        "proposal_stem": "demo",
        "content_digest": digest,
        "selected_decision": "accept",
        "accepted": True,
    }

    result = unsafe_perform_io(
        _revise_decision.enforce_revise_decisions(
            revise_input=RevisionInput(author=None, decisions=[decision]),
            project_root=tmp_path,
            spec_target=spec_target,
        )
    )

    assert isinstance(result, Success)
    assert (tmp_path / "tmp" / "livespec-spec-governance-journal.jsonl").is_file()


def test_delegated_missing_evidence_requires_explicit_human_input(*, tmp_path: Path) -> None:
    spec_target = tmp_path / "SPECIFICATION"
    proposals = spec_target / "proposed_changes"
    proposals.mkdir(parents=True)
    (proposals / "demo.md").write_text(
        "---\ntopic: demo\nauthor: agent\ncreated_at: 2026-08-04T00:00:00Z\n---\nbody\n",
        encoding="utf-8",
    )
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance":{"revise_decision_mode":"delegated"}}',
        encoding="utf-8",
    )
    revise_input = RevisionInput(
        author=None, decisions=[{"proposal_topic": "demo", "decision": "reject"}]
    )

    result = unsafe_perform_io(
        _revise_decision.enforce_revise_decisions(
            revise_input=revise_input,
            project_root=tmp_path,
            spec_target=spec_target,
        )
    )

    assert isinstance(result, Failure)


def test_unreadable_proposal_fails_closed_with_safe_default_config(*, tmp_path: Path) -> None:
    result = unsafe_perform_io(
        _revise_decision.enforce_revise_decisions(
            revise_input=RevisionInput(
                author=None,
                decisions=[{"proposal_topic": "missing", "decision": "reject"}],
            ),
            project_root=tmp_path,
            spec_target=tmp_path / "SPECIFICATION",
        )
    )

    assert isinstance(result, Failure)
