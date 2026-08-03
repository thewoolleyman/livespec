"""Tests for livespec.commands._revise_ratification."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from livespec.commands._revise_helpers import _compose_revision_body
from livespec.commands._revise_ratification import (
    _canonical_ratification_digest,
    _validate_ratification_reviews,
)
from livespec.schemas.dataclasses.revise_input import RevisionInput
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []

_DEFAULT_EVIDENCE = object()


def test_canonical_ratification_digest_uses_length_prefixes() -> None:
    decision = {
        "resulting_files": [
            {"path": "a", "content": "bc"},
            {"path": "ab", "content": "c"},
        ],
    }
    expected = hashlib.sha256(b"1:a2:bc2:ab1:c").hexdigest()

    assert _canonical_ratification_digest(decision=decision) == expected


def test_canonical_ratification_digest_skips_malformed_runtime_shapes() -> None:
    empty = hashlib.sha256().hexdigest()

    assert _canonical_ratification_digest(decision={"resulting_files": "bad"}) == empty
    assert _canonical_ratification_digest(decision={"resulting_files": ["bad"]}) == empty


def test_validate_ratification_reviews_accepts_valid_evidence_with_configured_model(
    *,
    tmp_path: Path,
) -> None:
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance":{"ratification_reviewer_model":"fable"}}',
        encoding="utf-8",
    )
    resulting_files = [{"path": "spec.md", "content": "new"}]
    revise_input = _mutating_input(resulting_files=resulting_files)

    result = unsafe_perform_io(
        _validate_ratification_reviews(revise_input=revise_input, project_root=tmp_path),
    )

    assert result == Success(revise_input)


def test_validate_ratification_reviews_rejects_non_no_blockers_verdict(
    *,
    tmp_path: Path,
) -> None:
    resulting_files = [{"path": "spec.md", "content": "new"}]
    evidence = _evidence(resulting_files=resulting_files)
    evidence["verdict"] = "BLOCKERS"
    revise_input = RevisionInput(
        author=None,
        decisions=[
            {
                "proposal_topic": "demo",
                "decision": "accept",
                "rationale": ".",
                "resulting_files": resulting_files,
                "ratification_review": "auto-spawn",
                "ratification_evidence": evidence,
            },
        ],
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(revise_input=revise_input, project_root=tmp_path),
    )

    assert isinstance(result, Failure)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reviewer_identity", "other"),
        ("separate_reviewer", False),
        ("read_only", False),
        ("reviewed_at", "2026-08-03T12:34Z"),
        ("proposal_stem", "other"),
        ("content_digest", "bad"),
        ("content_digest", "0" * 64),
    ],
)
def test_validate_ratification_reviews_rejects_malformed_evidence_fields(
    *,
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    resulting_files = [{"path": "spec.md", "content": "new"}]
    evidence = _evidence(resulting_files=resulting_files)
    evidence[field] = value
    revise_input = _mutating_input(resulting_files=resulting_files, evidence=evidence)

    result = unsafe_perform_io(
        _validate_ratification_reviews(revise_input=revise_input, project_root=tmp_path),
    )

    assert isinstance(result, Failure)


def test_validate_ratification_reviews_rejects_missing_evidence_and_bad_mode(
    *,
    tmp_path: Path,
) -> None:
    resulting_files = [{"path": "spec.md", "content": "new"}]
    missing = _evidence(resulting_files=resulting_files)
    del missing["read_only"]
    bad_mode = _mutating_input(resulting_files=resulting_files, mode="bad")
    no_evidence = _mutating_input(resulting_files=resulting_files, evidence=None)
    missing_field = _mutating_input(resulting_files=resulting_files, evidence=missing)

    for revise_input in (bad_mode, no_evidence, missing_field):
        result = unsafe_perform_io(
            _validate_ratification_reviews(revise_input=revise_input, project_root=tmp_path),
        )
        assert isinstance(result, Failure)


def test_validate_ratification_reviews_rejects_configured_model_mismatch(
    *,
    tmp_path: Path,
) -> None:
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance":{"ratification_reviewer_model":"other"}}',
        encoding="utf-8",
    )
    resulting_files = [{"path": "spec.md", "content": "new"}]
    revise_input = _mutating_input(resulting_files=resulting_files)

    result = unsafe_perform_io(
        _validate_ratification_reviews(revise_input=revise_input, project_root=tmp_path),
    )

    assert isinstance(result, Failure)


def test_validate_ratification_reviews_allows_reject_without_evidence(
    *,
    tmp_path: Path,
) -> None:
    revise_input = RevisionInput(
        author=None,
        decisions=[
            {
                "proposal_topic": "demo",
                "decision": "reject",
                "rationale": ".",
            },
        ],
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(revise_input=revise_input, project_root=tmp_path),
    )

    assert result == Success(revise_input)


def test_validate_ratification_reviews_never_spawns_agents() -> None:
    source = Path(
        ".claude-plugin/scripts/livespec/commands/_revise_ratification.py",
    ).read_text(encoding="utf-8")

    assert "subprocess" not in source
    assert "Task(" not in source
    assert "fable" not in source.lower()


def test_compose_revision_body_handles_malformed_runtime_evidence_defensively() -> None:
    body = _compose_revision_body(
        decision={
            "proposal_topic": "demo",
            "decision": "accept",
            "rationale": ".",
            "resulting_files": [],
            "ratification_review": "manual-spawn",
            "ratification_evidence": "bad",
        },
        author_human="Human <human@example.com>",
        author_llm="llm",
        revised_at="2026-08-03T12:34:56Z",
    )

    assert "## Ratification Review\n\n(none)" in body


def _evidence(*, resulting_files: list[dict[str, str]]) -> dict[str, object]:
    decision = {"resulting_files": resulting_files}
    return {
        "reviewer_identity": "fable",
        "reviewer_model": "fable",
        "separate_reviewer": True,
        "read_only": True,
        "reviewed_at": "2026-08-03T12:34:56Z",
        "verdict": "NO BLOCKERS",
        "proposal_stem": "demo",
        "content_digest": _canonical_ratification_digest(decision=decision),
    }


def _mutating_input(
    *,
    resulting_files: list[dict[str, str]],
    mode: str = "auto-spawn",
    evidence: dict[str, object] | None | object = _DEFAULT_EVIDENCE,
) -> RevisionInput:
    decision: dict[str, object] = {
        "proposal_topic": "demo",
        "decision": "accept",
        "rationale": ".",
        "resulting_files": resulting_files,
        "ratification_review": mode,
    }
    if evidence is _DEFAULT_EVIDENCE:
        decision["ratification_evidence"] = _evidence(resulting_files=resulting_files)
    elif evidence is not None:
        decision["ratification_evidence"] = evidence
    return RevisionInput(author=None, decisions=[decision])
