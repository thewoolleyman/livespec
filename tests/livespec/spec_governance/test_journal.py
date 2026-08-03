"""Tests for spec-governance journal validation."""

from __future__ import annotations

import json
from pathlib import Path

from livespec.spec_governance.journal import JournalAppend, append_journal_event, digest_json_bytes

__all__: list[str] = []


def test_digest_json_bytes_is_deterministic() -> None:
    assert digest_json_bytes(payload={"b": 1, "a": 2}) == digest_json_bytes(
        payload={"a": 2, "b": 1},
    )


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
