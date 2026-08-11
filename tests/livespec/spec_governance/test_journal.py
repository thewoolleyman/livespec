"""Tests for spec-governance journal validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec.spec_governance.journal import (
    JournalAppend,
    append_journal_event,
    append_journal_payload,
    digest_json_bytes,
)

__all__: list[str] = []


def test_digest_json_bytes_is_deterministic() -> None:
    assert digest_json_bytes(payload={"b": 1, "a": 2}) == digest_json_bytes(
        payload={"a": 2, "b": 1},
    )


def test_revise_decision_event_is_digest_only_and_io_failure_is_closed(*, tmp_path: Path) -> None:
    event = {
        "event_type": "revise_decision",
        "proposal_stem": "demo",
        "content_digest": "d" * 64,
        "effective_mode": "delegated",
        "effective_source": "global",
        "selected_decision": "accept",
        "decider_identity": "delegate",
        "decider_model": "model",
        "review_outcome": "NO BLOCKERS",
        "final_outcome": "proceed",
        "escalation_reason": "",
        "outcome": "selected",
    }

    assert isinstance(
        append_journal_payload(project_root=tmp_path, event=event),
        JournalAppend,
    )
    assert isinstance(
        append_journal_payload(
            project_root=tmp_path,
            event={**event, "resulting_files": [{"content": "raw"}]},
        ),
        str,
    )
    blocked_root = tmp_path / "not-a-directory"
    blocked_root.write_text("x", encoding="utf-8")
    failed = append_journal_payload(project_root=blocked_root, event=event)
    assert isinstance(failed, str)
    assert "append failed" in failed


def test_drift_revise_decision_event_carries_digest_only_consensus_evidence(
    *,
    tmp_path: Path,
) -> None:
    event = {
        "event_type": "revise_decision",
        "proposal_stem": "demo",
        "content_digest": "d" * 64,
        "effective_mode": "consensus",
        "effective_source": "global",
        "selected_decision": "accept",
        "decider_identity": "consensus-tier",
        "decider_model": "multi",
        "review_outcome": "NO BLOCKERS",
        "final_outcome": "proceed",
        "escalation_reason": "",
        "effective_drift_acceptance_mode": "consensus",
        "effective_drift_acceptance_source": "global",
        "consensus_evidence_digest": "e" * 64,
        "outcome": "selected",
    }

    assert isinstance(
        append_journal_payload(project_root=tmp_path, event=event),
        JournalAppend,
    )
    assert isinstance(
        append_journal_payload(
            project_root=tmp_path,
            event={**event, "consensus_evidence": {"raw": "forbidden"}},
        ),
        str,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("effective_drift_acceptance_mode", "delegated"),
        ("effective_drift_acceptance_source", "x"),
        ("consensus_evidence_digest", "not-a-digest"),
    ],
)
def test_drift_revise_decision_event_rejects_invalid_fields(
    *,
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    event = {
        "event_type": "revise_decision",
        "proposal_stem": "demo",
        "content_digest": "d" * 64,
        "effective_mode": "consensus",
        "effective_source": "global",
        "selected_decision": "accept",
        "decider_identity": "consensus-tier",
        "decider_model": "multi",
        "review_outcome": "NO BLOCKERS",
        "final_outcome": "proceed",
        "escalation_reason": "",
        "effective_drift_acceptance_mode": "consensus",
        "effective_drift_acceptance_source": "global",
        "consensus_evidence_digest": "e" * 64,
        "outcome": "selected",
    }
    event[field] = value

    assert isinstance(append_journal_payload(project_root=tmp_path, event=event), str)


def test_drift_revise_decision_event_requires_all_drift_fields(*, tmp_path: Path) -> None:
    event = {
        "event_type": "revise_decision",
        "proposal_stem": "demo",
        "content_digest": "d" * 64,
        "effective_mode": "consensus",
        "effective_source": "global",
        "selected_decision": "accept",
        "decider_identity": "consensus-tier",
        "decider_model": "multi",
        "review_outcome": "NO BLOCKERS",
        "final_outcome": "proceed",
        "escalation_reason": "",
        "effective_drift_acceptance_mode": "consensus",
        "outcome": "selected",
    }

    assert isinstance(append_journal_payload(project_root=tmp_path, event=event), str)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("proposal_stem", "Bad"),
        ("content_digest", "bad"),
        ("effective_mode", "manual"),
        ("selected_decision", "unknown"),
        ("decider_identity", ""),
        ("decider_model", None),
        ("review_outcome", ""),
        ("final_outcome", 7),
        ("escalation_reason", None),
    ],
)
def test_revise_decision_event_rejects_invalid_fields(
    *, tmp_path: Path, field: str, value: object
) -> None:
    event = {
        "event_type": "revise_decision",
        "proposal_stem": "demo",
        "content_digest": "d" * 64,
        "effective_mode": "delegated",
        "effective_source": "global",
        "selected_decision": "accept",
        "decider_identity": "delegate",
        "decider_model": "model",
        "review_outcome": "NO BLOCKERS",
        "final_outcome": "proceed",
        "escalation_reason": "",
        "outcome": "selected",
    }
    event[field] = value

    assert isinstance(append_journal_payload(project_root=tmp_path, event=event), str)


def test_revise_decision_event_rejects_missing_required_fields(*, tmp_path: Path) -> None:
    assert isinstance(
        append_journal_payload(
            project_root=tmp_path,
            event={
                "event_type": "revise_decision",
                "effective_source": "global",
                "outcome": "selected",
            },
        ),
        str,
    )


def test_spec_pr_merge_event_validates_and_appends(*, tmp_path: Path) -> None:
    event = {
        "event_type": "spec_pr_merge",
        "pull_request_identity": "thewoolleyman/livespec#123",
        "proposal_stems": ["spec-pr-merge", "spec-pr-merge-2"],
        "effective_policy": "auto-on-green",
        "effective_source": "proposal",
        "registration_result": "registered",
        "required_gate_state": "pending",
        "merge_evidence_digest": "e" * 64,
        "outcome": "selected",
    }

    result = append_journal_payload(project_root=tmp_path, event=event)

    assert isinstance(result, JournalAppend)
    journal = tmp_path / "tmp" / "livespec-spec-governance-journal.jsonl"
    [line] = journal.read_text(encoding="utf-8").splitlines()
    assert json.loads(line) == event


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("pull_request_identity", "", "pull_request_identity"),
        ("proposal_stems", [], "proposal_stems"),
        ("proposal_stems", ["Bad"], "proposal_stems"),
        ("proposal_stems", ["same", "same"], "proposal_stems"),
        ("effective_policy", "manual", "effective_policy"),
        ("registration_result", "maybe", "registration_result"),
        ("required_gate_state", "maybe", "required_gate_state"),
        ("merge_evidence_digest", "not-a-digest", "merge_evidence_digest"),
    ],
)
def test_spec_pr_merge_event_rejects_invalid_fields(
    *,
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    event = {
        "event_type": "spec_pr_merge",
        "pull_request_identity": "thewoolleyman/livespec#123",
        "proposal_stems": ["spec-pr-merge"],
        "effective_policy": "auto-on-green",
        "effective_source": "global",
        "registration_result": "registered",
        "required_gate_state": "green",
        "outcome": "selected",
    }
    event[field] = value

    result = append_journal_payload(project_root=tmp_path, event=event)

    assert isinstance(result, str)
    assert message in result


def test_spec_pr_merge_event_rejects_raw_content_and_missing_required_fields(
    *,
    tmp_path: Path,
) -> None:
    event = {
        "event_type": "spec_pr_merge",
        "pull_request_identity": "thewoolleyman/livespec#123",
        "proposal_stems": ["spec-pr-merge"],
        "effective_policy": "auto-on-green",
        "effective_source": "global",
        "registration_result": "registered",
        "required_gate_state": "green",
        "outcome": "selected",
    }

    raw_result = append_journal_payload(
        project_root=tmp_path,
        event={**event, "proposal_content": "raw text forbidden"},
    )
    missing_result = append_journal_payload(
        project_root=tmp_path,
        event={"event_type": "spec_pr_merge", "effective_source": "global"},
    )

    assert isinstance(raw_result, str)
    assert "digests" in raw_result
    assert isinstance(missing_result, str)
    assert "missing required fields" in missing_result


def test_unknown_event_type_rejection_message_does_not_enumerate_known_types(
    *,
    tmp_path: Path,
) -> None:
    result = append_journal_payload(
        project_root=tmp_path,
        event={"event_type": "unknown", "effective_source": "global", "outcome": "failed"},
    )

    assert result == "journal event_type is unsupported"


def test_append_authoring_event_writes_canonical_jsonl(*, tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "event_type": "authoring_auto_consumption",
                "operation": "propose-change",
                "governing_key": "propose_change_mode",
                "effective_source": "global",
                "input_envelope_digest": "a" * 64,
                "outcome": "consumed",
            },
        ),
        encoding="utf-8",
    )

    result = append_journal_event(project_root=tmp_path, event_path=event_path)

    assert isinstance(result, JournalAppend)
    journal = tmp_path / "tmp" / "livespec-spec-governance-journal.jsonl"
    assert len(journal.read_text(encoding="utf-8").splitlines()) == 1


def test_rejects_raw_message_fields(*, tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "event_type": "doctor_disposition",
                "check_id": "doctor-x",
                "spec_root": "SPECIFICATION",
                "finding_message_digest": "b" * 64,
                "selected_verb": "defer",
                "governing_key": "doctor_dispositions",
                "effective_source": "global",
                "outcome": "deferred",
                "message": "raw text forbidden",
            },
        ),
        encoding="utf-8",
    )

    result = append_journal_event(project_root=tmp_path, event_path=event_path)

    assert isinstance(result, str)
    assert "digests" in result


def test_rejects_malformed_unreadable_unknown_and_missing_events(*, tmp_path: Path) -> None:
    malformed = tmp_path / "bad.json"
    malformed.write_text("{", encoding="utf-8")
    non_object = tmp_path / "list.json"
    non_object.write_text("[]", encoding="utf-8")
    unknown = tmp_path / "unknown.json"
    unknown.write_text('{"event_type": "unknown"}', encoding="utf-8")
    missing = tmp_path / "missing.json"
    missing.write_text('{"event_type": "authoring_auto_consumption"}', encoding="utf-8")

    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=tmp_path / "nope"), str
    )
    assert isinstance(append_journal_event(project_root=tmp_path, event_path=malformed), str)
    assert isinstance(append_journal_event(project_root=tmp_path, event_path=non_object), str)
    assert isinstance(append_journal_event(project_root=tmp_path, event_path=unknown), str)
    assert isinstance(append_journal_event(project_root=tmp_path, event_path=missing), str)


def test_rejects_invalid_common_authoring_doctor_and_ratification_fields(
    *,
    tmp_path: Path,
) -> None:
    invalid_source = _event_file(
        tmp_path=tmp_path,
        name="source.json",
        event={
            "event_type": "authoring_auto_consumption",
            "operation": "critique",
            "governing_key": "critique_mode",
            "effective_source": "x",
            "input_envelope_digest": "a" * 64,
            "outcome": "consumed",
        },
    )
    invalid_outcome = _event_file(
        tmp_path=tmp_path,
        name="outcome.json",
        event={
            "event_type": "authoring_auto_consumption",
            "operation": "critique",
            "governing_key": "critique_mode",
            "effective_source": "global",
            "input_envelope_digest": "a" * 64,
            "outcome": "nope",
        },
    )
    invalid_authoring = _event_file(
        tmp_path=tmp_path,
        name="authoring.json",
        event={
            "event_type": "authoring_auto_consumption",
            "operation": "seed",
            "governing_key": "propose_change_mode",
            "effective_source": "global",
            "input_envelope_digest": "not-a-digest",
            "outcome": "consumed",
        },
    )
    invalid_authoring_digest = _event_file(
        tmp_path=tmp_path,
        name="authoring-digest.json",
        event={
            "event_type": "authoring_auto_consumption",
            "operation": "critique",
            "governing_key": "critique_mode",
            "effective_source": "global",
            "input_envelope_digest": "not-a-digest",
            "outcome": "consumed",
        },
    )
    invalid_doctor_missing = _event_file(
        tmp_path=tmp_path,
        name="doctor-missing.json",
        event={
            "event_type": "doctor_disposition",
            "effective_source": "global",
            "outcome": "deferred",
        },
    )
    invalid_doctor = _event_file(
        tmp_path=tmp_path,
        name="doctor-bad.json",
        event={
            "event_type": "doctor_disposition",
            "check_id": "doctor-x",
            "spec_root": "SPECIFICATION",
            "finding_message_digest": "not-a-digest",
            "selected_verb": "defer",
            "governing_key": "doctor_dispositions",
            "effective_source": "global",
            "outcome": "deferred",
        },
    )
    invalid_doctor_verb = _event_file(
        tmp_path=tmp_path,
        name="doctor-bad-verb.json",
        event={
            "event_type": "doctor_disposition",
            "check_id": "doctor-x",
            "spec_root": "SPECIFICATION",
            "finding_message_digest": "b" * 64,
            "selected_verb": "nope",
            "governing_key": "doctor_dispositions",
            "effective_source": "global",
            "outcome": "deferred",
        },
    )
    invalid_ratification = _event_file(
        tmp_path=tmp_path,
        name="ratification-bad.json",
        event={
            "event_type": "ratification_review",
            "proposal_stem": "topic-a",
            "content_digest": "not-a-digest",
            "reviewer_identity": "fable",
            "reviewer_model": "fable",
            "verdict": "NO BLOCKERS",
            "effective_source": "proposal",
            "outcome": "spawned",
        },
    )

    assert isinstance(append_journal_event(project_root=tmp_path, event_path=invalid_source), str)
    assert isinstance(append_journal_event(project_root=tmp_path, event_path=invalid_outcome), str)
    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=invalid_authoring), str
    )
    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=invalid_authoring_digest),
        str,
    )
    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=invalid_doctor_missing),
        str,
    )
    assert isinstance(append_journal_event(project_root=tmp_path, event_path=invalid_doctor), str)
    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=invalid_doctor_verb),
        str,
    )
    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=invalid_ratification),
        str,
    )


def test_rejects_bad_doctor_check_id_and_bad_ratification_stem(*, tmp_path: Path) -> None:
    bad_doctor = _event_file(
        tmp_path=tmp_path,
        name="bad-doctor-id.json",
        event={
            "event_type": "doctor_disposition",
            "check_id": "bad",
            "spec_root": "SPECIFICATION",
            "finding_message_digest": "b" * 64,
            "selected_verb": "defer",
            "governing_key": "doctor_dispositions",
            "effective_source": "global",
            "outcome": "deferred",
        },
    )
    bad_stem = _event_file(
        tmp_path=tmp_path,
        name="bad-stem.json",
        event={
            "event_type": "ratification_review",
            "proposal_stem": "Bad",
            "content_digest": "c" * 64,
            "reviewer_identity": "fable",
            "reviewer_model": "fable",
            "verdict": "NO BLOCKERS",
            "effective_source": "proposal",
            "outcome": "spawned",
        },
    )
    bad_ratification_missing = _event_file(
        tmp_path=tmp_path,
        name="bad-ratification-missing.json",
        event={
            "event_type": "ratification_review",
            "effective_source": "proposal",
            "outcome": "spawned",
        },
    )

    assert isinstance(append_journal_event(project_root=tmp_path, event_path=bad_doctor), str)
    assert isinstance(append_journal_event(project_root=tmp_path, event_path=bad_stem), str)
    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=bad_ratification_missing),
        str,
    )


def test_doctor_and_ratification_event_validation(*, tmp_path: Path) -> None:
    doctor_path = tmp_path / "doctor.json"
    doctor_path.write_text(
        json.dumps(
            {
                "event_type": "doctor_disposition",
                "check_id": "doctor-x",
                "spec_root": "SPECIFICATION",
                "finding_message_digest": "b" * 64,
                "selected_verb": "defer",
                "governing_key": "doctor_dispositions",
                "effective_source": "global",
                "outcome": "deferred",
            },
        ),
        encoding="utf-8",
    )
    ratification_path = tmp_path / "ratification.json"
    ratification_path.write_text(
        json.dumps(
            {
                "event_type": "ratification_review",
                "proposal_stem": "topic-a",
                "content_digest": "c" * 64,
                "reviewer_identity": "fable",
                "reviewer_model": "fable",
                "verdict": "NO BLOCKERS",
                "effective_source": "proposal",
                "outcome": "spawned",
            },
        ),
        encoding="utf-8",
    )

    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=doctor_path), JournalAppend
    )
    assert isinstance(
        append_journal_event(project_root=tmp_path, event_path=ratification_path),
        JournalAppend,
    )


def _event_file(*, tmp_path: Path, name: str, event: dict[str, object]) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(event), encoding="utf-8")
    return path


def test_journal_shapes_module_is_a_leaf() -> None:
    """The extracted shape primitives must not import back into `journal`.

    `_digest` and `_SOURCE_VALUES` are shared by validators on BOTH sides
    of the split, and they were moved into the child precisely so the
    dependency runs one way: `journal` imports from here, never the
    reverse. Leaving them behind would have forced the cycle instead.
    """
    source = (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec"
        / "spec_governance"
        / "_journal_shapes.py"
    ).read_text(encoding="utf-8")
    assert "spec_governance.journal" not in source, (
        "the shapes module must not import from `journal`; keeping the "
        "dependency one-way is what prevents an import cycle"
    )


def test_journal_mutation_events_module_is_a_leaf() -> None:
    """The spec-mutation validators must not import back into `journal`.

    They take `_validate_common` and their shape helpers from
    `_journal_shapes`, the shared-primitives leaf, rather than from
    `journal`. That is what keeps the dependency one-way; importing the
    parent here would form a cycle.
    """
    source = (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec"
        / "spec_governance"
        / "_journal_mutation_events.py"
    ).read_text(encoding="utf-8")
    assert "spec_governance.journal" not in source, (
        "the mutation-events module must not import from `journal`; the "
        "one-way dependency is what prevents an import cycle"
    )


def test_every_journal_event_type_still_resolves_a_validator() -> None:
    """Every dispatch entry must name a validator that actually exists.

    The extraction moved three validators out and left the dispatch table
    behind, so a mis-wired import would surface only when that event type
    is journalled. This walks the table itself rather than trusting that
    the imports look right — an earlier pass of this refactor DID drop the
    table entirely, and only a runtime NameError revealed it.
    """
    from livespec.spec_governance import journal as journal_module

    table = journal_module._EVENT_VALIDATORS  # noqa: SLF001
    assert set(table) == {
        "authoring_auto_consumption",
        "doctor_disposition",
        "ratification_review",
        "revise_decision",
        "spec_pr_merge",
    }, f"dispatch table event types changed: {sorted(table)}"
    for event_type, validator in table.items():
        assert callable(validator), f"{event_type} maps to a non-callable"
        assert validator({}) is not None, (
            f"{event_type}'s validator accepted an empty event, which means it "
            f"is not actually reachable through the table"
        )
